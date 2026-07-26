# Approval And Outbound Communication Policy

## Purpose

This policy defines the boundary between internal evidence review, Manager/Admin
approval, explicit resume, approved outbound preview, and any future send
behavior.

Current implementation references:

- Approval/resume lifecycle: SPEC-012 and workflow APIs
- Approved outbound preview foundation: `backend/app/outbound/`
- Workflow preview endpoint: `GET /api/v1/workflows/{workflow_id}/outbound/preview`
- Frontend operator docs: `docs/demo/FRONTEND_OPERATOR_GUIDE.md`

## Current Lifecycle Boundary

The current workflow lifecycle remains authoritative:

```text
/run -> WAITING_APPROVAL
Manager/Admin approval -> APPROVED
/resume -> COMPLETED
approved outbound preview can be loaded only after completed approval/resume evidence
```

No catalog, provider, RAG, Telegram, or outbound preview behavior may bypass
this lifecycle.

## Manager/Admin Approval Boundary

Before Manager/Admin approval:

- workflow may be reviewed internally;
- evidence may be displayed as reference material;
- Telegram replies may acknowledge intake/status only;
- no final quote may be issued;
- no real email may be sent;
- no discount approval, stock, or delivery promise may be claimed.

Approval must remain a human decision. Duplicate final decisions remain blocked
by existing approval behavior.

## Resume Boundary

Approval alone is not completion. After approval:

- `/resume` is the only continuation path;
- workflow continuation prepares the post-approval preview path;
- rejected workflows remain terminal;
- no automatic resume from Telegram, provider evidence, or frontend display is
  allowed.

## Approved Outbound Preview Rules

The current outbound preview foundation is preview-only.

Stable defaults:

```text
OUTBOUND_COMMUNICATION_ENABLED=false
OUTBOUND_SEND_ENABLED=false
OUTBOUND_PROVIDER=preview
OUTBOUND_REQUIRE_APPROVAL=true
```

Preview is allowed only when:

- outbound preview is explicitly enabled;
- send remains disabled;
- workflow is `COMPLETED`;
- workflow state contains explicit approval evidence;
- workflow state contains explicit resume completion evidence;
- workflow state contains explicit preview content such as subject and body.

The preview service must not synthesize customer-ready content from arbitrary
prose, events, agent summaries, RAG, Tavily, LLM output, or Telegram messages.

## Current No-Send State

Current implementation intentionally has:

- no send endpoint;
- no send button;
- no Gmail integration;
- no SMTP integration;
- no provider send call;
- no auto-send from workflow runtime;
- no auto-send from Telegram;
- no real email by default.

Frontend labels must keep preview separate from sent communication. The UI must
not claim "email sent" or "approved quote sent" without future backend evidence
from an approved send spec.

## Future Send Policy Requirements

Any future real send behavior requires a separate implementation spec covering:

- feature flag design;
- RBAC for send preparation and send execution;
- explicit user confirmation;
- provider choice and failure behavior;
- credential storage and redaction;
- persisted audit events;
- retry and idempotency;
- recipient validation;
- content safety validation;
- operator rollback/correction process;
- no CI provider key requirement;
- tests for no pre-approval send.

`OUTBOUND_SEND_ENABLED=false` must remain the default until that future spec is
approved and implemented.

## Audit And Event Requirements

Future outbound mutations should create bounded workflow/audit events for:

- draft created;
- preview exported if export becomes a mutation;
- send requested;
- send blocked by policy;
- send succeeded;
- send failed;
- provider retry scheduled;
- provider retry exhausted.

Event payloads must include enough evidence to prove policy compliance without
storing secrets or raw provider data.

Forbidden event payload content:

- provider API keys;
- SMTP/Gmail tokens;
- Authorization headers;
- cookies;
- raw prompts;
- raw provider payloads;
- raw customer attachments;
- embeddings or vector payloads;
- chain-of-thought.

## Recipient Safety

Future send behavior must validate:

- recipient email format;
- intended recipient role or source;
- no accidental demo credentials as customer contacts;
- no unbounded recipient lists;
- no secret-bearing recipient metadata.

Until future send is implemented, recipients in preview are display metadata
only.

## Content Safety

Outbound content must:

- be bounded;
- be generated only after approval/resume;
- identify that it is preview-only until sent by a future approved channel;
- not include raw prompts, provider payloads, secrets, embeddings, or
  chain-of-thought;
- not include unsupported item prices;
- not claim stock/delivery/discount approval unless future approved policy data
  explicitly supports it.

## Telegram Boundary

Telegram remains an intake/status channel in the current implementation.

Telegram must not:

- send final quotes automatically;
- send approved outbound previews automatically;
- auto-approve;
- auto-resume;
- call Gmail/SMTP/provider send paths;
- claim that email was sent.

## Approval/Outbound Review Checklist

Before changing approval or outbound behavior:

- [ ] Manager/Admin approval remains required.
- [ ] Explicit `/resume` remains required after approval.
- [ ] Rejected/failed/cancelled workflows stay terminal.
- [ ] No send endpoint is added unless a separate spec authorizes it.
- [ ] No send button is added unless backend send behavior exists and is
  governed.
- [ ] Preview text cannot be mistaken for sent email.
- [ ] Audit/event requirements are defined for any mutation.
- [ ] Tests prove no pre-approval final quote or send.
- [ ] Tests prove no raw provider payloads, prompts, tokens, or secrets are
  displayed or stored.
