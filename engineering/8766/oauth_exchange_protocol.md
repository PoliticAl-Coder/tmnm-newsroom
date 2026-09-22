# Isolated Meta OAuth Exchange — synthetic design only

Scope: auth code -> confidential exchange -> one-time opaque handoff -> 8766 -> DPAPI. No publishing capability.

## Protocol
8766 creates transaction_id + OAuth state and retains binding locally. Authorization request includes state and an opaque transaction binding. Meta callback reaches isolated HTTPS Apps Script. Server verifies state/transaction record, expiry and unused status before exchange. Exchange adapter is injected; production adapter is absent in synthetic build. Returned credential is held only in Script Properties/cache-like temporary store under random 256-bit handoff id, with transaction binding and expiry. Browser redirects to localhost with only handoff id + transaction id. 8766 POSTs handoff id + transaction proof to HTTPS redeem endpoint. Server atomically consumes once, returns credential in response body over HTTPS, and deletes temporary record. 8766 DPAPI-protects immediately, then performs existing GET-only page/access preflight.

No token in URL/query/fragment/browser/log/Drive/GitHub/clipboard. No article/publish/feed endpoints.

No blind retry: exchange and redemption failures are terminal HOLD for that transaction.

## Provisioning design
One-time only after separate authority: Alan opens NEW isolated Apps Script project -> Project Settings -> Script Properties -> Add script property. Name META_APP_SECRET. Value is pasted directly from Meta's App Secret display into the property value field, Save. No chat/Drive/GitHub/source/result/8766 transit. This is the minimum owner-simple manual provisioning route; not authorised yet.
