# AGENTS.md

Workspace này gồm ~30 dự án độc lập xếp cạnh nhau, cộng tầng tooling dùng chung của OpenCode. Không có root build, không có test suite chung: luôn verify bên trong dự án vừa động tới, bằng runner của chính dự án đó (README / package.json / pytest / venv riêng).

## Layout

- Thư mục dự án ở gốc repo (`autoclip/`, `webcrawler/`, `research/`, `Octop/`, ...) — mỗi dự án tự chọn stack; không suy luận stack của dự án này từ dự án khác.
- `.opencode/` — skills + config dự án (MCP: autoclip, hyperresearch, context7; skills paths).
- `.claude/` — bộ skill hyperresearch (pipeline nghiên cứu 16 bước, quy ước nằm ở `CLAUDE.md`).
- `docs/` — tài liệu thiết kế/architecture của nhánh evidence-engine / clippy, không phải chuẩn chung của toàn workspace.
