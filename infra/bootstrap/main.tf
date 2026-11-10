terraform {
  required_version = ">= 1.14.9, < 2.0.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.12.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id                 = var.subscription_id
  resource_provider_registrations = "none"
  storage_use_azuread             = true
}

variable "subscription_id" {
  type = string
}

variable "backend_storage_name" {
  type = string
  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.backend_storage_name))
    error_message = "Use a globally unique lowercase alphanumeric storage name (3-24 characters)."
  }
}

variable "github_oidc_subject_prefix" {
  type        = string
  description = "Exact repository part of the GitHub OIDC sub, e.g. repo:OWNER@ID/REPO@ID when immutable IDs are enabled. No wildcard."
  validation {
    condition     = can(regex("^repo:[^:*]+$", var.github_oidc_subject_prefix))
    error_message = "Supply the repository prefix of the real OIDC subject, without ref, environment or wildcard."
  }
}

variable "tenants" {
  type = map(object({
    resource_group_name = string
  }))
  description = "Simulated tenants. Each one gets its own resource group, state container, apply identity and GitHub environment."
  default = {
    sales      = { resource_group_name = "wpc-2026-sales" }
    operations = { resource_group_name = "wpc-2026-operations" }
  }
  validation {
    condition = length(var.tenants) > 0 && alltrue([
      for key, tenant in var.tenants :
      contains(["sales", "operations"], key) &&
      can(regex("^wpc-[a-z0-9-]{1,86}$", tenant.resource_group_name)) &&
      tenant.resource_group_name != "wpc-2026"
    ])
    error_message = "Tenants must be sales/operations and every new resource group must be a dedicated wpc-* group, never the shared lab group."
  }
}

locals {
  lab_resource_group = "wpc-2026"
  lab_scope          = "/subscriptions/${var.subscription_id}/resourceGroups/${local.lab_resource_group}"
  location           = "italynorth"
  tags = {
    project     = "wpc-2026"
    environment = "sandbox"
    owner       = "platform-team"
    costCenter  = "WPC-LAB"
  }
  lock_note = "WPC lab: deletes and replacements require a separate, approved cleanup change."
}

resource "azurerm_storage_account" "state" {
  name                            = var.backend_storage_name
  resource_group_name             = local.lab_resource_group
  location                        = local.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  account_kind                    = "StorageV2"
  public_network_access           = "Enabled"
  shared_access_key_enabled       = false
  allow_nested_items_to_be_public = false
  https_traffic_only_enabled      = true
  min_tls_version                 = "TLS1_2"
  default_to_oauth_authentication = true
  tags                            = merge(local.tags, { purpose = "terraform-state" })
  lifecycle {
    prevent_destroy = true
  }
}

resource "azurerm_storage_container" "state" {
  name                  = "tfstate"
  storage_account_id    = azurerm_storage_account.state.id
  container_access_type = "private"
}

resource "azurerm_user_assigned_identity" "plan" {
  name                = "wpc-2026-plan"
  resource_group_name = local.lab_resource_group
  location            = local.location
  tags                = local.tags
}

resource "azurerm_federated_identity_credential" "plan" {
  name                      = "github-plan"
  user_assigned_identity_id = azurerm_user_assigned_identity.plan.id
  issuer                    = "https://token.actions.githubusercontent.com"
  audience                  = ["api://AzureADTokenExchange"]
  subject                   = "${var.github_oidc_subject_prefix}:ref:refs/heads/main"
}

resource "azurerm_role_assignment" "plan_read" {
  scope                = local.lab_scope
  role_definition_name = "Reader"
  principal_id         = azurerm_user_assigned_identity.plan.principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_resource_group_policy_assignment" "private_workloads" {
  name                 = "wpc-private-storage"
  resource_group_id    = local.lab_scope
  policy_definition_id = "/providers/Microsoft.Authorization/policyDefinitions/b2982f36-99f2-4db5-8eff-283140c09693"
  display_name         = "WPC lab: disable public network for workload storage"
  description          = "Backend explicitly excluded for GitHub-hosted runner access. This is a lab exception, not private networking."
  enforce              = true
  not_scopes           = [azurerm_storage_account.state.id]
  parameters = jsonencode({
    effect = { value = "Deny" }
  })
}

resource "azurerm_management_lock" "state" {
  name       = "wpc-no-delete"
  scope      = azurerm_storage_account.state.id
  lock_level = "CanNotDelete"
  notes      = local.lock_note
}

# --- Simulated tenants: one resource group, state container and apply identity each ---

resource "azurerm_resource_group" "tenant" {
  for_each = var.tenants
  name     = each.value.resource_group_name
  location = local.location
  tags     = merge(local.tags, { tenant = each.key })
  lifecycle {
    prevent_destroy = true
  }
}

resource "azurerm_management_lock" "tenant" {
  for_each   = azurerm_resource_group.tenant
  name       = "wpc-no-delete"
  scope      = each.value.id
  lock_level = "CanNotDelete"
  notes      = local.lock_note
}

resource "azurerm_storage_container" "tenant_state" {
  for_each              = var.tenants
  name                  = "tfstate-${each.key}"
  storage_account_id    = azurerm_storage_account.state.id
  container_access_type = "private"
}

resource "azurerm_user_assigned_identity" "apply" {
  for_each            = var.tenants
  name                = "wpc-2026-apply-${each.key}"
  resource_group_name = local.lab_resource_group
  location            = local.location
  tags                = merge(local.tags, { tenant = each.key })
}

resource "azurerm_federated_identity_credential" "apply" {
  for_each                  = var.tenants
  name                      = "github-env-${each.key}"
  user_assigned_identity_id = azurerm_user_assigned_identity.apply[each.key].id
  issuer                    = "https://token.actions.githubusercontent.com"
  audience                  = ["api://AzureADTokenExchange"]
  subject                   = "${var.github_oidc_subject_prefix}:environment:${each.key}"
}

resource "azurerm_role_assignment" "apply_storage" {
  for_each             = var.tenants
  scope                = azurerm_resource_group.tenant[each.key].id
  role_definition_name = "Storage Account Contributor"
  principal_id         = azurerm_user_assigned_identity.apply[each.key].principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_role_assignment" "apply_state" {
  for_each             = var.tenants
  scope                = azurerm_storage_container.tenant_state[each.key].id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.apply[each.key].principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_role_assignment" "plan_tenant_read" {
  for_each             = var.tenants
  scope                = azurerm_resource_group.tenant[each.key].id
  role_definition_name = "Reader"
  principal_id         = azurerm_user_assigned_identity.plan.principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_role_assignment" "plan_tenant_state" {
  for_each             = var.tenants
  scope                = azurerm_storage_container.tenant_state[each.key].id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.plan.principal_id
  principal_type       = "ServicePrincipal"
}

# Used with `az deployment group what-if --validation-level ProviderNoRbac`: preview only, no write actions.
resource "azurerm_role_definition" "whatif" {
  name        = "wpc-2026 What-If preview"
  scope       = "/subscriptions/${var.subscription_id}"
  description = "WPC lab: run ARM/Bicep What-If on tenant resource groups without any write permission."
  permissions {
    actions = [
      "Microsoft.Resources/deployments/whatIf/action",
      "Microsoft.Resources/deployments/validate/action",
    ]
  }
  assignable_scopes = [for group in azurerm_resource_group.tenant : group.id]
}

resource "azurerm_role_assignment" "plan_whatif" {
  for_each           = var.tenants
  scope              = azurerm_resource_group.tenant[each.key].id
  role_definition_id = azurerm_role_definition.whatif.role_definition_resource_id
  principal_id       = azurerm_user_assigned_identity.plan.principal_id
  principal_type     = "ServicePrincipal"
}

resource "azurerm_resource_group_policy_assignment" "tenant_private_storage" {
  for_each             = azurerm_resource_group.tenant
  name                 = "wpc-private-storage"
  resource_group_id    = each.value.id
  policy_definition_id = "/providers/Microsoft.Authorization/policyDefinitions/b2982f36-99f2-4db5-8eff-283140c09693"
  display_name         = "WPC lab: disable public network for ${each.key} storage"
  enforce              = true
  parameters = jsonencode({
    effect = { value = "Deny" }
  })
}

# Platform-level backstop: even a plan that bypasses the CI gate cannot delete or replace lab storage.
resource "azurerm_policy_definition" "deny_storage_delete" {
  name         = "wpc-2026-deny-storage-delete"
  policy_type  = "Custom"
  mode         = "Indexed"
  display_name = "WPC lab: deny delete of lab storage accounts"
  description  = "denyAction on DELETE for storage accounts tagged project=wpc-2026, including resource group cascade."
  parameters = jsonencode({
    effect = {
      type          = "String"
      allowedValues = ["DenyAction", "Disabled"]
      defaultValue  = "DenyAction"
    }
  })
  policy_rule = jsonencode({
    if = {
      allOf = [
        { field = "type", equals = "Microsoft.Storage/storageAccounts" },
        { field = "tags['project']", equals = "wpc-2026" },
      ]
    }
    then = {
      effect = "[parameters('effect')]"
      details = {
        actionNames      = ["delete"]
        cascadeBehaviors = { resourceGroup = "deny" }
      }
    }
  })
}

resource "azurerm_resource_group_policy_assignment" "deny_storage_delete" {
  for_each             = merge({ lab = local.lab_scope }, { for key, group in azurerm_resource_group.tenant : key => group.id })
  name                 = "wpc-deny-storage-delete"
  resource_group_id    = each.value
  policy_definition_id = azurerm_policy_definition.deny_storage_delete.id
  display_name         = "WPC lab: deny delete of lab storage (${each.key})"
  enforce              = true
}

output "backend_storage_name" { value = azurerm_storage_account.state.name }
output "plan_client_id" { value = azurerm_user_assigned_identity.plan.client_id }
output "apply_client_ids" { value = { for key, identity in azurerm_user_assigned_identity.apply : key => identity.client_id } }
output "tenant_resource_groups" { value = { for key, group in azurerm_resource_group.tenant : key => group.name } }
output "tenant_id" { value = azurerm_user_assigned_identity.plan.tenant_id }
