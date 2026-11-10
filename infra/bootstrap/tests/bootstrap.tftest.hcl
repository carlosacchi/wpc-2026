mock_provider "azurerm" {
  mock_resource "azurerm_resource_group" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/wpc-mock" }
  }
  mock_resource "azurerm_storage_account" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/wpc-2026/providers/Microsoft.Storage/storageAccounts/wpcstatetest" }
  }
  mock_resource "azurerm_storage_container" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/wpc-2026/providers/Microsoft.Storage/storageAccounts/wpcstatetest/blobServices/default/containers/tfstate-mock" }
  }
  mock_resource "azurerm_user_assigned_identity" {
    defaults = {
      id           = "/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/wpc-2026/providers/Microsoft.ManagedIdentity/userAssignedIdentities/wpc-mock"
      principal_id = "00000000-0000-0000-0000-000000000003"
    }
  }
  mock_resource "azurerm_policy_definition" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000001/providers/Microsoft.Authorization/policyDefinitions/wpc-2026-deny-storage-delete" }
  }
  mock_resource "azurerm_role_definition" {
    defaults = { role_definition_resource_id = "/subscriptions/00000000-0000-0000-0000-000000000001/providers/Microsoft.Authorization/roleDefinitions/00000000-0000-0000-0000-000000000004" }
  }
}

variables {
  subscription_id            = "00000000-0000-0000-0000-000000000001"
  backend_storage_name       = "wpcstatetest"
  github_oidc_subject_prefix = "repo:example/lab"
}

run "bootstrap_boundaries" {
  command = plan
  assert {
    condition     = azurerm_storage_account.state.public_network_access == "Enabled" && !azurerm_storage_account.state.shared_access_key_enabled && !azurerm_storage_account.state.allow_nested_items_to_be_public
    error_message = "The backend exception must not enable Shared Key or anonymous access."
  }
  assert {
    condition     = azurerm_role_assignment.plan_read.role_definition_name == "Reader" && azurerm_federated_identity_credential.plan.subject == "repo:example/lab:ref:refs/heads/main"
    error_message = "The plan identity must stay read-only and bound to main without an environment."
  }
  assert {
    condition     = length(azurerm_resource_group_policy_assignment.private_workloads.not_scopes) == 1 && jsondecode(azurerm_resource_group_policy_assignment.private_workloads.parameters).effect.value == "Deny"
    error_message = "Exactly one explicit backend exception and an enforcing Deny are required."
  }
}

run "tenant_isolation_and_delete_protection" {
  # Mocked apply: the provider is mocked, so IDs are synthetic and no Azure call is made.
  command = apply
  assert {
    condition     = alltrue([for group in azurerm_resource_group.tenant : startswith(group.name, "wpc-") && group.name != "wpc-2026"])
    error_message = "Every tenant resource group must be a dedicated wpc-* group."
  }
  assert {
    condition     = length(azurerm_management_lock.tenant) == length(var.tenants) && alltrue([for lock in azurerm_management_lock.tenant : lock.lock_level == "CanNotDelete"]) && azurerm_management_lock.state.lock_level == "CanNotDelete"
    error_message = "Every tenant resource group and the state backend need a CanNotDelete lock."
  }
  assert {
    condition     = jsondecode(azurerm_policy_definition.deny_storage_delete.policy_rule).then.details.actionNames == ["delete"] && jsondecode(azurerm_policy_definition.deny_storage_delete.policy_rule).then.details.cascadeBehaviors.resourceGroup == "deny" && jsondecode(azurerm_policy_definition.deny_storage_delete.parameters).effect.defaultValue == "DenyAction"
    error_message = "Lab storage needs a denyAction on delete, including resource group cascade."
  }
  assert {
    condition     = toset(keys(azurerm_resource_group_policy_assignment.deny_storage_delete)) == toset(concat(["lab"], keys(var.tenants))) && alltrue([for a in azurerm_resource_group_policy_assignment.deny_storage_delete : a.enforce])
    error_message = "denyAction must be enforced on the shared lab group and on every tenant group."
  }
  assert {
    condition     = alltrue([for a in azurerm_resource_group_policy_assignment.tenant_private_storage : jsondecode(a.parameters).effect.value == "Deny" && a.enforce])
    error_message = "Every tenant group must deny public storage."
  }
  assert {
    condition = alltrue([for key, cred in azurerm_federated_identity_credential.apply :
      cred.subject == "repo:example/lab:environment:${key}" &&
      azurerm_role_assignment.apply_storage[key].role_definition_name == "Storage Account Contributor" &&
      azurerm_role_assignment.apply_storage[key].scope == azurerm_resource_group.tenant[key].id &&
      azurerm_role_assignment.apply_state[key].scope == azurerm_storage_container.tenant_state[key].id
    ])
    error_message = "Each apply identity must be bound to its own GitHub environment, resource group and state container only."
  }
  assert {
    condition     = toset(one(azurerm_role_definition.whatif.permissions).actions) == toset(["Microsoft.Resources/deployments/whatIf/action", "Microsoft.Resources/deployments/validate/action"])
    error_message = "The What-If role must not grant any write action."
  }
}

run "reject_non_lab_resource_group" {
  command = plan
  variables {
    tenants = { sales = { resource_group_name = "rg-production" } }
  }
  expect_failures = [var.tenants]
}

run "reject_shared_lab_resource_group_for_tenant" {
  command = plan
  variables {
    tenants = { sales = { resource_group_name = "wpc-2026" } }
  }
  expect_failures = [var.tenants]
}

run "reject_unknown_tenant" {
  command = plan
  variables {
    tenants = { finance = { resource_group_name = "wpc-2026-finance" } }
  }
  expect_failures = [var.tenants]
}

run "reject_wildcard_or_ref_in_subject_prefix" {
  command = plan
  variables {
    github_oidc_subject_prefix = "repo:example/*:ref:refs/heads/main"
  }
  expect_failures = [var.github_oidc_subject_prefix]
}
