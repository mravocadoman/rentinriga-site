# rentinrigalatvia.lv rebuild — plan (2026-11-03)

## Why
The current site is a WordPress/Divi brochure on SiteGround. It has no form (0 forms on the page), its testimonials are invented (one is signed by a 19th-century poet), and the four "featured flats" with street addresses are not real listings. It cannot capture a lead.

The new site is a **lead-generation site**. Someone relocating to Riga, mostly in IT, tells us what they need in two minutes. We pass the request to partner rental agencies, who compete to house them. Agencies pay us. The visitor pays us nothing.

## Goals
- Turn visits into complete, well-qualified rental requests: dates, length of stay, budget, rooms, areas, and who is moving.
- Help visitors decide (which area, what it costs, what to pay up front), so the form feels like the next step and not a gate.
- A second funnel for the supply side: rental agencies apply to receive leads (`/partners/`).
- Every lead lands in an n8n table, an e-mail and a Telegram ping within seconds.

## Non-goals (for now)
- No listings database or property pages. We don't hold inventory, and fake listings are worse than none.
- No automatic forwarding to agencies until real partners are signed. Rihards forwards by hand from the e-mail. Automate it once there are 2+ partners.
- No LV/RU versions yet. The audience searches in English; add RU/UA later if ads show demand.

## Anti-goals
- Invented reviews, invented listings, invented numbers. Every price on the site is a sourced range with a date.
- Sharing anyone's data without explicit, named consent (GDPR).

## Stack (same as Impromotion, proven on the same SiteGround account)
- Static HTML/CSS/JS, no build step, no npm. Leaflet (cdnjs) for the area map.
- Form → `POST text/plain` → n8n webhook `rentinriga-lead` → validate + honeypot + key → n8n data table → reply to site → Gmail to Rihards → Telegram.
- Deploy: push to `main` → GitHub Actions → rsync over SSH to SiteGround → cache flush.

## Pages
1. `/`: hero with a quick-start (move-in, length, budget); how it works; area explorer (map + typical rent per area, "find me a flat here"); move-in cost calculator (deposit + agency fee + first month + utilities); who it's for (individuals, companies relocating staff); safety tips (scams); FAQ (+ FAQPage schema); the 3-step request wizard; footer.
2. `/partners/`: for agencies. How leads arrive, what's in a lead, the standards partners must keep, and an application form.
3. `/privacy/`: GDPR notice: controller, purposes, recipients (partner agencies, with consent), retention, rights.

## Request wizard
Step 1 *Your stay*: move-in date, length (1–3 / 3–6 / 6–12 / 12+ months), adults, children, pets.
Step 2 *Your flat*: max budget (slider), rooms, furnished, preferred areas (chips), must-haves (workspace, parking, balcony, lift, pets OK).
Step 3 *Contact*: name, e-mail, phone/WhatsApp, preferred channel, "my employer pays/relocates me" + company, notes, consent checkbox.
A live "typical rent for what you picked" hint warns early when the budget is below market. The draft is kept in localStorage so a reload loses nothing. UTM/gclid/referrer and the landing page are captured. Honeypot + minimum fill time.

## Open (owner)
- Go-live: deploying replaces the WordPress homepage. Needs the SiteGround SSH user/host for this site + GitHub repo secrets.
- Legal entity for the privacy notice (currently Rihards Zeila as controller).
- Partner agencies to route leads to.
