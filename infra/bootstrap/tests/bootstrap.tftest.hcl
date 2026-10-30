mock_provider "azurerm" {}

variables {
  subscription_id      = "00000000-0000-0000-0000-000000000001"
  backend_storage_name = "wpcstatetest"
  plan_oidc_subject    = "repo:example/lab:ref:refs/heads/main"
  operator_object_id   = "00000000-0000-0000-0000-000000000002"
}

run "bootstrap_boundaries" {
  command = plan
  assert {
    condition     = azurerm_storage_account.state.public_network_access == "Enabled" && !azurerm_storage_account.state.shared_access_key_enabled && !azurerm_storage_account.state.allow_nested_items_to_be_public
    error_message = "The backend exception must not enable Shared Key or anonymous access."
  }

  assert {
    condition     = azurerm_role_assignment.plan_read.role_definition_name == "Reader" && azurerm_role_assignment.operator_storage.role_definition_name == "Storage Account Contributor" && azurerm_role_assignment.operator_storage.principal_type == "User" && azurerm_role_assignment.operator_storage.principal_id == var.operator_object_id && azurerm_federated_identity_credential.plan.subject == var.plan_oidc_subject
    error_message = "Planning and application must have different control-plane roles."
  }
  assert {
    condition     = length(azurerm_resource_group_policy_assignment.private_workloads.not_scopes) == 1 && jsondecode(azurerm_resource_group_policy_assignment.private_workloads.parameters).effect.value == "Deny"
    error_message = "Exactly one explicit backend exception and an enforcing Deny are required."
  }
}

run "reject_non_main_subject" {
  command = plan
  variables {
    plan_oidc_subject = "repo:example/lab:ref:refs/heads/feature"
  }
  expect_failures = [var.plan_oidc_subject]
}

run "reject_invalid_operator_id" {
  command = plan
  variables {
    operator_object_id = "not-an-object-id"
  }
  expect_failures = [var.operator_object_id]
}
