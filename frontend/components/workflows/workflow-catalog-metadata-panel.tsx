"use client";

import type { WorkflowState } from "@/lib/api/types";

const MAX_ADDONS = 6;
const MAX_TEXT_CHARS = 140;
const SENSITIVE_MARKERS = [
  "api_key",
  "apikey",
  "authorization",
  "bearer",
  "chain_of_thought",
  "cookie",
  "jwt",
  "password",
  "provider_payload",
  "raw_html",
  "raw_model",
  "raw_prompt",
  "raw_provider",
  "secret",
  "token",
  "vector_payload",
  "embedding",
];
const FORBIDDEN_CLAIM_MARKERS = [
  "approved quote",
  "approved quotation",
  "in stock",
  "stock available",
  "delivery date",
  "will deliver",
  "discount approved",
  "email sent",
];

export interface WorkflowCatalogMetadata {
  itemId: string | null;
  displayName: string | null;
  normalizedItemName: string | null;
  itemFamily: string | null;
  quantity: string | null;
  unit: string | null;
  requestedAddons: string[];
  supportedAddons: string[];
  catalogVersion: string | null;
  demoOnly: boolean | null;
}

interface WorkflowCatalogMetadataPanelProps {
  workflow: WorkflowState;
}

export function WorkflowCatalogMetadataPanel({
  workflow,
}: WorkflowCatalogMetadataPanelProps) {
  const catalog = extractWorkflowCatalogMetadata(workflow);

  if (!catalog) {
    return null;
  }

  const title =
    catalog.displayName ?? catalog.normalizedItemName ?? "Catalog item";
  const addons = catalog.requestedAddons.length
    ? catalog.requestedAddons
    : catalog.supportedAddons;

  return (
    <section className="ops-panel p-5">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="ops-kicker">Catalog match</p>
          <h2 className="mt-1 text-lg font-semibold">Catalog Metadata</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            Deterministic catalog match from demo/internal catalog metadata
            only. This is intake evidence, not a final quotation; pricing still
            requires workflow validation and Manager/Admin approval.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {catalog.catalogVersion ? (
            <span className="ops-chip">{catalog.catalogVersion}</span>
          ) : null}
          {catalog.demoOnly === true ? (
            <span className="ops-chip">Demo catalog</span>
          ) : null}
        </div>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <div className="rounded-md border border-border/70 bg-background/50 p-4">
          <p className="ops-kicker">Normalized item</p>
          <h3 className="mt-2 break-words text-base font-semibold">{title}</h3>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <CatalogFact label="Item ID" value={catalog.itemId} />
            <CatalogFact label="Item family" value={catalog.itemFamily} />
            <CatalogFact
              label="Normalized name"
              value={catalog.normalizedItemName}
            />
            <CatalogFact label="Quantity" value={catalog.quantity} />
            <CatalogFact label="Unit" value={catalog.unit} />
          </div>
        </div>

        <div className="rounded-md border border-border/70 bg-background/50 p-4">
          <p className="ops-kicker">Add-on compatibility</p>
          <h3 className="mt-2 text-base font-semibold">Requested add-ons</h3>
          {addons.length > 0 ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {addons.map((addon) => (
                <span className="ops-chip" key={addon}>
                  {formatAddonLabel(addon)}
                </span>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-muted-foreground">
              No explicit add-on metadata was supplied with this catalog match.
            </p>
          )}
          <p className="mt-4 text-sm leading-6 text-muted-foreground">
            Catalog support only means the item was normalized for workflow
            intake. It is not pricing proof, commercial commitment, or approval.
          </p>
        </div>
      </div>
    </section>
  );
}

export function extractWorkflowCatalogMetadata(
  workflow: WorkflowState,
): WorkflowCatalogMetadata | null {
  for (const candidate of explicitCatalogCandidates(workflow)) {
    const catalog = normalizeCatalogMetadata(candidate);
    if (catalog) {
      return catalog;
    }
  }

  return null;
}

function explicitCatalogCandidates(workflow: WorkflowState): unknown[] {
  const root = workflow as unknown as Record<string, unknown>;
  const request = asRecord(workflow.request);
  const metadata = asRecord(workflow.metadata);
  const metadataAttributes = asRecord(metadata?.attributes);
  const requestMetadata = asRecord(root.request_metadata);
  const requestPayload = asRecord(root.request_payload);
  const requestPayloadMetadata = asRecord(requestPayload?.metadata);
  const initialRequest = asRecord(root.initial_request);
  const initialRequestMetadata = asRecord(initialRequest?.metadata);

  return [
    root.catalog,
    root.catalog_metadata,
    request?.catalog,
    request?.catalog_metadata,
    metadata?.catalog,
    metadata?.catalog_item,
    metadataAttributes?.catalog,
    metadataAttributes?.catalog_item,
    requestMetadata?.catalog,
    requestMetadata?.catalog_item,
    requestPayloadMetadata?.catalog,
    requestPayloadMetadata?.catalog_item,
    initialRequestMetadata?.catalog,
    initialRequestMetadata?.catalog_item,
  ];
}

function normalizeCatalogMetadata(value: unknown): WorkflowCatalogMetadata | null {
  const record = asRecord(value);
  if (!record || containsSensitiveKey(record)) {
    return null;
  }

  const catalogVersion = safeText(
    record.catalog_version ?? record.catalogVersion,
    80,
  );
  const itemId = safeText(record.item_id ?? record.itemId ?? record.slug, 100);
  const displayName = safeText(record.display_name ?? record.displayName);
  const normalizedItemName = safeText(
    record.normalized_item_name ?? record.normalizedItemName,
  );
  const itemFamily = safeText(record.item_family ?? record.itemFamily, 100);
  const quantity = safeText(record.quantity, 40);
  const unit = safeText(record.unit, 40);
  const requestedAddons = normalizeStringList(
    record.requested_addons ?? record.requestedAddons,
  );
  const supportedAddons = normalizeStringList(
    record.supported_addons ?? record.supportedAddons,
  );
  const demoOnly =
    typeof record.demo_only === "boolean"
      ? record.demo_only
      : typeof record.demoOnly === "boolean"
        ? record.demoOnly
        : null;

  const looksCatalogShaped =
    catalogVersion !== null ||
    itemId !== null ||
    displayName !== null ||
    normalizedItemName !== null ||
    itemFamily !== null ||
    quantity !== null ||
    unit !== null ||
    requestedAddons.length > 0 ||
    supportedAddons.length > 0 ||
    demoOnly !== null;

  if (!looksCatalogShaped) {
    return null;
  }

  return {
    itemId,
    displayName,
    normalizedItemName,
    itemFamily,
    quantity,
    unit,
    requestedAddons,
    supportedAddons,
    catalogVersion,
    demoOnly,
  };
}

function CatalogFact({
  label,
  value,
}: {
  label: string;
  value: string | null;
}) {
  if (!value) {
    return null;
  }

  return (
    <div className="rounded-md border border-border/60 bg-background/55 p-3">
      <p className="ops-kicker">{label}</p>
      <p className="mt-1 break-words text-sm font-semibold">{value}</p>
    </div>
  );
}

function normalizeStringList(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  const safeValues: string[] = [];
  for (const item of value) {
    if (safeValues.length >= MAX_ADDONS) {
      break;
    }
    const text = safeText(item, 80);
    if (text && !safeValues.includes(text)) {
      safeValues.push(text);
    }
  }
  return safeValues;
}

function formatAddonLabel(value: string): string {
  if (value === "office_365") {
    return "Office 365";
  }
  return value
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function safeText(
  value: unknown,
  limit: number = MAX_TEXT_CHARS,
): string | null {
  if (typeof value !== "string" && typeof value !== "number") {
    return null;
  }
  const text = String(value)
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  if (!text) {
    return null;
  }
  if (containsSensitiveMarker(text) || containsForbiddenClaim(text)) {
    return "[redacted]";
  }
  return text.length > limit ? `${text.slice(0, limit).trimEnd()}...` : text;
}

function containsSensitiveKey(value: Record<string, unknown>): boolean {
  return Object.keys(value).some((key) => containsSensitiveMarker(key));
}

function containsSensitiveMarker(value: string): boolean {
  const normalized = value.toLowerCase();
  return SENSITIVE_MARKERS.some((marker) => normalized.includes(marker));
}

function containsForbiddenClaim(value: string): boolean {
  const normalized = value.toLowerCase();
  return FORBIDDEN_CLAIM_MARKERS.some((marker) => normalized.includes(marker));
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null
    ? (value as Record<string, unknown>)
    : null;
}
