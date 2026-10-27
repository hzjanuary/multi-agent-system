# SPEC-030 — Publication readiness

> **Source publication attempt stopped at a new CI blocker:** branch and
> [PR #1](https://github.com/hzjanuary/multi-agent-system/pull/1) exist; main is
> unchanged and v0.1.0 is not released. Real Actions clean-install FAIL occurred
> before dependency/OS scanning. See [actual outcomes](v0.1.0-publication-attempt.json).
> This is distinct from the owner-accepted disclosure of known OS findings.

> **2026-10-28 source-only owner decision:** early public source preview is
> authorized with disclosed residual OS risks. See [v0.1.0 decision](v0.1.0-source-preview.md).
> This does not clear the Docker image or change the existing security gate.
> The unrestricted image/security **NO-GO remains**; no reviewer approval is invented.

> **Phase 3 — owner decision package:** [SECURITY-SIGNOFF](SPEC-030-SECURITY-SIGNOFF.md).
> 40 HIGH rows reconciled: 0 supported-fix available, 6 confirmed affected/no-fix,
> 31 unresolved binary attribution, 3 not affected by concrete component absence.
> Six image-level CVEs still have affected components. Raw counts/gate unchanged;
> no exception, risk approval or remote CI. **NO-GO; owner decisions pending.**

> **Phase 2 mới nhất (2026-10-27): NO-GO.** Đã remediation và scan cùng DB:
> **40 HIGH / 58 MEDIUM / 60 LOW / 1 UNKNOWN**, 159 rows tổng (158 OS + 1 Python).
> 242 backend + 79 ops tests và packaging/install gates PASS; security gate FAIL.
> GitHub private vulnerability reporting được xác nhận **disabled** bằng GET.
> Xem [triage đầy đủ](SPEC-030-OS-TRIAGE.md), [evidence mới](spec-030-phase2-evidence.json)
> và [remote CI/disclosure checklist](RELEASE-CHECKLIST.md). Không có risk waiver,
> remote CI, inference hay quyền publication. Nội dung Phase 1 dưới đây là lịch sử.

## Phase 1 — historical result retained

Ngày kiểm tra: 2026-10-27. **Khuyến nghị: NO-GO cho phát hành hiện tại.**
Hai blocker ban đầu đã được sửa và có regression proof. Cổng scan OS của image
ứng viên vẫn FAIL: **44 HIGH / 64 MEDIUM / 62 LOW / 1 UNKNOWN, 0 CRITICAL**.
Không có ignore list, `ignore-unfixed` hay miễn trừ để làm xanh CI.

SPEC-029 vẫn **32 PASS / 0 BLOCKED**. Bằng chứng Groq, run/event/approval/resume,
image và provenance cũ không bị thay thế. Cloudflare chỉ configured/offline-tested,
chưa live-verified. SPEC-030 không gọi inference; lịch sử vẫn 5 requests.

## Provenance và phạm vi

- Baseline audit: `320e527a48ef9a6a2e725342ce165e3d6835931e`.
- Baseline image: `sha256:0bd614b44c98c0bef95402bedee371dba46ed7ad50c68b704cb237ec3a03c959`, runtime source `44a8c42373af1320986ad78d922aa79595775dbe`.
- Candidate source được build/test: `d84aeea6af592b56738456039445f480778744cf`.
- Image build từ clone sạch: `sha256:21f4073e53b9f3a657a933867c6d6921fd9634c1d503618da25224cc59c42100` (`multi-agent-os:spec030-clean-build`).
- Build đầu cùng source: `sha256:86985c009a6b33892f82bc9ce3732adc9b5c39bff7502e44d4cbe030eed32a64`.
  Cả hai qua kiểm tra độc lập 171 file runtime và cùng content identity của build
  inputs. Khác digest giữa hai build không được mô tả là byte-reproducible.
- Build-input SHA256: `dd107140ece240d54d3226bf16d93ae976ba97bda8057c203d4be80a2421357a` (139 files).
- Source archive candidate: SHA256 `08fe92205d2c43fd12dd710d568c5613710456e2dd94e78db080c80b82ffeca6` (225 files).
- HEAD bàn giao sau đó chỉ bổ sung tài liệu/bằng chứng; không gán image cũ cho SHA
  tài liệu mới. File [evidence](spec-030-evidence.json) ghi tool versions, hash và
  kết quả thực tế. Build logs/raw scan/config/session nằm riêng trong `.maos/`.

Đây là source distribution và Docker candidate cho một instance tin cậy; không
chứng nhận enterprise/internet-facing security, mọi provider/model hay toàn bộ
stack là MIT/OSI-only.

## Ma trận khắc phục

| Phát hiện / nguồn | Thay đổi thực tế | Kiểm chứng | Trạng thái / rủi ro còn lại |
| --- | --- | --- | --- |
| Runtime thiếu LICENSE/NOTICE — `backend/Dockerfile` | Root build context; COPY trực tiếp hai file canonical vào `/app/licenses/project/` | Baseline image thiếu cả 4 đường dẫn đã kiểm; image mới so byte/hash với Git | PASS; không có bản sao source bị lệch |
| Wheel metadata thiếu license files — langchain-core/langsmith | Full MIT upstream tại immutable version-matching commits; hash/version fail-closed | `release/third-party/sources.json`, build inventory, 2 license regression tests | PASS về evidence/notice; không khẳng định tư vấn pháp lý |
| certifi MPL-2.0 | Notice upstream, full MPL text, readable PEM source và hash trong image | Inventory/actual file integrity | PASS; MPL không đổi license ứng dụng |
| License của stack bị gộp với MIT | Inventory 59 Python distributions, 87 OS packages; source/notice locations; stack riêng | `/app/licenses/inventory.json`, `release/third-party/stack.json` | WARNING: Redis 7.4 RSALv2 OR SSPLv1 không OSI; giữ nguyên theo chỉ thị |
| Scanner bỏ toàn bộ tests — `scripts/ops/scan_secrets.py` | Scan toàn bộ tracked text/index và worktree, không skip thư mục tests | Synthetic test key: cũ 0 findings, mới 2; regression 13 scanner tests | PASS |
| PostgreSQL DSN và substring placeholder lọt | Detect embedded password; allowance exact path + SHA256 toàn dòng + lý do | DSN cũ 0/mới 1; substring cũ 0/mới 1; adjacent/appended key đều bị chặn | PASS; reviewer phải duyệt allowance mới, không tự tạo từ finding |
| Scanner lỗi đọc vẫn có thể thành công | Fail closed cho index/read/decode/binary/size/policy/symlink failures | Negative tests, staged-secret/worktree mismatch | PASS; scanner heuristic không bảo đảm tìm mọi bí mật tùy ý |
| Ignore thiếu private files ngoài `.maos` | `.gitignore`, root/backend `.dockerignore`, path deny policy | Force-add private env/auth/DB dump; index gate vẫn reject | PASS; ignore không phải security boundary |
| Symlink/untracked context có thể đưa dữ liệu vào artifact | Deny-by-default root context, independent context/index/tar gates; reject Dockerfile-specific ignore override | 8 adversarial artifact tests + actual source/image checks | PASS; thay đổi Dockerfile/policy vẫn cần code review |
| Image/source manifest chưa có independent proof | Git byte comparison, revision label, actual files/distributions/license hash checks; non-root/no network verifier | 171 runtime files; no tests/fakes/demo/private config; source archive exact Git | PASS |
| CI thiếu release-security checks | Backend, ops, lint/type/lock, scanner/path/archive/image/license, pip-audit, Trivy/SBOM, Compose, isolated install | Local reproduction; `.github/workflows/ci.yml` | WARNING: remote Actions NOT_RUN; OS gate dự kiến đỏ cho candidate này |
| Mutable Actions/base/infra refs | Verified immutable Actions commits, official registry digest pins; locked Trivy archive/binary SHA | `release/images.lock.json`, `release/tools.lock.json`; actual build | PASS về pin; cần review/update hàng tháng và trước release |
| Môi trường CI làm sai default-setting tests | Ba kiểm thử tự cô lập biến liên quan/explicit missing model; không nới assert | 25 focused tests với env model/extension khác rỗng; full gate dưới đây | PASS |
| README/providers còn AC-08 pending | Cập nhật completed Groq journey/32 PASS; Cloudflare offline only; OpenRouter failure là lịch sử | README, providers, report SPEC-029 cũ giữ provenance | PASS; không suy ra nguyên nhân OpenRouter từ Groq thành công |
| Privacy/exposure claims chưa đủ rõ | Strict defaults giữ nguyên; optional consent không default; TLS/proxy/rate/body/log/backup/operator boundaries | `provider_preferences.py` deny/ZDR; README/SECURITY/self-hosting | PASS; không thêm throttling/SSO/tenant isolation giả |
| Public log có machine path | Chuẩn hóa `<repo>`; giữ original byte-for-byte/hash riêng | `spec-030-baseline.json`, public sanitized log | PASS; historical Git không bị rewrite |
| Git author email / private reporting | Ghi owner review riêng; hướng dẫn bật GitHub Private Vulnerability Reporting, chưa tự đổi settings | SECURITY.md; private owner-review artifact | WARNING; owner xử lý trước publication |
| OS vulnerability scan | Trivy thực sự scan runtime Debian 13.7 + language packages, CycloneDX SBOM | 171 rows; 44 HIGH thuộc 8 CVE, chưa có fixed version được scanner báo | **BLOCKER — NO-GO**, không waive tự động |

## Lệnh và kết quả local

Tất cả dùng namespace mới `maos-spec030-*`, không dùng database/CLI/credential
smoke của operator. Test providers chỉ có trong tests, không có trong runtime.

```bash
python3 scripts/ops/reproduce_publication_blockers.py
python3 -m unittest discover -s scripts/ops -p 'test_*.py'
bash scripts/ci/backend-gate.sh
python3 scripts/ops/scan_secrets.py --strict --allow-approved-fixtures
python3 scripts/ops/release_artifacts.py index
MAOS_BUILD_NETWORK=host bash scripts/ci/release-gate.sh
python3 scripts/ops/verify_release_install.py --image multi-agent-os:spec030-d84aeea6af59 --source d84aeea6af592b56738456039445f480778744cf --directory .maos/spec-030/clean-clone-final --project maos-spec030-clean-final
python3 scripts/ops/release_security.py scan-image --tool .maos/spec-030/tools/trivy --image multi-agent-os:spec030-clean-build --output .maos/spec-030/evidence/clean-build-security
```

Không chạy lại lệnh install với directory/volume đã tồn tại: helper cố ý từ chối.
Để tái lập, dùng namespace mới; giữ nguyên dữ liệu cũ. Build root context là bắt
buộc. Các command, environment references và summary chi tiết ở evidence JSON;
không đưa password/token thực vào dòng lệnh hay báo cáo.

- Blocker reproduction PASS: 3 synthetic negative probes cũ lọt, mới đều bắt.
- Ops/security: **73 PASS**, gồm **26** scanner/artifact/license/security tests.
- Backend: **242 PASS / 0 FAIL**, 2 deprecation warnings; Ruff/Black/MyPy và `poetry check --lock` PASS.
- Ruff/Black cho ops thay đổi: PASS; lock, Ruff/Black/MyPy backend theo full gate.
- Source archive/index/build-input/image/license gates: PASS.
- Clean clone: migration có 0 users/runs/events; explicit bootstrap thành 1 admin,
  0 runs/events; API/worker healthy, doctor ready/worker available; CLI login và
  workflow/run discovery qua container riêng, `auth.json` mode 0600. Image build
  từ clone sạch được khởi động lại trên chính DB verification giữ nguyên,
  doctor/CLI PASS. Không kiểm tra model availability và không gọi provider check.
- Compose canonical + development override: PASS bằng `config --quiet` trong clone.
- pip-audit 2.10.1: **58 main dependencies, 0 known findings**. Image inventory có
  thêm pip từ base = 59 distributions. Đây không phải kết quả OS scan.
- Trivy 0.76.1: **FAIL** như bảng; SBOM CycloneDX đã tạo. Không quét thêm PG/Redis/
  Ollama images; không tuyên bố toàn deployment sạch. Operator phải scan các
  image phụ trước deployment theo threat model của họ.
- Markdown local file links: 0 missing targets (không khẳng định mọi website/
  external anchor đều còn hoạt động).
- Không inference, push/merge/tag/publish/deploy, sửa history hay xóa retained data.
  Tất cả services SPEC-030 được stop, volumes/config/session/evidence giữ nguyên.

## Security triage và disposition

Các HIGH là **package/CVE rows**, không phải 44 lỗ hổng độc lập. Có 8 CVE khác nhau:

| CVE / thành phần | Evidence và rủi ro | Owner / disposition |
| --- | --- | --- |
| CVE-2026-76642, CVE-2026-78408, CVE-2026-78409, CVE-2026-78410 — util-linux family | Nhiều package rows dùng chung source; privileged/local utility paths cần triage theo image/capabilities thực tế | Maintainer/security reviewer; BLOCK publication tới khi vendor update hoặc mitigation/applicability proof được duyệt |
| CVE-2026-54369 — libacl1 | Scanner HIGH, không báo fixed version trong Debian candidate | Maintainer/security reviewer; BLOCK, không suy ra không reachable chỉ vì runtime Python |
| CVE-2025-69720 — ncurses family | Upstream Debian nêu lỗi CLI infocmp, trixie marked vulnerable/no-dsa; cần chứng minh binary/path có trong image và cách bị gọi | Maintainer/security reviewer; BLOCK tới khi exact applicability được duyệt |
| CVE-2026-16742 — libsystemd0/libudev1 | Package present; service/path reachability chưa được chứng minh | Maintainer/security reviewer; BLOCK |
| CVE-2026-9538 — perl-base | Debian nêu Archive::Tar resource exhaustion; việc module/path có trong candidate chưa đủ evidence để waive | Maintainer/security reviewer; BLOCK |

Nguồn chính thức: [Debian util-linux](https://security-tracker.debian.org/tracker/CVE-2026-76642),
[Debian ncurses](https://security-tracker.debian.org/tracker/CVE-2025-69720),
[Debian Perl](https://security-tracker.debian.org/tracker/CVE-2026-9538).
Tất cả 8 trang tracker đã được truy xuất, hash/time evidence riêng. Debian có thể
xếp một issue là minor/no-dsa; điều đó không tự tạo ngoại lệ cho cổng HIGH của
candidate. Không lấy package unstable để lách scan, không đổi Redis/base family
hay nới threshold để có PASS. Bước nhỏ nhất là maintainer/security reviewer triage
8 CVE trên đúng image; dùng vendor-fixed digest khi có, hoặc quyết định mitigation/
ngoại lệ cụ thể có owner/expiry sau khi có applicability proof và authorization.

Các warning khác có disposition rõ:

| Warning | Owner | Rủi ro / release disposition |
| --- | --- | --- |
| MEDIUM/LOW/UNKNOWN OS rows | Maintainer/security reviewer | Review toàn bộ sanitized findings trước release; chưa được chấp nhận; nằm trong NO-GO hiện tại |
| Remote Actions NOT_RUN | Maintainer | Chỉ chạy sau push được cho phép riêng; cần run xanh trên candidate thực tế trước release, không đổi local PASS thành remote PASS |
| GitHub private disclosure chưa xác nhận | Repository owner | Bật theo SECURITY.md, kiểm tra private form; required manual pre-publication gate |
| Personal historical author email | Repository owner | Bản review riêng `.maos/spec-030/evidence/author-owner-review.txt`; owner chấp nhận công khai hoặc quyết định xử lý riêng; không tự rewrite |
| Redis source-available | Owner/distributor | Giữ Redis theo authority, công bố terms đúng; không tuyên bố toàn stack OSI/MIT. Valkey là ADR riêng, không phải remediation đã test |
| Infrastructure/model terms, unscanned auxiliary images | Deployment operator | Không nằm trong app-image clean claim; scan/license review theo deployment trước exposure; không bật paid services |
| Hash-pinned images vẫn cần cập nhật | Maintainer | Review hàng tháng/trước release, không đóng băng phần mềm hết hỗ trợ; update pins rồi gates lại |
| Pre-1.0 exposure limits | Deployment operator | Trusted single instance; TLS/access/rate limiting/backups/log protection bên ngoài; không bán như production certification |
| Hai deprecation warnings của test tooling | Maintainer | Không suppress; không làm sai assertion; review nâng FastAPI/Starlette/httpx trong dependency maintenance riêng |

## Quyết định publication

- **Local remediation:** hai blocker audit gốc có proof đã sửa; packaging và
  installation verification PASS. **Security release gate FAIL**, không gọi
  SPEC-030 đã đủ điều kiện GO. Plan còn active để theo dõi security disposition.
- **Remote CI:** NOT_RUN, không được suy diễn từ local commands.
- **Manual GitHub security/disclosure:** owner phải thực hiện/xác nhận riêng.
- **Final owner approval:** chưa được cấp; local commit/build không cho phép publish.

Checklist trước thay đổi quyết định: giải quyết OS findings với proof/decision cụ
thể; chạy lại scan/gates đúng candidate; xác nhận remote CI; bật private reporting;
review author email/license obligations; owner phê duyệt publication riêng.
Không cần gọi lại Groq/Cloudflare để làm việc này. Xem [checklist tái lập](RELEASE-CHECKLIST.md).
