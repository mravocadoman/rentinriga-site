#!/usr/bin/env python3
"""The /guides/ articles: cost of living, salaries, moving to Latvia, student housing.

Built by tools/build.py (guides.build()). Every number below is either from data/areas.json or from
the sources in SRC, checked on 2026-11-04. Change a figure here and the text, charts and
infographic all follow. Infographic PNGs are rendered separately, because they need Chrome:

    python3 tools/guides.py --render
"""
import subprocess
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build import ARROW, AREAS, CITY_AVG, DATA, ROOT, SITE, eur, ld, page  # noqa: E402
from charts import hbar, segbar, stats  # noqa: E402

UPDATED = '2026-11-04'
BY_ID = {a['id']: a for a in AREAS}

# ---- Sourced facts (see SRC for where each came from) ----
WAGE = {'gross': 1886, 'net': 1401, 'med_gross': 1527, 'med_net': 1168, 'riga_gross': 2068, 'min': 780}
TAX = {'si': .105, 'si_employer': .2359, 'pit': .255, 'pit_high': .33, 'high_from': 105300, 'extra_from': 200000,
       'untaxed': 550, 'dependant': 250}
NUMBEO = {'single': 869.30, 'family4': 2922.40, 'utilities85': 331.76}
PRICES = [  # Numbeo, Riga, last update 31 Oct 2026
    ('Meal at an inexpensive restaurant', 15.00), ('Three-course meal for two, mid-range restaurant', 60.00),
    ('Cappuccino', 3.32), ('Domestic draught beer, 0.5 l, in a bar', 5.00), ('Domestic beer, 0.5 l bottle, in a shop', 1.78),
    ('Milk, 1 l', 1.05), ('White bread, 500 g', 1.31), ('Eggs, 12', 3.17), ('Chicken fillets, 1 kg', 7.68),
    ('Gym membership, per month', 43.25), ('Mobile plan with 10 GB+ data, per month', 17.46),
    ('Home internet, 60 Mbps+, per month', 16.85),
]
TRANSPORT = {'month': 30, 'ride90': 1.50, 'day': 5, 'student': 12}
POWER_KWH = 0.273  # CSP ENC040, H1 2026, households using 1,000–2,499 kWh a year, all taxes
HEAT_45 = ('€116–142', '€46–57')  # Rīgas siltums example, 45 m², Dec–Jan, not insulated / insulated, excl. VAT
STUDENTS = {'mobile': 11.9, 'total': 76.4, 'origins': [('India', 28.7), ('Uzbekistan', 11.1), ('Sweden', 8.6)]}
DORMS = [  # monthly, per person, lowest listed price for that room type
    ('RSU Āgenskalns hostel, triple room', 105, 'rsu_ag'),
    ('LU Valdemāra 161, triple room', 142, 'lu'),
    ('LU Valdemāra 161, double room', 152, 'lu'),
    ('LU Valdemāra 161, single room', 220, 'lu'),
    ('RSU Āgenskalns hostel, single room', 230, 'rsu_ag'),
    ('LU Prima, single room', 291, 'lu'),
    ('RSU Dzirciems, single room', 525, 'rsu_dz'),
]

SRC = {
    'csp_wage': ('Official Statistics Portal (CSP): wages and salaries, Q2 2026 (2 Sep 2026)',
                 'https://stat.gov.lv/en/statistics-themes/labour-market/wages-and-salaries/press-releases/28686-wages-and-salaries-2nd'),
    'fm': ('Ministry of Finance: changes in taxation in 2026',
           'https://www.fm.gov.lv/en/changes-taxation-and-finances-2026'),
    'vid': ('State Revenue Service (VID): personal income tax rates (updated 30 Dec 2025)',
            'https://www.vid.gov.lv/en/personal-income-tax-rates'),
    'numbeo': ('Numbeo: cost of living in Riga (crowd-sourced, last update 31 Oct 2026)',
               'https://www.numbeo.com/cost-of-living/in/Riga'),
    'rents': (f'Rents: {DATA["sources"]["areas"]}; Riga average: {DATA["sources"]["city_avg"]}', f'{SITE}/riga-rent-prices/'),
    'rs_fares': ('LSM: Riga public transport fares unchanged (19 Mar 2026)',
                 'https://eng.lsm.lv/article/economy/transport/19.03.2026-rigas-bus-tickets-will-not-get-costlier-because-of-fuel-says-mayor.a639491/'),
    'rs_student': ('Rīgas satiksme: student monthly tickets cost EUR 12 (from 1 Jan 2024)',
                   'https://rigassatiksme.lv/en/current%20information/monthly-tickets-for-students-on-riga-public-transport-will-now-cost-eur-12'),
    'csp_power': ('CSP table ENC040: household electricity prices, H1 2026',
                  'https://stat.gov.lv/en/statistics-themes/business-sectors/energy/tables/enc040-electricity-prices-household-consumers'),
    'rs_heat': ('Rīgas siltums: about the company', 'https://www.rs.lv/saturs/rigas-siltums'),
    'csp_students': ('CSP: higher education topicalities, 2025/26 (12 Feb 2026)',
                     'https://stat.gov.lv/en/statistics-themes/education/higher-education/press-releases/26473-topicalities-higher-education'),
    'lu': ('University of Latvia: student accommodation (prices from 1 Jul 2026)', 'https://lu.lv/en/studies/student-life/accommodation'),
    'rsu_dz': ('Rīga Stradiņš University: Dzirciems hostel', 'https://www.rsu.lv/en/node/3720'),
    'rsu_ag': ('Rīga Stradiņš University: Āgenskalns hostel', 'https://rsu.lv/en/node/388'),
    'pmlp_decl': ('PMLP: declaring your place of residence', 'https://www.pmlp.gov.lv/en/declaration-residence-place'),
    'pmlp_eu': ('PMLP: residence documents for EU citizens', 'https://www.pmlp.gov.lv/en/what-residence-documents-are-issued-union-citizens-and-their-family-members'),
    'pmlp_code': ('PMLP: getting a personal identity number', 'https://www.pmlp.gov.lv/en/article/how-obtain-personal-identity-number-and-declared-place-residence-latvia'),
    'pmlp_work': ('PMLP: employment of foreigners', 'https://www.pmlp.gov.lv/en/employment-foreigners'),
    'pmlp_rp': ('PMLP: residence permits', 'https://www.pmlp.gov.lv/en/residence-permits'),
    'pmlp_fees': ('PMLP: state fees for residence permits', 'https://www.pmlp.gov.lv/en/state-fee-issuing-residence-permit'),
    'nvd': ('National Health Service: who gets state-funded healthcare', 'https://www.vmnvd.gov.lv/en/where-obtain-medical-assistance'),
    'lvportals': ('LV portāls: latvija.gov.lv logins from 1 Jan 2025',
                  'https://lvportals.lv/skaidrojumi/371272-portalam-latvija-lv-no-1-janvara-ar-internetbanku-pieslegties-nevares-2024'),
}


def net(gross, dependants=0):
    """Monthly take-home pay on a main job in 2026: employee social tax, then 25.5% income tax on what
    is left above the non-taxable minimum and dependant relief. Same formula as the calculator in main.js."""
    si = gross * TAX['si']
    pit = max(gross - si - TAX['untaxed'] - TAX['dependant'] * dependants, 0) * TAX['pit']
    return gross - si - pit


def pct(part, whole):
    return f'{part / whole * 100:.0f}%'


def money(v):
    return f'€{v:,.2f}' if v % 1 else eur(v)


def sources(keys):
    items = ''.join(f'<li><a href="{escape(SRC[k][1])}" rel="noopener" target="_blank">{escape(SRC[k][0])}</a></li>' for k in keys)
    return f'<aside class="sources"><h2>Sources</h2><ol>{items}</ol><p>Checked on {UPDATED}. Rents are asking prices; signed rents can be lower.</p></aside>'


GUIDES = []  # (slug, card title, card text) for the index, in order


def article(slug, title, desc, h1, eyebrow, lead, hero_stats, sections, faq, src, related, info_alt):
    """sections: [(id, heading, html)]. Writes /guides/<slug>/ with a contents box, FAQ, sources and
    the infographic with its embed code."""
    url = f'{SITE}/guides/{slug}/'
    img = f'/assets/img/infographics/{slug}.png'
    toc = ''.join(f'<li><a href="#{i}">{escape(h)}</a></li>' for i, h, _ in sections)
    body_secs = ''.join(f'<h2 id="{i}">{escape(h)}</h2>\n{html}\n' for i, h, html in sections)
    embed = (f'<a href="{url}"><img src="{SITE}{img}" alt="{escape(info_alt)}" width="1080" height="1350" '
             f'style="max-width:100%;height:auto"></a><br>Source: <a href="{url}">Riga Flat Match</a>')
    faq_html = ''.join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q, a in faq)
    rel = ''.join(f'<li><a href="{h}">{escape(t)}</a></li>' for h, t in related)
    body = f'''    <section class="hero guide-hero">
      <div class="hero-bg" aria-hidden="true"></div>
      <div class="wrap">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/guides/">Guides</a> / <span>{escape(h1)}</span></nav>
        <p class="eyebrow">{escape(eyebrow)}</p>
        <h1>{escape(h1)}</h1>
        <p class="lead">{lead}</p>
        <p class="article-meta">Updated {UPDATED[8:].lstrip("0")} November 2026 · Riga Flat Match</p>
        {stats(hero_stats)}
      </div>
    </section>

    <section>
      <article class="wrap prose">
        <nav class="toc" aria-label="Contents"><b>In this guide</b><ol>{toc}<li><a href="#faq">Quick answers</a></li></ol></nav>
{body_secs}
        <figure class="infographic">
          <img src="{img}" alt="{escape(info_alt)}" width="1080" height="1350" loading="lazy">
          <figcaption>
            <details class="embed-code"><summary>Share this infographic on your site</summary>
              <p>Free to use with a link back. Copy this code:</p>
              <textarea readonly rows="4" aria-label="Embed code">{escape(embed)}</textarea>
              <button class="btn btn-ghost" type="button" data-copy>Copy code</button>
            </details>
          </figcaption>
        </figure>

        <div class="how-cta">
          <h2>Looking for a flat in Riga?</h2>
          <p>Tell us your dates, budget and areas in about two minutes. We pass your request to up to three rental agencies, who reply with flats that fit. It’s free for you.</p>
          <a class="btn btn-primary" href="/#request">Get flat offers {ARROW}</a>
        </div>

        <div class="faq" id="faq">
          <h2>Quick answers</h2>
          {faq_html}
        </div>

        <h2>Related guides</h2>
        <ul>{rel}</ul>
        {sources(src)}
      </article>
    </section>
'''
    head = ld({'@context': 'https://schema.org', '@type': 'Article', 'headline': h1, 'description': desc,
               'image': SITE + img, 'datePublished': UPDATED, 'dateModified': UPDATED, 'inLanguage': 'en',
               'author': {'@type': 'Organization', 'name': 'Riga Flat Match', 'url': SITE + '/'},
               'publisher': {'@type': 'Organization', 'name': 'Riga Flat Match', 'url': SITE + '/'},
               'mainEntityOfPage': url})
    head += ld({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE + '/'},
        {'@type': 'ListItem', 'position': 2, 'name': 'Guides', 'item': SITE + '/guides/'},
        {'@type': 'ListItem', 'position': 3, 'name': h1, 'item': url}]})
    head += ld({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]})
    page(f'guides/{slug}', title, desc, body, head)


# ---------------------------------------------------------------- articles

def cost_of_living():
    rent1, rent2, rent3 = CITY_AVG[0], CITY_AVG[1], CITY_AVG[2]
    single = rent1 + NUMBEO['single']
    single_1bed = rent2 + NUMBEO['single']
    family = rent3 + NUMBEO['family4']
    month = segbar('One person in a studio: a month in Riga', [
        ('Rent, 1-room flat (Riga average)', rent1), ('Everything else (Numbeo estimate)', NUMBEO['single'])],
        lambda v: eur(v), note=f'Total {eur(single)} a month. Numbeo’s figure covers food, transport, utilities and other day-to-day costs.')
    households = hbar('Monthly total by household, rent included', [
        ('One person, studio flat', single), ('One person, 1-bedroom flat', single_1bed),
        ('Family of four, 2-bedroom flat', family)], eur,
        note='Riga average asking rent plus Numbeo’s living costs without rent.')
    studios = sorted(((a['name'], a['rent'][0]) for a in AREAS), key=lambda x: x[1])
    studio_chart = hbar('Average rent for a 1-room flat (studio) by neighbourhood', studios, eur,
                        note='Asking rent per month, March to October 2026, utilities not included.',
                        ref=(rent1, f'Riga average {eur(rent1)}'))
    prices = ''.join(f'<tr><td>{escape(n)}</td><td>{money(v)}</td></tr>' for n, v in PRICES)
    cheap = ', '.join(f'{n} ({eur(v)})' for n, v in studios[:3])
    sections = [
        ('summary', 'The short answer', f'''<p>A single person renting a studio in Riga should budget about <b>{eur(single)} a month</b> in 2026: {eur(rent1)} for the average 1-room flat plus about {eur(NUMBEO['single'])} for everything else, going by Numbeo’s crowd-sourced estimate. A family of four in a two-bedroom flat needs about <b>{eur(family)}</b>.</p>
<p>For scale, the average take-home pay in Latvia was <b>{eur(WAGE['net'])} a month</b> in the second quarter of 2026, and half of all full-time workers took home less than {eur(WAGE['med_net'])} (CSP). Rent is the one cost you have real control over, so where you live matters most.</p>
{month}
{households}'''),
        ('rent', 'Rent: the biggest cost', f'''<p>The average asking rent across Riga was {eur(rent1)} for a 1-room flat (a studio), {eur(rent2)} for a 2-room flat (one bedroom) and {eur(rent3)} for a 3-room flat (two bedrooms) between March and October 2026. Latvian listings count every room, so a “2-room” flat has a living room and one bedroom.</p>
<p>Prices vary a lot by area. The cheapest studios on average were in {cheap}; new-build districts and the centre cost more.</p>
{studio_chart}
<p>See every size and area on the <a href="/riga-rent-prices/">Riga rent prices</a> page, or let the <a href="/#match">neighbourhood matcher</a> pick areas for your budget.</p>'''),
        ('utilities', 'Utilities, heating and internet', f'''<p>Utilities are almost always paid on top of rent. Most of Riga is on district heating: Rīgas siltums supplies about 76% of the heat the city needs. The building’s insulation matters as much as your own habits. Rīgas siltums’ own example for a 45 m² flat is about <b>{HEAT_45[0]} a month</b> in December and January in an un-insulated building, against <b>{HEAT_45[1]}</b> in an insulated one (excluding VAT). Ask to see last winter’s bills before you sign.</p>
<ul>
<li><b>Electricity:</b> {money(POWER_KWH)} per kWh with all taxes for a typical small household in the first half of 2026 (CSP), so every 100 kWh costs about {eur(POWER_KWH * 100)}.</li>
<li><b>Internet:</b> about {money(16.85)} a month for 60 Mbps or faster (Numbeo).</li>
<li><b>Mobile:</b> about {money(17.46)} a month for a plan with 10 GB or more of data (Numbeo).</li>
</ul>
<p>Numbeo’s users put basic utilities for a larger 85 m² flat at about {eur(NUMBEO['utilities85'])} a month, averaged across the year.</p>'''),
        ('prices', 'Everyday prices in Riga', f'''<p>Typical prices from Numbeo, last updated on 31 October 2026. They are crowd-sourced, so treat them as a guide, not a quote.</p>
<div class="table-wrap"><table class="price-list"><tbody>{prices}</tbody></table></div>'''),
        ('transport', 'Getting around', f'''<p>Riga’s buses, trams and trolleybuses run on one ticket system. A <b>monthly ticket costs {eur(TRANSPORT['month'])}</b>, a 90-minute ticket with transfers {money(TRANSPORT['ride90'])} and a 24-hour ticket {eur(TRANSPORT['day'])}. Fares have not changed since 2023, and the mayor said in March 2026 that they would not go up. Students studying in Riga pay {eur(TRANSPORT['student'])} a month on a personalised e-ticket.</p>
<p>The centre, Old Town, Teika and Āgenskalns are walkable or a short tram ride from most offices, which can save the ticket altogether.</p>'''),
        ('save', 'How to spend less', '''<ul>
<li><b>Choose the area before the flat.</b> A 1-bedroom flat in Purvciems or Imanta costs about €250 a month less than in the centre.</li>
<li><b>Ask about insulation.</b> Renovated buildings can halve the winter heating bill.</li>
<li><b>Rent from the owner or negotiate the fee.</b> Agency fees are commonly half a month’s rent; many private landlords charge none.</li>
<li><b>Never pay before a viewing.</b> Fake listings that ask for a deposit up front are the most common scam aimed at newcomers.</li>
</ul>'''),
    ]
    faq = [
        ('How much does it cost to live in Riga per month?',
         f'About {eur(single)} a month for one person renting an average studio: {eur(rent1)} rent plus roughly {eur(NUMBEO["single"])} of other costs (Numbeo, October 2026). A family of four in a two-bedroom flat needs about {eur(family)}.'),
        ('Is Riga cheap to live in?',
         f'Riga is cheaper than most Western European capitals, but local wages are lower too: average take-home pay in Latvia was {eur(WAGE["net"])} a month in Q2 2026. A studio costs {eur(rent1)} on average.'),
        ('Are utilities included in rent in Riga?',
         'Usually not. Heating, water, waste, the building management fee and electricity are paid on top. Heating costs most in winter, especially in buildings without insulation.'),
        ('How much is public transport in Riga?',
         f'A monthly ticket costs {eur(TRANSPORT["month"])} and a 90-minute ticket {money(TRANSPORT["ride90"])}. Students pay {eur(TRANSPORT["student"])} a month.'),
    ]
    article('cost-of-living-in-riga',
            'Cost of living in Riga, Latvia (2026): monthly budget breakdown | Riga Flat Match',
            f'What it costs to live in Riga in 2026: about {eur(single)} a month for one person in a studio, {eur(family)} for a family of four. Rent by area, utilities, food and transport prices.',
            'Cost of living in Riga (2026)', 'Data guide',
            f'What a month in Riga really costs in 2026, built from {len(AREAS)} neighbourhoods of rent data, official statistics and crowd-sourced prices.',
            [(eur(single), 'one person in a studio, per month'), (eur(family), 'family of four, 2-bedroom flat'),
             (eur(rent1), 'average studio rent'), (eur(TRANSPORT['month']), 'monthly transport ticket')],
            sections, faq, ['rents', 'numbeo', 'csp_wage', 'rs_heat', 'csp_power', 'rs_fares', 'rs_student'],
            [('/guides/average-salary-latvia/', 'Average salary in Latvia and how far it goes on rent'),
             ('/riga-rent-prices/', 'Rent prices in Riga by neighbourhood'), ('/how-to-rent-in-riga/', 'How to rent a flat in Riga')],
            f'Infographic: a month in Riga costs about {eur(single)} for one person in a studio and {eur(family)} for a family of four in 2026.')
    GUIDES.append(('cost-of-living-in-riga', 'Cost of living in Riga (2026)',
                   f'About {eur(single)} a month for one person. Rent by area, utilities, food and transport.'))
    return {'single': single, 'family': family, 'month': month, 'households': households}


def salary():
    riga_net = net(WAGE['riga_gross'])
    min_net = net(WAGE['min'])
    wages = hbar('Monthly gross pay in Latvia, Q2 2026', [
        ('Minimum wage (2026)', WAGE['min']), ('Median, full-time', WAGE['med_gross']),
        ('Average, full-time', WAGE['gross']), ('Average in Riga', WAGE['riga_gross'])], eur,
        note='Before tax. Median: half of full-time workers earn less. Source: CSP, Ministry of Finance.')
    share_items = sorted(((a['name'], a['rent'][1] / WAGE['net'] * 100) for a in AREAS), key=lambda x: -x[1])
    share = hbar('Rent for a 1-bedroom flat as a share of average take-home pay', share_items, lambda v: f'{v:.0f}%',
                 note=f'Average asking rent for a 2-room flat in each area, divided by the average net wage of {eur(WAGE["net"])}.',
                 ref=(30, '30% of take-home pay, a common rule of thumb'))
    afford = [(n, w * .3) for n, w in [('Minimum wage', min_net), ('Median earner', WAGE['med_net']),
                                       ('Average earner', WAGE['net']), ('Average earner in Riga', riga_net)]]
    afford_rows = ''.join(f'<tr><td>{n}</td><td>{eur(v)}</td></tr>' for n, v in afford)
    calc = f'''<form class="chart-card calc-net" id="netcalc" onsubmit="return false">
  <label>Gross salary per month (€)<input type="number" name="gross" min="0" step="10" value="{WAGE['gross']}" inputmode="decimal"></label>
  <label>Dependants<select name="dep"><option>0</option><option>1</option><option>2</option><option>3</option><option>4</option></select></label>
  <ul class="net-out" aria-live="polite">
    <li class="net-main">Take-home pay<b data-out="net">–</b></li>
    <li>Social tax (10.5%)<b data-out="si">–</b></li>
    <li>Income tax<b data-out="pit">–</b></li>
    <li>Cost to employer<b data-out="employer">–</b></li>
  </ul>
</form>'''
    sections = [
        ('average', 'Average salary in Latvia in 2026', f'''<p>The average full-time gross wage in Latvia was <b>{eur(WAGE['gross'])} a month</b> in the second quarter of 2026, or <b>{eur(WAGE['net'])} after tax</b>, according to the Official Statistics Portal (CSP). Riga pays the most of any region, with an average of {eur(WAGE['riga_gross'])} gross.</p>
<p>The average is pulled up by high earners. The <b>median</b>, the pay of the worker in the middle, was {eur(WAGE['med_gross'])} gross and {eur(WAGE['med_net'])} net. The minimum wage rose to {eur(WAGE['min'])} a month in 2026, from €740.</p>
{wages}'''),
        ('tax', 'How salary tax works in 2026', f'''<p>On a regular payslip three things come off your gross pay:</p>
<ul>
<li><b>Social insurance:</b> {TAX['si'] * 100:.1f}% paid by you. Your employer pays another {TAX['si_employer'] * 100:.2f}% on top of your salary.</li>
<li><b>Non-taxable minimum:</b> the first {eur(TAX['untaxed'])} a month (after social insurance) is tax-free, plus {eur(TAX['dependant'])} for each dependant. This is applied at your main job, where your electronic salary tax booklet is held.</li>
<li><b>Income tax:</b> {TAX['pit'] * 100:.1f}% on the rest. Annual income above {eur(TAX['high_from'])} is taxed at {TAX['pit_high'] * 100:.0f}%, and income above {eur(TAX['extra_from'])} pays an extra 3%; both are settled in the annual tax return.</li>
</ul>
<p>Try it with your own offer. The calculator uses the 2026 rules above.</p>
{calc}
<p class="source-note">Estimate for a main job. It does not include employer benefits, other reliefs or the annual return.</p>'''),
        ('rent', 'How far a salary goes on rent', f'''<p>A common rule of thumb is to keep rent under about 30% of take-home pay. On the average Latvian net wage of {eur(WAGE['net'])}, an average 1-bedroom flat in Riga ({eur(CITY_AVG[1])}) takes {pct(CITY_AVG[1], WAGE['net'])}. Only Purvciems and Imanta come in around 30%; Ķīpsala takes {pct(BY_ID['kipsala']['rent'][1], WAGE['net'])}.</p>
{share}
<p>Riga salaries are higher than the national average. Using the 2026 tax rules, the average Riga gross wage of {eur(WAGE['riga_gross'])} works out at about <b>{eur(riga_net)} take-home</b>, which brings the average 1-bedroom flat down to {pct(CITY_AVG[1], riga_net)}.</p>
<p>Here is the rent that fits the 30% rule at different pay levels:</p>
<div class="table-wrap"><table class="price-list"><tbody>{afford_rows}</tbody></table></div>
<p>For comparison, the average studio costs {eur(CITY_AVG[0])}. See what each area costs on the <a href="/riga-rent-prices/">rent prices</a> page.</p>'''),
        ('offer', 'Checking a job offer in Riga', f'''<ul>
<li><b>Ask whether the figure is gross or net.</b> Latvian offers and job ads usually quote gross monthly pay.</li>
<li><b>Work out the take-home pay</b> with the calculator above, then budget rent at about a third of it.</li>
<li><b>Add the living costs.</b> Numbeo puts one person’s monthly costs without rent at about {eur(NUMBEO['single'])}. Our <a href="/guides/cost-of-living-in-riga/">cost of living guide</a> breaks it down.</li>
<li><b>Ask about relocation help.</b> Some employers pay the first month’s rent or the agency fee.</li>
</ul>'''),
    ]
    faq = [
        ('What is the average salary in Latvia in 2026?',
         f'{eur(WAGE["gross"])} a month gross and {eur(WAGE["net"])} net for full-time work in Q2 2026 (CSP). The median was {eur(WAGE["med_gross"])} gross.'),
        ('What is the average salary in Riga?',
         f'{eur(WAGE["riga_gross"])} a month gross in Q2 2026, the highest of any region. That is about {eur(riga_net)} after tax under the 2026 rules.'),
        ('What is the minimum wage in Latvia in 2026?', f'{eur(WAGE["min"])} a month gross, up from €740 in 2025.'),
        ('What is the income tax rate in Latvia?',
         f'{TAX["pit"] * 100:.1f}% on annual income up to {eur(TAX["high_from"])} and {TAX["pit_high"] * 100:.0f}% above it, plus 3% on income over {eur(TAX["extra_from"])}. Employees also pay {TAX["si"] * 100:.1f}% social insurance, and the first {eur(TAX["untaxed"])} a month is tax-free.'),
    ]
    article('average-salary-latvia',
            'Average salary in Latvia 2026: net pay, tax calculator and rent | Riga Flat Match',
            f'Average salary in Latvia in 2026: {eur(WAGE["gross"])} gross, {eur(WAGE["net"])} net; {eur(WAGE["riga_gross"])} in Riga. 2026 tax rules, a take-home pay calculator and how much of a salary goes on rent.',
            'Average salary in Latvia (2026), and how far it goes on rent', 'Data guide',
            'Official 2026 wage figures, a take-home pay calculator with this year’s tax rules, and what share of a salary rent takes in each Riga neighbourhood.',
            [(eur(WAGE['gross']), 'average gross wage'), (eur(WAGE['net']), 'average take-home pay'),
             (eur(WAGE['riga_gross']), 'average gross in Riga'), (eur(WAGE['min']), 'minimum wage 2026')],
            sections, faq, ['csp_wage', 'fm', 'vid', 'rents', 'numbeo'],
            [('/guides/cost-of-living-in-riga/', 'Cost of living in Riga'), ('/guides/moving-to-latvia/', 'Moving to Latvia: the checklist'),
             ('/riga-rent-prices/', 'Rent prices in Riga by neighbourhood')],
            f'Infographic: rent for a 1-bedroom flat takes {pct(min(a["rent"][1] for a in AREAS), WAGE["net"])} to {pct(max(a["rent"][1] for a in AREAS), WAGE["net"])} of the average Latvian take-home pay of {eur(WAGE["net"])}, depending on the Riga neighbourhood.')
    GUIDES.append(('average-salary-latvia', 'Average salary in Latvia (2026)',
                   f'{eur(WAGE["gross"])} gross, {eur(WAGE["net"])} net. Tax calculator and rent as a share of pay.'))
    return {'share': share}


def moving():
    steps = [
        ('Check which route applies to you', 'EU, EEA and Swiss citizens need no permit; everyone else needs a residence permit.', f'''<p><b>EU, EEA and Swiss citizens</b> can live and work in Latvia without a permit. If you stay longer than three months, you register (step 4).</p>
<p><b>Everyone else</b> needs a residence permit. The main routes are employment, the EU Blue Card, study and family. For a work permit, the employer first registers the vacancy with the State Employment Agency, and it has to stay open for 10 working days before a non-EU candidate can be hired. You apply at a Latvian embassy or consulate, or at the Office of Citizenship and Migration Affairs (PMLP) if you are already in Latvia legally. Permanent residence is possible after five years. Check the current state fees on <a href="{SRC['pmlp_fees'][1]}" rel="noopener" target="_blank">PMLP’s fee page</a>.</p>'''),
        ('Line up your work, study or business', 'It decides your permit and your budget.', '<p>Your permit and your budget both depend on it. Check a salary offer with our <a href="/guides/average-salary-latvia/">take-home pay calculator</a>, and see what a month costs in the <a href="/guides/cost-of-living-in-riga/">cost of living guide</a>.</p>'),
        ('Find a home', 'Your lease is the basis for registering your address.', '<p>Your lease is the legal basis for registering your address, so it comes early. Choose an area first: the <a href="/#match">neighbourhood matcher</a> scores eleven Riga areas on your budget, commute and priorities. Then read <a href="/how-to-rent-in-riga/">how to rent a flat in Riga</a> for deposits, agency fees and the lease, or <a href="/#request">send one request</a> and let agencies come to you.</p>'),
        ('EU citizens: get a registration certificate', 'In person at PMLP if you stay longer than 3 months.', f'<p>If you are an EU, EEA or Swiss citizen staying longer than three months, register in person at a PMLP office with a valid passport or ID card. See <a href="{SRC["pmlp_eu"][1]}" rel="noopener" target="_blank">PMLP’s page for EU citizens</a> for what to bring.</p>'),
        ('Get a personal code', 'Comes with a residence permit, or ask PMLP.', f'<p>Latvia’s personal identity number (personas kods) is how banks, doctors and e-services identify you. Non-EU nationals receive one with a temporary or permanent residence permit; a visa does not give one. Others can ask PMLP to add them to the Register of Natural Persons, which assigns a code. Details: <a href="{SRC["pmlp_code"][1]}" rel="noopener" target="_blank">pmlp.gov.lv</a>.</p>'),
        ('Declare your place of residence', 'Within 1 month. Free online at latvija.gov.lv.', '<p>Declare your address <b>within one month</b> of starting to live there. It is <b>free online</b> at latvija.gov.lv, or €4.27 in person. Internet bank logins no longer work on latvija.gov.lv (since 1 January 2025): sign in with an eID card, eParaksts mobile, a qualified Smart-ID or another EU eID. Most of these are linked to a personal code, so get the code first.</p>'),
        ('Register with a family doctor', 'Your way into state-funded care, if you’re covered.', f'<p>State-funded healthcare covers, among others, Latvian citizens and non-citizens, EU, EEA and Swiss citizens who work or are self-employed in Latvia and their families, permanent residence permit holders, and their children under 18. Temporary residence permit holders are generally not on the list and pay the clinic’s prices, so check whether you need private insurance. If you are covered, register with a family doctor (ģimenes ārsts): their referral unlocks most state-paid care. Changes to these rules were under discussion in 2025–26, so check <a href="{SRC["nvd"][1]}" rel="noopener" target="_blank">the National Health Service</a> for the current list.</p>'),
        ('Sort out getting around', 'Monthly ticket €30; students pay €12.', f'<p>Riga’s monthly public transport ticket costs {eur(TRANSPORT["month"])}, a 90-minute ticket {money(TRANSPORT["ride90"])}, and students studying in Riga pay {eur(TRANSPORT["student"])} a month on a personalised e-ticket.</p>'),
    ]
    checklist = '<ol class="checklist">' + ''.join(f'<li><h3>{escape(t)}</h3>{h}</li>' for t, _, h in steps) + '</ol>'
    sections = [
        ('checklist', 'The checklist, in order', checklist),
        ('first-weeks', 'Your first weeks in Riga', f'''<ul>
<li><b>Budget for the start.</b> Moving in usually costs the first month’s rent, a deposit of about one month (capped at two by law) and, through an agency, a fee of commonly half a month’s rent. The <a href="/#costs">move-in cost calculator</a> adds it up.</li>
<li><b>Expect a lower wage than in Western Europe and lower rents.</b> Average take-home pay was {eur(WAGE['net'])} in Q2 2026, and an average 1-bedroom flat costs {eur(CITY_AVG[1])}.</li>
<li><b>Prepare for winter.</b> Heating is the biggest utility bill from November to March. A renovated, insulated building can halve it.</li>
<li><b>Keep your documents together.</b> Passport, permit or registration certificate, lease and personal code are asked for again and again.</li>
</ul>'''),
    ]
    faq = [
        ('Do EU citizens need a visa or permit to move to Latvia?',
         'No. EU, EEA and Swiss citizens can live and work in Latvia freely, but must register at PMLP if they stay longer than three months.'),
        ('How do I get a residence permit in Latvia?',
         'Most non-EU nationals apply through work (with an employer as sponsor), the EU Blue Card, study or family. You apply at a Latvian embassy or consulate, or at PMLP if you are already legally in Latvia.'),
        ('How long do I have to declare my address in Latvia?',
         'One month from when you start living there. Declaring online at latvija.gov.lv is free; in person it costs €4.27.'),
        ('How do I get a personal code in Latvia?',
         'Non-EU nationals receive one with a residence permit. Others can ask PMLP to add them to the Register of Natural Persons, which assigns a code.'),
    ]
    article('moving-to-latvia',
            'Moving to Latvia in 2026: step-by-step checklist | Riga Flat Match',
            'Moving to Latvia or Riga in 2026: residence permits and EU registration, personal code, declaring your address, healthcare, finding a flat and your first weeks. With official links.',
            'Moving to Latvia: the 2026 checklist', 'Step-by-step guide',
            'Eight steps from permit to tram ticket, in the order you need them, with links to the official pages that have the final word.',
            [('8', 'steps, in order'), ('1 month', 'to declare your address'), ('€0', 'to declare it online'), ('5 years', 'to permanent residence')],
            sections, faq, ['pmlp_work', 'pmlp_rp', 'pmlp_fees', 'pmlp_eu', 'pmlp_code', 'pmlp_decl', 'lvportals', 'nvd', 'rs_fares', 'rs_student', 'csp_wage'],
            [('/how-to-rent-in-riga/', 'How to rent a flat in Riga'), ('/guides/cost-of-living-in-riga/', 'Cost of living in Riga'),
             ('/areas/', 'Riga neighbourhood guides')],
            'Infographic: the eight steps of moving to Latvia, from residence permit to public transport ticket.')
    GUIDES.append(('moving-to-latvia', 'Moving to Latvia: the 2026 checklist',
                   'Permits, personal code, address declaration and healthcare, in order.'))
    return {'steps': [(t, d) for t, d, _ in steps]}


def students():
    flats = [('Studio flat, Teika (average)', BY_ID['teika']['rent'][0]),
             ('Studio flat, Riga average', CITY_AVG[0]),
             ('Room in a shared 3-room flat, Purvciems', BY_ID['purvciems']['rent'][2] / 2)]
    items = sorted([(n, v) for n, v, _ in DORMS] + flats, key=lambda x: x[1])
    flat_names = {n for n, _ in flats}
    chart = hbar('Dorm or flat? Monthly rent per person', items, eur,
                 note='Dorms: lowest listed price for each room type. Flats: average asking rent, utilities extra.',
                 highlight=flat_names, key=('Private flat (utilities extra)', 'University housing'))
    dorm_rows = ''.join(f'<tr><td><a href="{SRC[k][1]}" rel="noopener" target="_blank">{escape(n)}</a></td><td>from {eur(v)}</td></tr>' for n, v, k in DORMS)
    share = STUDENTS['mobile'] / STUDENTS['total'] * 100
    origins = ', '.join(f'{c} ({p}%)' for c, p in STUDENTS['origins'])
    pv3 = BY_ID['purvciems']['rent'][2]
    im3 = BY_ID['imanta']['rent'][2]
    sections = [
        ('numbers', 'International students in Riga', f'''<p>Latvia had <b>{STUDENTS['mobile']:.1f} thousand international students</b> in the 2025/26 academic year, {share:.0f}% of all {STUDENTS['total']:.1f} thousand students in higher education (CSP counts students whose previous education was abroad). The largest groups came from {origins}. Most study in Riga, so student rooms go fast before September and February.</p>'''),
        ('dorms', 'University dorms and their prices', f'''<p>Dorms are the cheapest option and usually include utilities, but places are limited and often go to first-year and exchange students first. Monthly prices per person:</p>
<div class="table-wrap"><table class="price-list"><tbody>{dorm_rows}</tbody></table></div>
<p>The University of Latvia asks for a minimum stay of two months. RSU’s prices are for its own students; guests from other schools pay more. Riga Technical University runs its own housing in Ķīpsala, so check its prices directly.</p>
{chart}'''),
        ('flats', 'Renting a flat as a student', f'''<p>A private studio costs {eur(CITY_AVG[0])} a month on average across Riga, before utilities. Teika, Imanta and Purvciems are the cheapest areas we track, from about {eur(min(a['rent'][0] for a in AREAS))}.</p>
<p>Sharing is often cheaper than living alone. A 3-room flat (a living room and two bedrooms) averages {eur(pv3)} in Purvciems and {eur(im3)} in Imanta, so two students pay about <b>{eur(pv3 / 2)}</b> and <b>{eur(im3 / 2)}</b> each before utilities. Check that the lease names both of you, so each tenant can declare the address.</p>
<ul>
<li><b>Near RTU in Ķīpsala:</b> few flats and higher rents. Āgenskalns, on the same side of the river, is cheaper and has trams into the centre.</li>
<li><b>Lower rents, longer trips:</b> Purvciems and Imanta are the cheapest, with buses, trolleybuses or the suburban train into town. Teika is a good middle ground, with public transport straight down Brīvības gatve.</li>
</ul>
<p>Our <a href="/#match">neighbourhood matcher</a> takes your campus as the commute and your budget, and ranks all eleven areas.</p>'''),
        ('budget', 'A student budget', f'''<ul>
<li><b>Rent:</b> from about {eur(DORMS[0][1])} for a shared dorm room or {eur(DORMS[3][1])} for a single, or {eur(CITY_AVG[0])} for an average private studio plus utilities.</li>
<li><b>Transport:</b> {eur(TRANSPORT['student'])} a month with a student e-ticket, against {eur(TRANSPORT['month'])} at full price.</li>
<li><b>Phone and internet:</b> a mobile plan with 10 GB or more costs about {money(17.46)} a month (Numbeo).</li>
<li><b>Food:</b> see the everyday prices in our <a href="/guides/cost-of-living-in-riga/">cost of living guide</a>.</li>
</ul>
<p>Never pay a deposit for a flat you haven’t seen in person or on a live video call. Fake listings aimed at students arriving from abroad are common before each semester.</p>'''),
    ]
    faq = [
        ('How much is a student dorm in Riga?',
         f'From about {eur(DORMS[0][1])} a month for a bed in a shared room to {eur(DORMS[-1][1])} for a single room in a newer hostel. A single room at the University of Latvia’s Valdemāra 161 dorm starts at €220.'),
        ('How much does a studio flat cost in Riga for students?',
         f'The average asking rent for a studio (1-room flat) in Riga was {eur(CITY_AVG[0])} a month in 2026, before utilities. The cheapest areas start at about {eur(min(a["rent"][0] for a in AREAS))}.'),
        ('Do students get cheaper public transport in Riga?',
         f'Yes. Students studying in Riga pay {eur(TRANSPORT["student"])} a month on a personalised e-ticket, against {eur(TRANSPORT["month"])} at full price.'),
        ('How many international students are there in Latvia?',
         f'{STUDENTS["mobile"]:.1f} thousand in 2025/26, about {share:.0f}% of all higher-education students (CSP).'),
    ]
    article('student-housing-riga',
            'Student housing in Riga 2026: dorm prices vs flats | Riga Flat Match',
            f'Student accommodation in Riga for 2026: dorm prices at LU and RSU from {eur(DORMS[0][1])}, studio flats from {eur(min(a["rent"][0] for a in AREAS))}, sharing costs, student transport and where to live.',
            'Student housing in Riga: dorms vs flats (2026)', 'Data guide',
            f'University dorm prices, what a studio or shared flat costs by area, and a student’s monthly budget, for the {STUDENTS["mobile"]:.1f} thousand international students who study in Latvia.',
            [(f'{STUDENTS["mobile"]:.1f}k', 'international students'), (f'from {eur(DORMS[0][1])}', 'dorm bed per month'),
             (eur(CITY_AVG[0]), 'average studio rent'), (eur(TRANSPORT['student']), 'student transport ticket')],
            sections, faq, ['csp_students', 'lu', 'rsu_dz', 'rsu_ag', 'rents', 'rs_student', 'numbeo'],
            [('/guides/cost-of-living-in-riga/', 'Cost of living in Riga'), ('/areas/', 'Riga neighbourhood guides'),
             ('/how-to-rent-in-riga/', 'How to rent a flat in Riga')],
            f'Infographic: monthly rent per person in Riga, from {eur(DORMS[0][1])} for a dorm bed to {eur(DORMS[-1][1])} for a single room, against {eur(CITY_AVG[0])} for an average studio flat.')
    GUIDES.append(('student-housing-riga', 'Student housing in Riga (2026)',
                   f'Dorm prices from {eur(DORMS[0][1])}, studios and shared flats by area, student transport.'))
    return {'chart': chart}


def index():
    cards = ''.join(f'<a class="area-link" href="/guides/{s}/"><span class="area-link-name">{escape(t)}</span><span class="muted">{escape(d)}</span></a>'
                    for s, t, d in GUIDES)
    cards += ('<a class="area-link" href="/how-to-rent-in-riga/"><span class="area-link-name">How to rent a flat in Riga</span><span class="muted">Six steps, the Latvian words in listings, and the lease rules.</span></a>'
              '<a class="area-link" href="/riga-rent-prices/"><span class="area-link-name">Rent prices in Riga</span><span class="muted">Average rent by neighbourhood and flat size.</span></a>'
              '<a class="area-link" href="/areas/"><span class="area-link-name">Neighbourhood guides</span><span class="muted">Eleven Riga areas: feel, rents and getting around.</span></a>')
    body = f'''    <section class="hero guide-hero">
      <div class="hero-bg" aria-hidden="true"></div>
      <div class="wrap">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <span>Guides</span></nav>
        <p class="eyebrow">Guides and data</p>
        <h1>Living in Riga: guides and data</h1>
        <p class="lead">Costs, salaries, paperwork and housing for people moving to Riga, built on official statistics and our own rent data. Every guide lists its sources.</p>
      </div>
    </section>
    <section>
      <div class="wrap"><div class="guide-cards">{cards}</div></div>
    </section>
'''
    page('guides', 'Living in Riga: guides on costs, salaries and moving (2026) | Riga Flat Match',
         'Guides for moving to Riga in 2026: cost of living, average salary and tax, the moving checklist, student housing, rent prices and neighbourhoods.', body)


def infographics(data):
    """Writes one 1080×1350 HTML page per guide into docs/infographics/ (rendered to PNG by --render)."""
    out = ROOT / 'docs/infographics'
    out.mkdir(parents=True, exist_ok=True)
    blocks = {
        'cost-of-living-in-riga': ('What a month in Riga costs in 2026',
            stats([(eur(data['cost']['single']), 'one person, studio flat'), (eur(data['cost']['family']), 'family of four, 2-bedroom flat')])
            + data['cost']['month'] + data['cost']['households'], 'Rent: viszinis.lv, Mar–Oct 2026. Living costs: Numbeo, Oct 2026.'),
        'average-salary-latvia': ('How much of a Latvian salary goes on rent',
            data['salary']['share'], f'Average 1-bedroom rent by area (viszinis.lv, Mar–Oct 2026) ÷ average net wage {eur(WAGE["net"])} (CSP, Q2 2026).'),
        'moving-to-latvia': ('Moving to Latvia: the checklist',
            '<ol class="checklist">' + ''.join(f'<li><h3>{escape(t)}</h3><p>{escape(d)}</p></li>' for t, d in data['moving']['steps']) + '</ol>',
            'Official rules: pmlp.gov.lv, vmnvd.gov.lv. Check the latest before you apply.'),
        'student-housing-riga': ('Student housing in Riga: dorm or flat?',
            data['students']['chart'], 'Dorms: LU and RSU price lists, 2026. Flats: viszinis.lv average asking rent, Mar–Oct 2026.'),
    }
    for slug, (h, inner, src) in blocks.items():
        (out / f'{slug}.html').write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<link rel="stylesheet" href="../../styles.css"><link rel="stylesheet" href="infographic.css"></head>
<body class="ig"><main>
<header><img src="../../assets/brand/mark.svg" width="56" height="56" alt=""><span>Riga Flat <b>Match</b></span></header>
<h1>{escape(h)}</h1>
<div class="ig-body">{inner}</div>
<footer><p>{escape(src)}</p><p class="ig-url">rentinrigalatvia.lv/guides/{slug}/</p></footer>
</main></body></html>
''', encoding='utf-8')


def render():
    chrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    dest = ROOT / 'assets/img/infographics'
    dest.mkdir(parents=True, exist_ok=True)
    for f in sorted((ROOT / 'docs/infographics').glob('*.html')):
        png = dest / f'{f.stem}.png'
        subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                        '--window-size=1080,1350', '--virtual-time-budget=3000', f'--screenshot={png}', f.as_uri()],
                       check=True, capture_output=True)
        print('rendered', png.relative_to(ROOT))


def build():
    GUIDES.clear()
    data = {'cost': cost_of_living(), 'salary': salary(), 'moving': moving(), 'students': students()}
    index()
    infographics(data)
    return [f'guides/{s}/' for s, _, _ in GUIDES]


if __name__ == '__main__':
    # The take-home formula has to land on CSP's own average net wage (within 1%), or a rule is wrong.
    assert abs(net(WAGE['gross']) / WAGE['net'] - 1) < .01, net(WAGE['gross'])
    assert net(500) == 500 - 500 * TAX['si'] and net(2000, 9) == 2000 * (1 - TAX['si'])
    if '--render' in sys.argv:
        render()
    else:
        print('guides ok; run tools/build.py to write the pages, then --render for the PNGs')
