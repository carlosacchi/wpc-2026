import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { tenantResourceGroups } from "../scripts/plan-policy.mjs";

test("bootstrap defaults, team files and gate agree on tenant resource groups", () => {
  const bootstrap = readFileSync("infra/bootstrap/main.tf", "utf8");
  for (const [team, group] of Object.entries(tenantResourceGroups)) {
    assert.match(bootstrap, new RegExp(`${team}\\s*=\\s*\\{\\s*resource_group_name\\s*=\\s*"${group}"\\s*\\}`));
    const config = JSON.parse(readFileSync(`infra/workload/teams/${team}.tfvars.json`, "utf8"));
    assert.equal(config.resource_group_name, group);
  }
});

test("rollout applies only through tenant environments and never from pull requests", () => {
  const ring = readFileSync(".github/workflows/tenant-ring.yml", "utf8");
  const rollout = readFileSync(".github/workflows/rollout.yml", "utf8");
  assert.match(ring, /environment:\s*\n\s*name:\s*\$\{\{\s*inputs\.team\s*\}\}/);
  assert.equal((ring.match(/terraform -chdir=infra\/workload apply/g) ?? []).length, 1);
  assert.match(ring, /--validation-level ProviderNoRbac/);
  assert.doesNotMatch(rollout, /pull_request/);
  assert.match(rollout, /needs:\s*ring0/);
});
