import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { validateMetadata, verifyArtifact } from "../scripts/plan-artifact.mjs";

function fixture() {
  const metadata = {
    schema: 1, repository: "example/lab", team: "sales",
    sha256: "a".repeat(64), commit: "b".repeat(40),
    runId: "123", runAttempt: "1", terraformVersion: "1.14.9",
    subscriptionId: "00000000-0000-0000-0000-000000000001",
    tenantId: "00000000-0000-0000-0000-000000000002", stateAccount: "wpcstate"
  };
  const actual = {
    ...metadata,
    run: {
      id: 123, run_attempt: 1, head_sha: metadata.commit, head_branch: "main",
      event: "workflow_dispatch", path: ".github/workflows/plan.yml",
      status: "completed", conclusion: "success"
    }
  };
  return { metadata, actual };
}

test("accepts a matching saved plan from the successful main run", () => {
  const { metadata, actual } = fixture();
  assert.equal(verifyArtifact(metadata, actual), metadata);
});

for (const key of ["repository", "team", "sha256", "commit", "terraformVersion", "subscriptionId", "tenantId", "stateAccount"]) {
  test(`rejects artifact mismatch: ${key}`, () => {
    const { metadata, actual } = fixture();
    actual[key] = "different";
    assert.throws(() => verifyArtifact(metadata, actual), /mismatch/);
  });
}

for (const [key, value] of [
  ["id", 124], ["run_attempt", 2], ["head_sha", "c".repeat(40)],
  ["head_branch", "feature"], ["event", "pull_request"],
  ["path", ".github/workflows/other.yml"], ["status", "in_progress"], ["conclusion", "failure"]
]) {
  test(`rejects wrong workflow run: ${key}`, () => {
    const { metadata, actual } = fixture();
    actual.run[key] = value;
    assert.throws(() => verifyArtifact(metadata, actual), /successful main-branch/);
  });
}

for (const metadata of [null, {}, { ...fixture().metadata, runId: "../other" }, { ...fixture().metadata, schema: 2 }]) {
  test(`rejects malformed artifact metadata: ${JSON.stringify(metadata)}`, () => {
    assert.throws(() => validateMetadata(metadata), /Invalid/);
  });
}

test("CLI writes the actual binary digest, refuses overwrite and rejects non-CI use", () => {
  const directory = mkdtempSync(join(tmpdir(), "wpc-plan-artifact-"));
  try {
    const binary = Buffer.from("synthetic binary fixture, not a deployable Terraform plan");
    writeFileSync(join(directory, "workload.tfplan"), binary);
    const { metadata } = fixture();
    const env = {
      GITHUB_ACTIONS: "true", GITHUB_REPOSITORY: metadata.repository,
      GITHUB_REF: "refs/heads/main", GITHUB_RUN_ID: metadata.runId,
      GITHUB_RUN_ATTEMPT: metadata.runAttempt, GITHUB_SHA: metadata.commit,
      ARM_SUBSCRIPTION_ID: metadata.subscriptionId, ARM_TENANT_ID: metadata.tenantId,
      STATE_ACCOUNT: metadata.stateAccount
    };
    const args = ["scripts/plan-artifact.mjs", "write", directory, metadata.team, metadata.repository];
    const first = spawnSync(process.execPath, args, { env, encoding: "utf8" });
    assert.equal(first.status, 0, first.stderr);
    const written = JSON.parse(readFileSync(join(directory, "plan-metadata.json"), "utf8"));
    assert.deepEqual(written, { ...metadata, sha256: createHash("sha256").update(binary).digest("hex") });
    const repeated = spawnSync(process.execPath, args, { env, encoding: "utf8" });
    assert.equal(repeated.status, 1);
    assert.match(repeated.stderr, /EEXIST/);
    const local = spawnSync(process.execPath, args, { env: {}, encoding: "utf8" });
    assert.equal(local.status, 1);
    assert.match(local.stderr, /main-branch GitHub workflow/);
  } finally {
    rmSync(directory, { recursive: true });
  }
});
