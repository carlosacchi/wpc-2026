import { readFile } from "node:fs/promises";
import { checkPlan } from "./plan-policy.mjs";

const [path, team, expectation, ...extra] = process.argv.slice(2);
try {
  if (!path || !team || extra.length || (expectation && expectation !== "--expect-rename")) {
    throw new Error("Usage: node scripts/check-plan.mjs <plan.json> <sales|operations> [--expect-rename]");
  }
  const plan = JSON.parse(await readFile(path, "utf8"));
  const violations = checkPlan(plan, team);
  const workload = plan.resource_changes.find(resource =>
    resource.address === "module.storage.azurerm_storage_account.this");
  if (expectation === "--expect-rename") {
    const change = workload?.change;
    if (plan.resource_changes.length !== 1 || workload?.mode !== "managed" ||
        workload.type !== "azurerm_storage_account" ||
        change?.actions?.length !== 2 ||
        !change.actions.includes("delete") || !change.actions.includes("create") ||
        typeof change.before?.id !== "string" || !change.before.id ||
        typeof change.before?.name !== "string" || !change.before.name ||
        typeof change.after?.name !== "string" || !change.after.name ||
        change.before.name === change.after.name ||
        !change.replace_paths?.some(path => path.length === 1 && path[0] === "name")) {
      throw new Error("Expected an existing storage account renamed with a name-driven replacement. Apply and verify the baseline first; a fresh creation is not this demo.");
    }
    console.log(`IMPACT: ${workload.address}: ${JSON.stringify(change.actions)}; name ${JSON.stringify(change.before.name)} -> ${JSON.stringify(change.after.name)}.`);
    console.log("OBSERVED: Terraform plans to replace an existing storage account. No apply is performed; the policy gate must reject this plan.");
  }
  if (violations.length) {
    for (const message of violations) console.error(`DENY: ${message}`);
    process.exitCode = 1;
  } else {
    console.log("PASS: workload plan satisfies the selected lab rules. This is not a full security audit.");
  }
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exitCode = 1;
}
