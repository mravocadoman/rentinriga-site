# Riga Flat Match (rentinrigalatvia.lv)

The site was called "Rent in Riga" until 2026-11-04. It was renamed because an older agency, Rent In Riga (rentinriga.lv, since 2005), uses that name. The domain, the repo and the n8n workflow and table names keep the old name.

rentinrigalatvia.lv rebuilt from WordPress (Divi) as a lead-generation site: people relocating to Riga send one rental request, and we pass it to up to three partner agencies. Static HTML/CSS/JS, English only, no build step. The font (Plus Jakarta Sans, OFL) is self-hosted in `assets/fonts/` (latin + latin-ext, which Latvian letters need). Leaflet loads from cdnjs only when the map scrolls near.

## Files

- `index.html`: homepage (hero quick start, how it works, comparison, neighbourhood matcher, area explorer + map, move-in cost calculator, scam tips, 3-step request wizard, FAQ, closing CTA)
- `partners/`: page for rental agencies, with the partner application form
- `privacy/`: GDPR notice. Keep it in step with what the forms collect and where the data goes.
- `styles.css`, `main.js`: shared by every page. `main.js` returns early on pages without the wizard.
- `assets/img/`: gpt-image-2 photos (illustrative; the hero says so)
- `n8n/lead-workflow.js`: source of the live n8n workflow, kept here so the form and the workflow change together
- `docs/plan.md`: the rebuild plan and open owner decisions

## Generated pages (`tools/build.py`)

`data/areas.json` is the single source for area facts, rents and the Riga averages (with `ru` texts per area). After editing it, or `index.html` / `privacy/index.html`, run:

```bash
python3 tools/build.py
```

It writes and you commit:
- `assets/areas.js`, the data the browser uses (`window.RR_DATA`);
- `areas/` (an index plus 11 guides);
- `riga-rent-prices/`;
- `how-to-rent-in-riga/`, whose Latvian listing terms went through the latvian-writing review pass with no findings;
- `sitemap.xml`;
- `ru/` and `ru/privacy/`.

The deploy does not run the build.

The Russian pages are translations of the English ones through `data/i18n/ru-index.json` and `ru-privacy.json`, exact text to translation. The build **fails and lists any English text with no translation**, so a copy change in English can't silently ship half-translated. `main.js` keeps its own strings in the `T` table (EN and RU), picked by `<html lang>`. Form values stay English in both languages, so lead e-mails are uniform; each lead carries `lang`, and Russian leads are marked `[RU]` in Telegram and `[ru]` in the table's source column.

Links can prefill the form: `/?area=teika&rooms=2&budget=700#request` (area ids are the ids in `data/areas.json`).

## Run locally

```bash
python3 -m http.server 4173
```

Port 4173 matters: the n8n workflow only echoes CORS for `localhost:4173`, `127.0.0.1:4173` and the live domain, so a test submit from any other port reaches n8n but shows an error on the page.

## Market numbers

Every figure on the site comes from a dated source:

- Area rents (`AREAS` in `main.js`): viszinis.lv average asking rent per neighbourhood, 1 Mar – 31 Oct 2026, by Latvian room count.
- Vericity.ai median (`city_median`, about 2,175 listings, 2 Nov 2026) is quoted only on the rent-prices page, as a second source. Everything else, including the budget hint's Riga figure, uses the viszinis.lv averages.
- City-wide averages for the "vs Riga average" badges and the matcher's "Lowest rent" (`CITY_AVG`): viszinis.lv, same dataset and period as the area rents.
- Matcher (`TAGS`, `WORK` in `main.js`): area tags mirror the area card copy, and commute is the straight-line distance to the chosen work district. The score weighs budget fit 45%, distance 30% and priorities 25%.
- Heating (`HEAT`): scaled from Rīgas siltums' 45 m² example (insulated €46–57, not insulated €116–142 a month in Dec–Jan, excl. VAT).
- Deposit cap of 2 months, written lease, fixed term, 1-month tenant notice: Dzīvojamo telpu īres likums (likumi.lv/ta/id/322216).

Refresh them about twice a year, and update the source notes in `index.html` and `main.js` at the same time.

## Leads

Both forms POST `text/plain` JSON to the n8n workflow **Rent in Riga — leads** (`Bx3M3FCdtLpM5LkA`, webhook `/webhook/rentinriga-lead?k=rr-lv-2026`). The workflow:

1. Rejects posts with a bad key, a filled honeypot, a fill time under 3 s, no consent or an invalid e-mail.
2. Saves the lead to the n8n data table **Rent in Riga leads** (`IfphWRSOm2SkfFaD`, status `new`).
3. Answers the site.
4. E-mails rihards.zeila@gmail.com with reply-to set to the lead. The block between the dashed lines can be forwarded to an agency as-is.
5. Sends a Telegram message to Rihards' private chat. The alert text is HTML-escaped and sent with `parse_mode: HTML`, because Telegram's default Markdown dropped `[RU]` and would fail on names containing `_` or `*`.

6. Sends tenants (not agencies) a confirmation e-mail, "Rent in Riga" from Rihards' Gmail, in the site's language.
   - It contains only fixed text and validated fields (dates, rooms, budget, and areas from the known list), never the name or the notes. That way the form can't be used to mail arbitrary text to a stranger.
   - At most one goes to each address per 24 hours. The workflow remembers a hash of the address, not the address itself.
   - If it fails, nothing else is affected.

Failures go to the shared alert workflow.

Leads are forwarded to agencies by hand for now. Record each forward in the `sent_to` column.

Retention: the n8n workflow **Rent in Riga — delete leads after 12 months** (`tuTr2xL1aH7kEtOx`, source in `n8n/retention-workflow.js`) runs daily at 03:15 Riga time. It deletes rows whose `createdAt` is more than 12 months old, which keeps the privacy notice's promise. A guard stops it from ever using a cutoff younger than 360 days. Successful runs aren't saved, so execution logs keep no copies of deleted leads.

## Deploy

Push to `main`, and GitHub Actions (`.github/workflows/deploy.yml`) does the rest, the same way as Impromotion:

1. Stamps `?v=<commit>` on our own CSS, JS and image links.
2. Rsyncs the site files over SSH (port 18765) into `www/rentinrigalatvia.lv/public_html/`, without `--delete`, so `.well-known/` (SSL renewal) is never touched.
3. Flushes the SiteGround cache.

The old WordPress files were moved to `~/removed-from-public/2026-11-03-wordpress/` on the server (with its original `.htaccess`); nothing was deleted, and its database still exists. Our `.htaccess` serves `404.html`, redirects `www.` to the bare domain and answers 410 for old WordPress endpoints (`/feed/`, `/wp-json/`, `wp-login.php`, …), so search engines drop them.

The repo secrets are `SG_SSH_KEY`, `SG_HOST` (`ssh.rentinrigalatvia.lv`) and `SG_USER` (`u1891-1ebmevm4ybzb`). The deploy key lives at `~/.ssh/rentinriga_siteground` on Rihards' Mac and is imported as "Github deploy" in Site Tools → Devs → SSH Keys Manager for this site. New top-level files or folders have to be added to the rsync list.

## Search Console

URL-prefix property `https://rentinrigalatvia.lv/` under rihards.zeila@gmail.com, added and verified 2026-11-03 with `googlec3673720e3b0e240.html`. It's the same per-account file Impromotion uses. It is in the repo and the deploy list. **Never delete it**, or the property loses verification. `sitemap.xml` was submitted the same day; it reads Success, with 18 pages discovered. Indexing was requested for `/`, `/riga-rent-prices/`, `/ru/` and `/how-to-rent-in-riga/`. The build regenerates `sitemap.xml`; a page added outside the build has to be added to `urls` in `tools/build.py`.

## Analytics

Cloudflare Web Analytics, which is cookieless and needs no consent banner, runs under the Cloudflare account rihards@marketingaskola.lv: Analytics → Web analytics → rentinrigalatvia.lv.
- The beacon snippet (site token `a43d3f88…`, public by design) sits before `</body>` in every hand-written page and in the `page()` template in `tools/build.py`, so the generated and Russian pages carry it too.
- A new hand-written page needs the snippet added by hand.
- Lead sources are recorded separately on each lead (UTM, gclid, referrer).
