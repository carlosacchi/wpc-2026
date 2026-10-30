import { readFile } from "node:fs/promises";
import { checkPlan } from "./plan-policy.mjs";

try {
  const [path] = process.argv.slice(2);
  if (!path) throw new Error("Usage: node scripts/check-mock-plans.mjs <terraform-test-events.jsonl>");
  const events = (await readFile(path, "utf8")).trim().split("\n").map(line => JSON.parse(line));
  const summary = events.find(event => event.type === "test_summary");
  if (summary?.test_summary?.status !== "pass") throw new Error("Terraform mock tests did not pass.");
  for (const [run, team] of [["sales_baseline", "sales"], ["operations_baseline", "operations"]]) {
    const event = events.find(item => item.type === "test_plan" && item["@testrun"] === run);
    if (!event) throw new Error(`Missing actual Terraform mock plan: ${run}`);
    const plan = {
      format_version: event.test_plan.plan_format_version,
      resource_changes: event.test_plan.resource_changes
    };
    const violations = checkPlan(plan, team);
    if (violations.length) throw new Error(`${run}: ${violations.join("; ")}`);
    const config = JSON.parse(await readFile(`infra/workload/teams/${team}.tfvars.json`, "utf8"));
    const after = plan.resource_changes[0].change.after;
    for (const [property, value] of Object.entries({
      name: config.storage_account_name,
      costCenter: config.cost_center,
      owner: config.owner,
      serviceLabel: config.service_label
    })) {
      const actual = property === "name" ? after.name : after.tags?.[property];
      if (actual !== value) throw new Error(`${run}: versioned configuration mismatch for ${property}.`);
    }
    const negative = structuredClone(plan);
    negative.resource_changes[0].change.after.public_network_access = "Enabled";
    if (!checkPlan(negative, team).some(message => message.includes("public_network_access"))) {
      throw new Error(`${run}: the deliberate public-network mutation was not rejected.`);
    }
    console.log(`PASS: ${run}, actual mock plan accepted; public-network mutation rejected.`);
  }
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exitCode = 1;
}
