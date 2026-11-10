import test from "node:test";
import assert from "node:assert/strict";
import { checkWhatIf } from "../scripts/whatif-policy.mjs";

const rgId = rg => `/subscriptions/00000000-0000-0000-0000-000000000001/resourceGroups/${rg}`;
const storageId = (name, rg = "wpc-2026-sales") => `${rgId(rg)}/providers/Microsoft.Storage/storageAccounts/${name}`;

function storage(team = "sales") {
  return {
    location: "italynorth", kind: "StorageV2", sku: { name: "Standard_LRS" },
    properties: {
      publicNetworkAccess: "Disabled", allowSharedKeyAccess: false, allowBlobPublicAccess: false,
      supportsHttpsTrafficOnly: true, minimumTlsVersion: "TLS1_2"
    },
    tags: { project: "wpc-2026", environment: "sandbox", tenant: team, costCenter: "DEMO", owner: "platform" }
  };
}

function baseline(changeType = "Create", team = "sales", rg = "wpc-2026-sales") {
  return { status: "Succeeded", changes: [{ resourceId: storageId("syntheticstore", rg), changeType, after: storage(team) }] };
}

for (const changeType of ["Create", "Modify", "NoChange"]) {
  test(`accepts compliant ${changeType}`, () => assert.deepEqual(checkWhatIf(baseline(changeType), "sales"), []));
}
test("accepts operations in its own resource group", () => {
  assert.deepEqual(checkWhatIf(baseline("Create", "operations", "wpc-2026-operations"), "operations"), []);
});
test("ignores unrelated non-storage resources left outside the template", () => {
  const result = baseline("NoChange");
  result.changes.push({ resourceId: `${rgId("wpc-2026-sales")}/providers/Microsoft.Insights/components/other`, changeType: "Ignore" });
  assert.deepEqual(checkWhatIf(result, "sales"), []);
});
test("rejects implicit rename that would orphan the original storage", () => {
  const result = baseline("Create");
  result.changes.push({ resourceId: storageId("originalstore"), changeType: "Ignore" });
  assert.ok(checkWhatIf(result, "sales").some(message => message.includes("orphan")));
});
for (const [name, mutate] of [
  ["delete", r => { r.changes[0].changeType = "Delete"; }],
  ["deploy (not evaluable)", r => { r.changes[0].changeType = "Deploy"; }],
  ["unsupported", r => { r.changes[0].changeType = "Unsupported"; }],
  ["unknown change type", r => { r.changes[0].changeType = "Explode"; }],
  ["public network", r => { r.changes[0].after.properties.publicNetworkAccess = "Enabled"; }],
  ["shared key", r => { r.changes[0].after.properties.allowSharedKeyAccess = true; }],
  ["cross-tenant tag", r => { r.changes[0].after.tags.tenant = "operations"; }],
  ["wrong region", r => { r.changes[0].after.location = "westeurope"; }],
  ["non-wpc resource group", r => { r.changes[0].resourceId = storageId("syntheticstore", "production"); }],
  ["other tenant resource group", r => { r.changes[0].resourceId = storageId("syntheticstore", "wpc-2026-operations"); }],
  ["unexpected type", r => { r.changes[0].resourceId = `${rgId("wpc-2026-sales")}/providers/Microsoft.Web/sites/app`; }],
  ["malformed resource ID", r => { r.changes[0].resourceId = "storage"; }],
  ["missing workload", r => { r.changes = []; }],
  ["two workloads", r => { r.changes.push({ ...r.changes[0], resourceId: storageId("second") }); }]
]) {
  test(`rejects ${name}`, () => {
    const result = baseline();
    mutate(result);
    assert.ok(checkWhatIf(result, "sales").length > 0);
  });
}
test("rejects failed or malformed What-If results", () => {
  for (const result of [null, {}, { ...baseline(), status: "Failed" }, { ...baseline(), error: { code: "X" } }]) {
    assert.throws(() => checkWhatIf(result, "sales"));
  }
});
test("rejects unsupported teams", () => assert.throws(() => checkWhatIf(baseline(), "production")));
