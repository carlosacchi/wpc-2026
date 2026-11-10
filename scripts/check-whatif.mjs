import { readFile } from "node:fs/promises";
import { checkWhatIf } from "./whatif-policy.mjs";

const [path, team, ...extra] = process.argv.slice(2);
try {
  if (!path || !team || extra.length) {
    throw new Error("Usage: node scripts/check-whatif.mjs <whatif.json> <sales|operations>");
  }
  const result = JSON.parse(await readFile(path, "utf8"));
  const violations = checkWhatIf(result, team);
  for (const change of result.changes) {
    console.log(`IMPACT: ${change.changeType} ${change.resourceId}`);
  }
  if (violations.length) {
    for (const message of violations) console.error(`DENY: ${message}`);
    process.exitCode = 1;
  } else {
    console.log("PASS: Bicep What-If satisfies the selected lab rules. Preview only; Bicep is never deployed by this lab.");
  }
} catch (error) {
  console.error(`ERROR: ${error.message}`);
  process.exitCode = 1;
}
