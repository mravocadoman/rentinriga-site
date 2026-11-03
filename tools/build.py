#!/usr/bin/env python3
"""Builds everything that comes from data/areas.json. Run after editing the data:

    python3 tools/build.py

Writes assets/areas.js (the browser copy of the data), areas/ (index + one guide per area),
riga-rent-prices/ and sitemap.xml. The output is committed; the deploy does not run this.
"""
import json
import math
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / 'data/areas.json').read_text(encoding='utf-8'))
AREAS, CITY_AVG = DATA['areas'], DATA['city_avg']
SITE = 'https://rentinrigalatvia.lv'
ROOMS = ['1-room (studio)', '2-room (1 bed)', '3-room (2 beds)', '4+ room (3+ beds)']
MAX_RENT = [max(a['rent'][i] or 0 for a in AREAS) for i in range(4)]
OLD_TOWN = (56.9472, 24.1067)  # Town Hall Square
ARROW = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
LOGO = '<svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="9" fill="#1f5eff"/><path d="M8 24V14l8-6 8 6v10h-5.5v-6h-5v6z" fill="#fff"/></svg>'


def eur(n):
    return f'€{n:,.0f}'


def km(a, b):
    r = math.pi / 180
    h = math.sin((b[0] - a[0]) * r / 2) ** 2 + math.cos(a[0] * r) * math.cos(b[0] * r) * math.sin((b[1] - a[1]) * r / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def vs_avg(rent, i):
    if not rent or not CITY_AVG[i]:
        return None
    return round((rent / CITY_AVG[i] - 1) * 100)


def badge(d):
    if not d:
        return ''
    return f'<span class="vs {"up" if d > 0 else "down"}" title="vs Riga average">{"+" if d > 0 else "−"}{abs(d)}%</span>'


def page(path, title, description, body, extra_head=''):
    canonical = f'{SITE}/{path}'
    html = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#ffffff">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{escape(title)}">
  <meta property="og:description" content="{escape(description)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{SITE}/assets/img/og.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="/apple-touch-icon.png">
  <link rel="preload" href="/assets/fonts/plus-jakarta-sans-latin.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="preload" href="/assets/fonts/plus-jakarta-sans-latin-ext.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/styles.css">
{extra_head}</head>
<body>
  <header class="site-header">
    <nav class="nav wrap" aria-label="Main">
      <a class="logo" href="/" aria-label="Rent in Riga, home">
        {LOGO}
        Rent in Riga
      </a>
      <button class="menu-toggle" aria-expanded="false" aria-controls="nav-links" aria-label="Menu">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
      </button>
      <ul class="nav-links" id="nav-links">
        <li><a href="/#how">How it works</a></li>
        <li><a href="/areas/">Neighbourhoods</a></li>
        <li><a href="/riga-rent-prices/">Rent prices</a></li>
        <li><a href="/#faq">FAQ</a></li>
        <li><a href="/partners/">For agencies</a></li>
      </ul>
      <a class="btn btn-primary" href="/#request">Get flat offers</a>
    </nav>
  </header>

  <main>
{body}
    <section class="cta-band">
      <div class="wrap cta-inner">
        <div>
          <h2>Moving to Riga soon?</h2>
          <p>Send one request and let agents who know the city do the searching. It takes about two minutes and it’s free.</p>
        </div>
        <a class="btn btn-primary btn-light" href="/#request">Get flat offers {ARROW}</a>
      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div class="wrap">
      <div class="foot-grid">
        <div>
          <a class="logo" href="/">{LOGO.replace('30', '28')} Rent in Riga</a>
          <p>Free flat-matching for people relocating to Riga, Latvia. We connect tenants with rental agencies. We don’t own or list flats ourselves.</p>
        </div>
        <div>
          <p class="foot-h">Guides</p>
          <ul>
            <li><a href="/areas/">Riga neighbourhoods</a></li>
            <li><a href="/how-to-rent-in-riga/">How to rent in Riga</a></li>
            <li><a href="/riga-rent-prices/">Rent prices in Riga</a></li>
            <li><a href="/#costs">Move-in cost calculator</a></li>
          </ul>
        </div>
        <div>
          <p class="foot-h">Contact</p>
          <ul>
            <li><a href="mailto:rihards.zeila@gmail.com">rihards.zeila@gmail.com</a></li>
            <li><a href="https://wa.me/37126673384" rel="noopener" target="_blank">WhatsApp</a></li>
            <li><a href="/partners/">For rental agencies</a></li>
            <li><a href="/privacy/">Privacy notice</a></li>
          </ul>
        </div>
      </div>
      <p class="small">© <span data-year>{date.today().year}</span> Rent in Riga Latvia</p>
    </div>
  </footer>
  <script src="/main.js" defer></script>
</body>
</html>
'''
    out = ROOT / path / 'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')


def ld(obj):
    return f'  <script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>\n'


def rent_bars(a):
    rows = []
    for i, r in enumerate(a['rent']):
        if not r:
            rows.append(f'<li><div class="row"><span>{ROOMS[i]}</span><span class="muted">too few listings</span></div></li>')
            continue
        rows.append(f'<li><div class="row"><span>{ROOMS[i]}</span><span><b>{eur(r)}</b>{badge(vs_avg(r, i))}</span></div>'
                    f'<div class="bar"><i style="width:{round(r / MAX_RENT[i] * 100)}%"></i></div></li>')
    return '<ul class="rent-bars">' + ''.join(rows) + '</ul>'


def area_card_link(a):
    r2 = a['rent'][1]
    return (f'<a class="area-link" href="/areas/{a["id"]}/"><span class="area-link-name">{escape(a["name"])}</span>'
            f'<span class="muted">{escape(a["tagline"])}</span>'
            f'<span class="area-link-rent">2-room avg <b>{eur(r2)}</b>{badge(vs_avg(r2, 1))}</span></a>')


def area_page(a):
    name, i2 = escape(a['name']), 1
    r2 = a['rent'][1]
    d = km(a['at'], OLD_TOWN)
    dist = 'Under 1 km' if d < 1 else f'{d:.1f} km'
    signing = round(r2 * 2.5)
    lv = f' <span class="muted">({escape(a["lv"])} in Latvian)</span>' if a['lv'] != a['name'] else ''
    others = ''.join(area_card_link(o) for o in AREAS if o['id'] != a['id'])
    title = f'Renting a flat in {a["name"]}, Riga (2026): rents and area guide'
    desc = f'{a["tagline"]} Average asking rent for a 2-room flat in {a["name"]}: {eur(r2)} a month (Mar–Oct 2026). Get offers from rental agencies for free.'
    crumbs = ld({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Rent in Riga', 'item': SITE + '/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Neighbourhoods', 'item': SITE + '/areas/'},
        {'@type': 'ListItem', 'position': 3, 'name': a['name'], 'item': f'{SITE}/areas/{a["id"]}/'}]})
    body = f'''    <section class="hero guide-hero">
      <div class="hero-bg" aria-hidden="true"></div>
      <div class="wrap">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/areas/">Neighbourhoods</a> / <span>{name}</span></nav>
        <p class="eyebrow">Riga neighbourhood guide</p>
        <h1>Renting in {name}{lv}</h1>
        <p class="lead">{escape(a['tagline'])} {escape(a['feel'])}</p>
        <div class="guide-actions">
          <a class="btn btn-primary" href="/?area={a['id']}#request">Get flat offers in {name} {ARROW}</a>
          <a class="btn btn-ghost" href="/?area={a['id']}#areas">See it on the map</a>
        </div>
        <ul class="stats">
          <li><strong>{eur(r2)}</strong><span>average 2-room asking rent</span></li>
          <li><strong>{(f"{vs_avg(r2, 1):+d}%" if vs_avg(r2, 1) else "≈ avg")}</strong><span>vs the Riga average</span></li>
          <li><strong>{dist}</strong><span>from Town Hall Square (straight line)</span></li>
          <li><strong>{eur(signing)}</strong><span>typical cost at signing (2-room)</span></li>
        </ul>
      </div>
    </section>

    <section>
      <div class="wrap guide-grid">
        <div>
          <h2>What to expect</h2>
          <div class="cards">
            <article><h3>What it’s like</h3><p>{escape(a['feel'])}</p></article>
            <article><h3>Getting around</h3><p>{escape(a['move'])}</p></article>
            <article><h3>Good for</h3><p>{escape(a['good'])}</p></article>
          </div>
        </div>
        <div class="area-card">
          <h3>Average asking rent in {name}</h3>
          <p class="tagline">Per month, excluding utilities. Latvian listings count all rooms, so a 2-room flat has one bedroom.</p>
          {rent_bars(a)}
          <p class="source-note">{escape(DATA['sources']['areas'])}. The % compares with the Riga-wide average from the same data. Signed rents can be lower.</p>
        </div>
      </div>
    </section>

    <section class="areas">
      <div class="wrap">
        <div class="section-head">
          <h2>What moving in costs here</h2>
          <p class="lead">For an average 2-room flat in {name} at {eur(r2)} a month, expect about <b>{eur(signing)}</b> due when you sign. That covers the first month’s rent, a one-month deposit (refundable) and an agency fee of half a month, if one is charged. Utilities come on top, and heating is the big one in winter.</p>
          <a class="btn btn-ghost" href="/#costs">Work it out for your budget</a>
        </div>
      </div>
    </section>

    <section>
      <div class="wrap">
        <div class="section-head">
          <h2>Compare with other neighbourhoods</h2>
        </div>
        <div class="area-links">{others}</div>
      </div>
    </section>
'''
    page(f'areas/{a["id"]}', title, desc, body, crumbs)


def areas_index():
    cards = ''.join(area_card_link(a) for a in sorted(AREAS, key=lambda a: -a['rent'][1]))
    body = f'''    <section class="hero guide-hero">
      <div class="hero-bg" aria-hidden="true"></div>
      <div class="wrap">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <span>Neighbourhoods</span></nav>
        <p class="eyebrow">Neighbourhood guides</p>
        <h1>Where to live in Riga</h1>
        <p class="lead">Eleven popular Riga neighbourhoods compared: average asking rents, what each area is like and how it connects to the rest of the city. Not sure yet? <a href="/#match">Try the neighbourhood matcher</a>.</p>
      </div>
    </section>
    <section>
      <div class="wrap">
        <div class="area-links">{cards}</div>
        <p class="source-note">Sorted by average 2-room asking rent. {escape(DATA['sources']['areas'])}.</p>
      </div>
    </section>
'''
    page('areas', 'Riga neighbourhood guides for renters (2026) | Rent in Riga',
         'Where to live in Riga: 11 neighbourhoods compared, with average asking rents for 2026, transport and what each area is like.', body)


def prices_page():
    rows = ''.join(
        f'<tr><th scope="row"><a href="/areas/{a["id"]}/">{escape(a["name"])}</a></th>'
        + ''.join(f'<td>{eur(r) if r else "–"}</td>' for r in a['rent']) + '</tr>'
        for a in sorted(AREAS, key=lambda a: -a['rent'][1]))
    avg = CITY_AVG
    med = DATA['city_median']
    cheapest = min(AREAS, key=lambda a: a['rent'][1])
    priciest = max(AREAS, key=lambda a: a['rent'][1])
    faq = [
        ('What is the average rent in Riga in 2026?',
         f'Across Riga listings from March to October 2026, the average asking rent was {eur(avg[0])} a month for a 1-room flat, {eur(avg[1])} for a 2-room flat and {eur(avg[2])} for a 3-room flat, excluding utilities.'),
        ('Which Riga neighbourhood is the cheapest to rent in?',
         f'Of the areas we track, {cheapest["name"]} had the lowest average 2-room asking rent at {eur(cheapest["rent"][1])} a month. {priciest["name"]} was the highest at {eur(priciest["rent"][1])}.'),
        ('Are utilities included in Riga rents?',
         'Usually not. Heating, water, waste, the building management fee and electricity are paid on top, and heating costs most in winter, especially in un-insulated buildings.'),
    ]
    faq_ld = ld({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': t}} for q, t in faq]})
    faq_html = ''.join(f'<details><summary>{escape(q)}</summary><p>{escape(t)}</p></details>' for q, t in faq)
    body = f'''    <section class="hero guide-hero">
      <div class="hero-bg" aria-hidden="true"></div>
      <div class="wrap">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <span>Rent prices</span></nav>
        <p class="eyebrow">Updated {DATA['updated'][:4]}</p>
        <h1>Rent prices in Riga (2026)</h1>
        <p class="lead">Average asking rents by neighbourhood and flat size, from listings published between March and October 2026. Rents are per month and exclude utilities.</p>
        <ul class="stats">
          <li><strong>{eur(avg[0])}</strong><span>1-room (studio), Riga average</span></li>
          <li><strong>{eur(avg[1])}</strong><span>2-room (1 bed), Riga average</span></li>
          <li><strong>{eur(avg[2])}</strong><span>3-room (2 beds), Riga average</span></li>
          <li><strong>{eur(cheapest['rent'][1])}–{eur(priciest['rent'][1])}</strong><span>2-room range across areas</span></li>
        </ul>
      </div>
    </section>

    <section>
      <div class="wrap">
        <div class="section-head">
          <h2>Average rent by neighbourhood</h2>
          <p class="lead">Latvian listings count all rooms, not bedrooms: a 2-room flat has a living room and one bedroom.</p>
        </div>
        <div class="table-wrap">
          <table class="price-table">
            <thead><tr><th scope="col">Neighbourhood</th>{''.join(f'<th scope="col">{r}</th>' for r in ROOMS)}</tr></thead>
            <tbody>{rows}</tbody>
            <tfoot><tr><th scope="row">Riga average</th>{''.join(f'<td>{eur(v) if v else "–"}</td>' for v in avg)}</tr></tfoot>
          </table>
        </div>
        <p class="source-note">Neighbourhoods: {escape(DATA['sources']['areas'])}. Riga average: {escape(DATA['sources']['city_avg'])}. A second source, {escape(DATA['sources']['city_median'])}, puts the typical (median) rent a little higher: {eur(med[0])}, {eur(med[1])} and {eur(med[2])} for 1, 2 and 3 rooms. Medians and averages differ because a few large or cheap flats pull the average. These are asking prices; signed rents can be lower.</p>
      </div>
    </section>

    <section class="areas">
      <div class="wrap guide-grid">
        <div>
          <h2>What else you’ll pay</h2>
          <div class="cards">
            <article><h3>Deposit</h3><p>Usually one month’s rent. Latvia’s Residential Tenancy Law caps it at two months.</p></article>
            <article><h3>Agency fee</h3><p>Commonly 50% of one month’s rent on agency listings. Flats rented straight from a private owner often have no fee.</p></article>
            <article><h3>Utilities</h3><p>Heating, water, waste, the building fee and electricity come on top. An un-insulated 45 m² flat can cost around €116–142 a month to heat in December–January, against about €46–57 in an insulated building (Rīgas siltums example, excl. VAT).</p></article>
          </div>
          <p><a class="btn btn-ghost" href="/#costs">Open the move-in cost calculator</a></p>
        </div>
        <div class="faq">
          <h2>Quick answers</h2>
          {faq_html}
        </div>
      </div>
    </section>
'''
    page('riga-rent-prices', 'Rent prices in Riga 2026: average rent by neighbourhood | Rent in Riga',
         f'Average rent in Riga in 2026: {eur(avg[0])} for a studio, {eur(avg[1])} for a 1-bedroom (2-room) flat and {eur(avg[2])} for 2 bedrooms. Compare 11 neighbourhoods.',
         body, faq_ld)


def sitemap():
    urls = ['', 'ru/', 'how-to-rent-in-riga/', 'riga-rent-prices/', 'areas/'] + [f'areas/{a["id"]}/' for a in AREAS] + ['partners/', 'privacy/', 'ru/privacy/']
    today = date.today().isoformat()
    body = ''.join(f'  <url><loc>{SITE}/{u}</loc><lastmod>{today}</lastmod></url>\n' for u in urls)
    (ROOT / 'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}</urlset>\n', encoding='utf-8')


def how_to_rent():
    avg = CITY_AVG
    glossary = [
        ('dzīvoklis', 'flat'),
        ('istaba', 'room. Listings count every room, so “2 istabas” is a living room and one bedroom'),
        ('izīrē', 'for rent (the section to look in on listing sites)'),
        ('īres maksa', 'monthly rent'),
        ('komunālie maksājumi', 'utilities'),
        ('apsaimniekošanas maksa', 'building management fee'),
        ('drošības nauda', 'security deposit'),
        ('mēbelēts', 'furnished'),
        ('stāvs', 'floor'),
        ('īres līgums', 'lease'),
        ('bez starpniekiem', 'no agents involved, so usually no agency fee'),
        ('deklarēt dzīvesvietu', 'declare your place of residence'),
    ]
    gl = ''.join(f'<dt lang="lv">{escape(lv)}</dt><dd>{escape(en)}</dd>' for lv, en in glossary)
    article = ld({'@context': 'https://schema.org', '@type': 'Article',
                  'headline': 'How to rent a flat in Riga as a foreigner (2026)',
                  'datePublished': DATA['updated'], 'dateModified': DATA['updated'], 'inLanguage': 'en',
                  'author': {'@type': 'Organization', 'name': 'Rent in Riga Latvia', 'url': SITE + '/'},
                  'publisher': {'@type': 'Organization', 'name': 'Rent in Riga Latvia', 'url': SITE + '/'},
                  'mainEntityOfPage': f'{SITE}/how-to-rent-in-riga/'})
    body = f"""    <section class="hero guide-hero">
      <div class="hero-bg" aria-hidden="true"></div>
      <div class="wrap">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <span>How to rent in Riga</span></nav>
        <p class="eyebrow">Step-by-step guide</p>
        <h1>How to rent a flat in Riga as a foreigner</h1>
        <p class="lead">Six steps from setting a budget to getting your keys, with the costs, the Latvian words you’ll meet in listings, and the rules that protect you. Updated for 2026.</p>
        <div class="guide-actions">
          <a class="btn btn-primary" href="/#request">Skip the search: get offers {ARROW}</a>
          <a class="btn btn-ghost" href="/#match">Find my neighbourhood</a>
        </div>
      </div>
    </section>

    <section>
      <article class="wrap prose how-to">
        <h2>1. Set a realistic budget</h2>
        <p>Across Riga listings from March to October 2026, the average asking rent was <b>{eur(avg[0])}</b> a month for a 1-room flat (studio), <b>{eur(avg[1])}</b> for a 2-room flat (one bedroom) and <b>{eur(avg[2])}</b> for a 3-room flat (two bedrooms), before utilities. Central areas cost more. See <a href="/riga-rent-prices/">rent prices by neighbourhood</a>.</p>
        <p>Plan for more than the rent when you sign:</p>
        <ul>
          <li><b>Deposit:</b> usually one month’s rent. Latvia’s Residential Tenancy Law caps it at two months.</li>
          <li><b>Agency fee:</b> commonly 50% of one month’s rent on agency listings. Flats rented straight from the owner often have none.</li>
          <li><b>Utilities:</b> heating, water, waste, the building management fee and electricity are usually paid on top. Heating is the big one in winter, and it costs far more in an un-insulated building.</li>
        </ul>
        <p>The <a href="/#costs">move-in cost calculator</a> adds it up for your rent.</p>

        <h2>2. Choose where to live</h2>
        <p>Think about your commute first, then what you want around you: cafés and walkability in the centre, parks and quiet in areas like Teika or Mežaparks, or lower rents in large estates like Purvciems and Imanta. The <a href="/#match">neighbourhood matcher</a> scores all eleven areas on your budget, workplace and priorities, and each has its own <a href="/areas/">neighbourhood guide</a>.</p>

        <h2>3. Read Latvian listings</h2>
        <p>Many listings are in Latvian or Russian. These words come up all the time:</p>
        <dl class="glossary">{gl}</dl>

        <h2>4. View the flat safely</h2>
        <p>Never pay a deposit or reservation fee for a flat you haven’t seen in person or on a live video call where someone walks through it. A known scam aimed at newcomers is a fake listing with copied photos that asks for money up front. At the viewing:</p>
        <ul>
          <li>Ask for last winter’s utility bills, not just the summer ones.</li>
          <li>Check the windows, the water pressure, the heating and where the internet comes from.</li>
          <li>Ask who owns the flat. A real owner or agent can show it; ownership can be checked in the Land Register (zemesgramata.lv).</li>
          <li>Take photos of everything, including existing damage, before you move in.</li>
        </ul>

        <h2>5. Sign a proper lease</h2>
        <p>Under the Residential Tenancy Law (in force since 2021), a lease has to be in writing and for a fixed term. It should state the rent and how and when it can change, the deposit, who pays which bills, and an inventory of the furniture. Tenants can usually end a lease with one month’s written notice. Registering the lease in the Land Register is optional, but an unregistered lease can end when a new owner registers the flat, so ask about it for a long stay. The landlord has to return any unused part of the deposit when you move out, unless the contract says otherwise. Read the law itself at <a href="https://likumi.lv/ta/id/322216" rel="noopener" target="_blank">likumi.lv</a>.</p>

        <h2>6. Move in and register</h2>
        <p>If you live in Latvia on a residence permit or an EU registration certificate, declare your place of residence within one month of moving in. You can do it online at latvija.gov.lv, and your lease is the legal basis for the address. EU citizens staying longer than three months also need a registration certificate from the Office of Citizenship and Migration Affairs. Check the current rules at <a href="https://www.pmlp.gov.lv/en/declaration-residence-place" rel="noopener" target="_blank">pmlp.gov.lv</a>.</p>

        <div class="how-cta">
          <h2>Rather not do all of this alone?</h2>
          <p>Tell us your dates, budget and areas in about two minutes. We pass your request to up to three rental agencies, who reply with flats that fit. It’s free for you.</p>
          <a class="btn btn-primary" href="/#request">Get flat offers {ARROW}</a>
        </div>
      </article>
    </section>
"""
    page('how-to-rent-in-riga', 'How to rent a flat in Riga as a foreigner (2026 guide) | Rent in Riga',
         f'Renting in Riga step by step: average rents ({eur(avg[1])} for a 1-bedroom), deposit and agency fees, Latvian listing words, avoiding scams, the lease and registering your address.',
         body, article)


def translate(src, table, what):
    """Swaps visible text and translatable attributes through table (exact, whitespace-normalised).
    Scripts, styles and form values are left alone. Fails on any untranslated text."""
    import re
    from html import unescape
    missing = []

    def tr(text):
        key = ' '.join(unescape(text).split())
        if not key or not any(c.isalpha() for c in key):
            return None
        if key not in table:
            missing.append(key)
            return None
        return table[key]

    def text_node(m):
        raw = m.group(1)
        t = tr(raw)
        if t is None:
            return m.group(0)
        lead, trail = raw[:len(raw) - len(raw.lstrip())], raw[len(raw.rstrip()):]
        return '>' + lead + escape(t, quote=False) + trail + '<'

    def attr(m):
        t = tr(m.group(2))
        return m.group(0) if t is None else f'{m.group(1)}="{escape(t)}"'

    out = []
    # SVG stays in: it has no text, and cutting it out would split the labels next to icons.
    for part in re.split(r'(<script\b.*?</script>|<style\b.*?</style>)', src, flags=re.S):
        if part.startswith(('<script', '<style')):
            out.append(part)
            continue
        part = re.sub(r'>([^<]+)<', text_node, part)
        part = re.sub(r'\b(alt|placeholder|aria-label|title)="([^"]*)"', attr, part)
        part = re.sub(r'(<meta (?:name|property)="(?:description|og:title|og:description|og:image:alt)" content)="([^"]*)"', attr, part)
        out.append(part)
    if missing:
        raise SystemExit(f'{what}: {len(missing)} untranslated string(s):\n  ' + '\n  '.join(dict.fromkeys(missing)))
    return ''.join(out)


def russian():
    table = json.loads((ROOT / 'data/i18n/ru-index.json').read_text(encoding='utf-8'))
    s = translate((ROOT / 'index.html').read_text(encoding='utf-8'), table, 'ru/index.html')
    for a, b in [
        ('<html lang="en">', '<html lang="ru">'),
        ('<link rel="canonical" href="https://rentinrigalatvia.lv/">', '<link rel="canonical" href="https://rentinrigalatvia.lv/ru/">'),
        ('<meta property="og:url" content="https://rentinrigalatvia.lv/">', '<meta property="og:url" content="https://rentinrigalatvia.lv/ru/">\n  <meta property="og:locale" content="ru_RU">'),
        ('<a class="lang-switch" href="/ru/" hreflang="ru" lang="ru">RU</a>', '<a class="lang-switch" href="/" hreflang="en" lang="en">EN</a>'),
        ('href="/privacy/"', 'href="/ru/privacy/"'),
        ('<a class="logo" href="/"', '<a class="logo" href="/ru/"'),
    ]:
        assert a in s, a
        s = s.replace(a, b)
    (ROOT / 'ru').mkdir(exist_ok=True)
    (ROOT / 'ru/index.html').write_text(s, encoding='utf-8')

    table = json.loads((ROOT / 'data/i18n/ru-privacy.json').read_text(encoding='utf-8'))
    s = translate((ROOT / 'privacy/index.html').read_text(encoding='utf-8'), table, 'ru/privacy/index.html')
    for a, b in [
        ('<html lang="en">', '<html lang="ru">'),
        ('<link rel="canonical" href="https://rentinrigalatvia.lv/privacy/">', '<link rel="canonical" href="https://rentinrigalatvia.lv/ru/privacy/">'),
        ('<a class="logo" href="/"', '<a class="logo" href="/ru/"'),
        ('href="/#request"', 'href="/ru/#request"'),
        ('<a href="/">', '<a href="/ru/">'),
    ]:
        assert a in s, a
        s = s.replace(a, b)
    (ROOT / 'ru/privacy').mkdir(parents=True, exist_ok=True)
    (ROOT / 'ru/privacy/index.html').write_text(s, encoding='utf-8')


if __name__ == '__main__':
    # A sanity check before writing anything: every area has 4 rent slots and a known tag set.
    for a in AREAS:
        assert len(a['rent']) == 4 and a['rent'][1], a['id']
        assert set(a['tags']) <= {'walk', 'quiet', 'green', 'new', 'character', 'cafes'}, a['id']
    (ROOT / 'assets/areas.js').write_text(
        '// Generated by tools/build.py from data/areas.json. Do not edit by hand.\nwindow.RR_DATA = '
        + json.dumps(DATA, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
    for a in AREAS:
        area_page(a)
    areas_index()
    prices_page()
    how_to_rent()
    russian()
    sitemap()
    print(f'built {len(AREAS)} area guides, areas index, rent prices page, sitemap, assets/areas.js')
