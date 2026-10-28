# SPEC-030 Phase 2 — OS triage và candidate hardening

2026-10-27. **NO-GO**: 40 HIGH còn được scanner báo và chưa có owner approval
cho residual risk. Đã hoàn tất remediation độc lập, rebuild, triage và local
verification; security release gate vẫn FAIL. Không có exception/ignore mới.
SPEC-029 giữ **32 PASS / 0 BLOCKED**, 5 historical requests; không inference mới.

## Artifact và phương pháp

Baseline chính xác là image `sha256:21f4073e53b9f3a657a933867c6d6921fd9634c1d503618da25224cc59c42100`,
source `d84aeea6af592b56738456039445f480778744cf`. Candidate được build từ clean
source `281537a24220f6a2fe2df2aaa438e1f9cb60a6a6`, image
`sha256:7e94df64783b09c385a9aebb3b7ba05289b20a5879bfe6fd40e43d56070f4c3c`.
Các thay đổi CI/triage/documentation sau source này không đổi build inputs/runtime.
Digest là local OCI identity, chưa publish registry. OS cả hai: Debian **13.7**,
linux/amd64. Python/application lock và base digest không đổi.

Trivy **0.76.1**, binary SHA từ tools lock. Phase 2 scan lại baseline và candidate
với **cùng DB bytes**, SHA256
`9d08581c36e14a521489a0f659093fd0bf435151361e6b01c13d2d6ec6672047`:
DB UpdatedAt `2026-10-27T13:12:49.474279883Z`, DownloadedAt
`2026-10-27T15:14:44.805351599Z`. Dùng `--scanners vuln --skip-db-update`, cache
riêng, `--ignorefile /dev/null`, không severity filter hay ignore-unfixed. SBOM
CycloneDX tạo trên final image. Các timestamp scan, package/source versions,
vendor statuses/severities/fixes, probe/hash đầy đủ trong
[machine-readable triage](spec-030-phase2-triage.json) và
[provenance](spec-030-phase2-evidence.json).

Báo cáo lịch sử không embed DB metadata; metadata cache được khôi phục riêng.
So sánh Phase 2 dựa trên hai scan mới cùng DB, không suy đoán từ cache cũ.
Baseline scan lại có counts giống scan lịch sử; không có thay đổi count do DB
trong phép so sánh này. Original scans/SBOM và report Phase 1 được giữ nguyên.

## Before / after — không đồng nhất row với CVE

| Phạm vi | C/H/M/L/U trước | C/H/M/L/U sau | Rows trước → sau | Unique CVEs | Affected packages |
| --- | --- | --- | --- | --- | --- |
| Tất cả scanner findings | 0/44/64/62/1 | 0/40/58/60/1 | 171 → 159 | 78 → 72 | 42 → 40 |
| OS thực tế | 0/44/58/61/1 | 0/40/57/60/1 | 164 → 158 | **71 → 71** | 40 → 39 |
| Python packages | 0/0/6/1/0 | 0/0/1/0/0 | 7 → 1 | 7 → 1 | 2 → 1 |

- **Version-fixed findings: 0.** Không tìm được supported OS upgrade trong apt.
- 12 record biến mất vì package thật bị gỡ: mount 6 (4 HIGH/1 MEDIUM/1 LOW),
  pip 6 (5 MEDIUM/1 LOW). Không nói 12 CVE đã được vá; các util-linux CVE vẫn có
  record ở package thư viện khác. Không có record mới.
- Remaining scanner-fixable: **OS 0; Python 1** (Mako 1.3.12 → 1.4.2 theo Trivy).
  Mako record mô tả Windows TemplateLookup path; image là Linux, luồng ứng dụng
  không dùng model input làm template path. Giữ lock theo authority; applicability/
  maintenance review riêng còn pending, không tự waive. pip-audit báo 0 trên 58
  main packages; hai scanner có advisory coverage khác nhau, không bỏ qua Trivy.
- 158 OS rows còn lại không được scanner báo fixed version. Điều đó **không**
  chứng minh an toàn. Scan all HIGH/CRITICAL vẫn trả exit 1.

## Lựa chọn và thay đổi thực tế

| Phương án | Evidence | Quyết định |
| --- | --- | --- |
| Refresh cùng `3.12-slim` / `3.12-slim-trixie` | Official registry metadata và manifest-byte SHA trỏ cùng digest `12316de…bfe8f` đã pin; apt update/simulate upgrade: 0 upgrades | Giữ base hiện tại; không tạo refresh giả |
| `3.12-slim-bookworm` | Verified digest `6dd8b6dab6b3adc7812bab69eca5dbdc1a5cc690ad28306d234ffb4ef8ac9753`; Debian LTS còn hỗ trợ amd64; tracker vẫn open các HIGH chính | Không đổi suite để giảm số đếm; chưa build/test phương án này |
| Apt security updates | Candidate versions từ trixie/trixie-security bằng installed versions cho HIGH/core runtime | Không unpinned upgrade, không lấy package unstable/ABI khác |
| Gỡ runtime tools | `mount` không được application gọi; apt simulation chỉ purge package này không Essential. pip chỉ cần khi build | Purge mount; uninstall pip trong build dependencies và runtime base; bỏ ensurepip runtime; giữ package DB, libs và notices |
| Gỡ libsystemd/libudev/ncurses-bin | Resolver cho thấy Essential dependencies; ncurses-bin Essential | **Không** force-remove Essential packages hoặc xóa metadata để né scan |
| Containment | Non-root cũ giữ nguyên; app không cần privileged ports/capabilities | API/worker/CLI/migrations qua Compose `cap_drop: ALL`, `no-new-privileges:true`; actual HostConfig và runtime probe được kiểm |

Application Python source, PostgreSQL/Redis pins và Python dependency lock không
đổi. Runtime còn 86 OS packages, 58 Python distributions; 170 shipped files qua
independent manifest/license gate. Pip/ensurepip/mount không còn trên merged
runtime filesystem. Build stages vẫn có installers; không tuyên bố toàn build
chain không có vulnerability. Các base layers gốc không bị rewrite. Extensions
cần install tool/dependency phải build image được review; không `pip install`
trong running runtime container. Không thay application business behavior.
Custom extensions gọi mount/pip hoặc cần capabilities bổ sung không nằm trong
integration proof này; phải review/rebuild và kiểm chứng riêng nếu có yêu cầu đó.
Không gán live Groq proof của image cũ cho image mới.

## HIGH và UNKNOWN — vendor và actual functionality

Tất cả HIGH có Debian trixie status open, không supported fixed version trong
snapshot/apt. `nodsa`/vendor urgency không được đổi thành severity scanner khác.
Full từng package/version/row nằm trong JSON; bảng này gộp remediation theo source.

| CVE / group | Actual runtime / exposure evidence | Disposition |
| --- | --- | --- |
| CVE-2026-76642 / util-linux | mount tool đã gỡ, libmount vẫn có; bug privileged post-mount hooks. App không mount; non-root/NNP/cap-drop kiểm được | Unresolved no-fix; library/custom extension exposure cần owner review |
| CVE-2026-78408 / util-linux | nsenter và --join-cgroup vẫn có; cần privileged operator/target interaction, không phải đường xử lý workflow | Unresolved; không gọi nó để thử exploit, không tự miễn trừ |
| CVE-2026-78409 / util-linux | Detached-tree symlink issue, libmount còn; không app filesystem mount, không CAP_SYS_ADMIN trong supported Compose | Unresolved; containment không thay vendor fix |
| CVE-2026-78410 / util-linux | Restricted bind mount ownership redirection; mount executable gỡ, libs còn; fstab image rỗng | Unresolved; root/privileged custom deployments ngoài bảo đảm này |
| CVE-2026-54369 / acl | libacl1 2.3.2-2+b1 còn, core utilities phụ thuộc; app không gọi ACL pathname API | Unresolved; upstream 2.4.0 không phải patched trixie package, không tự backport ABI |
| CVE-2025-69720 / ncurses | infocmp còn trong Essential ncurses-bin; app không invoke nhưng executable vẫn có | Unresolved; không xóa Essential package hay tự kết luận safe |
| CVE-2026-16742 / systemd | Advisory nhắm **systemd-homed** authenticate path. Không homed package/service/executable; libsystemd0/libudev1 vẫn có | Specific affected component absent, có file/package proof; giữ nguyên scanner rows và HIGH gate, không general systemd exception |
| CVE-2026-9538 / perl | Archive::Tar không có file/module, Perl module load fails; perl-base 5.40.1-6+deb13u1 vẫn có | Specific affected component absent; không general Perl exception |
| **CVE-2026-82560 / UNKNOWN** | Pod::Text nested-POD resource exhaustion; không Pod/Text.pm, module load fails; Debian open/no-dsa, urgency chưa assigned | Affected module absent trong exact image; **UNKNOWN giữ nguyên**. Reassess khi thêm Perl modules/extension; không risk approval |

Nguồn chính thức: [Debian tracker](https://security-tracker.debian.org/tracker/),
[libacl advisory](https://security-tracker.debian.org/tracker/CVE-2026-54369),
[systemd-homed upstream](https://github.com/systemd/systemd/security/advisories/GHSA-jm29-p7hh-vjhv),
[nsenter upstream](https://github.com/util-linux/util-linux/security/advisories/GHSA-55fx-f4gg-cfhj),
[UNKNOWN advisory](https://security-tracker.debian.org/tracker/CVE-2026-82560).
Debian urgency/nodsa và các VendorSeverity raw map được giữ tách với Trivy
severity. Không suy ra khả năng khai thác chỉ từ số lượng hay từ việc app là Python.

## MEDIUM / LOW maintenance groups

JSON gộp đủ 22 nhóm (kể cả pip đã gỡ/Mako), mọi OS row có vendor release evidence,
package/source version và disposition. Các nhóm cần ưu tiên theo runtime:

- glibc: 26 MEDIUM/16 LOW; gcc-14 runtime libs: 6 MEDIUM. Core runtime còn dùng,
  ưu tiên supported vendor updates; không chọn upstream version thay Debian patch.
- util-linux: 8 MEDIUM/8 LOW còn lại; systemd: 2 MEDIUM/10 LOW; shadow: 6 LOW,
  PAM: 4 MEDIUM. Không app shell/namespace/login-service path; trusted extensions
  vẫn có quyền process nên phải giữ containment và theo dõi vendor.
- acl/attr/bzip2: mỗi nhóm 1 MEDIUM; sqlite3: 2 MEDIUM/2 LOW;
  tar: 3 MEDIUM/2 LOW; zlib: 2 MEDIUM. Data parsers/OS utilities không được coi
  tự động safe; không nhận archive hoặc path không tin cậy vào các utility này.
- ncurses: 4 LOW; apt: 2 LOW; bash/dash/diffutils/coreutils/sysvinit: 9 LOW tổng.
  Tracked maintenance, không đổi Essential packages chỉ để giảm scan.

Owner mọi nhóm: **maintainer/security reviewer**. MEDIUM cần applicability/
maintenance decision trước release; LOW theo dõi supported vendor updates.
Review **trước release hoặc 2026-11-26, cái nào đến trước**, và khi đổi image,
capabilities, extension hoặc exposure. Không residual-risk acceptance được cấp.

## Verification và phần còn lại

- Backend: **242 PASS**, 2 deprecation warnings; lock/Ruff/Black/strict MyPy PASS.
- Ops/security: **79 PASS**, gồm 6 regression mới cho comparison, record
  disappearance, same-DB, vendor/scanner severity và applicability proof guard.
- Full tracked secret/index/source/context/image/license gates PASS; source
  revision và canonical MIT/NOTICE hash đúng; no tests/fakes/private config.
- Isolated clean clone install: 0 users/runs/events sau migrate; explicit new
  verification-admin bootstrap; API/worker healthy/doctor ready; separate CLI
  login/discovery; auth mode0600; actual cap-drop/NNP/user app PASS.
- Runtime probe: CapEff=0, CapBnd=0, NoNewPrivs=1 với supported Compose-equivalent
  flags. HostConfig được lấy từ API/worker thật. Đây không phải default image
  capability guarantee khi operator override Docker flags/user.
- Python audit: 58 packages/0 known findings; Trivy vẫn 1 MEDIUM Python record.
- OS/security scan **FAIL có chủ ý chính sách** vì còn HIGH, không phải PASS.
  Independent SBOM/license inventory được tạo lại. DB/input/original logs giữ riêng.
- Chỉ services verification mới được stop; volumes/config/admin/CLI giữ lại.
  Không chạm operator/historical campaigns; không provider request/inference.

Remote Actions **NOT_RUN**. Workflow có nhánh SPEC-030 trong push filter,
security gates không tắt và upload exact sanitized proof files ngay cả khi scan
FAIL. Chưa push. Owner phải cho phép push candidate đã review; xem
[checklist](RELEASE-CHECKLIST.md#remote-ci-only-after-owner-authorizes-push).

Read-only `GET /repos/hzjanuary/multi-agent-system/private-vulnerability-reporting`
trả **HTTP 200, enabled=false** lúc `2026-10-27T16:08:12Z`; không phải unconfirmed
nữa. Không có settings write. Owner: Settings → Security and quality → Advanced
Security → Private vulnerability reporting → Enable, rồi kiểm tra private report
form. Final publication approval vẫn riêng và chưa được cấp.

**Quyết định: NO-GO.** Không có supported HIGH fix đang bị bỏ qua; các HIGH còn
lại chưa có vendor fix hoặc cần owner đánh giá containment/applicability. Local
application/packaging gates PASS không thay cho security approval, remote CI,
private disclosure hay quyền publish. Plan còn active cho các quyết định đó.
