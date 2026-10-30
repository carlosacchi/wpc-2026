import test from "node:test";
import assert from "node:assert/strict";
import { checkPlan } from "../scripts/plan-policy.mjs";

function baseline(team = "sales") {
  return {
    format_version: "1.2",
    complete: true,
    resource_changes: [{
      mode: "managed",
      address: "module.storage.azurerm_storage_account.this",
      type: "azurerm_storage_account",
      change: {
        actions: ["create"],
        after_unknown: {},
        after: {
          resource_group_name: "wpc-2026", location: "italynorth",
          account_tier: "Standard", account_replication_type: "LRS", account_kind: "StorageV2",
          public_network_access: "Disabled", shared_access_key_enabled: false,
          allow_nested_items_to_be_public: false, https_traffic_only_enabled: true,
          min_tls_version: "TLS1_2",
          tags: { project: "wpc-2026", environment: "sandbox", tenant: team, costCenter: "DEMO", owner: "platform" }
        }
      }
    }]
  };
}

for (const team of ["sales", "operations"]) {
  test(`accepts compliant ${team} plan`, () => assert.deepEqual(checkPlan(baseline(team), team), []));
}
for (const [name, mutate] of [
  ["public network", p => { p.resource_changes[0].change.after.public_network_access = "Enabled"; }],
  ["missing costCenter", p => { delete p.resource_changes[0].change.after.tags.costCenter; }],
  ["empty owner", p => { p.resource_changes[0].change.after.tags.owner = " "; }],
  ["shared key", p => { p.resource_changes[0].change.after.shared_access_key_enabled = true; }],
  ["unknown network", p => { p.resource_changes[0].change.after_unknown.public_network_access = true; }],
  ["unknown tags", p => { p.resource_changes[0].change.after_unknown.tags = true; }],
  ["cross-team tags", p => { p.resource_changes[0].change.after.tags.tenant = "operations"; }],
  ["wrong region", p => { p.resource_changes[0].change.after.location = "westeurope"; }],
  ["wrong scope", p => { p.resource_changes[0].change.after.resource_group_name = "production"; }],
  ["delete", p => { p.resource_changes[0].change.actions = ["delete"]; }],
  ["replacement", p => { p.resource_changes[0].change.actions = ["delete", "create"]; }],
  ["unreviewed resource", p => { p.resource_changes.push({ ...p.resource_changes[0], address: "unexpected" }); }],
  ["missing workload", p => { p.resource_changes = []; }],
  ["missing after", p => { p.resource_changes[0].change.after = null; }],
  ["empty actions", p => { p.resource_changes[0].change.actions = []; }]
]) {
  test(`rejects ${name}`, () => {
    const plan = baseline();
    mutate(plan);
    assert.ok(checkPlan(plan, "sales").length > 0);
  });
}
test("rejects malformed, errored and partial plans", () => {
  for (const plan of [null, {}, { ...baseline(), errored: true }, { ...baseline(), complete: false }]) {
    assert.throws(() => checkPlan(plan, "sales"));
  }
});
test("rejects unsupported teams", () => assert.throws(() => checkPlan(baseline(), "production")));
