# Release candidate checklist

A local build never authorizes publication. SPEC-029 remains 32 PASS / 0 BLOCKED;
its successful direct Groq inference belongs to its recorded source/image, not a
new packaging candidate. Cloudflare is configured/offline-tested, not live-verified.

1. Review `SPEC-030-PUBLICATION-READINESS.md` and all outstanding risk dispositions.
2. Install locked backend tooling; run `scripts/ci/all-gates.sh` with an explicitly
   isolated `MAOS_TEST_DATABASE_URL` and private generated configuration for Compose.
3. Commit the reviewed candidate locally. Run `bash scripts/ci/release-gate.sh`.
   Root context is mandatory: the Dockerfile copies canonical LICENSE/NOTICE.
   `MAOS_BUILD_NETWORK=host` is an optional host-specific package-index workaround.
   The default tag is revision-specific; no historical image is overwritten.
4. Export locked main requirements and run pip-audit 2.10.1 with hashes, no
   dependency resolution/ignore list. Install Trivy using
   `python3 scripts/ops/release_security.py install-trivy --tool .maos/tools/trivy`.
   Run `python3 scripts/ops/release_security.py scan-image --tool .maos/tools/trivy
   --image <candidate-tag> --output .maos/release-security`.
   HIGH/CRITICAL, including unfixed findings, block release. Scan failure is not
   a clean result. Review lower-severity findings separately. SBOM is CycloneDX.
5. Rehearse empty install, explicit bootstrap, API/worker readiness, doctor and
   CLI across separate containers in a new named project; stop without deleting
   volumes. No model calls are required for packaging verification.
6. After separately authorized push, require actual remote GitHub Actions on the
   exact candidate. Local command reproduction is not remote CI verification.
7. Maintainer: enable and verify private vulnerability reporting (SECURITY.md),
   review historical public author email, confirm license obligations and resolve
   security blockers. Owner approval is required before any publication/tag/push.

## Inventory and license scope

Root MIT applies to project-owned source. In the runtime image:

- `/app/licenses/project/LICENSE` and `/app/licenses/project/NOTICE` exactly match
  the candidate's root files. No manually maintained duplicate is used.
- `/app/licenses/inventory.json` lists actual installed Python distributions,
  declared licenses, copied full notices and hashes; OS package versions and
  `/usr/share/doc/<package>/copyright`; `/usr/share/common-licenses` and
  `/usr/local/LICENSE` remain readable in the base image.
- Exact-version supplements and immutable upstream evidence are in
  `release/third-party/sources.json`. langchain-core 1.4.9 and langsmith 0.10.2
  wheel/sdist omit their MIT text: the build supplies full verified upstream
  texts, checks exact versions, and fails if evidence is missing/stale.
- certifi is MPL-2.0: upstream notice, full MPL text and readable unmodified PEM
  source are shipped. Its license does not relicense the application.
- PostgreSQL, Redis, optional Ollama and base OS have independent licenses.
  **Redis 7.4 is RSALv2 OR SSPLv1, source-available, neither OSI-approved**;
  the whole Compose stack must not be described as MIT or OSI-only.
  See [Redis's license terms](https://redis.io/legal/licenses/) and
  `release/third-party/stack.json`. No Redis replacement is authorized here.
- Model weights and remote services are not shipped and retain separate terms.
  No universal legal compliance/certification is asserted. This release candidate
  targets source archive/Docker; PyPI wheel publication is outside this procedure.

## Update and exception policy

Review `release/images.lock.json` monthly and before releases: fetch official
registry manifest bytes, verify their SHA256 against the registry digest, review
version support/advisories/licenses, then update Dockerfile/Compose/CI together.
Run image, vulnerability and isolated install gates again. Digest pins provide
content identity, not indefinite support or byte-for-byte image reproducibility.
Poetry lock hashes protect runtime downloads; build tools/pip base state and
vulnerability DB timestamps remain part of recorded provenance.

Actions use immutable verified commits. Trivy archive and binary hashes are
locked in `release/tools.lock.json`; updates require upstream release/checksum
verification, not a mutable installer. No vulnerability exceptions currently
exist. A future exception needs exact CVE/package/version, applicability proof,
owner, expiry and explicit release decision; never blanket ignore unfixed issues.

Scanner allowances in `scripts/ci/secret-fixtures.json` are exact path + full-line
SHA256 + review reason for synthetic fixtures/historical isolated test metadata.
Changing a line invalidates it; adjacent or appended credentials still fail.
Never generate approvals from unreviewed findings. The worktree policy must
match the staged policy. All tracked text, including tests/CI/agent files, is
scanned; binary/unreadable/oversized inputs fail closed for explicit review.

Git ignore rules are convenience only. The index gate rejects force-added
private paths and symlinks. The root Docker context is a deny-by-default
allowlist; context verification independently rejects modified, untracked or
linked build inputs. Source archive and actual image manifests are independently
compared to the committed source. Keep generated scans/logs/source archives in
ignored private storage; publish only reviewed sanitized evidence.
