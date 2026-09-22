# 8766 Connect Facebook — Phase 2
Current app ID: 1754274758914441. Expected Page: 1021402681056527.

Flow: CONNECT FACEBOOK -> Meta-owned OAuth dialog -> loopback callback -> protected Windows DPAPI token store -> GET-only /me/accounts?fields=name,access_token,tasks -> exact Page binding -> sanitised result.

Requested scopes: pages_show_list, pages_read_engagement, pages_manage_posts.

Owner configuration gate before execution: the current TMNM Publisher app must have Facebook Login enabled and must accept the exact callback URI used by 8766. Proposed fixed callback: http://localhost:8767/meta/callback. Do not ask the owner to change this until Master inspects it.

Raw credentials must never be written to GitHub, Drive, clipboard, console, result files, or ordinary logs. No Facebook write endpoint exists in this Phase-2 module.
