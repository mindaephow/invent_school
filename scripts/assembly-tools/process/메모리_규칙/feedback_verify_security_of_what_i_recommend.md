---
name: feedback-verify-security-of-what-i-recommend
description: "After recommending SQL/functions that touch a shared DB, test that anonymous callers are actually blocked — I once told the user to create an open run_sql_query"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 66b15530-3124-4d75-84e3-f4a90cbda3aa
  modified: 2026-09-19T11:59:33.152Z
---

When I hand the user SQL to run, check the security consequence myself and verify it afterward with the public key. `run_sql_query` (SECURITY DEFINER, executes arbitrary SQL) copied from another project's MCP boilerplate was callable by anyone with the publishable key — I ran `select current_user` through it and got `postgres`. It had been live in the shared Supabase (유쇼츠/홍허브 data) until I noticed.

**Why:** the recipe I copied only said "risky, create only when needed" and I passed it on without `revoke ... from public, anon, authenticated`. The user pays for that mistake with their other products' data.

**How to apply:**
- Any SECURITY DEFINER / RPC / new table: end the SQL with explicit revokes, then curl it with the anon key and confirm `permission denied` before saying it's done.
- Tell the user immediately and plainly when I find such a hole, give the exact fix, and re-check after they run it.
- New Supabase projects here: "Automatically expose new tables" off means service_role also needs explicit GRANTs; publishable-key writes need column-level grants.
