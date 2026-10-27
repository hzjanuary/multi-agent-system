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
  `/usr/local/lib/python3.12/LICENSE.txt` remain readable in the base image.
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

## Phase 2 OS disposition and current candidate

Latest evidence: [OS triage](SPEC-030-OS-TRIAGE.md),
[machine-readable rows](spec-030-phase2-triage.json),
[provenance](spec-030-phase2-evidence.json). Original Phase 1 evidence is retained.
The previous 171 rows mixed 164 OS and 7 Python findings; use the separate counts.
Candidate has 158 OS + 1 Python row; **NO-GO, 40 HIGH not waived**. Removing the
unused mount package and build-only installers is not a vendor-version fix.

For comparable scans, copy the already downloaded Trivy `db/` to a new private
cache, preserve metadata/DB hashes, then run both actual image IDs through
`release_security.py scan-image --cache-dir <private-cache> --skip-db-update`.
Normal CI still refreshes the advisory database; record its timestamp and separate
DB drift from runtime changes. Never reuse old counts without binding the DB.
The script refuses incomplete/no-OS results; all severities remain in its report.

HIGH/CRITICAL gates remain active including unfixed issues. A supported applicable
fix must be applied; otherwise owner/security review needs exact applicability,
exposure, containment and residual risk, not just "no fix". MEDIUM needs an owner
maintenance decision; LOW is tracked; UNKNOWN requires explicit investigation.
No exceptions have been approved. Reassess current groups before release or
2026-11-26, whichever is earlier. A future exception must name CVE/package/version,
reason/proof, owner, review date and expiry/reassessment condition and require
explicit approval; no broad ignore or automatic risk acceptance.

## Remote CI — only after owner authorizes push

Do not run this block during local hardening. It is the minimal future procedure
for the reviewed candidate, not publication approval. The workflow push filter
includes the SPEC-030 branch; no PR, merge, tag or release is required.

```bash
spec030_candidate_sha=$(git rev-parse HEAD)
git status --short
# Proceed only after owner approval of this exact clean candidate.
git push origin HEAD:refs/heads/feat/spec-030-open-source-release-hardening
gh run list --repo hzjanuary/multi-agent-system --workflow ci.yml --branch feat/spec-030-open-source-release-hardening --commit "$spec030_candidate_sha" --json databaseId,headSha,status,conclusion,url
# Substitute the returned run ID; inspect that headSha equals the approved SHA.
gh run watch <run-id> --repo hzjanuary/multi-agent-system --exit-status
gh run view <run-id> --repo hzjanuary/multi-agent-system --log-failed
gh run download <run-id> --repo hzjanuary/multi-agent-system --name "release-security-$spec030_candidate_sha" --dir .maos/remote-ci/<run-id>
```

Without GitHub CLI, use Actions → Release candidate CI, select the exact push
commit, inspect job logs and download `release-security-<source-sha>`. Record run
URL/ID, head SHA, workflow result, tool/DB identity and reviewed artifact hashes in
a new evidence entry. Do not relabel local proof as remote PASS. Current known
HIGHs are expected to fail the security step; investigate, do not disable it.
Only exact sanitized scan/SBOM/audit/image-verification files are uploaded, even
on failure; no whole `.maos/`, credentials, sessions, build logs or private inputs.

## Disclosure and owner gate

Read-only documented GitHub GET returned **200 / enabled=false** on
2026-10-27T16:08:12Z. The connector did not support this endpoint; the fallback was
the public unauthenticated API, not a privileged settings write. Owner must enable
Private Vulnerability Reporting under repository Settings → Security and quality
→ Advanced Security, then verify the private reporting form and update evidence.
Remote CI NOT_RUN, private reporting disabled/pending owner action, residual-risk
review and final explicit publication approval remain prerequisites.


## Owner signoff package (Phase 3)

Use [SECURITY-SIGNOFF](SPEC-030-SECURITY-SIGNOFF.md) and
[per-row decision ledger](spec-030-security-decisions.json) before any publication
decision. The 6/31/3 categories are component-level reconciliation of 40 raw HIGH
rows, not an adjusted scan. No active exception or approved residual risk exists.
All named owner/reviewer decisions, genuine CI and private reporting proof remain
pending. For a future authorized push, enforce the exact clean owner-approved SHA
checks in the signoff procedure; record push event/headSha/image/DB/artifact and
every required step outcome. A skipped check is NOT_RUN. This task did not push
or invoke a workflow, change settings/policy, rebuild or archive the plan.
