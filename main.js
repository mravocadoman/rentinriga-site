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
    $$('#wizard, #quick, #calc, #matcher').forEach((el) => fo.observe(el));
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
      body: JSON.stringify({ ...payload, lang: document.documentElement.lang, source: leadSource, page: location.href.split('#')[0], t: Date.now() - loadedAt }),
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

  /* ---------- Guides: embed-code copy, take-home pay calculator ---------- */
  document.querySelectorAll('[data-copy]').forEach((b) => b.addEventListener('click', async () => {
    const box = b.parentElement.querySelector('textarea');
    try { await navigator.clipboard.writeText(box.value); } catch { box.select(); document.execCommand('copy'); }
    b.textContent = 'Copied';
  }));
  const netcalc = $('#netcalc');
  if (netcalc) {
    // 2026 rules, same as net() in tools/guides.py: 10.5% social tax, €550 tax-free + €250 per dependant, 25.5% income tax.
    const eur = (n) => '€' + Math.round(n).toLocaleString('en-GB');
    const run = () => {
      const g = Math.max(+netcalc.gross.value || 0, 0), dep = +netcalc.dep.value;
      const si = g * 0.105, pit = Math.max(g - si - 550 - 250 * dep, 0) * 0.255;
      const out = { net: g - si - pit, si, pit, employer: g * 1.2359 };
      for (const k in out) $(`[data-out="${k}"]`, netcalc).textContent = eur(out[k]);
    };
    netcalc.addEventListener('input', run);
    run();
  }

  const wizard = $('#wizard');
  if (!wizard) return; // the rest is the homepage only

  /* ---------- Area data ----------
     One source: data/areas.json, built into assets/areas.js by tools/build.py (see README). */
  const { areas: AREAS, city_avg: CITY_AVG } = window.RR_DATA;
  // ponytail: no reliable city-wide typical 4+ room figure, so the budget hint stays quiet for that size.
  const MAX_RENT = [0, 1, 2, 3].map((i) => Math.max(...AREAS.map((a) => a.rent[i] || 0)));
  const ROOM_INDEX = { 1: 0, 2: 1, 3: 2, '4+': 3 };
  // Everything this script writes is in T, one table per page language (<html lang>). Form values stay English.
  const RU = document.documentElement.lang === 'ru';
  const T = RU ? {
    rooms: ['1-комнатная (студия)', '2-комнатная (1 спальня)', '3-комнатная (2 спальни)', '4+ комнаты (3+ спальни)'],
    tooFew: 'мало объявлений', vsAvg: 'по сравнению со средним по Риге',
    like: 'Атмосфера:', move: 'Транспорт:', good: 'Подходит для:',
    pick: 'Добавить в заявку', picked: '✓ В заявке (убрать)', guide: (n) => `Гид по району ${n} (англ.) →`,
    source: 'Средняя запрашиваемая аренда в месяц, без коммунальных, по объявлениям за март–октябрь 2026 (viszinis.lv). Процент — сравнение со средним по Риге по тем же данным, полоски — относительно самого дорогого района. Реальная цена договора может быть ниже, а 1-комнатная квартира в новых районах вроде Скансте часто больше.',
    steps: ['проживание', 'квартира', 'контакты'], step: (n, l) => `Шаг ${n} из 3: ${l}`,
    in1: (n) => `в районе ${n}`, inMany: 'в выбранных районах', city: 'по Риге',
    warn: (r, w, t, b) => `Обратите внимание: ${r} ${w} стоит в среднем ${t}. При бюджете ${b} предложений будет меньше.`,
    closer: (l) => ` Районы ближе к вашему бюджету: ${l}.`, fewer: ' Попробуйте меньше комнат или больший бюджет.',
    below: (r, w, t) => `${r} ${w}: в среднем ${t}. Ваш бюджет чуть ниже, но это реально.`,
    covers: (r, w, t) => `${r} ${w}: в среднем ${t}. Ваш бюджет это покрывает.`,
    short: 'Большинство арендодателей предпочитают длинные договоры, поэтому вариантов на 1–3 месяца меньше. Мы передадим заявку агентствам, которые работают с краткосрочной арендой.',
    asap: 'Как можно скорее', locale: 'ru-RU',
    sending: 'Отправляем заявку…',
    failed: 'Не получилось отправить. Ваши ответы сохранены, попробуйте ещё раз через минуту или напишите на rihards.zeila@gmail.com.',
    work: { centre: 'центра', skanste: 'Скансте', teika: 'Тейки / ВЭФ', left: 'левого берега' },
    vibe: { walk: 'всё рядом пешком', quiet: 'тихие улицы', green: 'много зелени', new: 'новые дома', character: 'историческая застройка', cafes: 'кафе и ночная жизнь', value: 'аренда ниже средней' },
    priced: (e, r, f) => `${r}: в среднем ${e}${f === 1 ? ', в пределах бюджета' : f === 0.5 ? ', чуть выше бюджета' : ', выше бюджета'}`,
    unpriced: (r) => `${r}: слишком мало объявлений, чтобы оценить цену`,
    dist: (d, w) => `${d < 1 ? 'Меньше 1' : 'Около ' + d.toFixed(1).replace('.', ',')} км от ${w} (по прямой)`,
    matches: (l) => `Совпадает: ${l}`, best: 'Лучший вариант', onMap: 'Показать на карте',
    use: 'Добавить эти районы в заявку',
    weights: 'Оценка учитывает бюджет (45%), расстояние до работы (30%) и ваши приоритеты (25%). Цены — средняя запрашиваемая аренда, март–октябрь 2026.',
    added: (l) => `Добавили в заявку: ${l}. Теперь выберите дату заезда.`,
  } : {
    rooms: ['1-room (studio)', '2-room (1 bed)', '3-room (2 beds)', '4+ room (3+ beds)'],
    tooFew: 'too few listings', vsAvg: 'vs Riga average',
    like: 'What it’s like:', move: 'Getting around:', good: 'Good for:',
    pick: 'Add to my request', picked: '✓ In my request (remove)', guide: (n) => `Full ${n} guide →`,
    source: 'Average monthly asking rent, excl. utilities, from listings between March and October 2026 (viszinis.lv). The % compares with the Riga-wide average from the same data, and bars are scaled to the priciest area. Signed rents can be lower, and a 1-room flat in newer areas such as Skanste is often larger.',
    steps: ['Your stay', 'Your flat', 'Your contact details'], step: (n, l) => `Step ${n} of 3: ${l}`,
    in1: (n) => `in ${n}`, inMany: 'in the areas you picked', city: 'across Riga',
    warn: (r, w, t, b) => `Heads-up: the average asking rent for a ${r} flat ${w} is ${t}. You’ll get fewer offers at ${b}.`,
    closer: (l) => ` Areas closer to your budget: ${l}.`, fewer: ' Try fewer rooms or a higher budget.',
    below: (r, w, t) => `Average asking rent for a ${r} flat ${w}: ${t}. Your budget is a little below that but realistic.`,
    covers: (r, w, t) => `Average asking rent for a ${r} flat ${w}: ${t}. Your budget covers it.`,
    short: 'Most landlords prefer longer leases, so there are fewer options for 1–3 months. We’ll pass it to agencies that handle short lets.',
    asap: 'ASAP', locale: 'en-GB',
    sending: 'Sending your request…',
    failed: 'Sorry, that didn’t go through. Your answers are saved, so please try again in a moment, or e-mail rihards.zeila@gmail.com.',
    work: { centre: 'the centre', skanste: 'Skanste', teika: 'Teika / VEF', left: 'the left bank' },
    vibe: { walk: 'walkable', quiet: 'quiet', green: 'green', new: 'modern buildings', character: 'historic character', cafes: 'cafés & nightlife', value: 'below-average rent' },
    priced: (e, r, f) => `Average ${e} for a ${r} flat${f === 1 ? ', within your budget' : f === 0.5 ? ', a little over your budget' : ', over your budget'}`,
    unpriced: (r) => `Too few ${r} listings to price`,
    dist: (d, w) => `${d < 1 ? 'Under 1' : 'About ' + d.toFixed(1)} km from ${w} (straight line)`,
    matches: (l) => `Matches: ${l}`, best: 'Best fit', onMap: 'Show on map',
    use: 'Use these areas in my request',
    weights: 'Scores weigh budget fit (45%), distance to work (30%) and your priorities (25%). Rents are average asking prices, Mar–Oct 2026.',
    added: (l) => `Added ${l} to your request. Now pick your move-in date.`,
  };
  const ROOM_LABEL = T.rooms;
  // Area text in the page language; names stay English in form values so lead e-mails are consistent.
  const nm = (a) => (RU ? a.ru.name : a.name);
  const tx = (a, k) => (RU ? a.ru[k] : a[k]);

  /* ---------- Wizard: area chips (filled first so the explorer can toggle them) ---------- */
  const chipBox = $('#area-chips');
  chipBox.innerHTML = AREAS.map((a) => `<label class="chip"><input type="checkbox" name="areas" value="${a.name}">${nm(a)}</label>`).join('');
  const areaInput = (a) => $(`input[name="areas"][value="${a.name}"]`, chipBox);

  /* ---------- Neighbourhood explorer ---------- */
  const tabs = $('#area-tabs');
  const card = $('#area-card');
  const markers = {};
  let current = AREAS[0];
  tabs.innerHTML = AREAS.map((a) => `<button type="button" class="chip" data-area="${a.id}" aria-pressed="false">${nm(a)}</button>`).join('');

  function renderCard(a) {
    const picked = areaInput(a).checked;
    card.innerHTML = `
      <h3>${nm(a)}</h3>
      ${a.lv !== nm(a) ? `<p class="small muted" lang="lv">${a.lv}</p>` : ''}
      <p class="tagline">${tx(a, 'tagline')}</p>
      <ul class="rent-bars" aria-label="${nm(a)}">${a.rent.map((r, i) => {
        if (!r) return `<li><div class="row"><span>${ROOM_LABEL[i]}</span><span class="muted">${T.tooFew}</span></div></li>`;
        const d = CITY_AVG[i] ? Math.round((r / CITY_AVG[i] - 1) * 100) : null;
        const vs = d === null || d === 0 ? '' : `<span class="vs ${d > 0 ? 'up' : 'down'}" title="${T.vsAvg}">${d > 0 ? '+' : '−'}${Math.abs(d)}%</span>`;
        return `<li><div class="row"><span>${ROOM_LABEL[i]}</span><span><b>${eur(r)}</b>${vs}</span></div><div class="bar"><i style="width:${Math.round((r / MAX_RENT[i]) * 100)}%"></i></div></li>`;
      }).join('')}</ul>
      <ul class="facts">
        <li><b>${T.like}</b> ${tx(a, 'feel')}</li>
        <li><b>${T.move}</b> ${tx(a, 'move')}</li>
        <li><b>${T.good}</b> ${tx(a, 'good')}</li>
      </ul>
      <div class="card-actions">
        <button type="button" class="btn ${picked ? 'btn-ghost' : 'btn-primary'}" data-pick="${a.id}">${picked ? T.picked : T.pick}</button>
        <a class="guide-link" href="/areas/${a.id}/">${T.guide(nm(a))}</a>
      </div>
      <p class="source-note">${T.source}</p>`;
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
  // Leaflet (~150 KB) loads only when the map comes near the screen, so it never slows the first paint.
  function loadMap() {
    const LEAFLET = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min';
    const css = document.createElement('link');
    css.rel = 'stylesheet';
    css.href = LEAFLET + '.css';
    css.onload = () => map && map.invalidateSize();
    document.head.append(css);
    const js = document.createElement('script');
    js.src = LEAFLET + '.js';
    js.onload = initMap;
    js.onerror = initMap; // CDN blocked: initMap hides the map and the cards still work
    document.head.append(js);
  }
  if ('IntersectionObserver' in window) {
    const mo = new IntersectionObserver((entries) => {
      if (entries.some((en) => en.isIntersecting)) { mo.disconnect(); loadMap(); }
    }, { rootMargin: '600px 0px' });
    mo.observe($('#map'));
  } else {
    loadMap();
  }

  /* ---------- Move-in cost calculator ---------- */
  const calm = matchMedia('(prefers-reduced-motion: reduce)').matches;
  function countTo(el, to) {
    const from = Number(el.dataset.v || to);
    el.dataset.v = to;
    if (calm || from === to) { el.textContent = eur(to); return; }
    const t0 = performance.now();
    const tick = (t) => {
      const k = Math.min(1, (t - t0) / 350);
      el.textContent = eur(from + (to - from) * (1 - (1 - k) ** 3));
      if (k < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }
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
    countTo($('#calc-total'), rent + dep + fee);
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
  const labels = T.steps;
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
    $('#step-label').textContent = T.step(n, labels[n - 1]);
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
    const prices = (picked.length ? picked.map((a) => a.rent[i]) : [CITY_AVG[i]]).filter(Boolean);
    if (!prices.length) { hint.textContent = ''; return; }
    const lo = Math.min(...prices);
    const where = picked.length ? (picked.length === 1 ? T.in1(nm(picked[0])) : T.inMany) : T.city;
    const typical = lo === Math.max(...prices) ? eur(lo) : `${eur(lo)}–${eur(Math.max(...prices))}`;
    if (b < lo * 0.85) {
      const cheaper = AREAS.filter((a) => a.rent[i] && a.rent[i] <= b).map(nm).slice(0, 3);
      hint.dataset.tone = 'warn';
      hint.textContent = T.warn(ROOM_LABEL[i], where, typical, eur(b)) + (cheaper.length ? T.closer(cheaper.join(', ')) : T.fewer);
    } else if (b < lo) {
      hint.dataset.tone = '';
      hint.textContent = T.below(ROOM_LABEL[i], where, typical);
    } else {
      hint.dataset.tone = '';
      hint.textContent = T.covers(ROOM_LABEL[i], where, typical);
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
      ? T.short
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
  // Links from the area guides and ads can prefill the form: /?area=teika&rooms=2&budget=700#request
  const params = new URLSearchParams(location.search);
  const linked = AREAS.find((a) => a.id === params.get('area'));
  if (linked) { areaInput(linked).checked = true; selectArea(linked.id, { pan: false }); }
  if (params.get('rooms') in ROOM_INDEX) wizard.elements.rooms.value = params.get('rooms');
  if (Number(params.get('budget')) > 0) budget.value = Number(params.get('budget'));
  if (linked || params.has('rooms') || params.has('budget')) saveDraft();
  updateBudget();
  stayHint();

  /* ---------- Hero quick start → wizard ---------- */
  const quick = $('#quick');
  const monthSel = $('#quick-month');
  const opts = [`<option value="asap">${T.asap}</option>`];
  for (let i = 1; i <= 6; i++) {
    const d = new Date(today.getFullYear(), today.getMonth() + i, 1);
    opts.push(`<option value="${iso(d)}">${d.toLocaleString(T.locale, { month: 'long', year: 'numeric' })}</option>`);
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
    say(T.sending);
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
      say(T.failed, 'error');
    } finally {
      submit.disabled = false;
    }
  });

  /* ---------- Neighbourhood matcher ---------- */

  const WORK = {
    centre: { at: [56.9520, 24.1130], label: T.work.centre }, skanste: { at: [56.9690, 24.1240], label: T.work.skanste },
    teika: { at: [56.9725, 24.1650], label: T.work.teika }, left: { at: [56.9470, 24.0850], label: T.work.left },
  };
  const VIBE = T.vibe;
  const km = ([a1, o1], [a2, o2]) => {
    const r = Math.PI / 180;
    const h = Math.sin((a2 - a1) * r / 2) ** 2 + Math.cos(a1 * r) * Math.cos(a2 * r) * Math.sin((o2 - o1) * r / 2) ** 2;
    return 12742 * Math.asin(Math.sqrt(h));
  };
  const matcher = $('#matcher');
  const results = $('#match-results');
  const mBudget = matcher.elements.m_budget;
  const mOut = $('#m-budget-out');
  const showMBudget = () => { mOut.textContent = Number(mBudget.value) >= Number(mBudget.max) ? eur(mBudget.value) + '+' : eur(mBudget.value); };
  mBudget.addEventListener('input', showMBudget);
  showMBudget();
  matcher.addEventListener('change', (e) => {
    if (e.target.name !== 'vibe') return;
    const on = $$('input[name="vibe"]:checked', matcher);
    if (on.length > 3) e.target.checked = false;
  });

  function rank(f) {
    const i = ROOM_INDEX[f.get('m_rooms')];
    const b = Number(f.get('m_budget'));
    const work = WORK[f.get('work')];
    const want = f.getAll('vibe');
    const median4 = AREAS.map((a) => a.rent[3]).filter(Boolean).sort((x, y) => x - y)[5];
    return AREAS.map((a) => {
      const r = a.rent[i];
      const tags = [...a.tags, ...((CITY_AVG[i] ? r < CITY_AVG[i] : r < median4) && r ? ['value'] : [])];
      const fit = !r ? 0.3 : r <= b ? 1 : r <= b * 1.15 ? 0.5 : 0;
      const d = work ? km(a.at, work.at) : 0;
      const near = work ? Math.max(0, 1 - d / 7) : 1;
      const hits = want.filter((w) => tags.includes(w));
      const score = 0.45 * fit + 0.3 * near + 0.25 * (want.length ? hits.length / want.length : 1);
      const why = [
        !r ? T.unpriced(ROOM_LABEL[i]) : T.priced(eur(r), ROOM_LABEL[i], fit),
        work && T.dist(d, work.label),
        hits.length && T.matches(hits.map((h) => VIBE[h]).join(', ')),
      ].filter(Boolean);
      return { a, score, why };
    }).sort((x, y) => y.score - x.score).slice(0, 3);
  }

  let picks = [];
  matcher.addEventListener('submit', (e) => {
    e.preventDefault();
    const f = new FormData(matcher);
    picks = rank(f);
    results.innerHTML = `
      <div class="match-cards">${picks.map((p, n) => `
        <article class="match-card">
          <p class="match-rank">${n === 0 ? T.best : `#${n + 1}`}</p>
          <h3>${nm(p.a)}</h3>
          <p class="muted">${tx(p.a, 'tagline')}</p>
          <ul>${p.why.map((w) => `<li>${w}</li>`).join('')}</ul>
          <button type="button" class="btn btn-ghost" data-show="${p.a.id}">${T.onMap}</button>
        </article>`).join('')}
      </div>
      <div class="match-actions">
        <button type="button" class="btn btn-primary" id="match-use">${T.use}</button>
        <p class="small muted">${T.weights}</p>
      </div>`;
    results.hidden = false;
    results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    // Carry the answers into the request form.
    wizard.elements.rooms.value = f.get('m_rooms');
    setBudget(Number(f.get('m_budget')));
    saveDraft();
  });
  results.addEventListener('click', (e) => {
    const show = e.target.closest('[data-show]');
    if (show) { selectArea(show.dataset.show); $('#areas').scrollIntoView({ behavior: 'smooth' }); return; }
    if (e.target.closest('#match-use')) {
      picks.forEach((p) => { areaInput(p.a).checked = true; });
      updateBudget();
      renderCard(current);
      saveDraft();
      showStep(1, false);
      say(T.added(picks.map((p) => nm(p.a)).join(', ')), 'ok');
      $('#request').scrollIntoView({ behavior: 'smooth' });
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
