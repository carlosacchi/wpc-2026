import { resourceGroupFor } from "./plan-policy.mjs";

const storageType = "microsoft.storage/storageaccounts";
const idPattern = /^\/subscriptions\/[^/]+\/resourceGroups\/([^/]+)\/providers\/([^/]+\/[^/]+)\/([^/]+)$/i;

function parseId(resourceId) {
  const match = idPattern.exec(resourceId ?? "");
  return match ? { resourceGroup: match[1], type: match[2].toLowerCase(), name: match[3] } : null;
}

// Gate for `az deployment group what-if --no-pretty-print` output (Bicep comparison only).
export function checkWhatIf(result, team) {
  const resourceGroup = resourceGroupFor(team);
  if (!result || result.status !== "Succeeded" || result.error || !Array.isArray(result.changes)) {
    throw new Error("Expected a succeeded ARM What-If result with a changes array.");
  }

  const violations = [];
  const created = [];
  const ignoredStorage = [];
  let workloadCount = 0;
  for (const change of result.changes) {
    const id = parseId(change.resourceId);
    if (!id) {
      violations.push(`${change.resourceId}: unexpected resource ID shape.`);
      continue;
    }
    if (id.resourceGroup.toLowerCase() !== resourceGroup) {
      violations.push(`${change.resourceId}: outside tenant resource group ${resourceGroup}.`);
      continue;
    }
    if (change.changeType === "Ignore") {
      if (id.type === storageType) ignoredStorage.push(id.name);
      continue;
    }
    if (["Delete", "Deploy", "Unsupported"].includes(change.changeType)) {
      violations.push(`${id.name}: What-If change ${change.changeType} is forbidden or not reviewable.`);
      continue;
    }
    if (!["Create", "Modify", "NoChange"].includes(change.changeType)) {
      violations.push(`${id.name}: unknown What-If change ${JSON.stringify(change.changeType)}.`);
      continue;
    }
    if (id.type !== storageType) {
      violations.push(`${id.name}: ${id.type} is outside the workload allowlist.`);
      continue;
    }
    workloadCount += 1;
    if (change.changeType === "Create") created.push(id.name);
    const after = change.after;
    const expected = {
      location: "italynorth",
      kind: "StorageV2",
      "sku.name": "Standard_LRS",
      "properties.publicNetworkAccess": "Disabled",
      "properties.allowSharedKeyAccess": false,
      "properties.allowBlobPublicAccess": false,
      "properties.supportsHttpsTrafficOnly": true,
      "properties.minimumTlsVersion": "TLS1_2",
      "tags.tenant": team,
      "tags.project": "wpc-2026",
      "tags.environment": "sandbox"
    };
    for (const [path, value] of Object.entries(expected)) {
      const actual = path.split(".").reduce((node, key) => node?.[key], after);
      if (actual !== value) violations.push(`${id.name}: ${path} must be ${JSON.stringify(value)}.`);
    }
  }
  if (workloadCount !== 1) violations.push("Expected exactly one workload storage account in the What-If result.");
  if (created.length && ignoredStorage.length) {
    violations.push(`Create ${created.join(", ")} while ${ignoredStorage.join(", ")} stays outside the template: Bicep incremental mode would leave the original as an orphan (implicit rename).`);
  }
  return violations;
}
