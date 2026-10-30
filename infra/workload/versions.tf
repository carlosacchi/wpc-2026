terraform {
  required_version = ">= 1.14.9, < 2.0.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.12.0"
    }
  }
  backend "azurerm" {}
}

provider "azurerm" {
  features {
    storage {
      data_plane_available = false
    }
  }
  subscription_id                 = var.subscription_id
  resource_provider_registrations = "none"
  storage_use_azuread             = true
}
