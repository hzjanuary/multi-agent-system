> Historical diagnosis, retained unchanged below. Later direct Groq verification completed SPEC-029 (32 PASS / 0 BLOCKED); it does not establish the cause of these OpenRouter failures.

# SPEC-029 — Chẩn đoán 429 không inference (27/10/2026)

**Kết luận: HTTP 429 chưa xác định nguyên nhân vì thiếu bằng chứng nhận diện.**
Chưa đủ căn cứ xác nhận giới hạn platform/account OpenRouter hay giới hạn/capacity
upstream. Note này bổ sung [bằng chứng lần chạy thất bại](openrouter-live-attempt.json),
không thay thế lịch sử hoặc đổi trạng thái acceptance: **30 PASS, 2 BLOCKED**
(AC-08 và phần model thật của AC-29).

## Bằng chứng cũ được xác nhận

Run `75039b34-2bf1-4e89-a1c1-704dd2f0be28` FAILED; duy nhất node `analyze`,
execution `592a0849-2b61-44bf-87b2-6d2e31d0d485`, attempt 1, reservation/call count 1,
không output và sáu event. Hash của cả 20 artifact lịch sử khớp bản đã ghi.
Application retry = 0, transport retry = 0, `allow_fallbacks=false`, chỉ pin
`google/gemma-4-31b-it:free` / `google-ai-studio`: bằng chứng xác nhận đúng một
client generation attempt, không phải hai; không khẳng định số lần xử lý nội bộ upstream.

Mã đã lưu là `provider_rate_limit`; HTTP 429 suy ra từ ánh xạ duy nhất của adapter
đã chạy. **Body/header/status HTTP gốc không được lưu bền vững.** Không có
`error.code/type/message` gốc, provider identification, upstream error code,
`Retry-After`, `X-RateLimit-*`/reset hoặc provider request ID để trích xuất.
Không được suy ra server đã không gửi các trường này.

Đã đọc log của API/worker đang dừng (83/1 dòng), không khởi động service. API có
37 `request_id` nội bộ, không có thông tin lỗi OpenRouter bổ sung. Ví dụ ID của
POST start là `1c2a4576-a5de-48e5-bcd1-2891e2c65cdc` (HTTP API **202**), **không phải**
request ID phía OpenRouter. Run được tạo/cập nhật FAILED lúc khoảng
**12:56:46–12:56:48 ngày 27/10/2026, giờ Việt Nam (UTC+7)**.

## Quan sát quota hiện tại, không phải trạng thái lúc lỗi

Đã thực hiện đúng **một** authenticated `GET https://openrouter.ai/api/v1/key`,
HTTP **200**, lúc **13:12:15 ngày 27/10/2026, UTC+7**. Không retry, redirect hoặc
inference. Chỉ giữ snapshot đã lọc tại
`.maos/openrouter-free-smoke/diagnosis-20261027/key-info-sanitized.json`.
Không lưu raw response, key, Authorization header hay thông tin nhận diện account.

| Trường đã thu | Giá trị |
| --- | --- |
| `is_free_tier` | `true` |
| `limit`, `limit_remaining`, `limit_reset` | đều `null` |
| `usage`, `usage_daily`, `usage_weekly`, `usage_monthly` | đều `0` credit/USD tổng hợp |
| `rate_limit` cũ | `requests=-1`, `interval=10s`; deprecated, không dùng làm quota/reset thực tế |
| Header quota/retry của lookup hiện tại | không có trong snapshot; chỉ có Date |

Theo [tài liệu limits chính thức](https://openrouter.ai/docs/api_reference/limits),
`limit=null` là không đặt credit cap riêng cho key; usage tiền tệ khác bộ đếm
request free. Các số trên **không giải thích hoặc loại trừ** giới hạn request/
capacity trước đó và không được quy usage/cost tổng hợp cho run này. Cost/usage
của run vẫn unknown.

**Giới hạn của lần trích lọc:** allowlist ban đầu không thu
`free_model_daily_requests`, `budgets`, `effective_budget`; raw response đã bỏ nên
không thể xác nhận chúng có hay vắng trong response. Không gọi lookup lần hai.
[Tài liệu key hiện tại](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key)
mô tả các trường này; không dùng dữ liệu ví dụ trong tài liệu làm dữ liệu account.
Không có Retry-After/reset đã quan sát cho request lỗi, nên **không có thời gian
chờ hoặc giờ reset cụ thể có thể tính sang giờ Việt Nam**. `10s` deprecated không
phải chỉ dẫn thử lại.

## Hành động nhỏ nhất và một phương án dự phòng

Kiểm tra bản ghi Activity hiện có của chính request vào khoảng 12:56:46–12:56:48
UTC+7 hoặc nhờ OpenRouter support xác định nguồn limit từ dữ liệu phía họ; giữ
thông tin account/text riêng tư. Không gửi yêu cầu hỗ trợ tự động trong tác vụ này.
Chưa có căn cứ để nạp tiền, đổi policy, kết luận Google AI Studio hết capacity
hoặc hẹn lịch retry.

Chỉ chuẩn bị **một đề xuất metadata**, chưa áp dụng:
`google/gemma-4-26b-a4b-it:free`, canonical
`google/gemma-4-26b-a4b-it-20260403`, route **`google-ai-studio`** (Google AI Studio).
[Endpoint chính thức](https://openrouter.ai/api/v1/models/google/gemma-4-26b-a4b-it:free/endpoints)
được kiểm tra lúc **13:19:27 UTC+7, 27/10/2026**: status 0, prompt/completion price
đều **0**, request fee bị lược/không được quảng bá, không giả thành metadata 0.
Nếu sau này được duyệt, vẫn phải giữ request-price ceiling 0 và mọi giới hạn cũ.
Endpoint hỗ trợ `temperature`, `max_tokens`, `response_format` dùng cho JSON-object;
context 262144, max completion 32768; reasoning không bắt buộc và mặc định tắt,
phù hợp về tham số với cap 1024. Schema validation vẫn giữ nguyên.

Đây là model endpoint khác nhưng cùng provider; **không bảo đảm capacity, chất
lượng JSON hay vượt được quota account chung**. Không thay pin hoặc tạo profile
mới. Ứng viên Liquid được xem xét trước đó nhưng không chọn vì reasoning bắt buộc,
chưa xác minh phù hợp ngân sách output ngắn; chỉ đề xuất Gemma 26B nêu trên.

**Không có generation request bổ sung (0); tổng lịch sử vẫn 1 request đã tiêu thụ.**
Không retry/resume run FAILED, không tạo run mới, không ghi đè/reset `attempt.json`,
không đổi budget/model/route/privacy, không khởi động service, rebuild image, chạy
suite, push/merge/publish/deploy hoặc xóa tài nguyên giữ lại. Mọi service vẫn dừng.
Lần thử tương lai cần quyết định riêng cho **tối đa hai generation request bổ sung**,
vẫn bảo toàn một request cũ và toàn bộ bằng chứng. AC-08/AC-29 tiếp tục BLOCKED.
