# Web Crawler Platform — Design

**Ngày:** 2026-09-26
**Trạng thái:** Approved by user (chờ spec review)
**Địa điểm:** `C:\Opencode\webcrawler\`

## 1. Bối cảnh & Mục tiêu

Xây hệ thống crawl web free 100%, chạy trên máy Windows cá nhân (Python 3.12, không Docker, không API key, không cloud), dùng chung 1 library + 3 runner độc lập cho 3 mục tiêu:

- **Mode A — Research corpus:** crawl tài liệu/bài viết chất lượng theo chủ đề → markdown → nạp cho AI research (hyperresearch).
- **Mode C — ML dataset:** bulk crawl theo config → export JSONL/CSV để huấn luyện model.
- **Mode D — Real-time monitor:** chạy định kỳ (Task Scheduler), phát hiện nội dung mới → alert.

**Nguồn (tất cả 5 nhóm):** mạng xã hội, SERP/search, báo-chứng-blog, tài liệu kỹ thuật, forum/comment.

## 2. Non-goals

- Không phải distributed/cloud — chạy 1 máy, crawl polite chậm chấp nhận.
- Không tính năng realtime streaming (monitor dùng lịch chạy định kỳ).
- Không index vector/RAG (tương lai, có thể thêm sqlite-vec).
- Không login vào tài khoản cá nhân (trang cần login → đánh dấu `blocked`, dùng browser fallback khi public page vẫn bị chặn).

## 3. Kiến trúc — Hướng 3: library chung + 3 runner riêng

```
C:\Opencode\webcrawler\
├── core\                    ← library chung (import bởi 3 runner)
│   ├── sources\             ← 5 connector, mỗi nguồn 1 file
│   │   ├── social.py        Reddit JSON, YouTube RSS/yt-dlp, HN Firebase API
│   │   ├── serp.py          DuckDuckGo (ddgs lib, free)
│   │   ├── news.py          RSS/Atom feed
│   │   ├── docs.py          GitHub API, StackExchange API, sitemap.xml
│   │   └── forum.py         Discourse API, Reddit, Voz qua browser
│   ├── fetch.py             Scrapling → fallback Camoufox
│   ├── extract.py           HTML → text/markdown (trafilatura)
│   ├── url_db.py            sqlite registry URL — dedup chung
│   ├── robots.py            robots.txt + rate limiter từng domain
│   └── store.py             data\raw\ + data\md\ + metadata
├── runners\
│   ├── research_crawl.py    ← mode A
│   ├── dataset_build.py     ← mode C
│   └── monitor.py           ← mode D
├── datasets\                ← config YAML cho mode C
├── tests\                   ← pytest + fixture HTML
└── data\
    ├── raw\                 ← HTML/PDF gốc
    ├── md\                  ← text sạch có frontmatter
    ├── alerts\alerts.md     ← output mode D
    └── url_db.sqlite
```

**Quy tắc:**

1. Mọi connector implement chung interface: `discover(seed) -> list[URL]` và `fetch(url) -> Document`. Thêm nguồn = thêm 1 file, không sửa code elsewhere.
2. `url_db.sqlite` là registry chung — cả 3 runner check trước khi crawl → không trùng, không giẫm rate-limit.
3. Polite crawling: tôn trọng robots.txt, delay tối thiểu per-domain, concurrency cap 4.

## 4. Core components

### 4.1 Connector (`core/sources/`)
Mỗi file exposes `discover(seed)` — seed là keyword, feed URL, repo, hoặc list file. Trả về list URL kèm metadata `{url, source_type, discovered_at}`.

| File | Nguồn free | Ghi chú |
|---|---|---|
| social.py | Reddit `.json` endpoint, YouTube RSS + yt-dlp, HN Firebase API | X/Facebook/IG không có API free → nếu cần thì browser (Camoufox), để phase sau |
| serp.py | `ddgs` (DuckDuckGo) | fallback: SearXNG self-host (tương lai) |
| news.py | RSS/Atom — hầu hết báo/blog đều có | feed list + discovery từ item |
| docs.py | GitHub REST API (token free 5000 req/h nếu cần), StackExchange API, sitemap.xml | |
| forum.py | Discourse `/latest.json`, Reddit, thread qua fetch | Voz qua Camoufox (JS-heavy) |

### 4.2 Fetch (`core/fetch.py`)
Thứ tự: **Scrapling** (adaptive, vượt anti-bot nhẹ) → fail/403 → **Camoufox** (browser anti-detect, JS render) → vẫn fail → đánh dấu `blocked`. Retry 3 lần, exponential backoff.

### 4.3 Extract (`core/extract.py`)
`trafilatura` (OSS) → text + metadata (title, author, date). Output markdown có YAML frontmatter:

```yaml
---
title: ...
url: ...
source: reddit|serp|news|docs|forum
fetched_at: 2026-09-26T...
topic: <từ runner A>
---
```

### 4.4 url_db (`core/url_db.py`)
SQLite (WAL mode), schema:

```sql
CREATE TABLE urls (
  url TEXT PRIMARY KEY,
  source TEXT,                 -- connector tìm ra
  status TEXT DEFAULT 'pending', -- pending|fetched|failed|blocked
  content_hash TEXT,           -- dedup nội dung
  first_seen TEXT,
  last_crawled TEXT,
  next_retry TEXT,
  domain TEXT
);
CREATE TABLE runs (id, runner, started_at, finished_at, stats_json);
```

Dedup 2 lớp: URL (chưa crawl?) + content_hash (nội dung trùng?).

### 4.5 Store (`core/store.py`)
- `data\raw\<domain>\<hash>.html` — bản gốc
- `data\md\<topic|dataset>\<slug>.md` — text sạch + frontmatter
- Prune theo config `max_raw_mb`.

## 5. Runner

### A. `research_crawl.py`
```powershell
python runners\research_crawl.py --topic "RAG architecture" --limit 200 [--seeds seeds.txt]
```
Seed → discover (5 connector) → url_db filter → fetch/extract → `data\md\<topic>\` + index file. Output đọc trực tiếp bởi hyperresearch/AI.

### C. `dataset_build.py`
```powershell
python runners\dataset_build.py --config datasets\rag_corpus.yaml --export jsonl --out data\dataset.jsonl
```
Config YAML: keywords, nhóm nguồn, khoảng ngày, limit. Dedup chặt (content-hash + title chuẩn hóa: lowercase, bỏ dấu/ký tự đặc biệt, so bằng nhau tuyệt đối). Export JSONL/CSV: `{text, url, source, timestamp}`. Ưu tiên dùng lại raw/md đã có.

### D. `monitor.py`
```powershell
schtasks /create /tn "webcrawler-monitor" /tr "python C:\Opencode\webcrawler\runners\monitor.py" /sc hourly
```
Chạy 1 tiếng/lần: fetch feed list → so `last_seen` với url_db → item mới → extract → append `data\alerts\alerts.md` + Windows toast. Trạng thái trong sqlite → restart không mất dấu.

## 6. Xử lý lỗi

| Sự cố | Xử lý |
|---|---|
| Fetch fail | retry 3× backoff → `failed`, cooldown vài ngày rồi thử lại |
| 403/anti-bot | Scrapling → Camoufox → `blocked`, bỏ qua |
| Rate-limit domain | min-delay per domain + concurrency global 4 |
| Crash giữa chừng | state trong sqlite WAL → chạy lại resume |
| Hết disk | `max_raw_mb` prune raw cũ (giữ md) |

## 7. Testing

1. **Unit (pytest):** fixture HTML lưu sẵn trong `tests\fixtures\` → test parse từng connector (không network), dedup url_db, extract.
2. **Smoke:** mỗi connector `--limit 3` chạy thật.
3. **E2E:** 1 lượt runner A thật → verify file md + frontmatter.

## 8. Thứ tự build

1. `core` (fetch, extract, url_db, robots, store) + connector `news.py` (RSS — dễ, luôn chạy được) + runner A mỏng → **có thể dùng ngay**
2. 4 connector còn lại (serp, docs, forum, social)
3. Runner C (+ export)
4. Runner D (+ Task Scheduler)

## 9. Tương lai (ngoài scope)

Vector index (sqlite-vec) cho search ngữ nghĩa · SearXNG self-host · Telegram bot alert · X/Facebook qua browser · push corpus vào hyperresearch vault tự động.
