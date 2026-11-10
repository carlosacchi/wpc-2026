import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { diffTeams, baselineDir, teamsDir } from "../scripts/demo-reset.mjs";
import { tenantResourceGroups } from "../scripts/plan-policy.mjs";

const files = overrides => {
  const map = {};
  for (const team of Object.keys(tenantResourceGroups)) {
    const base = JSON.parse(readFileSync(`${baselineDir}/${team}.tfvars.json`, "utf8"));
    map[`${baselineDir}/${team}.tfvars.json`] = JSON.stringify(base);
    map[`${teamsDir}/${team}.tfvars.json`] = JSON.stringify({ ...base, ...overrides[team] });
  }
  return [path => map[path], () => Object.keys(tenantResourceGroups).map(t => `${t}.tfvars.json`)];
};

test("versioned baseline keeps the same shape and tenant boundaries as the team files", () => {
  for (const [team, group] of Object.entries(tenantResourceGroups)) {
    const baseline = JSON.parse(readFileSync(`${baselineDir}/${team}.tfvars.json`, "utf8"));
    const live = JSON.parse(readFileSync(`${teamsDir}/${team}.tfvars.json`, "utf8"));
    assert.deepEqual(Object.keys(baseline).sort(), Object.keys(live).sort());
    assert.equal(baseline.resource_group_name, group);
    assert.match(baseline.storage_account_name, /^[a-z0-9]{3,24}$/);
  }
});

test("aligned team files report no drift", () => {
  assert.deepEqual(diffTeams(...files({})), []);
});

test("demo edits (rename and service label) are reported for reset", () => {
  const drift = diffTeams(...files({ sales: { storage_account_name: "wpc26salesb0b966r", service_label: "sales-analytics" } }));
  assert.deepEqual(drift.map(d => `${d.team}.${d.key}`), ["sales.service_label", "sales.storage_account_name"]);
});

test("added or removed keys are drift too", () => {
  const drift = diffTeams(...files({ operations: { extra: "x" } }));
  assert.deepEqual(drift.map(d => `${d.team}.${d.key}`), ["operations.extra"]);
});

test("a baseline outside the tenant boundary is refused", () => {
  const [read, list] = files({});
  const tampered = path => path === `${baselineDir}/sales.tfvars.json`
    ? JSON.stringify({ ...JSON.parse(read(path)), resource_group_name: "wpc-2026" }) : read(path);
  assert.throws(() => diffTeams(tampered, list), /baseline resource group must be wpc-2026-sales/);
});

test("baseline directory must contain exactly the known tenants", () => {
  const [read] = files({});
  assert.throws(() => diffTeams(read, () => ["sales.tfvars.json"]), /must contain exactly/);
});
