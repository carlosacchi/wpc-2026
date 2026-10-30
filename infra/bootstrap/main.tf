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

variable "plan_oidc_subject" {
  type        = string
  description = "Exact GitHub OIDC sub for main without an environment, including immutable IDs if enabled. No wildcard."
  validation {
    condition     = startswith(var.plan_oidc_subject, "repo:") && endswith(var.plan_oidc_subject, ":ref:refs/heads/main") && !strcontains(var.plan_oidc_subject, "*")
    error_message = "Supply the exact main-branch subject, without an environment."
  }
}

variable "operator_object_id" {
  type        = string
  description = "Object ID of the dedicated human operator. No deployment federation is granted to GitHub."
  validation {
    condition     = can(regex("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$", var.operator_object_id))
    error_message = "Supply the Entra object ID of the human operator, not an application client ID."
  }
}

locals {
  scope = "/subscriptions/${var.subscription_id}/resourceGroups/wpc-2026"
  tags = {
    project     = "wpc-2026"
    environment = "sandbox"
    owner       = "platform-team"
    costCenter  = "WPC-LAB"
  }
}

resource "azurerm_storage_account" "state" {
  name                            = var.backend_storage_name
  resource_group_name             = "wpc-2026"
  location                        = "italynorth"
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
  resource_group_name = "wpc-2026"
  location            = "italynorth"
  tags                = local.tags
}

resource "azurerm_federated_identity_credential" "plan" {
  name                      = "github-plan"
  user_assigned_identity_id = azurerm_user_assigned_identity.plan.id
  issuer                    = "https://token.actions.githubusercontent.com"
  audience                  = ["api://AzureADTokenExchange"]
  subject                   = var.plan_oidc_subject
}

resource "azurerm_role_assignment" "plan_read" {
  scope                = local.scope
  role_definition_name = "Reader"
  principal_id         = azurerm_user_assigned_identity.plan.principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_role_assignment" "operator_storage" {
  scope                = local.scope
  role_definition_name = "Storage Account Contributor"
  principal_id         = var.operator_object_id
  principal_type       = "User"
}

resource "azurerm_role_assignment" "plan_state" {
  scope                = "${azurerm_storage_account.state.id}/blobServices/default/containers/${azurerm_storage_container.state.name}"
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.plan.principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_role_assignment" "operator_state" {
  scope                = "${azurerm_storage_account.state.id}/blobServices/default/containers/${azurerm_storage_container.state.name}"
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.operator_object_id
  principal_type       = "User"
}

resource "azurerm_resource_group_policy_assignment" "private_workloads" {
  name                 = "wpc-private-storage"
  resource_group_id    = local.scope
  policy_definition_id = "/providers/Microsoft.Authorization/policyDefinitions/b2982f36-99f2-4db5-8eff-283140c09693"
  display_name         = "WPC lab: disable public network for workload storage"
  description          = "Backend explicitly excluded for GitHub-hosted runner access. This is a lab exception, not private networking."
  enforce              = true
  not_scopes           = [azurerm_storage_account.state.id]
  parameters = jsonencode({
    effect = { value = "Deny" }
  })
}

output "backend_storage_name" { value = azurerm_storage_account.state.name }
output "plan_client_id" { value = azurerm_user_assigned_identity.plan.client_id }
output "operator_object_id" { value = var.operator_object_id }
output "tenant_id" { value = azurerm_user_assigned_identity.plan.tenant_id }
