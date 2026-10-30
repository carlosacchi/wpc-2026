import { readFile } from "node:fs/promises";
import { checkPlan } from "./plan-policy.mjs";

const [path, team] = process.argv.slice(2);
try {
  if (!path || !team) throw new Error("Usage: node scripts/check-plan.mjs <plan.json> <sales|operations>");
  const plan = JSON.parse(await readFile(path, "utf8"));
  const violations = checkPlan(plan, team);
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
