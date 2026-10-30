terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
    }
  }
}

variable "name" { type = string }
variable "resource_group_name" { type = string }
variable "location" { type = string }
variable "team" { type = string }
variable "cost_center" { type = string }
variable "owner" { type = string }
variable "service_label" {
  type    = string
  default = ""
}

resource "azurerm_storage_account" "this" {
  name                            = var.name
  resource_group_name             = var.resource_group_name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  account_kind                    = "StorageV2"
  public_network_access           = "Disabled"
  shared_access_key_enabled       = false
  allow_nested_items_to_be_public = false
  https_traffic_only_enabled      = true
  min_tls_version                 = "TLS1_2"
  tags = merge({
    project     = "wpc-2026"
    environment = "sandbox"
    tenant      = var.team
    costCenter  = var.cost_center
    owner       = var.owner
  }, var.service_label == "" ? {} : { serviceLabel = var.service_label })
}

output "id" {
  value = azurerm_storage_account.this.id
}

output "security" {
  value = {
    public_network_access = azurerm_storage_account.this.public_network_access
    shared_key_enabled    = azurerm_storage_account.this.shared_access_key_enabled
    anonymous_enabled     = azurerm_storage_account.this.allow_nested_items_to_be_public
    tags                  = azurerm_storage_account.this.tags
  }
}
