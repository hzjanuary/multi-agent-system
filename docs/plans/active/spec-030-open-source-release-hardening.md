# SPEC-030 — Open-source release hardening

Started 2026-10-27. Branch `feat/spec-030-open-source-release-hardening`.
Baseline `320e527a48ef9a6a2e725342ce165e3d6835931e` was clean.
Authority: explicit maintainer SPEC-030 request. Preserve SPEC-029's archived
32 PASS/0 BLOCKED evidence and all five historical generation requests. No
inference, campaign, Redis replacement, remote write/publication, history rewrite
or retained-data deletion. Runtime product scope stays frozen.

## Decisions and boundaries

- Use root build context with an explicit allowlist; COPY canonical root LICENSE
  and NOTICE, without duplicated source copies. Update current build consumers;
  historical executed commands remain historical evidence.
- Scan all tracked text, fail closed, explicit file/content fixture allowances;
  independent index/path, source archive, context and image gates.
- Keep Redis 7.4 licensing explicit (RSALv2/SSPLv1). Any Valkey migration requires
  a separate architectural decision. No automatic license/security acceptance.
- Remote Actions, GitHub disclosure settings and publishing approval remain
  separate manual gates, never fabricated as local PASS.

## Progress

- [x] P1 actual baseline image lacks project licenses; synthetic test-file,
  credentialized PostgreSQL URL and substring-exception probes all evade old
  scanner. [Sanitized reproduction](../../release/spec-030-baseline.json).
- [ ] P2 canonical project licenses, verified dependency texts/inventory including
  certifi and missing-wheel-license cases; base/infra/provider categories.
- [ ] P3 scanner/precise fixture allowances/adversarial regressions/fail-closed.
- [ ] P4 ignores, index/path/symlink and independent archive/context/image gates.
- [ ] P5 CI ops/security/dependency/license/image gates, immutable Actions/image
  pins, SBOM and OS scan with explicit results/dispositions.
- [ ] P6 README/providers/privacy/security/disclosure, sanitized public logs;
  preserve original log privately with its original hash; author email review.
- [ ] P7 full quality/security gates; final committed-source image build and
  isolated empty-install/bootstrap/API/worker/CLI checks without inference.
- [ ] Final remediation matrix, source/image/tool provenance, risk owners and
  GO/CONDITIONAL/NO-GO disposition. Archive only after local requirements met.

## Verification / recovery

Use repository backend gates with explicit isolated MAOS_TEST_DATABASE_URL,
ops/security unit tests, strict index scan, archive/context/image checks,
Compose validation, dependency audit, SBOM and OS scan. Retain raw scan evidence
privately and publish only sanitized findings. Never suppress meaningful scan
failures. Unknown/unavailable scans remain explicit blockers or conditional gates.
Operator DB/credentials/volumes/session are not used for installation rehearsal;
use a new named verification namespace and stop it without deleting data.

## Checkpoint — scanner and upstream verification

- New scanner/path policy implemented; 13 adversarial tests PASS. No whole-test
  skip or substring placeholder rule. Explicit reviewed full-line SHA256 policy
  currently has 95 synthetic-code/evidence lines. Still need index-policy
  consistency, archive/context/image gates and combined tests.
- Root .dockerignore is an allowlist; Git/backend ignores strengthened. Build
  context moves to root; Dockerfile and both Compose contexts updated. New
  optional MAOS_IMAGE interpolation is actually consumed; default remains local.
- Registry manifest digests verified against exact bytes for Python3.12 slim,
  PostgreSQL16, Redis7 (no replacement) and optional Ollama0.13.5, recorded in
  release/images.lock.json. Latest Actions immutable SHAs and Trivy0.76.1 tool
  archive/binary hashes verified, release/tools.lock.json. Trivy private binary
  at .maos/spec-030/tools/trivy.
- Exact-version sdists of langchain-core1.4.9/langsmith0.10.2 lack license files.
  Upstream tag commits found: 1c3a4186cf2ba4f28face59118ac7786de009f91 and
  687fc8d527a28504432f52bd08c75f2894c209fe. Langsmith uses Hatch dynamic version
  in python/langsmith/__init__.py; verified __version__=0.10.2. Full immutable
  upstream MIT supplements and certifi2026.10.23 upstream notice/full MPL2.0 text
  are being recorded in release/third-party/sources.json. No guessed license PASS.
- Baseline Trivy OS/language scan completed: 171 rows, 44 HIGH / 64 MEDIUM /
  62 LOW / 1 UNKNOWN; no CRITICAL. HIGH rows have no vendor fix version. Raw
  private report .maos/spec-030/evidence/baseline-image-os-scan.json. No ignore
  or exception applied. Final candidate must be scanned; an unsatisfied security
  gate remains NO-GO pending evidence-based mitigation/owner triage, never green
  by blanket suppression. Complete all independent remediation first.
- Runtime live requests stay five historically; no new inference or campaign.
