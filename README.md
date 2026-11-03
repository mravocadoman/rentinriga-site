# Rent in Riga Latvia

rentinrigalatvia.lv rebuilt from WordPress (Divi) as a lead-generation site: people relocating to Riga send one rental request, and we pass it to up to three partner agencies. Static HTML/CSS/JS, English only, no build step, no dependencies beyond Leaflet from cdnjs.

## Files

- `index.html`: homepage (hero quick start, how it works, area explorer + map, move-in cost calculator, scam tips, 3-step request wizard, FAQ)
- `partners/`: page for rental agencies, with the partner application form
- `privacy/`: GDPR notice. Keep it in step with what the forms collect and where the data goes.
- `styles.css`, `main.js`: shared by every page. `main.js` returns early on pages without the wizard.
- `assets/img/`: gpt-image-2 photos (illustrative; the hero says so)
- `n8n/lead-workflow.js`: source of the live n8n workflow, kept here so the form and the workflow change together
- `docs/plan.md`: the rebuild plan and open owner decisions

## Run locally

```bash
python3 -m http.server 4173
```

Port 4173 matters: the n8n workflow only echoes CORS for `localhost:4173`, `127.0.0.1:4173` and the live domain, so a test submit from any other port reaches n8n but shows an error on the page.

## Market numbers

Every figure on the site comes from a dated source:

- Area rents (`AREAS` in `main.js`): viszinis.lv average asking rent per neighbourhood, 1 Mar – 31 Oct 2026, by Latvian room count.
- City-wide fallback (`CITY`): vericity.ai median of about 2,175 listings, 2 Nov 2026.
- Heating (`HEAT`): scaled from Rīgas siltums' 45 m² example (insulated €46–57, not insulated €116–142 a month in Dec–Jan, excl. VAT).
- Deposit cap of 2 months, written lease, fixed term, 1-month tenant notice: Dzīvojamo telpu īres likums (likumi.lv/ta/id/322216).

Refresh them about twice a year, and update the source notes in `index.html` and `main.js` at the same time.

## Leads

Both forms POST `text/plain` JSON to the n8n workflow **Rent in Riga — leads** (`Bx3M3FCdtLpM5LkA`, webhook `/webhook/rentinriga-lead?k=rr-lv-2026`). The workflow:

1. Rejects posts with a bad key, a filled honeypot, a fill time under 3 s, no consent or an invalid e-mail.
2. Saves the lead to the n8n data table **Rent in Riga leads** (`IfphWRSOm2SkfFaD`, status `new`).
3. Answers the site.
4. E-mails rihards.zeila@gmail.com with reply-to set to the lead. The block between the dashed lines can be forwarded to an agency as-is.
5. Sends a Telegram message to Rihards' private chat.

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
