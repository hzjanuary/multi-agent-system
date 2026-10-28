# SPEC-030 Phase 3 — Security signoff / owner decision package

**Khuyến nghị: NO-GO. Owner/security signoff chưa được cấp.** Ngày review
2026-10-27. Đây là hồ sơ quyết định, không phải Trivy ignore/VEX hoặc policy mới.
Không thay application, image, CI hay severity; không archive SPEC-030.

## Artifact và giới hạn kết luận

- Handoff được review: `e3ec3f7cfdb994365cae743e14490b9457352133`.
- Runtime source: `281537a24220f6a2fe2df2aaa438e1f9cb60a6a6`.
- Exact image: `sha256:7e94df64783b09c385a9aebb3b7ba05289b20a5879bfe6fd40e43d56070f4c3c`, linux/amd64, Debian 13.7.
- Trivy 0.76.1; DB UpdatedAt `2026-10-27T13:12:49.474279883Z`, DB SHA256
  `9d08581c36e14a521489a0f659093fd0bf435151361e6b01c13d2d6ec6672047`.
  Raw scan SHA256 `22f93fdbcfca00b19647cbf4012420e713ffb0880df39a17101320626deee0cb`;
  file gốc giữ riêng `.maos/spec-030/phase2/candidate-scan/image-vulnerabilities.private.json`.
- Raw counts **0 CRITICAL / 40 HIGH / 58 MEDIUM / 60 LOW / 1 UNKNOWN** giữ nguyên.
  Kết quả gate vẫn **FAIL**, policy-adjusted result **NOT_PRODUCED**.
- [Ledger từng row/quyết định](spec-030-security-decisions.json),
  [component ownership/hash/symbol proof](spec-030-security-component-proof.json),
  [triage lịch sử](spec-030-phase2-triage.json), [provenance](spec-030-phase2-evidence.json).

Phase 3 đọc lại advisory Debian cho 8 HIGH CVE và UNKNOWN; các trang vẫn ghi
trixie vulnerable, không công bố supported trixie fixed version. Không đồng nhất
bản upstream/unstable đã sửa với distro backport. Apt candidate inspection giữ
nguyên từ Phase 2; Phase 3 không chạy apt, scan DB mới hoặc rebuild. Đây là kết
luận có thời điểm, phải kiểm tra lại trước release nếu vendor cập nhật.

Có thêm một container kiểm tra **read-only/network-none**, không API/worker/DB,
chỉ đọc ownership/hash và symbol exports của 4 binary/library; không gọi hàm
mount/ACL, không đổi namespace hay thử exploit. Proof ràng buộc đúng image ở trên.

## Phân loại đủ 40 HIGH

**Đơn vị đếm là scanner row (CVE + reported binary package), không phải số CVE.**

| Phân loại | Rows | Ý nghĩa |
| --- | ---: | --- |
| Confirmed affected, supported fix available | **0** | Không có supported trixie fix được tìm thấy trong evidence review |
| Confirmed affected, no supported fix | **6** | Package sở hữu component được vendor mô tả, vulnerable distro version và binary/library/function hiện diện |
| Not affected, concrete component absence | **3** | 2 homed rows + 1 Archive::Tar row; không dựa vào “thường không gọi” |
| Unresolved, insufficient per-binary attribution | **31** | Source-package propagation; chưa đủ proof từng reported package chứa code bị lỗi, **không** tự đổi thành not affected |
| **Tổng** | **40** | Mọi row, installed version và advisory đều trace được trong ledger |

Ở **image/CVE level**, cả 6 CVE thuộc util-linux/acl/ncurses vẫn có component
bị ảnh hưởng. Ba mươi mốt row attribution chưa rõ không phải 31 CVE độc lập và
không làm giảm 6 image-level risks này. Chúng cũng không được tự gán confirmed
cho mọi thư viện chỉ vì cùng source package. Không thực hiện exploitation proof;
confirmed ở đây là component/version affected, không phải mọi deployment đều
khai thác được. Non-root, NNP/cap-drop hoặc không có call path thông thường là
mitigation, không phải bằng chứng not affected.

### Package/version sets và HIGH disposition matrix

Các tập dưới đây giữ nguyên binary versions (bao gồm epoch/rebuild suffix):

- **U (8):** bsdutils `1:2.41.5-0+deb13u1`; libblkid1, liblastlog2-2,
  libmount1, libsmartcols1, libuuid1, util-linux mỗi package `2.41.5-0+deb13u1`;
  login `1:4.16.0-2+really2.41.5-0+deb13u1`.
- **N (4):** libncursesw6, libtinfo6, ncurses-base, ncurses-bin đều `6.5+20250216-2`.
- **A (1):** libacl1 `2.3.2-2+b1` (source `2.3.2-2`).
- **S (2):** libsystemd0, libudev1 đều `257.13-1~deb13u1`.
- **P (1):** perl-base `5.40.1-6+deb13u1`.

| CVE / reported set | Affected primary component | Confirmed no-fix / unresolved / not affected | Vendor / decision |
| --- | --- | --- | --- |
| CVE-2026-76642 / U | libmount1 owns libmount.so.1; mount context API exported. Standalone mount tool removed, library retained | 1 / 7 / 0 | [Debian](https://security-tracker.debian.org/tracker/CVE-2026-76642); SG-UTIL-LINUX |
| CVE-2026-78408 / U | util-linux owns nsenter; --join-cgroup present | 1 / 7 / 0 | [Debian](https://security-tracker.debian.org/tracker/CVE-2026-78408); SG-UTIL-LINUX |
| CVE-2026-78409 / U | libmount1 retained; vulnerable distro version. Kernel/fstab/privilege conditions constrain exposure, not component classification | 1 / 7 / 0 | [Debian](https://security-tracker.debian.org/tracker/CVE-2026-78409); SG-UTIL-LINUX |
| CVE-2026-78410 / U | libmount1 retained; privileged bind-mount/ownership context is not an app workflow | 1 / 7 / 0 | [Debian](https://security-tracker.debian.org/tracker/CVE-2026-78410); SG-UTIL-LINUX |
| CVE-2026-54369 / A | libacl1 owns libacl.so.1; all four vendor-named pathname ACL functions exported | 1 / 0 / 0 | [Debian](https://security-tracker.debian.org/tracker/CVE-2026-54369); SG-ACL |
| CVE-2025-69720 / N | ncurses-bin owns infocmp; executable present, vulnerable distro version | 1 / 3 / 0 | [Debian](https://security-tracker.debian.org/tracker/CVE-2025-69720); SG-NCURSES |
| CVE-2026-16742 / S | systemd-homed service/package/executable absent; installed shared libs do not supply the advisory's homed authenticate service | 0 / 0 / 2 | [Debian](https://security-tracker.debian.org/tracker/CVE-2026-16742); exact-image absence review |
| CVE-2026-9538 / P | No Archive/Tar.pm; Perl module load fails. Absence, not merely non-use | 0 / 0 / 1 | [Debian](https://security-tracker.debian.org/tracker/CVE-2026-9538); exact-image absence review |

Debian's no-dsa/minor-issue/urgency annotations are not used to downgrade Trivy
HIGH. The 3 not-affected technical dispositions apply only to those CVEs and
this exact image/module set. Raw records remain; they do not approve an ignore
or establish that all systemd/Perl source-package issues are irrelevant.

## Owner residual-risk decision records — all PENDING

Required approvers: repository owner **hzjanuary** and a **named security
reviewer (currently UNASSIGNED)**. Review date 2026-10-27. Each decision includes
all exact CVE/package/version row IDs in the ledger; no source-package wildcards.

| Record / scope | Remaining exposure and potential impact | Mitigation / proposed disposition |
| --- | --- | --- |
| **SG-UTIL-LINUX:** 32 U rows; CVE-2026-76642, -78408, -78409, -78410 | libmount/nsenter remain; privileged mount/namespace/operator interactions can alter permissions, expose host paths or affect unrelated processes. Custom extensions, altered capabilities/kernel/fstab or root/operator actions change exposure; 28 binary-attribution rows unresolved | mount/umount removed, empty fstab, non-root, cap-drop ALL, NNP; no app mount/namespace path. **Defer publication** until supported fix or explicit scoped owner/security decision |
| **SG-ACL:** libacl1 / CVE-2026-54369 | Pathname ACL operations can follow attacker-controlled symlinks in privileged consumers. App has no ACL call path, but callable library/utilities remain. “No normal call” does not eliminate risk | Non-root/NNP restrict privilege escalation; restrict untrusted local files/extensions. **Defer publication**; do not import an unsupported ABI or approve risk automatically |
| **SG-NCURSES:** 4 N rows / CVE-2025-69720 | Malformed infocmp input can corrupt memory/crash; impact follows the invoking process's privileges. Executable remains in Essential ncurses-bin; 3 binary-attribution rows unresolved | No app invocation; unprivileged process/NNP; do not feed hostile local data to utilities. **Defer publication**; do not remove Essential metadata to obtain green scan |

**No risk acceptance recommended solely because no fix exists.** If owner wants
to consider a time-bound exception, the necessary conditions are:

1. Record exact approved image, source, CVE, binary package/version and every
   covered row. Resolve attribution or explicitly review the still-affected
   image/CVE risk; do not call missing attribution a false positive.
2. Review exposure/impact and why the existing mitigations are adequate for the
   intended release audience. Keep trusted extensions, non-root, ALL capabilities
   dropped, NNP, no privileged/host-system/Docker-socket mounts and restricted
   exposure. These are necessary proposed boundaries, not proof of acceptable risk.
3. Assign named owner and reviewer, signed decision/date and an expiry **no later
   than 2026-11-26**, or earlier when required by review. Reassess immediately on
   any image/base/package/kernel/extension/security-option change, new exploit,
   supported fix or advisory update; before release if earlier.
4. Separately authorize and review any narrowly scoped policy implementation;
   retain raw scan and policy-adjusted result side by side. Current scanner/CI
   code cannot become green merely because this document is signed.
5. Obtain genuine remote CI and disclosure proof and separate final publication
   approval. The conditions above do **not** constitute an accepted exception.

No machine-readable exception candidate or VEX is generated: the ledger is a
non-executable decision record, not consumed by CI. Active exceptions and owner
approvals are empty. For the 3 component-absence rows, the named reviewer should
validate scope first; even a later scoped adjustment would leave all other
unresolved/affected HIGHs blocking under the current policy.

## MEDIUM / LOW / UNKNOWN and Mako

- **57 OS MEDIUM:** keep vendor/package remediation groups from Phase 2; owner
  maintenance/applicability decision still required before release. Core runtime
  glibc/gcc/ACL/compression/SQLite/PAM groups are not automatically safe.
- **1 separate Python MEDIUM:** Mako `1.3.12`, CVE-2026-102991; Trivy reports
  `1.4.2` as fixed and a Windows TemplateLookup path issue. Linux alone is not
  an approved exception. Preserve lock; reviewer must reconcile platform/source
  applicability and dependency maintenance. pip-audit's 0 known findings does
  not override Trivy's different advisory coverage.
- **60 LOW:** tracked vendor maintenance, owner/reviewer to confirm review cadence
  before release or 2026-11-26; no blanket accepted-risk approval recorded.
- **UNKNOWN CVE-2026-82560 / perl-base:** affected Pod::Text is absent by file
  search and failed module load in exact image. Retain **UNKNOWN** in the raw
  scan, not LOW/PASS. [Vendor](https://security-tracker.debian.org/tracker/CVE-2026-82560).
  Reassess when image/Perl modules/extensions change. Technical absence proof
  is distinct from permission to alter policy.

## Remote CI coverage and exact owner-authorized procedure

Workflow `.github/workflows/ci.yml`, job **backend** currently maps:

| Local gate | Remote step/script |
| --- | --- |
| Full backend tests, Ruff/Black/strict MyPy, lock | Offline and database gates → `scripts/ci/backend-gate.sh`, isolated PostgreSQL/Redis services |
| Full ops/security + changed ops lint/format | Operations and release-security tests |
| Tracked secrets/private paths | Full tracked-file secret and private-path scan |
| Source archive, context, actual image/revision/content/license | Source archive, release build, revision, licenses and image manifest → `release-gate.sh` |
| Canonical/dev Compose and CLI importability | Validate CLI and Compose without provider credentials |
| Migration, empty DB/bootstrap, health/doctor, separate CLI | Isolated clean-clone installation without inference |
| Locked Python dependency vulnerability audit | Python dependency vulnerability audit, no exceptions |
| Actual image OS/language scan, DB provenance, SBOM | OS and language vulnerability scan, HIGH/CRITICAL fail |
| Sanitized proof on failure | Always upload exact scan/SBOM/audit/image-verification paths, immutable Action pin |

Corresponding automated gates exist; **remote CI is NOT_RUN**. Steps are
sequential: an earlier failure can skip later checks; skipped/missing checks are
NOT_RUN, never PASS. Owner risk/disclosure/signature review and this Phase 3
binary-attribution review are manual governance evidence, not automated CI signoff.

Only after owner approves an exact clean source SHA, use the existing
[copyable checklist procedure](RELEASE-CHECKLIST.md).
Push uses the scoped SPEC-030 branch filter, not main/merge/tag/publication.
Before its push command, require:

```bash
spec030_approved_sha='REPLACE_WITH_OWNER_APPROVED_40_CHAR_SHA'
test -z "$(git status --porcelain)"
test "$(git rev-parse HEAD)" = "$spec030_approved_sha"
# Owner-authorized future action only; not executed in this review.
git push origin "$spec030_approved_sha:refs/heads/feat/spec-030-open-source-release-hardening"
gh run list --repo hzjanuary/multi-agent-system --workflow ci.yml --branch feat/spec-030-open-source-release-hardening --event push --commit "$spec030_approved_sha" --json databaseId,headSha,status,conclusion,url
spec030_run_id='REPLACE_WITH_RUN_ID'
gh run watch "$spec030_run_id" --repo hzjanuary/multi-agent-system --exit-status
gh run view "$spec030_run_id" --repo hzjanuary/multi-agent-system --log-failed
gh run download "$spec030_run_id" --repo hzjanuary/multi-agent-system --name "release-security-$spec030_approved_sha" --dir ".maos/remote-ci/$spec030_run_id"
```

Required evidence: workflow URL/run ID/attempt, event=push, headSha equals approved
SHA, immutable workflow version, all required step outcomes, image revision and
actual digest, Python/OS scan raw status/counts, Trivy binary/DB time/hash, SBOM/
artifact hashes and reviewed failures. Current HIGHs are expected to fail. Do not
rerun until green by disabling gates. A new CI-built image or changed DB needs
matching component proof/reconciliation; local dispositions do not silently
transfer to a different digest. No workflow was invoked by this task.

## Private disclosure and final publication checklist

Prior read-only GET was **200/enabled=false at 2026-10-27T16:08:12Z**. Phase 3
has not changed or re-certified this setting; it remains disabled/pending owner
action in the evidence. Exact owner procedure:

1. Repository Settings → Security and quality → Advanced Security → Private
   vulnerability reporting → **Enable**, using owner's authorized session.
2. Verify Security → Advisories shows **Report a vulnerability**, and open the
   private form (do not submit a dummy report or public vulnerability details).
3. Read-only `gh api repos/hzjanuary/multi-agent-system/private-vulnerability-reporting --jq '.enabled'`
   must return `true`. Record timestamp/URL and sanitized form-availability proof;
   do not claim configured from the intended setting alone.

Before publication, owner must check:

- [ ] Resolve supported-fix blockers if vendor releases one; no such fix found in this review.
- [ ] Decide all three HIGH groups and binary-attribution uncertainties; validate 3 exact-scope absence rows and UNKNOWN; review Mako/MEDIUM/LOW maintenance.
- [ ] Any approved policy adjustment is separate, exact/time-bound/reviewed; raw scan remains visible. Current gate is still FAIL.
- [ ] Genuine remote CI on exact approved SHA/image, including all required checks and reviewed artifacts, not local test substitution.
- [ ] Private reporting enabled and form/API verified; owner/license/historical-email review from publication checklist completed.
- [ ] Explicit final owner permission to publish; neither a risk signature nor an approved push is permission to publish.

Local Phase 2 proof (242 backend/79 ops PASS) remains bound to its original
source/image; Phase 3 adds reconciliation, read-only component evidence and
focused documentation/index/integrity checks only. No backend-suite rerun or
image rebuild is claimed. SPEC-029 remains 32 PASS / 0 BLOCKED at its original
live provenance. **Stop at owner decision boundary: NO-GO, plan stays active.**


## Later owner decision — source-only publication

On 2026-10-28 the owner separately authorized the early v0.1.0 source preview
with disclosed residual OS risks. [Decision](v0.1.0-source-preview.md). This is not
a risk exception, image-distribution clearance or security-reviewer signature.
All technical findings, raw scan severity, gate FAIL and full-image NO-GO above
remain unchanged. The SPEC-030 plan stays active. Private reporting has since
been confirmed enabled during the publication session; prior disabled evidence
remains historical. Actual remote CI/publication results are recorded separately.
