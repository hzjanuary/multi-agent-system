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

## Phase 2 — authorized OS remediation (2026-10-27)

Resume from clean f185c02 on the same branch. Maintainer authorizes supported OS
updates, concrete package removal/build isolation, complete triage and a new
actual runtime image. Preserve Python dependency lock, non-root runtime, licenses,
all release-security gates, SPEC-029 and operator/historical state. No provider
requests, inference, remote write/publication or residual-risk approval.

- [x] P2.1 bind old artifact/scanner/database identity; compare current same-suite
  base and supported updates; vendor data and actual runtime package/function proof.
- [x] P2.2 full HIGH/UNKNOWN and grouped MEDIUM/LOW machine-readable triage;
  distinguish OS/language rows, CVEs, packages, vendor severity/fixes/exposure.
- [x] P2.3 implement supported pinned minimal remediation and offline regressions.
- [x] P2.4 commit/build final candidate, comparable same-DB old/new scans, SBOM,
  license/manifest; full backend/ops/lint/type/lock/security/audit/Compose/install.
- [x] P2.5 update release decision/evidence; read-only disclosure check, precise
  future authorized remote CI steps, risk ownership and remaining decisions.


### Phase 2 result / next boundary

- Starting f185c02 clean. Runtime/code source 281537a24220f6a2fe2df2aaa438e1f9cb60a6a6;
  local image sha256:7e94df64783b09c385a9aebb3b7ba05289b20a5879bfe6fd40e43d56070f4c3c.
  Host CI/triage refinement f5a1bc7 adds only CI/tool metadata/report assessment;
  final docs do not change the 139-file build-input identity
  86f6a9a6a47dfd34dc804c5ad8bd5558c7a40241e46dfaf2df7af726ae8a1e43.
- Official registry same-suite tags still resolve existing base digest; apt
  update/simulate upgrade has 0 upgrades. Bookworm supported amd64 LTS metadata
  examined; same principal HIGHs open, not adopted. No unpinned apt upgrade or
  unsupported source-package/ABI mixing, Python distribution change or Redis change.
- Actual unused non-Essential mount purged; pip/ensurepip removed from merged
  runtime, dependency installation remains in build stages. Essential ncurses-bin/
  util-linux/coreutils and libraries retained; no scanner metadata deletion.
  Compose drops ALL caps and enables NNP; actual API/worker HostConfig and runtime
  CapEff=0/CapBnd=0/NoNewPrivs=1 observed with corresponding flags.
- Original 171 rows =164 OS/7 language; baseline rescan with frozen DB reproduces
  counts. Candidate 159 rows =158 OS/1 language: 0C/40H/58M/60L/1U. Twelve rows
  removed due to actual mount/pip removal, 0 vendor-version fixes, 0 new rows.
  OS unique CVEs 71 unchanged. OS supported-fixable rows 0; Mako Windows-path
  MEDIUM with Trivy fixed1.4.2 remains separately pending; app lock preserved.
- Trivy0.76.1 DB UpdatedAt2026-10-27T13:12:49.474279883Z; identical DB hash
  9d08581c36e14a521489a0f659093fd0bf435151361e6b01c13d2d6ec6672047,
  --skip-db-update, --ignorefile /dev/null, all severities/no ignore-unfixed.
  HIGH gate FAIL; no exception. HIGH/UNKNOWN affected components checked; homed,
  Archive::Tar, Pod::Text absent with actual module/file/package proof, without
  suppressing rows or granting general source-package exemptions.
- Full local backend242PASS+2warnings, lock/Ruff/Black/strictMyPyPASS; ops79PASS.
  Source/index/context/image/licensingPASS:86OS/58Python/170shipped files. Fresh
  isolated clone migrate empty/bootstrap/healthy API+worker/doctor/separate CLI
  login/discovery/auth0600/containmentPASS. Python audit58/0known, Trivy retains
  separate MEDIUM. All phase2 services stopped; every volume/config/CLI retained.
- Full detailed public triage and provenance: docs/release/SPEC-030-OS-TRIAGE.md,
  spec-030-phase2-triage.json, spec-030-phase2-evidence.json. Original scans, logs,
  history and SPEC-02932PASS remain preserved; no provider request/inference.
- Read-only GitHub public GET200/enabled=false proves disclosure disabled; owner
  enable/verify pending, no settings writes. RemoteCI NOT_RUN; branch push filter
  and exact sanitized proof artifact upload pinned/prepared; no push authorized.
- **NO-GO**: remaining HIGH/no-fix applicability/exposure/mitigation/residual risk
  requires owner/security decision, not automatic waiver. MEDIUM review and LOW
  maintenance owned by maintainer, reassess before release or2026-11-26.
  Plan stays active; required security release gate has not passed, so do not
  declare all engineering Definition-of-Done/release prerequisites complete.
  Next work requires vendor-fixed digest or explicit scoped risk decision; no
  new campaign, paid inference, architecture migration or publication implied.

## Phase 3 — bounded security signoff package (2026-10-27)

Authority: explicit owner request to reconcile residual risk and prepare decisions,
not accept risk, change scanner/CI policy, rebuild/refactor or publish. Starting
clean e3ec3f7. Keep raw Phase2 scan and all prior evidence byte-for-byte.

- [x] Reconcile all 40 HIGH rows at binary/component level, distinguish source-
  package duplication from image-level risk; separately review UNKNOWN and Mako.
- [x] Produce SECURITY-SIGNOFF and a non-executable decision ledger, technical
  proof/provenance, explicit owner/reviewer/expiry/reassessment requirements.
- [x] Map local gates to CI; exact approved-SHA future commands, evidence and
  disclosure enable/verify steps. No remote execution or settings changes.
- [x] Verify new documents/index/source and historical hashes; stop at owner
  boundary. Keep mandatory risk/disclosure/remote-CI/publication decisions open.


### Phase 3 closeout — decision package prepared, owner boundary retained

- SECURITY-SIGNOFF.md and non-executable spec-030-security-decisions.json cover
  every remaining raw HIGH tuple exactly once (CVE/package/version/severity).
  Counts: supported-fix0; confirmed affected/no supported fix6; unresolved
  per-binary source-package attribution31; concrete component absence3.
  Six image-level CVEs still have affected primary components. No claim that
  libraries are safe merely because the application normally does not call them.
- New network-disabled read-only exact-image inspection binds actual ownership/
  hashes/exports for libmount1/libacl1/nsenter/infocmp. It calls no affected API,
  mounts no operator volume, starts no application service and changes no image.
- Nine official vendor advisory pages reviewed; supported trixie fixed version
  not announced. Original Phase2 raw scan/hash/severity and all 40 records remain
  unchanged. UNKNOWN Pod::Text absence reviewed separately; Mako MEDIUM retained.
- Three HIGH decision groups require owner hzjanuary plus named security reviewer
  (unassigned), exact scope, review/signature/expiry and reassessment no later
  than2026-11-26 or earlier material change. No exception candidates, VEX, active
  exceptions, risk approval, adjusted result or scanner/CI policy change created.
- CI gate coverage reviewed step-by-step; copyable future exact-owner-approved-SHA
  push/watch/failure/artifact procedure and mandatory run/source/image/DB proof
  recorded. RemoteCI NOT_RUN. Private reporting last observed disabled; exact
  owner Enable + form/GETtrue verification steps prepared, no settings operation.
- Focused reconciliation/historical hashes/link checks PASS; tracked secret/path
  scan247files PASS; 139 build inputs retain content hash86f6a9a6a47dfd34dc804c5ad8bd5558c7a40241e46dfaf2df7af726ae8a1e43.
  Source archive gate verified after local documentation commit. Phase2 backend
  242PASS/ops79PASS evidence retained, NOT rerun; no executable inputs changed,
  no rebuild/rescan claimed. SPEC02932PASS/0BLOCKED preserved.
- NO-GO: mandatory raw HIGH gate remains FAIL. Phase3 preparation is complete,
  SPEC030 stays active/unarchived pending owner/security decisions, genuine remote
  CI, verified private disclosure and separate publication authority. No inference,
  push/merge/tag/publication/deployment/history rewrite or retained-data deletion.

## v0.1.0 early SOURCE preview — owner publication authority (2026-10-28)

Owner explicitly authorizes reviewed source branch push, PR to main, normal merge
if protections permit, and v0.1.0 pre-release with GitHub-generated source only.
This supersedes prior no-remote-action boundary only for this source publication.
Known OS findings remain disclosed; no security gate/policy downgrade, reviewer
signature, Docker-image publication or production-security approval is authorized.
Stop for real secrets/private artifacts, integrity defects, unexpected blockers
or branch protection; no force push/bypass. Keep this SPEC030 plan active.

- [x] Confirm live main/remotes/tag collision/protections/PVR; inspect new history.
- [x] Visitor-focused README with visible security notice; source-only owner
  decision, current disclosure evidence and honest historical image provenance.
- [x] Local secrets/private-path/source/license/link/meaningful test checks.
- [x] Push reviewed branch, create/review PR; record actual Actions outcomes.
- [ ] Normal merge only if protections permit and no unexpected blocker; verify
  resulting tree contains headless code and excludes retired active demo stack.
- [ ] Create v0.1.0 pre-release, source archives only; verify tag/main/release/
  archive/disclosure read-only; record outcome without claiming image signoff.


### Source preview pre-push checkpoint

- Live public main92e5f1c is the retired product and an ancestor; intended
  replacement removes legacy frontend/demo/RAG/Telegram active files (not operator
  volumes). Normal merge retains history. No v0.1.0 tag/release exists. Main is
  unprotected (protection404), rulesets empty at read-only preflight.
- Live PVR GET true recorded, owner enabled it independently. README security
  section is before installation and discloses exact recorded raw counts/image
  limits. Source-only owner scope is distinct from image NO-GO; internal version
  0.2.0 preserved, source milestone v0.1.0 per explicit owner authority.
- New-range history27commits/332blobs reviewed:7 findings in one historical
  scanner-test blob (temporary scanner inputs/redaction assertions, deterministic
  token scaffolds/incomplete key marker), no confirmed real credential. No blanket
  exception or current scanner policy change. Current tree has no legacy active
  modules/private paths; links/LICENSE/NOTICE PASS.
- Local ops79PASS; lock/Ruff/Black124files/MyPy122files PASS; scanner/index248
  files PASS. Historical full backend242PASS remains bound to original source;
  actual remote backend/database suite will run for the publication candidate.
  Source archive is checked after the local doc commit and before push.
- Known raw image findings remain0C/40H/58M/60L/1U and gateFAIL. No model calls,
  image publication, changed policy or security reviewer signature. Remaining
  remote outcomes will be recorded as observed, not assumed.


### Source preview stopped — new remote CI blocker (not the known OS gate)

- Source branch7f970293f56461a0909e244e64db1f11a42404b1 pushed normally; PR1
  https://github.com/hzjanuary/multi-agent-system/pull/1 OPEN, not merged. Reviewed
  GitHub tree matches all248 local blob hashes/modes;666 changed files include
  466 intended legacy removals. Actual GitHub branch source tar248files matches
  exact committed tree, secret/private-path/license checks PASS.
- Genuine push run40550114746/job122351242561 and PR run40550164202/
  job122351418089 FAIL at Isolated clean-clone installation without inference.
  Remote backend242PASS+2warnings, ops79PASS, lock/lint/type/secret/source/archive/
  image/license/Compose steps PASS. Python audit/Trivy/diff-hygiene SKIPPED due
  earlier install failure, not PASS and not a Trivy-known-HIGH failure.
- Read-only non-inference docker compose config reproduction confirms workflow
  global DATABASE_URL/JWT override helper's --env-file: API/worker database host
  localhost instead of isolated postgres. Helper inherits environment without
  sanitation. Remote logs retain only statusFAIL; inner command/stderr evidence
  was not uploaded, so do not assert this is the only cause. No code fix/retry
  or new image rebuild was initiated after the user-defined stop boundary.
- Full attempt details: docs/release/v0.1.0-publication-attempt.json. CI artifact
  contains image-verification JSON only; the image was built for checks, never
  published. Prior local raw40HIGH findings and security gate remain unchanged.
- Latest main still92e5f1cfb2b0144bdb39a48db99371974bd372a5 (old product).
  No v0.1.0 tag/release created. PVR live true. A later read finds active main
  ruleset25977726, PR-required/no-force/no-delete, no required status checks.
  No setting/bypass change by agent; stop is unexpected install FAIL, not an
  invented branch-protection rejection.
- Stop per explicit owner condition for new unexpected blocking issues. Next
  bounded remediation: isolate verify_release_install subprocess Compose env,
  retain sanitized failure operation/evidence, regression-test CI-like inherited
  env, then rerun actual checks before merge/release. No disable/relabel security.
- This outcome-record commit is local only, not a new remote candidate. Keep
  original pushed PR SHA/run evidence distinct. SPEC030 stays active; SPEC029
  remains32PASS/0BLOCKED. No inference, tag/merge/release/image publication/
  deployment/history rewrite or retained-resource deletion.


### Authorized clean-install CI isolation repair and source preview continuation

- Owner authorizes a narrow helper isolation/diagnostic correction, regression
  tests, hostile-parent local installation, relevant full gates, and update of
  existing PR1. Keep historical failed runs and known raw vulnerability gate.
- In progress: explicit safe host/Docker environment allowlist; compare resolved
  API/worker/CLI private database, Redis, JWT and model settings before startup;
  allowlisted public failure summary, private subprocess records, scoped stop.
- Required proof: synthetic hostile CI environment, stage/exit/redaction/cleanup
  regression tests, actual empty migration/bootstrap/readiness/separate CLI; no
  inference. Run new Actions candidate; Python audit and Trivy must execute.
- Resume normal merge/tag/source-only prerelease only if all newly required
  checks pass and remaining scan failure is limited to disclosed findings. Stop
  for new unexpected failure, material security delta or repository protection.
  No image publication, security policy relaxation, data deletion or new campaign.

- Local repair source866126702552e67017dd5d9679cb6ee9ff2e0449 verified:
  backend242PASS/2warnings/210.60s; ops90PASS (11 new regression tests), lock,
  Ruff/Black/MyPy122sourcefiles, Compose, tracked secrets/private paths, source
  archive, LICENSE/NOTICE and image integrity PASS. Runtime build inputs unchanged
  (139/hash86f6a9a6...), local rebuilt image3c33bcd31de18dccb7b08e0759787d224c93d41614c27cdd398f065b83b0b616.
- Actual hostile-parent install PASS: users/runs/events0/0/0 after migration,
  explicit bootstrap1/0/0, API/worker healthy and contained, separate CLI login/
  text_review discovery, auth0600. Four services stopped; volume/evidence retained.
- pip-audit2.10.1:58dependencies/0findings. Trivy0.76.1 frozen Phase2 DB:
  exactly identical159rows,0C/40H/58M/60L/1U; raw gateFAIL, no changed policy.
  First local setup errors (bridgeDNS, missing Redis test service) retained and
  corrected using existing host build-network option/isolated Redis; full gates
  subsequently PASS. No application/runtime/build-input change or model request.
- Private `.maos/spec-030/source-preview/ci-fix/` retains detailed logs/credentials;
  public `v0.1.0-clean-install-fix.json` only approved proof. Fresh remote push/
  PR Actions and source-only merge/release decision remain pending.

- New push40629729678/job122623054912 and PR40629733848/job122623067765 on
  head108547c completed: backend242/ops90/clean-install/audit/source/image/licenses
  PASS; only Trivy FAIL, diff hygiene SKIPPED (localPASS). Downloaded five exact
  allowlisted artifacts per run; ZIP digests match GitHub metadata. Both private
  profiles resolve postgres/redis correctly; all four services stopped.
- Trivy fetched updated DB2026-10-28T01:21:08Z/hash e68b667c74000c274351566d7bce26de2022f7937e4cc6e2787e2dbdac96e978.
  Full159-row multiset identical to historical scan:0new/0removed; raw0C/40H/
  58M/60L/1U, no gate/threshold/status changes. Python audit58deps/0vulns.
  Push source108547c image9148acdf76a0a8e2d54adf433b219a4eea89d216455336711ecebfbd4b98095c;
  PR synthetic merge source8f609371c078878e88fa305dbf345de4db3d3d06 image9a3e48f2f1da4bc8401086a1ce2f2e667d4564e231d366f6db0d83eaa1556298.
- Public actual evidence v0.1.0-remote-ci.json; earlier failed attempt evidence
  unchanged. Documentation-only checkpoint records observed results, not a false
  all-green CI or completed publication. Verify final candidate Actions and live
  rules, then owner-authorized normal merge/source-only prerelease. SPEC030 remains
  open for security maintenance; no Docker publication/production approval.
