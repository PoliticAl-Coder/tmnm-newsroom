# TMNM Published Article Catalogue

**Project:** Truth Matters News Media (TMNM) — public, published-only article discovery page.

**Account:** `PoliticAl-Coder`  
**Repository:** https://github.com/PoliticAl-Coder/tmnm-newsroom  
**Source branch:** `gh-pages` (isolated from `master`)  
**Static page:** `index.html` at branch root  
**GitHub source page:** https://github.com/PoliticAl-Coder/tmnm-newsroom/blob/gh-pages/index.html  
**Hosting setup:** https://github.com/PoliticAl-Coder/tmnm-newsroom/settings/pages  
**Intended public page:** https://political-coder.github.io/tmnm-newsroom/ — **not verified deployed**  
**Original isolated first-build commit:** `77ae8097a606f567d4efd9a62a84f4e89c6a8515` (18 October 2026). Later updates are in the same branch history.

## Current data — 18 October 2026

**Three published article records**, with only established destination URLs:

| Article | Author | Publication evidence | Linked destinations | Internal source |
|---|---|---|---|---|
| The SpaceX Space Jellyfish — What's Really in That Glowing Cloud? | Politic-Al | Owner explicitly confirmed manual Substack + personal Politic-Al Facebook publication on 15 Oct 2026; Facebook permalink not recorded | Substack only | Pipeline editorial register `1U0fd7VPQf2bYoarQPjdx5HYDeJfJAmYvCCh126kNYok`, REF `PIPELINE-20261015-JELLYFISH-OWNER-PUBLISHED-230` |
| The Cost of Saying No | Politic-Al | Owner confirmed written Substack and TMNM Facebook publication; both URLs recorded. Current content/availability not independently verified | Substack + Facebook | Publication standard `1dVzp3b5T-jT5uyfCA2RMztX9qncOT_i20NjMiAJD738`; canonical manifest `1T5tZ4cX_FKiL7tIKRYS8SPG7TIbCwdo70GeEZzYWh2E` |
| The Sunday Sit-Down: They Sold the Headline Before the Receipt Cleared | Tony Two Sources | Facebook terminal provider publication receipt from 9 Aug 2026 at 17:38:09 UTC, post ID `1021402681056527_122120958357212493`; no verified Substack publication | Facebook only | Tony published package record `1IWhKG8xTEJXyHRbORXlAdzN8VyN6HrI5tcMOQxpEAeo` and Meta audit `1SNifRA_PXx3QJqtjdAmfkOsyRpFS-wT9` |

For these records, `publishedDate` identifies the date of the documented publication record, **not necessarily a provider-verified publication timestamp**. The historical Tony provider receipt supplies an actual timestamp. Do not represent owner testimony alone as independent provider verification.

## Article catalogue scope and display

- Public **published** stories only. Do **not** include drafts, review queues, QA/test fixtures, held unpublished packages or placeholder public URLs.
- Links point directly to original platform posts; the catalogue does not duplicate article bodies, artwork or videos.
- Explore using title/keyword search, author filter, category tabs (Series, Explainers, Investigations, Analysis), series selection, date or alphabetical sort.
- Keep named or numbered series in their true canonical order. The dated Tony Sunday series is a weekly franchise, not a numbered sequence.
- Only show a Substack/Facebook link when its actual URL is recorded; missing destination links are omitted rather than fabricated.
- Preserve the separation between owner-confirmed published and provider-verified publication receipts in source metadata.

## Existing published records still awaiting catalogue evidence

Do **not** add the following solely based on draft files or historical partial evidence:
- Asha's historical manually published series: identify the individual **published** canonical edition and real Substack/Facebook permalinks; exclude unpublished or held parts.
- Rogue Presidency: a post ID/permalink was produced in a 26 Aug 2026 safety incident during an unintended timed-out technical call; **do not promote into the public editorial catalogue without an explicit current owner/editorial disposition**. See Drive incident `1r4fQWQWS5vJjfxlyC8c7_qG_1hHk2-zYsmkBNJt96Sc`.
- Unpublished Tony Kiriakou investigation and 9 Aug Sunday Sit-Down Substack archive companion: not independently published; exclude.
- Other OSINT, weather, Asha, Politic-Al, trader or Ben authored **drafts/series**: publication must be proven **per edition**, not inferred from manuscript titles.

## Safe future population

Read the original canonical publication-status and exact URL evidence first, especially Pipeline's editorial register, the publication links standard and provider publication receipts. Add a record to the `ARTICLES` array in `index.html` **only when publication is evidenced and at least one genuine public publisher URL is recorded**. Preserve the existing data format; do not infer an additional channel, image, approval, or public release permission.

An author-provided draft or Google Drive source document is **not** a public publication URL. An owner-confirmed post may remain published even without an exact provider receipt, but there is no catalogue link until its destination URL is known.

## Hosting / release status

The source is committed in GitHub but **GitHub Pages deployment has not been verified**. A GitHub repository administrator can use **Settings → Pages**, choose **Deploy from a branch**, set branch **gh-pages** and folder **/(root)**, then Save. Afterwards verify the generated live page rather than assuming the intended URL works.

Creating/updating the isolated `gh-pages` branch does not modify the protected `master` branch or TMNM's private 8766 OwnerConsole and carries **no provider publication, OBS, rights, credential or safety-hold change**.

## Change record

- **18 Oct 2026** — Owner instructed Director to build the catalogue in existing GitHub without distracting image recovery. The isolated `gh-pages` branch was created, with a standalone `index.html`, `README.md`, and `.nojekyll`, subsequently isolated to those files at commit `77ae8097a606f567d4efd9a62a84f4e89c6a8515`.
- **18 Oct 2026** — Owner requested these details be recorded and that the site be populated. Director populated the page with three existing documented publications. The exact commit appears in GitHub history.

**Operational state:** BUILT AND POPULATED IN GITHUB. **Live GitHub Pages URL:** NOT VERIFIED. **Published records in source:** 3. **Additional catalogued records:** add only when evidence is available.
