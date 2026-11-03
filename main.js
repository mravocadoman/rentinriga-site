(() => {
  'use strict';

  const LEAD_URL = 'https://marketingaskola.app.n8n.cloud/webhook/rentinriga-lead?k=rr-lv-2026';
  const loadedAt = Date.now();
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const eur = (n) => '€' + Math.round(n).toLocaleString('en-US');
  const store = {
    get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} },
    del(k) { try { localStorage.removeItem(k); } catch {} },
  };

  /* ---------- Header, menu, year, reveal ---------- */
  const header = $('.site-header');
  const onScroll = () => header.classList.toggle('scrolled', scrollY > 8);
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  const toggle = $('.menu-toggle');
  const links = $('#nav-links');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const open = links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open);
    });
    links.addEventListener('click', (e) => {
      if (e.target.closest('a')) { links.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); }
    });
  }
  $$('[data-year]').forEach((el) => { el.textContent = new Date().getFullYear(); });
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => entries.forEach((en) => {
      if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
    }), { rootMargin: '0px 0px -8% 0px' });
    $$('.reveal').forEach((el) => io.observe(el));
  } else {
    $$('.reveal').forEach((el) => el.classList.add('in'));
  }
  if ('IntersectionObserver' in window && $('.wa-float')) {
    const forms = new Set();
    const fo = new IntersectionObserver((entries) => {
      entries.forEach((en) => (en.isIntersecting ? forms.add(en.target) : forms.delete(en.target)));
      document.body.classList.toggle('form-in-view', forms.size > 0);
    });
    $$('#wizard, #quick, #calc').forEach((el) => fo.observe(el));
  }

  /* ---------- Where the visitor came from (first touch, kept for the visit) ---------- */
  const leadSource = (() => {
    const q = new URLSearchParams(location.search);
    const utm = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term'].map((k) => q.get(k)).filter(Boolean).join('/');
    let s = utm ? 'utm:' + utm : '';
    if (q.get('gclid')) s += (s ? ' ' : '') + 'gclid';
    if (q.get('fbclid')) s += (s ? ' ' : '') + 'fbclid';
    if (!s && document.referrer) { try { const h = new URL(document.referrer).host; if (h !== location.host) s = 'ref:' + h; } catch {} }
    try {
      if (s && !sessionStorage.getItem('rr-src')) sessionStorage.setItem('rr-src', (s + ' | landed ' + location.pathname).slice(0, 200));
      return sessionStorage.getItem('rr-src') || 'direct';
    } catch { return s || 'direct'; }
  })();

  /* ---------- Shared POST to n8n ---------- */
  async function sendLead(payload) {
    // text/plain keeps this a "simple" request: no CORS preflight.
    const res = await fetch(LEAD_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: JSON.stringify({ ...payload, source: leadSource, page: location.href.split('#')[0], t: Date.now() - loadedAt }),
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    (window.dataLayer = window.dataLayer || []).push({ event: 'generate_lead', lead_kind: payload.kind });
  }

  /* ---------- Partner application (/partners/) ---------- */
  const partner = $('#partner-form');
  if (partner) {
    const status = $('#partner-status');
    partner.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!partner.reportValidity()) return;
      const d = new FormData(partner);
      const btn = $('[type="submit"]', partner);
      btn.disabled = true;
      status.dataset.tone = '';
      status.textContent = 'Sending…';
      try {
        await sendLead({
          kind: 'partner', name: d.get('name'), email: d.get('email'), phone: d.get('phone'), company: d.get('company'),
          site: d.get('site'), units: d.get('units'), areas: d.getAll('areas'), message: d.get('message'),
          website: d.get('website'), consent: d.get('consent') === 'on',
        });
        partner.reset();
        status.dataset.tone = 'ok';
        status.textContent = 'Thanks! We’ve got your application and will be in touch within two working days.';
      } catch {
        status.dataset.tone = 'error';
        status.textContent = 'That didn’t go through. Please try again, or e-mail rihards.zeila@gmail.com.';
      } finally {
        btn.disabled = false;
      }
    });
  }

  const wizard = $('#wizard');
  if (!wizard) return; // the rest is the homepage only

  /* ---------- Area data ----------
     rent = average asking rent, EUR/month excl. utilities, by Latvian room count [1, 2, 3, 4+],
     viszinis.lv per-neighbourhood averages, 1 Mar – 31 Oct 2026 (checked 3 Nov 2026). */
  const AREAS = [
    { id: 'centre', name: 'Centre', lv: 'Centrs', at: [56.9575, 24.1185], rent: [440, 670, 975, 1170],
      tagline: 'Art Nouveau streets, cafés and offices within walking distance.',
      feel: 'Grand early-1900s buildings, busy by day, lively evenings. The “quiet centre” around Alberta iela is calmer.',
      move: 'Walk or cycle almost everywhere; most public transport lines pass through.',
      good: 'A car-free life and short commutes.' },
    { id: 'old-town', name: 'Old Town', lv: 'Vecrīga', at: [56.9490, 24.1065], rent: [490, 630, 935, 1435],
      tagline: 'Medieval lanes at the heart of Riga’s UNESCO-listed historic centre.',
      feel: 'Beautiful and central, but touristy and loud on weekend nights. Lifts and parking are rare.',
      move: 'On foot. Cars are restricted in much of it.',
      good: 'Short stays and people who want the postcard.' },
    { id: 'kipsala', name: 'Ķīpsala', lv: 'Ķīpsala', at: [56.9555, 24.0805], rent: [470, 870, 1175, null],
      tagline: 'A quiet island across the river from the Old Town.',
      feel: 'Riverside apartment buildings, restored wooden houses and a university campus. Calm, with skyline views.',
      move: 'Across the Vanšu bridge to the centre; buses and cycling.',
      good: 'People who want calm close to town.' },
    { id: 'skanste', name: 'Skanste', lv: 'Skanste', at: [56.9690, 24.1240], rent: [460, 770, 1205, 1705],
      tagline: 'Riga’s new business district, next to the centre.',
      feel: 'Glass offices, new-build towers and the Arena Riga. Modern flats, often with parking.',
      move: 'Walk to the centre; buses and trolleybuses along Skanstes iela.',
      good: 'Working in the Skanste offices; anyone who wants a new building.' },
    { id: 'teika', name: 'Teika', lv: 'Teika', at: [56.9745, 24.1720], rent: [300, 505, 820, 980],
      tagline: 'Green, residential and practical.',
      feel: 'Pre-war and Soviet-era blocks among parks, with shops on Brīvības gatve. Several large office complexes nearby.',
      move: 'Public transport along Brīvības gatve runs straight to the centre.',
      good: 'Offices in the Teika / VEF area; good value with an easy commute.' },
    { id: 'agenskalns', name: 'Āgenskalns', lv: 'Āgenskalns', at: [56.9435, 24.0705], rent: [330, 535, 765, 1035],
      tagline: 'Wooden houses and a market hall across the river.',
      feel: 'One of Riga’s most charming neighbourhoods: historic wooden architecture, the Āgenskalns market and local cafés.',
      move: 'Trams over the Stone Bridge to the Old Town and centre.',
      good: 'Character on a reasonable budget.' },
    { id: 'tornakalns', name: 'Torņakalns', lv: 'Torņakalns', at: [56.9345, 24.0920], rent: [335, 525, 795, 1215],
      tagline: 'Left-bank area next to Victory Park.',
      feel: 'A mix of new developments and older streets near the University of Latvia’s science campus.',
      move: 'Trams, buses and Torņakalns train station.',
      good: 'New flats with green space and fair prices.' },
    { id: 'avoti', name: 'Avoti & Grīziņkalns', lv: 'Avoti, Grīziņkalns', at: [56.9530, 24.1460], rent: [330, 505, 715, 835],
      tagline: 'Just east of the centre, cheaper and a bit rough around the edges.',
      feel: 'Older brick and wooden buildings, Grīziņkalns park and a growing café scene. Building quality varies a lot.',
      move: 'Within walking distance of the centre.',
      good: 'Being close to the centre for less money.' },
    { id: 'mezaparks', name: 'Mežaparks', lv: 'Mežaparks', at: [57.0005, 24.1475], rent: [390, 710, 955, 1275],
      tagline: 'A garden district of villas in a pine forest.',
      feel: 'Quiet and leafy, by Lake Ķīšezers and the Song Festival grounds. Mostly houses and small apartment buildings.',
      move: 'Tram to the centre; a car helps.',
      good: 'Families, dog owners and lovers of nature.' },
    { id: 'purvciems', name: 'Purvciems', lv: 'Purvciems', at: [56.9590, 24.1960], rent: [310, 420, 530, 620],
      tagline: 'A large housing estate with Riga’s lowest rents.',
      feel: 'Soviet-era apartment blocks, some renovated, with big supermarkets and shopping centres.',
      move: 'Buses and trolleybuses to the centre; allow more time than from the inner areas.',
      good: 'Tight budgets and bigger flats for the money.' },
    { id: 'imanta', name: 'Imanta', lv: 'Imanta', at: [56.9530, 23.9960], rent: [305, 425, 490, 830],
      tagline: 'A quiet western housing estate with a train link.',
      feel: 'Residential and green, near forest and the road to Jūrmala.',
      move: 'Suburban train and public transport to the centre.',
      good: 'Low rents and easy trips to the seaside.' },
  ];
  // City-wide asking rent (vericity.ai median of ~2,175 listings, 2 Nov 2026) for when no area is picked.
  // ponytail: no reliable city-wide typical 4+ room figure, so the hint stays quiet for that size.
  const CITY = [340, 590, 850, null];
  const ROOM_INDEX = { 1: 0, 2: 1, 3: 2, '4+': 3 };
  const ROOM_LABEL = ['1-room (studio)', '2-room (1 bed)', '3-room (2 beds)', '4+ room (3+ beds)'];

  /* ---------- Wizard: area chips (filled first so the explorer can toggle them) ---------- */
  const chipBox = $('#area-chips');
  chipBox.innerHTML = AREAS.map((a) => `<label class="chip"><input type="checkbox" name="areas" value="${a.name}">${a.name}</label>`).join('');
  const areaInput = (a) => $(`input[name="areas"][value="${a.name}"]`, chipBox);

  /* ---------- Neighbourhood explorer ---------- */
  const tabs = $('#area-tabs');
  const card = $('#area-card');
  const markers = {};
  let current = AREAS[0];
  tabs.innerHTML = AREAS.map((a) => `<button type="button" class="chip" data-area="${a.id}" aria-pressed="false">${a.name}</button>`).join('');

  function renderCard(a) {
    const picked = areaInput(a).checked;
    card.innerHTML = `
      <h3>${a.name}</h3>
      ${a.lv !== a.name ? `<p class="small muted" lang="lv">${a.lv}</p>` : ''}
      <p class="tagline">${a.tagline}</p>
      <table class="rent-table"><caption class="visually-hidden">Average asking rent in ${a.name}</caption>
        <tbody>${a.rent.map((r, i) => `<tr><th scope="row">${ROOM_LABEL[i]}</th><td>${r ? eur(r) : 'too few listings'}</td></tr>`).join('')}</tbody>
      </table>
      <ul class="facts">
        <li><b>What it’s like:</b> ${a.feel}</li>
        <li><b>Getting around:</b> ${a.move}</li>
        <li><b>Good for:</b> ${a.good}</li>
      </ul>
      <button type="button" class="btn ${picked ? 'btn-ghost' : 'btn-primary'}" data-pick="${a.id}">${picked ? '✓ In my request (remove)' : 'Add to my request'}</button>
      <p class="source-note">Average monthly asking rent, excl. utilities, from listings between March and October 2026 (viszinis.lv). Signed rents can be lower. A 1-room flat in newer areas such as Skanste is often larger.</p>`;
  }

  function selectArea(id, { pan = true } = {}) {
    current = AREAS.find((a) => a.id === id) || AREAS[0];
    $$('button', tabs).forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.area === current.id)));
    // Labels overlap in the centre, so only the selected area keeps its label open; the rest show on hover.
    Object.entries(markers).forEach(([k, m]) => {
      const on = k === current.id;
      m.getElement()?.querySelector('.pin')?.classList.toggle('active', on);
      m.setZIndexOffset(on ? 1000 : 0);
      if (on) m.openTooltip(); else m.closeTooltip();
    });
    if (pan && map) map.panTo(current.at, { animate: true });
    renderCard(current);
  }

  tabs.addEventListener('click', (e) => { const b = e.target.closest('[data-area]'); if (b) selectArea(b.dataset.area); });
  card.addEventListener('click', (e) => {
    const b = e.target.closest('[data-pick]');
    if (!b) return;
    const inp = areaInput(current);
    inp.checked = !inp.checked;
    inp.dispatchEvent(new Event('change', { bubbles: true }));
    renderCard(current);
  });

  let map = null;
  function initMap() {
    const el = $('#map');
    if (!window.L) { el.hidden = true; return; } // CDN blocked: the cards still work on their own
    // No one-finger dragging on phones, so the map never traps page scrolling.
    map = L.map(el, { scrollWheelZoom: false, dragging: !L.Browser.mobile, zoomControl: true }).setView([56.958, 24.11], 12);
    // ponytail: OSM's public tiles are fine for a low-traffic site; switch to a paid tile host if traffic grows.
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18,
    }).addTo(map);
    AREAS.forEach((a) => {
      const m = L.marker(a.at, { icon: L.divIcon({ className: '', html: '<div class="pin"></div>', iconSize: [18, 18], iconAnchor: [9, 9] }), title: a.name, keyboard: false })
        .addTo(map)
        .bindTooltip(a.name, { direction: 'right', offset: [10, 0], className: 'pin-label' })
        .on('click', () => selectArea(a.id, { pan: false }));
      markers[a.id] = m;
    });
    map.fitBounds(AREAS.map((a) => a.at), { padding: [16, 16] });
    selectArea(current.id, { pan: false });
  }
  selectArea(current.id, { pan: false });
  // Leaflet is a deferred script before this one, so it has run by now if it loaded at all.
  initMap();

  /* ---------- Move-in cost calculator ---------- */
  // Heating in the coldest months, scaled by floor area from Rīgas siltums' published example
  // for a 45 m² flat (insulated ≈ €46–57, not insulated ≈ €116–142 a month in Dec–Jan, excl. VAT).
  const HEAT = { small: [45, 145], mid: [70, 220], large: [100, 315] };
  const calc = $('#calc');
  const calcRent = $('#calc-rent');
  function updateCalc() {
    const d = new FormData(calc);
    const rent = Number(calcRent.value);
    const dep = rent * Number(d.get('deposit'));
    const fee = rent * Number(d.get('fee'));
    const [h1, h2] = HEAT[d.get('size')];
    $('#calc-rent-out').textContent = eur(rent);
    $('#calc-first').textContent = eur(rent);
    $('#calc-dep').textContent = eur(dep);
    $('#calc-fee').textContent = eur(fee);
    $('#calc-total').textContent = eur(rent + dep + fee);
    $('#calc-rent2').textContent = eur(rent);
    $('#calc-heat').textContent = `${eur(h1)}–${eur(h2)}`;
  }
  calc.addEventListener('input', updateCalc);
  updateCalc();
  $('#calc-cta').addEventListener('click', () => {
    setBudget(Number(calcRent.value));
    const size = new FormData(calc).get('size');
    wizard.elements.rooms.value = { small: '2', mid: '3', large: '4+' }[size];
    saveDraft();
  });

  /* ---------- Wizard ---------- */
  const steps = $$('.step', wizard);
  const labels = ['Your stay', 'Your flat', 'Your contact details'];
  const status = $('#form-status');
  const back = $('#back');
  const next = $('#next');
  const submit = $('#submit');
  const budget = wizard.elements.budget;
  const budgetOut = $('#budget-out');
  const moveIn = wizard.elements.move_in;
  let step = 1;

  const iso = (d) => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
  const today = new Date();
  const maxDate = new Date(today.getFullYear() + 1, today.getMonth() + 6, today.getDate());
  moveIn.min = iso(today);
  moveIn.max = iso(maxDate);

  const say = (text, tone = '') => { status.textContent = text; status.dataset.tone = tone; };

  function showStep(n, focus = true) {
    step = n;
    steps.forEach((s) => { s.hidden = Number(s.dataset.step) !== n; });
    $$('.progress span', wizard).forEach((s, i) => s.classList.toggle('done', i < n));
    $('#step-label').textContent = `Step ${n} of 3: ${labels[n - 1]}`;
    back.hidden = n === 1;
    next.hidden = n === 3;
    submit.hidden = n !== 3;
    say('');
    if (focus) steps[n - 1].querySelector('input, select, textarea')?.focus({ preventScroll: true });
  }

  function validStep(n) {
    const fields = $$('input, select, textarea', steps[n - 1]).filter((f) => f.name !== 'website');
    for (const f of fields) {
      f.removeAttribute('aria-invalid');
      if (!f.checkValidity()) {
        f.setAttribute('aria-invalid', 'true');
        f.reportValidity();
        return false;
      }
    }
    return true;
  }

  next.addEventListener('click', () => { if (validStep(step)) { showStep(step + 1); wizard.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); } });
  back.addEventListener('click', () => showStep(step - 1));
  // Enter in a text field moves forward instead of submitting a half-filled form.
  wizard.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && step < 3 && e.target.tagName === 'INPUT') { e.preventDefault(); next.click(); }
  });

  function setBudget(v) {
    budget.value = Math.min(Number(budget.max), Math.max(Number(budget.min), v));
    updateBudget();
  }

  function updateBudget() {
    const b = Number(budget.value);
    budgetOut.textContent = b >= Number(budget.max) ? eur(b) + '+' : eur(b);
    const i = ROOM_INDEX[wizard.elements.rooms.value];
    const picked = AREAS.filter((a) => areaInput(a).checked);
    const hint = $('#budget-hint');
    const prices = (picked.length ? picked.map((a) => a.rent[i]) : [CITY[i]]).filter(Boolean);
    if (!prices.length) { hint.textContent = ''; return; }
    const lo = Math.min(...prices);
    const where = picked.length ? (picked.length === 1 ? 'in ' + picked[0].name : 'in the areas you picked') : 'across Riga';
    const typical = lo === Math.max(...prices) ? eur(lo) : `${eur(lo)}–${eur(Math.max(...prices))}`;
    if (b < lo * 0.85) {
      const cheaper = AREAS.filter((a) => a.rent[i] && a.rent[i] <= b).map((a) => a.name).slice(0, 3);
      hint.dataset.tone = 'warn';
      hint.textContent = `Heads-up: the average asking rent for a ${ROOM_LABEL[i]} flat ${where} is ${typical}. You’ll get fewer offers at ${eur(b)}.` +
        (cheaper.length ? ` Areas closer to your budget: ${cheaper.join(', ')}.` : ' Try fewer rooms or a higher budget.');
    } else if (b < lo) {
      hint.dataset.tone = '';
      hint.textContent = `Average asking rent for a ${ROOM_LABEL[i]} flat ${where}: ${typical}. Your budget is a little below that but realistic.`;
    } else {
      hint.dataset.tone = '';
      hint.textContent = `Average asking rent for a ${ROOM_LABEL[i]} flat ${where}: ${typical}. Your budget covers it.`;
    }
  }
  wizard.addEventListener('input', (e) => { if (['budget', 'rooms', 'areas'].includes(e.target.name)) updateBudget(); });
  wizard.addEventListener('change', (e) => {
    if (['rooms', 'areas'].includes(e.target.name)) updateBudget();
    if (e.target.name === 'areas') renderCard(current);
    if (e.target.name === 'stay') stayHint();
  });

  function stayHint() {
    $('#stay-hint').textContent = wizard.elements.stay.value === '1-3'
      ? 'Most landlords prefer longer leases, so there are fewer options for 1–3 months. We’ll pass it to agencies that handle short lets.'
      : '';
  }

  /* ---------- Draft: a reload or a closed tab loses nothing ---------- */
  const DRAFT = 'rr-draft';
  const SKIP = ['consent', 'website'];
  function saveDraft() {
    const d = {};
    for (const el of wizard.elements) {
      if (!el.name || SKIP.includes(el.name)) continue;
      if (el.type === 'checkbox') { if (el.checked) (d[el.name] = d[el.name] || []).push(el.value); } else d[el.name] = el.value;
    }
    store.set(DRAFT, d);
  }
  function loadDraft() {
    const d = store.get(DRAFT);
    if (!d) return;
    for (const el of wizard.elements) {
      if (!el.name || SKIP.includes(el.name) || !(el.name in d)) {
        if (el.type === 'checkbox' && el.name && !SKIP.includes(el.name)) el.checked = false;
        continue;
      }
      if (el.type === 'checkbox') el.checked = [].concat(d[el.name]).includes(el.value);
      else el.value = d[el.name];
    }
    if (moveIn.value && (moveIn.value < moveIn.min || moveIn.value > moveIn.max)) moveIn.value = '';
  }
  wizard.addEventListener('input', saveDraft);
  wizard.addEventListener('change', saveDraft);
  loadDraft();
  updateBudget();
  stayHint();

  /* ---------- Hero quick start → wizard ---------- */
  const quick = $('#quick');
  const monthSel = $('#quick-month');
  const opts = ['<option value="asap">ASAP</option>'];
  for (let i = 1; i <= 6; i++) {
    const d = new Date(today.getFullYear(), today.getMonth() + i, 1);
    opts.push(`<option value="${iso(d)}">${d.toLocaleString('en-GB', { month: 'long', year: 'numeric' })}</option>`);
  }
  monthSel.innerHTML = opts.join('');
  quick.addEventListener('submit', (e) => {
    e.preventDefault();
    const d = new FormData(quick);
    const m = d.get('month');
    moveIn.value = m === 'asap' ? iso(new Date(today.getTime() + 14 * 864e5)) : m;
    wizard.elements.stay.value = d.get('stay');
    setBudget(Number(d.get('budget')));
    stayHint();
    saveDraft();
    showStep(1, false);
    $('#request').scrollIntoView({ behavior: 'smooth' });
    setTimeout(() => wizard.elements.adults.focus({ preventScroll: true }), 600);
  });

  /* ---------- Submit ---------- */
  wizard.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (step !== 3) { next.click(); return; }
    for (let n = 1; n <= 3; n++) if (!validStep(n)) { showStep(n); validStep(n); return; }
    const d = new FormData(wizard);
    submit.disabled = true;
    say('Sending your request…');
    try {
      await sendLead({
        kind: 'tenant',
        name: d.get('name'), email: d.get('email'), phone: d.get('phone'), channel: d.get('channel'),
        move_in: d.get('move_in'), stay: d.get('stay'), adults: d.get('adults'), children: d.get('children'), pets: d.get('pets'),
        budget: Number(d.get('budget')), rooms: d.get('rooms'), furnished: d.get('furnished'),
        areas: d.getAll('areas'), wants: d.getAll('wants'),
        relocation: d.get('relocation') ? 'employer' : 'self', company: d.get('company'), message: d.get('message'),
        website: d.get('website'), consent: d.get('consent') === 'on',
      });
      store.del(DRAFT);
      steps.forEach((s) => { s.hidden = true; });
      $('#wizard-nav').hidden = true;
      $('.progress', wizard).hidden = true;
      $('#step-label').hidden = true;
      say('');
      const done = $('#done');
      done.hidden = false;
      done.focus();
    } catch {
      say('Sorry, that didn’t go through. Your answers are saved, so please try again in a moment, or e-mail rihards.zeila@gmail.com.', 'error');
    } finally {
      submit.disabled = false;
    }
  });

  /* ---------- FAQ structured data, built from the visible answers ---------- */
  $('#faq-schema').textContent = JSON.stringify({
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: $$('#faq-list details').map((q) => ({
      '@type': 'Question',
      name: $('summary', q).textContent.trim(),
      acceptedAnswer: { '@type': 'Answer', text: $('p', q).textContent.trim() },
    })),
  });
})();
