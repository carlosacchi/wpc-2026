mock_provider "azurerm" {}

run "sales_baseline" {
  command = plan
  variables {
    subscription_id      = "00000000-0000-0000-0000-000000000001"
    team                 = "sales"
    storage_account_name = "wpcsalestest"
    cost_center          = "DEMO-SALES"
    owner                = "platform-team"
  }
  assert {
    condition     = module.storage.security.public_network_access == "Disabled" && !module.storage.security.shared_key_enabled && !module.storage.security.anonymous_enabled
    error_message = "Workload storage must disable public network, Shared Key and anonymous blob access."
  }
  assert {
    condition     = module.storage.security.tags.tenant == "sales" && module.storage.security.tags.costCenter == "DEMO-SALES"
    error_message = "Sales ownership tags must be preserved."
  }
}

run "operations_baseline" {
  command = plan
  variables {
    subscription_id      = "00000000-0000-0000-0000-000000000001"
    team                 = "operations"
    storage_account_name = "wpcoperationstest"
    cost_center          = "DEMO-OPS"
    owner                = "platform-team"
  }
  assert {
    condition     = module.storage.security.public_network_access == "Disabled" && module.storage.security.tags.tenant == "operations"
    error_message = "Operations must use the same network baseline and its own tenant tag."
  }
}

run "reject_unknown_team" {
  command = plan
  variables {
    subscription_id      = "00000000-0000-0000-0000-000000000001"
    team                 = "other"
    storage_account_name = "wpcinvalidtest"
    cost_center          = "DEMO"
    owner                = "platform-team"
  }
  expect_failures = [var.team]
}
