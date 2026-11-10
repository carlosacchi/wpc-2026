// Brings the demo back to its versioned starting point by rolling forward, never by deleting:
// team files are restored from demo/baseline through a normal PR, then the governed rollout
// re-aligns Azure in place (tags only). Idempotent: an aligned lab produces no changes.
import { execFileSync } from "node:child_process";
import { readFileSync, readdirSync, writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { tenantResourceGroups } from "./plan-policy.mjs";

export const baselineDir = "demo/baseline";
export const teamsDir = "infra/workload/teams";

export function diffTeams(read = path => readFileSync(path, "utf8"), list = dir => readdirSync(dir)) {
  const teams = Object.keys(tenantResourceGroups);
  const files = list(baselineDir).filter(name => name.endsWith(".tfvars.json")).sort();
  const expected = teams.map(team => `${team}.tfvars.json`).sort();
  if (JSON.stringify(files) !== JSON.stringify(expected)) {
    throw new Error(`${baselineDir} must contain exactly ${expected.join(", ")}.`);
  }
  const drift = [];
  for (const team of teams) {
    const baseline = JSON.parse(read(`${baselineDir}/${team}.tfvars.json`));
    if (baseline.resource_group_name !== tenantResourceGroups[team]) {
      throw new Error(`${team}: baseline resource group must be ${tenantResourceGroups[team]}.`);
    }
    const live = JSON.parse(read(`${teamsDir}/${team}.tfvars.json`));
    const keys = [...new Set([...Object.keys(baseline), ...Object.keys(live)])].sort();
    for (const key of keys) {
      if (JSON.stringify(baseline[key]) !== JSON.stringify(live[key])) {
        drift.push({ team, key, baseline: baseline[key], live: live[key] });
      }
    }
  }
  return drift;
}

const run = (cmd, args, options = {}) =>
  execFileSync(cmd, args, { encoding: "utf8", stdio: ["ignore", "pipe", "inherit"], ...options }).trim();

function openDemoPrs() {
  const prs = JSON.parse(run("gh", ["pr", "list", "--state", "open", "--json", "number,headRefName,title,files"]));
  return prs.filter(pr => pr.files.some(file => file.path.startsWith(`${teamsDir}/`)));
}

function dispatchRollout() {
  const out = run("gh", ["workflow", "run", "rollout.yml", "--ref", "main", "-f", "scenario=baseline", "-f", "rings=all"]);
  const url = out.match(/https:\/\/\S+\/actions\/runs\/\d+/)?.[0];
  console.log(`ROLLOUT: ${url ?? "dispatched (see Actions tab)"}`);
  console.log("Ring 0 (sales) then ring 1 (operations). A ring asks for approval only if Azure differs from the baseline; otherwise apply is skipped and only the health/drift check runs.");
}

function status() {
  const drift = diffTeams();
  if (drift.length === 0) console.log("FILES: team files match demo/baseline.");
  for (const d of drift) console.log(`DRIFT: ${d.team}.${d.key}: ${JSON.stringify(d.live)} (baseline ${JSON.stringify(d.baseline)})`);
  for (const pr of openDemoPrs()) console.log(`OPEN PR: #${pr.number} ${pr.headRefName} touches team files: ${pr.title}`);
  const pending = JSON.parse(run("gh", ["run", "list", "--workflow", "rollout.yml", "--limit", "10", "--json", "databaseId,status,url"]))
    .filter(r => r.status !== "completed");
  for (const r of pending) console.log(`RUN NOT COMPLETED: ${r.status} ${r.url} (rollouts are serialised: a reset waits for it)`);
  return drift;
}

function reset({ skipRollout }) {
  if (run("git", ["status", "--porcelain"]) !== "") throw new Error("Working tree is not clean.");
  run("git", ["fetch", "-q", "origin", "main"]);
  run("git", ["checkout", "-q", "main"]);
  run("git", ["merge", "-q", "--ff-only", "origin/main"]);
  const drift = status();
  if (drift.length > 0) {
    const branch = `demo-reset/${new Date().toISOString().replace(/[-:]/g, "").slice(0, 15)}`;
    run("git", ["checkout", "-q", "-b", branch]);
    for (const team of Object.keys(tenantResourceGroups)) {
      writeFileSync(`${teamsDir}/${team}.tfvars.json`, readFileSync(`${baselineDir}/${team}.tfvars.json`));
    }
    run("git", ["commit", "-q", "-am", `Reset demo team files to ${baselineDir}\n\nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`]);
    run("git", ["push", "-q", "-u", "origin", branch]);
    const url = run("gh", ["pr", "create", "--base", "main", "--head", branch, "--title", "Demo reset: restore team files to baseline",
      "--body", `Roll-forward to \`${baselineDir}\`. No resource is deleted: the rollout re-aligns tags in place through the same gates and approvals.`]);
    console.log(`PR: ${url}`);
    execFileSync("sleep", ["15"]);
    run("gh", ["pr", "checks", url, "--watch", "--interval", "10"], { stdio: ["ignore", "ignore", "inherit"] });
    try {
      run("gh", ["pr", "merge", url, "--merge", "--delete-branch"]);
    } catch {
      throw new Error(`Checks passed but merge is blocked (approval required?). Approve and merge ${url}, then run: node scripts/demo-reset.mjs rollout`);
    }
    run("git", ["checkout", "-q", "main"]);
    run("git", ["merge", "-q", "--ff-only", "origin/main"]);
    console.log("MERGED: main team files match demo/baseline.");
  }
  for (const pr of openDemoPrs()) console.log(`NOTE: close or keep PR #${pr.number} (${pr.headRefName}) before the next session.`);
  if (!skipRollout) dispatchRollout();
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [mode = "status", flag] = process.argv.slice(2);
  try {
    if (mode === "status") status();
    else if (mode === "reset") reset({ skipRollout: flag === "--no-rollout" });
    else if (mode === "rollout") dispatchRollout();
    else throw new Error("Usage: node scripts/demo-reset.mjs status | reset [--no-rollout] | rollout");
  } catch (error) {
    console.error(`ERROR: ${error.message}`);
    process.exitCode = 1;
  }
}
