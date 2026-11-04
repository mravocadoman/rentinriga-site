// Source of the n8n workflow "Rent in Riga — leads" (n8n Workflow SDK).
// Kept in the repo so the form and the workflow change together; the live copy is in n8n.
import { workflow, node, trigger, expr } from '@n8n/workflow-sdk';

const hook = trigger({
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: {
    name: 'Lead from rentinrigalatvia.lv',
    parameters: { httpMethod: 'POST', path: 'rentinriga-lead', responseMode: 'responseNode', options: { rawBody: true } },
  },
});

const gate = node({
  type: 'n8n-nodes-base.code',
  version: 2,
  config: {
    name: 'Parse and gate',
    parameters: {
      mode: 'runOnceForAllItems',
      jsCode: `// The site posts text/plain (no CORS preflight), so the body arrives as a string.
// The key ships in client JS, so it only stops drive-by noise. Never read $env here.
const KEY = 'rr-lv-2026';
const NL = String.fromCharCode(10);
const ORIGINS = ['https://rentinrigalatvia.lv', 'https://www.rentinrigalatvia.lv', 'http://localhost:4173', 'http://127.0.0.1:4173'];
const inp = $input.first().json;
if ((inp.query || {}).k !== KEY) throw new Error('bad key');
let body = inp.body;
if (typeof body === 'string') { try { body = JSON.parse(body); } catch (e) { throw new Error('bad body'); } }
body = body || {};
if (body.website) throw new Error('honeypot');
if (Number(body.t) > 0 && Number(body.t) < 3000) throw new Error('too fast');
if (body.consent !== true) throw new Error('no consent');

// Public webhook: every value is cut to size before it goes anywhere.
const clip = (v, n) => String(v == null ? '' : v).trim().slice(0, n);
const list = (v, n) => (Array.isArray(v) ? v : []).slice(0, 15).map((x) => clip(x, n)).filter(Boolean).join(', ');
const kind = body.kind === 'partner' ? 'partner' : 'tenant';
const name = clip(body.name, 100);
const email = clip(body.email, 254);
const phone = clip(body.phone, 40);
const at = email.indexOf('@');
if (at < 1 || email.lastIndexOf('.') < at + 2 || email.includes(' ')) throw new Error('bad email');
if (!name) throw new Error('no name');

const channel = clip(body.channel, 20);
const moveIn = /^\\d{4}-\\d{2}-\\d{2}$/.test(String(body.move_in)) ? String(body.move_in) : '';
const moveInLv = moveIn ? moveIn.split('-').reverse().join('.') : '';
const stay = clip(body.stay, 20);
const adults = clip(body.adults, 3);
const children = clip(body.children, 3);
const pets = clip(body.pets, 60);
const people = [adults && adults + ' adult(s)', children && children !== '0' && children + ' child(ren)', pets && 'pets: ' + pets].filter(Boolean).join(', ');
const budget = Math.max(0, Math.min(20000, Math.round(Number(body.budget) || 0)));
const rooms = clip(body.rooms, 20);
const furnished = clip(body.furnished, 20);
const areas = list(body.areas, 40);
const wants = list(body.wants, 40);
const relocation = clip(body.relocation, 20);
const company = clip(body.company, 120);
const website = clip(body.site, 200);
const units = clip(body.units, 40);
const message = clip(body.message, 3000);
const source = clip(body.source, 200);
const page = clip(body.page, 300);
const lang = body.lang === 'ru' ? 'ru' : 'en';
const langLine = lang === 'ru' ? 'Russian (the lead used the Russian site; reply in Russian if you can)' : '';

const line = (k, v) => (v ? k + ': ' + v + NL : '');
let subject, detail, alert;
if (kind === 'tenant') {
  const what = [rooms && rooms + ' rooms', budget && 'up to EUR ' + budget, moveInLv && 'from ' + moveInLv, stay && stay + ' months'].filter(Boolean).join(', ');
  subject = 'Riga Flat Match request: ' + (what || 'flat') + ' | ' + name;
  // The block between the rules is safe to forward to a partner agency as-is (the lead consented to that).
  detail = '---- request (forwardable) ----' + NL +
    line('Language', langLine) + line('Name', name) + line('E-mail', email) + line('Phone / WhatsApp', phone) + line('Prefers', channel) +
    line('Move-in', moveInLv) + line('Length of stay', stay && stay + ' months') + line('Who', people) +
    line('Budget (max, per month)', budget && 'EUR ' + budget) + line('Rooms', rooms) + line('Furnished', furnished) +
    line('Areas', areas) + line('Must-haves', wants) +
    line('Relocation', relocation === 'employer' ? 'employer-backed' + (company ? ' (' + company + ')' : '') : (company ? 'self, works at ' + company : '')) +
    (message ? NL + message + NL : '') + '-------------------------------' + NL +
    line('Source', source) + line('Page', page);
  alert = '🏠 New rental request' + (lang === 'ru' ? ' [RU]' : '') + NL + name + ' | ' + (what || '-') + (areas ? NL + 'Areas: ' + areas : '') +
    (relocation === 'employer' ? NL + '💼 Employer-backed' + (company ? ': ' + company : '') : '') +
    NL + [phone, email].filter(Boolean).join(' | ') + (source ? NL + '🔗 ' + source : '');
} else {
  subject = 'Riga Flat Match partner application: ' + (company || name);
  detail = line('Agency', company) + line('Website', website) + line('Contact', name) + line('E-mail', email) +
    line('Phone', phone) + line('Flats managed / listed', units) + line('Areas', areas) +
    (message ? NL + message + NL : '') + line('Source', source) + line('Page', page);
  alert = '🤝 New partner application' + NL + (company || '-') + ' | ' + name + NL + [phone, email].filter(Boolean).join(' | ');
}

// Confirmation e-mail to the tenant. Fixed text plus validated fields only (never the name or the
// notes), so the form can't be used to send someone else arbitrary text; at most one per address
// per 24 h, remembered as a hash, not the address.
let confirm = { send: false };
if (kind === 'tenant') {
  const store = $getWorkflowStaticData('global');
  store.confirmed = store.confirmed || {};
  const now = Date.now();
  for (const k of Object.keys(store.confirmed)) if (now - store.confirmed[k] > 864e5) delete store.confirmed[k];
  let h = 2166136261;
  for (const c of email.toLowerCase()) { h ^= c.codePointAt(0); h = Math.imul(h, 16777619) >>> 0; }
  const hk = h.toString(36);
  if (!store.confirmed[hk]) {
    store.confirmed[hk] = now;
    const RU = lang === 'ru';
    const AREA_RU = { 'Centre': 'Центр', 'Old Town': 'Старая Рига', 'Ķīpsala': 'Кипсала', 'Skanste': 'Скансте', 'Teika': 'Тейка', 'Āgenskalns': 'Агенскалнс', 'Torņakalns': 'Торнякалнс', 'Avoti & Grīziņkalns': 'Авоты и Гризинькалнс', 'Mežaparks': 'Межапаркс', 'Purvciems': 'Пурвциемс', 'Imanta': 'Иманта' };
    const picked = (Array.isArray(body.areas) ? body.areas : []).filter((x) => x in AREA_RU).map((x) => (RU ? AREA_RU[x] : x));
    const STAY = RU ? { '1-3': '1–3 месяца', '3-6': '3–6 месяцев', '6-12': '6–12 месяцев', '12+': '12+ месяцев' } : { '1-3': '1–3 months', '3-6': '3–6 months', '6-12': '6–12 months', '12+': '12+ months' };
    const ROOMS = RU ? { '1': '1 комната (студия)', '2': '2 комнаты', '3': '3 комнаты', '4+': '4+ комнаты' } : { '1': '1 room (studio)', '2': '2 rooms', '3': '3 rooms', '4+': '4+ rooms' };
    const facts = [
      moveInLv && (RU ? 'Заезд: ' : 'Move-in: ') + moveInLv + (STAY[stay] ? ' (' + STAY[stay] + ')' : ''),
      ROOMS[rooms] && (RU ? 'Квартира: ' : 'Flat: ') + ROOMS[rooms] + (budget ? (RU ? ', до ' + budget + ' EUR в месяц' : ', up to EUR ' + budget + ' a month') : ''),
      (RU ? 'Районы: ' : 'Areas: ') + (picked.length ? picked.join(', ') : (RU ? 'любые' : 'any')),
    ].filter(Boolean).join(NL);
    const text = RU
      ? ['Здравствуйте!', '', 'Спасибо за заявку на Riga Flat Match. Вот что мы получили:', '', facts, '', 'Что будет дальше', '1. Мы проверяем заявку, обычно в течение одного рабочего дня.', '2. До трёх агентств связываются с вами удобным для вас способом.', '3. Вы сравниваете квартиры, договариваетесь о просмотрах и выбираете. Без обязательств.', '', 'Совет: никогда не платите депозит или бронь, пока не увидели квартиру лично или по видеосвязи.', '', 'Что-то не так или планы изменились? Просто ответьте на это письмо.', '', 'Riga Flat Match', 'https://rentinrigalatvia.lv/ru/'].join(NL)
      : ['Hi,', '', 'Thanks for your request on Riga Flat Match. This is what we received:', '', facts, '', 'What happens next', '1. We check your request, usually within one working day.', '2. Up to three rental agencies contact you by your preferred channel.', '3. You compare flats, book viewings and choose. There is no obligation.', '', 'A tip while you wait: never pay a deposit or reservation fee before you have seen the flat in person or on a live video call.', '', 'Something wrong, or plans changed? Just reply to this e-mail.', '', 'Riga Flat Match', 'https://rentinrigalatvia.lv/'].join(NL);
    confirm = { send: true, to: email, subject: RU ? 'Мы получили вашу заявку на квартиру в Риге' : 'We’ve got your Riga flat request', text };
  }
}

// Telegram gets parse_mode HTML, so user text is escaped (Markdown would eat [RU] or choke on _ and *).
alert = alert.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const origin = (inp.headers || {}).origin || '';
return [{ json: {
  row: {
    kind, name, email, phone, channel, move_in: moveIn, stay, people, budget, rooms: rooms + (furnished ? ' / furnished: ' + furnished : ''),
    areas, wants, company: kind === 'partner' ? [company, website, units && units + ' flats'].filter(Boolean).join(' | ') : company,
    message, source: (lang === 'ru' ? '[ru] ' : '') + source, page, consent_at: new Date().toISOString(), status: 'new', sent_to: '', raw: JSON.stringify(body).slice(0, 8000),
  },
  email, subject, detail, alert, confirm,
  cors: ORIGINS.includes(origin) ? origin : ORIGINS[0],
} }];`,
    },
  },
});

const save = node({
  type: 'n8n-nodes-base.dataTable',
  version: 1.1,
  config: {
    name: 'Save to table',
    parameters: {
      resource: 'row',
      operation: 'insert',
      dataTableId: { __rl: true, mode: 'id', value: 'IfphWRSOm2SkfFaD', cachedResultName: 'Rent in Riga leads' },
      columns: {
        mappingMode: 'defineBelow',
        value: {
          kind: '={{ $json.row.kind }}',
          name: '={{ $json.row.name }}',
          email: '={{ $json.row.email }}',
          phone: '={{ $json.row.phone }}',
          channel: '={{ $json.row.channel }}',
          move_in: '={{ $json.row.move_in }}',
          stay: '={{ $json.row.stay }}',
          people: '={{ $json.row.people }}',
          budget: '={{ $json.row.budget }}',
          rooms: '={{ $json.row.rooms }}',
          areas: '={{ $json.row.areas }}',
          wants: '={{ $json.row.wants }}',
          company: '={{ $json.row.company }}',
          message: '={{ $json.row.message }}',
          source: '={{ $json.row.source }}',
          page: '={{ $json.row.page }}',
          consent_at: '={{ $json.row.consent_at }}',
          status: '={{ $json.row.status }}',
          sent_to: '={{ $json.row.sent_to }}',
          raw: '={{ $json.row.raw }}',
        },
        schema: [
          { id: 'kind', displayName: 'kind', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'name', displayName: 'name', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'email', displayName: 'email', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'phone', displayName: 'phone', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'channel', displayName: 'channel', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'move_in', displayName: 'move_in', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'stay', displayName: 'stay', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'people', displayName: 'people', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'budget', displayName: 'budget', required: false, defaultMatch: false, display: true, type: 'number', canBeUsedToMatch: true },
          { id: 'rooms', displayName: 'rooms', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'areas', displayName: 'areas', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'wants', displayName: 'wants', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'company', displayName: 'company', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'message', displayName: 'message', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'source', displayName: 'source', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'page', displayName: 'page', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'consent_at', displayName: 'consent_at', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'status', displayName: 'status', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'sent_to', displayName: 'sent_to', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
          { id: 'raw', displayName: 'raw', required: false, defaultMatch: false, display: true, type: 'string', canBeUsedToMatch: true },
        ],
      },
      options: {},
    },
  },
});

const reply = node({
  type: 'n8n-nodes-base.respondToWebhook',
  version: 1.5,
  config: {
    name: 'Answer the site',
    parameters: {
      respondWith: 'json',
      responseBody: '{"ok":true}',
      options: {
        responseHeaders: {
          entries: [
            { name: 'Access-Control-Allow-Origin', value: expr("{{ $('Parse and gate').item.json.cors }}") },
            { name: 'Vary', value: 'Origin' },
          ],
        },
      },
    },
  },
});

const mail = node({
  type: 'n8n-nodes-base.gmail',
  version: 2.1,
  config: {
    name: 'E-mail Rihards',
    parameters: {
      resource: 'message',
      operation: 'send',
      sendTo: 'rihards.zeila@gmail.com',
      subject: expr("{{ $('Parse and gate').item.json.subject }}"),
      emailType: 'text',
      message: expr("{{ $('Parse and gate').item.json.detail }}"),
      options: { appendAttribution: false, senderName: 'Riga Flat Match website', replyTo: expr("{{ $('Parse and gate').item.json.email }}") },
    },
    credentials: { gmailOAuth2: { id: 'OxLeeAoOPOzsUtpV', name: 'Rihards personal | Gmail account' } },
  },
});

const ping = node({
  type: 'n8n-nodes-base.telegram',
  version: 1.2,
  config: {
    name: 'Telegram alert',
    onError: 'continueRegularOutput',
    parameters: {
      resource: 'message',
      operation: 'sendMessage',
      chatId: '6091120403',
      text: expr("{{ $('Parse and gate').item.json.alert }}"),
      additionalFields: { appendAttribution: false, disable_web_page_preview: true, parse_mode: 'HTML' },
    },
    credentials: { telegramApi: { id: 'Q8gMn5hYpVdgOH6K', name: 'Telegram account' } },
  },
});

const wantsConfirm = node({
  type: 'n8n-nodes-base.if',
  version: 2.2,
  config: {
    name: 'Confirmation due?',
    parameters: {
      conditions: {
        options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' },
        conditions: [{ leftValue: expr("{{ $('Parse and gate').item.json.confirm.send }}"), rightValue: '', operator: { type: 'boolean', operation: 'true', singleValue: true } }],
        combinator: 'and',
      },
    },
  },
});

const confirmMail = node({
  type: 'n8n-nodes-base.gmail',
  version: 2.1,
  config: {
    name: 'Confirmation to tenant',
    onError: 'continueRegularOutput',
    parameters: {
      resource: 'message',
      operation: 'send',
      sendTo: expr("{{ $('Parse and gate').item.json.confirm.to }}"),
      subject: expr("{{ $('Parse and gate').item.json.confirm.subject }}"),
      emailType: 'text',
      message: expr("{{ $('Parse and gate').item.json.confirm.text }}"),
      options: { appendAttribution: false, senderName: 'Riga Flat Match' },
    },
    credentials: { gmailOAuth2: { id: 'OxLeeAoOPOzsUtpV', name: 'Rihards personal | Gmail account' } },
  },
});

export default workflow('rentinriga-lead', 'Rent in Riga — leads', { settings: { executionOrder: 'v1', errorWorkflow: 'R9OmXjBXdhYetZkM' } })
  .add(hook)
  .to(gate)
  .to(save)
  .to(reply)
  .to(mail)
  .to(ping)
  .to(wantsConfirm.onTrue(confirmMail));
