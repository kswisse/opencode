# Webcrawler — Topic-Crawl Agent (Mode A+) — Design

**Ngày:** 2026-09-29
**Trạng thái:** Approved by user (chờ spec review)
**Địa điểm:** `C:\Opencode\webcrawler\` + `C:\Opencode\agent\web-crawler.md`
**Mở rộng từ:** `docs/superpowers/specs/2026-09-26-webcrawler-design.md` (Approved)

## 1. Bối cảnh & Mục tiêu

Spec 2026-09-26 định nghĩa nền tảng (core library + 3 runner). Giai đoạn 1 đã xong: `core/` (fetch httpx+scrapling fallback, extract trafilatura, robots, store, url_db) + connector `news.py` + runner `research_crawl.py`.

Yêu cầu mới: **1 agent 形式 "web-crawler"** — người dùng đưa 1 câu prompt/chủ đề → agent tự tìm seed, crawl ~50–500 trang chất lượng, lọc relevance, trả về kho markdown + SQLite FTS5. Free 100% (trừ quota Gemini free tier người dùng đã có).

**Quyết định đã chốt với người dùng:**
- Phạm vi **A**: chất lượng > số lượng, 50–500 trang/chạy, vài phút–1 giờ.
- Output **c**: markdown (đọc/ghi chú) + SQLite FTS5 (tra cứu).
- Lọc relevance **ii**: BM25 lọc trước → Gemini chấm điểm cuối.

## 2. Non-goals

- Không crawl hàng nghìn trang (phạm vi B) — limit cứng `--max 500`.
- Không JS rendering cho giai đoạn này (site React → lấy phần tĩnh, chấp nhận theo phạm vi A).
- Không thay thế `research_crawl.py` (mode A gốc giữ nguyên — đây là runner mới `topic_crawl.py`).
- Không vector search (FTS5 text-based; vector để phase sau, xem spec 26/09 mục 9).

## 3. Kiến trúc

```
prompt (CLI arg)
  → seeds     core/sources/serp.py      ddgs search → 20–50 URL (không key)
  → crawl     runners/topic_crawl.py    loop: robots check → fetch → extract
              (dùng core.fetch, core.extract, core.robots, core.url_db có sẵn)
  → score     core/score.py             BM25 prefilter → Gemini batch final score
  → store     data/md/<slug>/*.md + data/index.db (FTS5) + manifest.json
```

Bọc ngoài: `agent/web-crawler.md` (opencode agent) + skill `webcrawler` — lớp mỏng, chỉ gọi CLI và đọc `manifest.json` báo cáo.

**Nguyên tắc tái dùng:** không viết lại fetch/extract/robots/store/url_db. Thêm mới chỉ 3 file: `core/sources/serp.py`, `core/score.py`, `runners/topic_crawl.py`.

## 4. Core components mới

### 4.1 `core/sources/serp.py` — seed discovery
- Thư viện `ddgs` (DuckDuckGo, free, không key — đã nằm trong spec 26/09).
- `discover(query, limit=50, lang="vi"|"en") -> list[URL]`, dedup theo domain (tối đa 3 URL/domain để tránh 1 nguồn chiếm hết).
- Thêm dependency: `ddgs`.

### 4.2 `core/score.py` — 2 tầng lọc relevance

**Tầng 1 — BM25 (offline, free):**
- Thư viện `rank-bm25`; nếu dependency xung đột thì tự viết BM25 chuẩn ~40 dòng (không chặn tiến độ).
- Tokenization: lowercase + tách từ đơn giản, hỗ trợ tiếng Việt (không cần morphological analyzer ở giai đoạn này).
- Corpus = prompt tokens + title/lead text của trang.
- Quy tắc cố định: giữ lại **top 40% trang có BM25 score cao nhất** (tối thiểu 20 trang nếu tổng > 50) → chuyển tiếp Gemini.

**Tầng 2 — Gemini final score:**
- REST gọi `generativelanguage.googleapis.com` qua `httpx` có sẵn — **không thêm SDK**.
- Key lấy từ env `GEMINI_API_KEY` (đã có trên máy).
- Batch 10 trang/req (title + 500 ký tự đầu, không gửi cả trang → tiết kiệm quota), model `gemini-2.5-flash`.
- Output JSON `[{url, score: 0..1, reason}]`. Prompt yêu cầu chấm "mức liên quan đến chủ đề X".
- Ngưỡng mặc định `--min-score 0.6`.

**Fallback (bắt buộc):** Gemini lỗi/rate-limit/offline → giữ nguyên kết quả BM25, ghi warning vào manifest. Không bao giờ fail cả run vì Gemini.

### 4.3 `runners/topic_crawl.py` — CLI

```powershell
python runners\topic_crawl.py --topic "RAG architecture" --max 300 [--lang vi] [--min-score 0.6] [--no-gemini]
```

- Flow: serp discover → url_db lọc (chưa crawl bao giờ) → loop fetch/extract (rate-limit per-domain đã có trong `core.robots`) → BM25 → Gemini → chỉ lưu trang đạt → markdown + FTS5 index.
- **Checkpoint/resume:** trạng thái trong `url_db.sqlite` (đã có schema `status`) — chạy lại giữa chừng không crawl lại trang đã xử lý.
- `--no-gemini` chạy được hoàn toàn offline (BM25 only).

### 4.4 Output

- `data/md/<topic-slug>/*.md` — YAML frontmatter (title, url, score, reason, source, fetched_at) + body (format giống store.py hiện tại).
- `data/index.db` — SQLite FTS5:
  ```sql
  CREATE VIRTUAL TABLE docs USING fts5(title, body, url UNINDEXED, topic, score, fetched_at);
  ```
  (một DB chung cho mọi topic, cột `topic` để lọc)
- `data/md/<topic-slug>/manifest.json` — `{topic, run_at, discovered, fetched, kept, skipped, gemini_used, stats}` — agent đọc file này để báo cáo.

## 5. Agent layer

- **`agent/web-crawler.md`** — agent markdown theo format của 239 agent hiện có trong `agent/`. Nhiệm vụ: nhận prompt → chạy CLI → theo dõi tiến độ → đọc manifest → báo cáo danh sách trang đã giữ (title/url/score) + gợi ý bước sau (đọc kho, export...).
- **Skill `webcrawler`** (`.opencode/skills/webcrawler/SKILL.md`) — router: khi user nói "crawl chủ đề X", nạp skill → biết cách gọi CLI + cách tra `index.db` bằng FTS5 query sau đó.
- Agent KHÔNG tự viết lại logic crawl — chỉ điều phối CLI có sẵn (nguyên tắc: skill/agent mỏng, code nằm trong `webcrawler/`).

## 6. Xử lý lỗi

| Sự cố | Xử lý |
|---|---|
| ddgs rate-limit / fail | thử lại 2× → nếu vẫn fail, nhận seed từ `--seeds file.txt` (đã có pattern trong research_crawl) |
| Trang fetch fail/403 | retry 2× → đánh dấu `failed/blocked` trong url_db, bỏ qua, tiếp tục |
| Gemini 429/quota | exponential backoff 1 lần → vẫn fail → fallback BM25-only, ghi `gemini_used: false` vào manifest |
| Không có trang nào qua BM25 | hạ ngưỡng BM25 1 lần, warning; nếu vẫn 0 → báo người dùng prompt quá hẹp |
| Crash giữa chừng | resume qua url_db status (WAL) |

## 7. Testing

1. **Unit (pytest, không network):** `score.py` — BM25 ranking với fixture text; Gemini response parser với JSON mẫu; lỗi Gemini → fallback. `serp.py` — dedup domain logic (mock ddgs).
2. **Integration:** topic_crawl với seed file tĩnh (bỏ qua ddgs) → verify md + manifest + FTS5 row.
3. **Smoke thật (1 lần):** `--topic "test topic" --max 5 --no-gemini` chạy mạng thật.
4. Chạy `pytest webcrawler/tests` — không phá test hiện có (research_crawl vẫn pass).

## 8. Thứ tự build

1. `core/sources/serp.py` + dependency `ddgs` → test unit
2. `core/score.py` (BM25 trước, Gemini sau) + test unit
3. `runners/topic_crawl.py` nối pipeline + output md/FTS5/manifest + integration test
4. `agent/web-crawler.md` + skill → thử end-to-end qua 1 lượt gọi agent thật

## 9. Tương lai (ngoài scope)

JS rendering (Playwright) cho site SPA · vector search (sqlite-vec) · push corpus tự động vào hyperresearch vault · Mode C/D theo spec 26/09 · Telegram alert.
