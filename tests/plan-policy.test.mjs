import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
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

function renamePlan(actions = ["delete", "create"]) {
  const plan = baseline();
  const change = plan.resource_changes[0].change;
  change.actions = actions;
  change.before = { id: "/synthetic/storage/account", name: "originalstorage" };
  change.after.name = "renamedstorage";
  change.replace_paths = [["name"]];
  return plan;
}

for (const actions of [["delete", "create"], ["create", "delete"]]) {
  test(`rename CLI exposes real impact and rejects ${actions.join("/")}`, () => {
    const result = runGate(renamePlan(actions), "--expect-rename");
    assert.equal(result.status, 1);
    assert.match(result.stdout, /IMPACT:.*originalstorage.*renamedstorage/);
    assert.match(result.stdout, /OBSERVED: Terraform plans to replace/);
    assert.match(result.stderr, /DENY:.*replacement/);
  });
}

for (const [name, mutate] of [
  ["fresh creation", plan => { plan.resource_changes[0].change.actions = ["create"]; }],
  ["no original identity", plan => { delete plan.resource_changes[0].change.before.id; }],
  ["unchanged name", plan => { plan.resource_changes[0].change.after.name = "originalstorage"; }],
  ["unrelated replacement", plan => { plan.resource_changes[0].change.replace_paths = [["location"]]; }],
  ["extra resource", plan => { plan.resource_changes.push(plan.resource_changes[0]); }],
  ["wrong address", plan => { plan.resource_changes[0].address = "unexpected"; }],
  ["missing workload", plan => { plan.resource_changes = []; }]
]) {
  test(`rename CLI refuses to present ${name} as a name-driven replacement`, () => {
    const plan = renamePlan();
    mutate(plan);
    const result = runGate(plan, "--expect-rename");
    assert.equal(result.status, 1);
    assert.match(result.stderr, /ERROR: Expected an existing storage account/);
    assert.doesNotMatch(result.stdout, /OBSERVED:/);
  });
}

test("normal CLI still accepts a compliant creation and rejects unknown options", () => {
  assert.equal(runGate(baseline()).status, 0);
  assert.match(runGate(baseline(), "--skip-policy").stderr, /Usage:/);
});

function runGate(plan, ...args) {
  const directory = mkdtempSync(join(tmpdir(), "wpc-plan-gate-"));
  try {
    const path = join(directory, "plan.json");
    writeFileSync(path, JSON.stringify(plan));
    return spawnSync(process.execPath, ["scripts/check-plan.mjs", path, "sales", ...args], { encoding: "utf8" });
  } finally {
    rmSync(directory, { recursive: true });
  }
}
