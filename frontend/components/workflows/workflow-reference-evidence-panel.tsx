"use client";

import type { WorkflowState } from "@/lib/api/types";

const MAX_SOURCES = 3;
const MAX_REFERENCE_PRICES = 3;
const MAX_WARNINGS = 3;
const MAX_TEXT_CHARS = 180;
const MAX_URL_CHARS = 260;
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

export interface ReferenceEvidenceSource {
  title: string;
  url: string | null;
}

export interface ReferenceEvidencePrice {
  label: string;
  amount: string | null;
  currency: string | null;
  unit: string | null;
  quantityBasis: string | null;
}

export interface ReferenceEvidence {
  provider: string | null;
  evidenceLabel: string | null;
  referencePrices: ReferenceEvidencePrice[];
  sources: ReferenceEvidenceSource[];
  confidence: number | null;
  retrievedAt: string | null;
  warnings: string[];
  isFinalQuote: boolean;
}

interface WorkflowReferenceEvidencePanelProps {
  workflow: WorkflowState;
}

export function WorkflowReferenceEvidencePanel({
  workflow,
}: WorkflowReferenceEvidencePanelProps) {
  const evidence = extractReferenceEvidence(workflow);

  if (!evidence) {
    return null;
  }

  const displayReferencePrices = evidence.isFinalQuote
    ? []
    : evidence.referencePrices;
  const displaySources = evidence.isFinalQuote ? [] : evidence.sources;
  const hasDisplayEvidence =
    displaySources.length > 0 || displayReferencePrices.length > 0;

  return (
    <section className="ops-panel p-5">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="ops-kicker">Reference evidence</p>
          <h2 className="mt-1 text-lg font-semibold">
            Reference Price Evidence
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            Reference evidence only. Final quotation still requires
            Manager/Admin approval. Amounts shown here are review material, not
            customer-ready pricing.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {evidence.provider ? (
            <span className="ops-chip">Provider: {evidence.provider}</span>
          ) : null}
          {evidence.confidence !== null ? (
            <span className="ops-chip">
              Confidence {formatConfidence(evidence.confidence)}
            </span>
          ) : null}
          {evidence.retrievedAt ? (
            <span className="ops-chip">Retrieved {evidence.retrievedAt}</span>
          ) : null}
        </div>
      </div>

      {evidence.isFinalQuote ? (
        <div className="mt-5 rounded-md border border-warning/40 bg-warning/10 p-4">
          <p className="text-sm font-semibold text-warning">
            Evidence requires internal review
          </p>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            This evidence was marked as quotation-like by upstream data. The UI
            has downgraded it to review-only evidence and will not display it as
            approved customer pricing.
          </p>
        </div>
      ) : null}

      {!hasDisplayEvidence ? (
        <p className="mt-5 text-sm leading-6 text-muted-foreground">
          No structured source or reference amount is available. Manual pricing
          review is still required.
        </p>
      ) : (
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {displayReferencePrices.length > 0 ? (
            <div className="rounded-md border border-border/70 bg-background/50 p-4">
              <h3 className="text-sm font-semibold">Structured amounts</h3>
              <div className="mt-3 grid gap-3">
                {displayReferencePrices.map((price) => (
                  <ReferencePriceRow
                    key={[
                      price.label,
                      price.amount,
                      price.currency,
                      price.unit,
                    ].join("|")}
                    price={price}
                  />
                ))}
              </div>
            </div>
          ) : null}
          {displaySources.length > 0 ? (
            <div className="rounded-md border border-border/70 bg-background/50 p-4">
              <h3 className="text-sm font-semibold">Bounded citations</h3>
              <div className="mt-3 grid gap-3">
                {displaySources.map((source) => (
                  <ReferenceSourceRow
                    key={[source.title, source.url].join("|")}
                    source={source}
                  />
                ))}
              </div>
            </div>
          ) : null}
        </div>
      )}

      {evidence.warnings.length > 0 ? (
        <div className="mt-5 rounded-md border border-border/70 bg-background/45 p-4">
          <h3 className="text-sm font-semibold">Warnings</h3>
          <ul className="mt-2 grid gap-2 text-sm leading-6 text-muted-foreground">
            {evidence.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

export function extractReferenceEvidence(
  workflow: WorkflowState,
): ReferenceEvidence | null {
  const candidates = explicitEvidenceCandidates(workflow);

  for (const candidate of candidates) {
    const evidence = normalizeReferenceEvidence(candidate);
    if (evidence) {
      return evidence;
    }
  }

  return null;
}

function ReferencePriceRow({ price }: { price: ReferenceEvidencePrice }) {
  const parts = [price.amount, price.currency].filter(Boolean).join(" ");
  const unit = price.unit ? ` / ${price.unit}` : "";
  const basis = price.quantityBasis ? `Basis: ${price.quantityBasis}` : null;

  return (
    <article className="rounded-md border border-border/60 bg-background/55 p-3">
      <p className="text-sm font-semibold">{price.label}</p>
      {parts ? (
        <p className="mt-1 break-words text-sm text-primary">
          {parts}
          {unit}
        </p>
      ) : null}
      <p className="mt-2 text-xs leading-5 text-muted-foreground">
        Reference only. Not customer-ready pricing.
      </p>
      {basis ? (
        <p className="mt-1 text-xs leading-5 text-muted-foreground">{basis}</p>
      ) : null}
    </article>
  );
}

function ReferenceSourceRow({ source }: { source: ReferenceEvidenceSource }) {
  return (
    <article className="rounded-md border border-border/60 bg-background/55 p-3">
      <p className="break-words text-sm font-semibold">{source.title}</p>
      {source.url ? (
        <p className="mt-1 break-all font-mono text-xs leading-5 text-muted-foreground">
          {source.url}
        </p>
      ) : null}
    </article>
  );
}

function explicitEvidenceCandidates(workflow: WorkflowState): unknown[] {
  const root = workflow as unknown as Record<string, unknown>;
  const runtimeContext = asRecord(workflow.runtime_context);
  const outputs = asRecord(workflow.outputs);
  const rootEvidence = asRecord(root.evidence);
  const runtimeEvidence = asRecord(runtimeContext?.evidence);
  const outputEvidence = asRecord(outputs?.evidence);

  return [
    root.price_research,
    root.reference_price_research,
    root.reference_evidence,
    root.rag_evidence,
    rootEvidence?.price_research,
    runtimeContext?.price_research,
    runtimeContext?.reference_price_research,
    runtimeContext?.reference_evidence,
    runtimeContext?.rag_evidence,
    runtimeEvidence?.price_research,
    outputs?.price_research,
    outputs?.reference_price_research,
    outputs?.reference_evidence,
    outputs?.rag_evidence,
    outputEvidence?.price_research,
  ];
}

function normalizeReferenceEvidence(value: unknown): ReferenceEvidence | null {
  const record = asRecord(value);
  if (!record || containsSensitiveKey(record)) {
    return null;
  }

  const evidenceLabel = safeText(record.evidence_label);
  const provider = safeText(record.provider, 80);
  const sources = normalizeSources(record.sources);
  const referencePrices = normalizeReferencePrices(record.reference_prices);
  const warnings = normalizeWarnings(record.warnings);
  const confidence = safeConfidence(record.confidence);
  const retrievedAt = safeText(record.retrieved_at, 80);
  const isFinalQuote = record.is_final_quote === true;

  const looksEvidenceShaped =
    evidenceLabel !== null ||
    provider !== null ||
    Array.isArray(record.sources) ||
    Array.isArray(record.reference_prices) ||
    Array.isArray(record.warnings) ||
    typeof record.confidence === "number" ||
    record.is_final_quote === true;

  if (!looksEvidenceShaped) {
    return null;
  }

  return {
    provider,
    evidenceLabel,
    referencePrices,
    sources,
    confidence,
    retrievedAt,
    warnings,
    isFinalQuote,
  };
}

function normalizeSources(value: unknown): ReferenceEvidenceSource[] {
  if (!Array.isArray(value)) {
    return [];
  }
  const sources: ReferenceEvidenceSource[] = [];
  for (const item of value) {
    if (sources.length >= MAX_SOURCES) {
      break;
    }
    const source = asRecord(item);
    if (!source || containsSensitiveKey(source)) {
      continue;
    }
    const title =
      safeText(source.title) ??
      safeText(source.citation_label) ??
      safeText(source.url) ??
      "Reference source";
    const url = safeUrl(source.url);
    sources.push({ title, url });
  }
  return sources;
}

function normalizeReferencePrices(value: unknown): ReferenceEvidencePrice[] {
  if (!Array.isArray(value)) {
    return [];
  }
  const prices: ReferenceEvidencePrice[] = [];
  for (const item of value) {
    if (prices.length >= MAX_REFERENCE_PRICES) {
      break;
    }
    const price = asRecord(item);
    if (!price || containsSensitiveKey(price)) {
      continue;
    }
    const label = safeText(price.label, 80) ?? "Reference amount";
    const amount = safeText(price.amount ?? price.observed_price, 80);
    const currency = safeText(price.currency, 16);
    const unit = safeText(price.unit, 40);
    const quantityBasis = safeText(price.quantity_basis, 40);
    prices.push({ label, amount, currency, unit, quantityBasis });
  }
  return prices;
}

function normalizeWarnings(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .slice(0, MAX_WARNINGS)
    .map((warning) => safeText(warning))
    .filter((warning): warning is string => Boolean(warning));
}

function safeConfidence(value: unknown): number | null {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return null;
  }
  return Math.max(0, Math.min(value, 1));
}

function formatConfidence(value: number): string {
  return `${Math.round(Math.max(0, Math.min(value, 1)) * 100)}%`;
}

function safeUrl(value: unknown): string | null {
  const text = safeText(value, MAX_URL_CHARS);
  if (!text || containsSensitiveMarker(text)) {
    return null;
  }
  if (!/^https?:\/\//i.test(text)) {
    return null;
  }
  return text;
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
  if (containsSensitiveMarker(text)) {
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

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null
    ? (value as Record<string, unknown>)
    : null;
}
