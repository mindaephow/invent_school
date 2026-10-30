---
name: project-fresh-season-blog
description: fresh-season.kr blog automation project — batch rewriting old blog posts to current publishing standards via the MCP server.
metadata: 
  node_type: memory
  type: project
  originSessionId: b218dd49-4447-452a-997f-dfbe8e2a8635
---

User runs the fresh-season.kr food/health blog via an MCP server (id 194671ec-9fc8-460b-ac05-134289562dd0). Publishing rules live in that server's `get_system_prompt` — `main` (current rules) and `main2` (append-only learning log/changelog), not in this repo. Always load both at the start of any blog-writing session; `main2` holds prior mistakes and their fixes.

**Ongoing task (as of 2026-07-10):** batch-rewriting old blog posts whose SEO metadata is empty (`seo_score IS NULL`) to match the current content standard — real content rewrite with fresh benchmarking, not just filling in metadata. Started with a list of ~7 posts (오이냉국, 청양고추, 자두 손질법, 자두-대구, 대구치맥옥수수, 전복죽, 수박); user directed doing 자두/옥수수/전복죽/수박 next, one at a time.

**Why:** older posts predate several rule changes (title scoring rubric, coupang banner policy, "정직 정정" honest-correction technique for stale hooks) and don't reflect them.

**How to apply:** Before trusting any inherited handoff note about which posts are/aren't done, re-verify against `blog_posts.seo_score IS NULL` — the DB state can drift from written handoff notes across sessions. See [[feedback-one-task-at-a-time]] and [[feedback-no-filler-meta-commentary]] for behavioral corrections learned mid-batch. Note: `coupang_url` alone does NOT auto-display banners on blog pages (only `coupang_banner_html_blog` manually inserted does) — this is documented in the server's own `main` prompt (re-confirmed 2026-07-10), not repeated here since it lives at the source of truth.
