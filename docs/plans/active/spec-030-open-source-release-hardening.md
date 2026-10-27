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
- [x] P2 canonical project licenses, verified dependency texts/inventory including
  certifi and missing-wheel-license cases; base/infra/provider categories.
- [x] P3 scanner/precise fixture allowances/adversarial regressions/fail-closed.
- [x] P4 ignores, index/path/symlink and independent archive/context/image gates.
- [x] P5 CI ops/security/dependency/license/image gates, immutable Actions/image
  pins, SBOM and OS scan with explicit results/dispositions.
- [x] P6 README/providers/privacy/security/disclosure, sanitized public logs;
  preserve original log privately with its original hash; author email review.
- [x] P7 full quality/security gates; final committed-source image build and
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


## Final local checkpoint — implementation/evidence complete, security disposition open

- Local commits 7898293 / df0b738 / d84aeea implement the bounded release work.
  Tested executable/build-input source: d84aeea6af592b56738456039445f480778744cf.
  Remaining handoff changes are public sanitized documentation/evidence only.
- New scanner has 100 exact file/full-line review allowances (no test-directory
  skip); staged policy must match worktree. Baseline executable reproduction
  proves all three old negative cases escape, while all now trigger findings.
- Full final backend gate: 242 PASS, 0 FAIL, 2 deprecation warnings; lock/Ruff/
  Black/MyPy PASS. First run was 239 PASS/3 FAIL due to ambient CI model/extension
  variables; three default-configuration tests now explicitly isolate those
  variables without changing assertions or runtime behavior. Focused 25 PASS
  under nonempty ambient configuration, then full suite rerun PASS.
- Ops: 73 PASS including 26 adversarial release/scanner/license/security tests.
  Source archive/index/context/image gates all PASS. 139 build inputs, 171
  shipped files, 59 Python distributions, 87 OS packages; canonical project MIT/
  NOTICE, certifi MPL and immutable upstream missing-wheel texts verified.
- Independent clean clone builds image
  sha256:21f4073e53b9f3a657a933867c6d6921fd9634c1d503618da25224cc59c42100.
  Initial build same source: sha256:86985c009a6b33892f82bc9ce3732adc9b5c39bff7502e44d4cbe030eed32a64.
  Both match independent byte manifests; do not claim byte-identical builds.
- Empty install has zero users/runs/events; explicit new verification bootstrap,
  healthy API/worker/doctor, separate CLI login/discovery, mode0600, retained DB
  on clean-build image restart PASS. Canonical and dev Compose PASS. All new
  SPEC-030 services stopped; volumes/config/CLI retained. Existing operator
  services/state were not stopped or altered. No generation, remote mutation or
  retained-data deletion. Historical generation count stays five.
- pip-audit2.10.1: 58 main dependencies, zero known findings. Trivy0.76.1 actual
  final image scan: 44 HIGH,64 MEDIUM,62 LOW,1 UNKNOWN,0 CRITICAL (171 rows);
  8 distinct HIGH CVEs, no fixed versions reported. HIGH gate FAIL, no ignores.
  CycloneDX SBOM generated privately; public sanitized findings/hash retained.
- Final report: docs/release/SPEC-030-PUBLICATION-READINESS.md. **NO-GO** pending
  maintainer/security-reviewer triage/mitigation for exact OS findings. Remote
  Actions NOT_RUN, GitHub private reporting unconfirmed, owner author-email/
  license/publication review outstanding. No publication authority was granted.
- Leave this single plan active for the material security disposition; do not
  archive/declare local release readiness while the HIGH gate is unsatisfied.
  No additional implementation/inference is implied by a future continuation;
  resume from the recorded candidate and actual security decision.
