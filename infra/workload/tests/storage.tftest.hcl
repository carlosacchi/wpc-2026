mock_provider "azurerm" {}

run "sales_baseline" {
  command = plan
  variables {
    subscription_id      = "00000000-0000-0000-0000-000000000001"
    team                 = "sales"
    resource_group_name  = jsondecode(file("teams/sales.tfvars.json")).resource_group_name
    storage_account_name = jsondecode(file("teams/sales.tfvars.json")).storage_account_name
    cost_center          = jsondecode(file("teams/sales.tfvars.json")).cost_center
    owner                = jsondecode(file("teams/sales.tfvars.json")).owner
    service_label        = jsondecode(file("teams/sales.tfvars.json")).service_label
  }
  assert {
    condition     = module.storage.security.public_network_access == "Disabled" && !module.storage.security.shared_key_enabled && !module.storage.security.anonymous_enabled
    error_message = "Workload storage must disable public network, Shared Key and anonymous blob access."
  }
  assert {
    condition     = module.storage.security.tags.tenant == "sales" && module.storage.security.tags.costCenter == "WPC-SALES" && module.storage.security.tags.serviceLabel == jsondecode(file("teams/sales.tfvars.json")).service_label
    error_message = "Sales ownership tags must be preserved."
  }
}

run "operations_baseline" {
  command = plan
  variables {
    subscription_id      = "00000000-0000-0000-0000-000000000001"
    team                 = "operations"
    resource_group_name  = jsondecode(file("teams/operations.tfvars.json")).resource_group_name
    storage_account_name = jsondecode(file("teams/operations.tfvars.json")).storage_account_name
    cost_center          = jsondecode(file("teams/operations.tfvars.json")).cost_center
    owner                = jsondecode(file("teams/operations.tfvars.json")).owner
    service_label        = jsondecode(file("teams/operations.tfvars.json")).service_label
  }
  assert {
    condition     = module.storage.security.public_network_access == "Disabled" && module.storage.security.tags.tenant == "operations"
    error_message = "Operations must use the same network baseline and its own tenant tag."
  }
}

run "preserve_tags_when_service_label_omitted" {
  command = plan
  variables {
    subscription_id      = "00000000-0000-0000-0000-000000000001"
    team                 = "sales"
    resource_group_name  = "wpc-2026-sales"
    storage_account_name = "wpcsalestest"
    cost_center          = "DEMO-SALES"
    owner                = "platform-team"
  }
  assert {
    condition     = !contains(keys(module.storage.security.tags), "serviceLabel")
    error_message = "Omitting service_label must preserve the previous tag set."
  }
}

run "reject_unknown_team" {
  command = plan
  variables {
    subscription_id      = "00000000-0000-0000-0000-000000000001"
    team                 = "other"
    resource_group_name  = "wpc-2026-sales"
    storage_account_name = "wpcinvalidtest"
    cost_center          = "DEMO"
    owner                = "platform-team"
  }
  expect_failures = [var.team]
}

run "reject_resource_group_outside_lab_boundary" {
  command = plan
  variables {
    subscription_id      = "00000000-0000-0000-0000-000000000001"
    team                 = "sales"
    resource_group_name  = "rg-production"
    storage_account_name = "wpcsalestest"
    cost_center          = "DEMO-SALES"
    owner                = "platform-team"
  }
  expect_failures = [var.resource_group_name]
}

run "reject_shared_lab_resource_group" {
  command = plan
  variables {
    subscription_id      = "00000000-0000-0000-0000-000000000001"
    team                 = "sales"
    resource_group_name  = "wpc-2026"
    storage_account_name = "wpcsalestest"
    cost_center          = "DEMO-SALES"
    owner                = "platform-team"
  }
  expect_failures = [var.resource_group_name]
}
