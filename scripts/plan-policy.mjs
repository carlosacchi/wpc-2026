const supportedTeams = new Set(["sales", "operations"]);
const requiredTags = ["project", "environment", "tenant", "costCenter", "owner"];

export function checkPlan(plan, team) {
  if (!supportedTeams.has(team)) throw new Error("Expected team sales or operations.");
  if (!plan || plan.errored || plan.complete === false ||
      typeof plan.format_version !== "string" ||
      !plan.format_version.startsWith("1.") ||
      !Array.isArray(plan.resource_changes)) {
    throw new Error("Expected a complete, non-errored Terraform plan JSON (format 1.x).");
  }

  const violations = [];
  let workloadCount = 0;
  for (const resource of plan.resource_changes) {
    if (resource.mode !== "managed") {
      violations.push(`${resource.address}: data sources are not part of this minimal lab.`);
      continue;
    }
    const change = resource.change;
    if (!change || !Array.isArray(change.actions) || change.actions.length === 0) {
      violations.push(`${resource.address}: missing actions.`);
      continue;
    }
    if (resource.type !== "azurerm_storage_account" ||
        resource.address !== "module.storage.azurerm_storage_account.this") {
      violations.push(`${resource.address}: resource outside the workload allowlist.`);
      continue;
    }
    workloadCount += 1;
    if (change.actions.some(action => !["create", "update", "no-op"].includes(action))) {
      violations.push(`${resource.address}: delete, replacement or unsupported action is forbidden.`);
      continue;
    }
    const after = change.after;
    if (!after || typeof after !== "object") {
      violations.push(`${resource.address}: planned values are missing.`);
      continue;
    }
    const expected = {
      resource_group_name: "wpc-2026",
      location: "italynorth",
      account_tier: "Standard",
      account_replication_type: "LRS",
      account_kind: "StorageV2",
      public_network_access: "Disabled",
      shared_access_key_enabled: false,
      allow_nested_items_to_be_public: false,
      https_traffic_only_enabled: true,
      min_tls_version: "TLS1_2"
    };
    for (const [property, value] of Object.entries(expected)) {
      if (after[property] !== value || change.after_unknown?.[property]) {
        violations.push(`${resource.address}: ${property} must be ${JSON.stringify(value)} and known at plan time.`);
      }
    }
    for (const key of requiredTags) {
      if (typeof after.tags?.[key] !== "string" || !after.tags[key].trim() ||
          change.after_unknown?.tags === true || change.after_unknown?.tags?.[key]) {
        violations.push(`${resource.address}: required tag ${key} must have a known non-empty value.`);
      }
    }
    for (const [key, value] of Object.entries({ tenant: team, project: "wpc-2026", environment: "sandbox" })) {
      if (after.tags?.[key] !== value) {
        violations.push(`${resource.address}: tag ${key} must equal ${value}.`);
      }
    }
  }
  if (workloadCount !== 1) violations.push("Expected exactly one managed workload storage account.");
  return violations;
}
