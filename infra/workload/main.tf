variable "subscription_id" {
  type = string
}

variable "team" {
  type = string
  validation {
    condition     = contains(["sales", "operations"], var.team)
    error_message = "team must be sales or operations."
  }
}

variable "storage_account_name" {
  type = string
  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.storage_account_name))
    error_message = "Use a globally unique, lowercase alphanumeric storage name (3-24 characters)."
  }
}

variable "cost_center" {
  type = string
  validation {
    condition     = length(trimspace(var.cost_center)) > 0
    error_message = "cost_center must not be empty."
  }
}

variable "owner" {
  type = string
  validation {
    condition     = length(trimspace(var.owner)) > 0
    error_message = "owner must not be empty."
  }
}

variable "service_label" {
  type    = string
  default = ""
}

module "storage" {
  source              = "../modules/workload-storage"
  name                = var.storage_account_name
  resource_group_name = "wpc-2026"
  location            = "italynorth"
  team                = var.team
  cost_center         = var.cost_center
  owner               = var.owner
  service_label       = var.service_label
}

output "storage_account_id" {
  value = module.storage.id
}
