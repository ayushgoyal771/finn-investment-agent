'use strict';

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon = name => `<svg aria-hidden="true"><use href="#i-${esc(name)}"/></svg>`;
const initials = name => name.split(' ').slice(0, 2).map(w => w[0]).join('');
const number = (n, decimals = 0) => Number(n).toLocaleString('en-IN', {maximumFractionDigits: decimals});
const pct = n => n == null ? '—' : `${n > 0 ? '+' : ''}${Number(n).toFixed(1)}%`;
const changeClass = n => n >= 0 ? 'positive' : 'negative';
const safeUrl = value => { try { const u = new URL(value); return u.protocol === 'https:' ? esc(u.href) : '#'; } catch { return '#'; } };
const metricSourceLabel = metric => metric.source_kind === 'transcript' ? 'Call transcript' : 'Annual report';
const dateText = value => new Date(value).toLocaleString('en-IN', {day:'numeric', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit', timeZone:'Asia/Kolkata'}) + ' IST';
const timeAgo = value => { const mins = Math.max(0, Math.floor((Date.now() - new Date(value)) / 60000)); return mins < 60 ? `${mins}m ago` : mins < 1440 ? `${Math.floor(mins / 60)}h ago` : `${Math.floor(mins / 1440)}d ago`; };
let state = {route:'brief', mode:'demo', filter:'all', brief:null, network:null, report:null, token:sessionStorage.getItem('finn-token') || '', modelAvailable:false};
let briefSequence = 0, networkSequence = 0, toastTimer, refreshTimer, researchBusy = false;

function toast(message) { const el = $('#toast'); el.textContent = message; el.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => el.hidden = true, 3800); }

async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body) headers.set('Content-Type', 'application/json');
  if (state.token) headers.set('Authorization', `Bearer ${state.token}`);
  const response = await fetch(path, {...options, headers, signal:options.signal || AbortSignal.timeout(150000)});
  const body = await response.json().catch(() => ({detail:'The server returned an unreadable response.'}));
  if (response.status === 401) { if (!$('#auth-dialog').open) $('#auth-dialog').showModal(); throw new Error('Unlock the workspace to continue.'); }
  if (!response.ok) {
    const message = Array.isArray(body.detail) ? body.detail.map(e => e.msg).join(' · ') : body.detail;
    throw new Error(message || `Request failed (${response.status}).`);
  }
  return body;
}

function notice() {
  const live = state.mode === 'live';
  const el = $('#global-notice');
  el.className = `notice ${live ? 'live-notice' : 'demo-notice'}`;
  el.innerHTML = live
    ? '<span class="notice-dot"></span><span>Live sources <span class="notice-detail">· End-of-day data. Source failures and stale observations remain visible.</span></span><a href="#research">Research a company ↗</a>'
    : '<span class="notice-dot"></span><span>Demo workspace <span class="notice-detail">· Fictional signals and people. Research uses attributed FY2025 evidence.</span></span><a href="#research">Explore the evidence ↗</a>';
}

async function route() {
  const next = location.hash.slice(1) || 'brief';
  state.route = ['brief','research','network','saved'].includes(next) ? next : 'brief';
  const view = state.route === 'saved' ? 'brief' : state.route;
  $$('.view').forEach(el => el.hidden = el.id !== `view-${view}`);
  $$('[data-nav]').forEach(el => { const active = el.dataset.nav === state.route; el.classList.toggle('active', active); if (active) el.setAttribute('aria-current','page'); else el.removeAttribute('aria-current'); });
  const names = {brief:'Today’s brief', research:'Research', network:'Your network', saved:'Saved signals'};
  $('#page-name').textContent = names[state.route]; document.title = `${names[state.route]} · FINN`;
  $('#feed-heading').textContent = state.route === 'saved' ? 'Worth coming back to.' : 'The signals that matter.';
  $('#time-window').disabled = state.route === 'saved';
  if (view === 'brief') await loadBrief();
  if (view === 'network' && !state.network) await loadNetwork();
}

function sparkline(values, change) {
  if (!values?.length) return '';
  const low = Math.min(...values), high = Math.max(...values), span = high - low || 1;
  const points = values.map((n,i) => `${(i * 48 / (values.length - 1 || 1)).toFixed(1)},${(23 - (n - low) / span * 20).toFixed(1)}`).join(' ');
  return `<svg class="sparkline ${change < 0 ? 'negative' : ''}" viewBox="0 0 48 25" aria-label="21-session price trend"><polyline points="${points}"/></svg>`;
}

async function loadBrief({quiet = false} = {}) {
  const id = ++briefSequence;
  const saved = state.route === 'saved';
  if (!quiet) {
    state.brief = null;
    $('#signal-feed').innerHTML = '<div class="loading-card">Preparing your fieldnotes…</div>';
    $('#brief-stats').innerHTML = '';
    $('#radar-list').innerHTML = '';
    $('#radar-note').textContent = 'Waiting for the selected data sources…';
    $('#routine-wrap').hidden = true;
  }
  $('#signal-feed').setAttribute('aria-busy','true');
  $('#brief-errors').innerHTML = '';
  try {
    const data = await api(`/api/brief?mode=${state.mode}&hours=${$('#time-window').value}&saved=${saved}`);
    if (id !== briefSequence || !['brief','saved'].includes(state.route)) return;
    const previous = state.brief;
    state.brief = data;
    renderBrief();
    if (quiet && previous && data.stats.unread > previous.stats.unread) toast(`${data.stats.unread - previous.stats.unread} new signals in your brief`);
  } catch(error) {
    if (id !== briefSequence) return;
    $('#signal-feed').innerHTML = `<div class="empty-state"><h3>The sources need a moment.</h3><p>${esc(error.message)}</p><button class="text-button" data-action="refresh">Try again ${icon('refresh')}</button></div>`;
    $('#brief-stats').innerHTML = '';
  } finally { if (id === briefSequence) $('#signal-feed').setAttribute('aria-busy','false'); }
}

function renderBrief() {
  const data = state.brief;
  if (!data) return;
  const stats = [[data.stats.companies,'Companies watched','Across your portfolio'],[data.stats.filings,'Disclosures in view',state.route==='saved'?'Saved for later':`In the last ${data.hours} hours`],[data.stats.signals,'Signals to consider','The important changes'],[data.stats.network_paths,'Paths to context','People you can learn from']];
  $('#ticker-options').innerHTML = data.market.map(m=>`<option value="${esc(m.symbol)}">${esc(m.name)}</option>`).join('');
  $('#brief-stats').innerHTML = stats.map(([n,title,sub]) => `<div class="stat"><span class="stat-number">${n.toString().padStart(2,'0')}</span><div class="stat-text"><strong>${esc(title)}</strong><span class="stat-detail">${esc(sub)}</span></div></div>`).join('');
  $('#nav-count').textContent = data.stats.unread;
  $('#feed-updated').textContent = 'Updated just now';
  $('#brief-errors').innerHTML = data.warnings.map(w => `<div class="error-inline">${esc(w)}</div>`).join('');
  const matchesFilter = item => state.filter === 'all' || (state.filter === 'market' ? item.category === 'market' : item.category !== 'market');
  const items = data.priority.filter(matchesFilter);
  $('#signal-feed').innerHTML = items.length ? items.map((item,i) => signalCard(item,i === 0)).join('') : `<div class="empty-state"><h3>${state.route === 'saved' ? 'Keep a thought for later.' : 'A quieter window.'}</h3><p>${state.route === 'saved' ? 'Use the bookmark on a signal to save it here. Saved signals persist between visits.' : 'No high-priority signals match this view. Try another window or filter.'}</p></div>`;
  const routine = data.routine.filter(matchesFilter);
  $('#routine-count').textContent = `· ${routine.length}`;
  $('#routine-wrap').hidden = routine.length === 0;
  $('#routine-feed').innerHTML = routine.map(item => `<div class="routine-row"><span class="company-monogram">${esc(item.symbol.slice(0,2))}</span><button data-item="${esc(item.id)}">${esc(item.title)}<small>${esc(item.symbol)} · ${esc(item.category_label)} · ${esc(timeAgo(item.published_at))}</small></button><button class="icon-button ${item.saved?'is-saved':''}" data-save="${esc(item.id)}" aria-label="${item.saved?'Unsave':'Save'} ${esc(item.title)}" aria-pressed="${item.saved}">${icon('bookmark')}</button></div>`).join('');
  const radar = [...data.market].sort((a,b) => (b.volume_ratio || 0) - (a.volume_ratio || 0)).slice(0,5);
  $('#radar-list').innerHTML = radar.map(item => `<div class="radar-row"><span class="company-monogram">${esc(item.symbol.slice(0,2))}</span><div class="radar-company"><strong>${esc(item.symbol)}</strong><small>${esc(item.name)}</small></div>${!item.error?sparkline(item.history,item.change):''}<div class="radar-price">${item.error ? '<span class="muted">Unavailable</span>' : `₹${number(item.close)}<small class="${changeClass(item.change)}">${pct(item.change)}${item.stale?' · stale':''}</small>`}</div></div>`).join('');
  $('#radar-note').textContent = data.mode === 'demo' ? 'Synthetic EOD prices · not market observations.' : 'Last completed session · source date shown in full portfolio.';
}

function signalCard(item, featured) {
  const contact = item.network[0];
  return `<article class="signal-card ${featured?'featured':''}"><div class="signal-topline"><div class="signal-meta"><span class="category-tag ${esc(item.category)}">${esc(item.category_label)}</span><span class="signal-company">${esc(item.symbol)}</span><time datetime="${esc(item.published_at)}">${esc(timeAgo(item.published_at))}</time></div><button class="icon-button ${item.saved?'is-saved':''}" data-save="${esc(item.id)}" aria-pressed="${item.saved}" aria-label="${item.saved?'Unsave':'Save'} ${esc(item.title)}">${icon('bookmark')}</button></div><h3 class="signal-title"><button data-item="${esc(item.id)}">${esc(item.title)}</button></h3><p><span class="why-label">WHY IT MATTERS</span>${esc(item.why)}</p>${contact?`<div class="connection-strip"><span class="avatar">${esc(initials(contact.name))}</span><div class="connection-copy"><strong>${esc(contact.name)}</strong> adds context<small>${esc(contact.path.length?'A second-degree path to the incoming CFO':contact.title)}</small></div><button class="text-button" data-contact="${esc(contact.id)}">Your connection ${icon('up-right')}</button></div>`:''}<div class="signal-actions"><button class="read-button" data-item="${esc(item.id)}">Read the signal ${icon('arrow')}</button><span class="score-label">${item.alert?'ALERT ON · ':''}<strong>${item.score}</strong> / 100 priority</span></div></article>`;
}

function allItems() { return state.brief ? [...state.brief.priority,...state.brief.routine] : []; }

async function saveItem(id) {
  const item = allItems().find(i => i.id === id);
  if (!item) return;
  const next = !item.saved;
  try { await api(`/api/items/${encodeURIComponent(id)}`,{method:'PATCH',body:JSON.stringify({saved:next})}); item.saved = next; if (state.route === 'saved') await loadBrief({quiet:true}); else renderBrief(); toast(next?'Signal saved to your fieldnotes':'Signal removed from saved'); } catch(e) { toast(e.message); }
}

function showDetail(html, label = 'SIGNAL NOTES') {
  $('#dialog-label').textContent = label;
  $('#dialog-body').innerHTML = html;
  const dialog = $('#detail-dialog');
  if (!dialog.open) dialog.showModal();
  dialog.scrollTop = 0;
}

async function showItem(id) {
  const item = allItems().find(i => i.id === id);
  if (!item) return;
  const finance = item.results;
  const table = finance ? `<div class="detail-section"><p class="eyebrow">A FIRST CUT OF THE NUMBERS</p><div class="table-scroll"><table><thead><tr><th>Metric</th><th>Quarter</th><th>Prev. Q</th><th>Year-ago Q</th><th>QoQ</th><th>YoY</th></tr></thead><tbody>${finance.rows.map(r => {const qoq = growth(r.values[0],r.values[1]), yoy = growth(r.values[0],r.values[2]);return `<tr><td>${esc(r.metric)}</td>${r.values.map(v=>`<td>${number(v)}</td>`).join('')}<td class="${changeClass(qoq)}">${pct(qoq)}</td><td class="${changeClass(yoy)}">${pct(yoy)}</td></tr>`;}).join('')}</tbody></table></div><p class="table-footnote">${esc(finance.unit)}. Demonstrates comparison logic; these figures are not extracted from a real filing.</p></div>` : '';
  const incoming = item.incoming_person ? `<div class="detail-section"><p class="eyebrow">WHO IS COMING IN?</p><h3>${esc(item.incoming_person.name)}</h3><p>${esc(item.incoming_person.title)} · ${esc(item.incoming_person.education)}</p>${item.incoming_person.roles.map(r=>`<div class="career-row"><strong>${esc(r.title)}</strong> · ${esc(r.company)}<small>${r.start}–${r.end || 'present'}</small></div>`).join('')}<p class="table-footnote">${esc(item.incoming_person.provenance)}</p></div>` : '';
  const paths = item.network.length ? `<div class="detail-section"><p class="eyebrow">WHO CAN HELP YOU UNDERSTAND THIS</p>${item.network.map(c=>`<div class="mini-contact">${c.path.length?`<div class="network-path">${c.path.map(p=>`<span>${esc(p)}</span>`).join('<span aria-hidden="true">→</span>')}</div>`:''}<div class="mini-contact-head"><span class="avatar">${esc(initials(c.name))}</span><strong>${esc(c.name)}</strong></div><p>${esc(c.reasons[0])}</p><p><em>Ask: “${esc(c.suggested_question)}”</em></p><button class="text-button" data-contact="${esc(c.id)}">See career and connection ${icon('arrow')}</button></div>`).join('')}</div>` : '';
  showDetail(`<div class="source-banner">${item.demo?'FICTIONAL DEMO SCENARIO · Not an actual company announcement':'LIVE EXCHANGE / MARKET SOURCE · Verify the original'}</div><h2>${esc(item.title)}</h2><div class="signal-meta"><span class="category-tag">${esc(item.category_label)}</span><span>${esc(item.company)}</span></div><p>${esc(dateText(item.published_at))}</p><p>${esc(item.summary)}</p><div class="detail-section"><p class="eyebrow">WHY IT MATTERS</p><p>${esc(item.why)}</p><p class="table-footnote">Priority ${item.score}/100 = category weight plus a small network-context boost. Classification and ranking are deterministic.</p></div>${table}${incoming}${paths}<div class="detail-actions">${item.source_url?`<a class="text-button" href="${safeUrl(item.source_url)}" target="_blank" rel="noopener noreferrer">Open original source ${icon('up-right')}</a>`:'<span class="muted">Synthetic event · no original filing</span>'}<button class="primary-button" data-go-research="${esc(item.symbol)}">Research ${esc(item.symbol)} ${icon('arrow')}</button></div>`);
  if (!item.seen) { try { await api(`/api/items/${encodeURIComponent(id)}`,{method:'PATCH',body:JSON.stringify({seen:true})}); item.seen = true; state.brief.stats.unread = Math.max(0,state.brief.stats.unread-1); $('#nav-count').textContent = state.brief.stats.unread; } catch(e) {toast(e.message);} }
}

function growth(current, prior) {return prior > 0 ? (current/prior-1)*100 : null;}

function portfolioDialog() {
  if (!state.brief) return;
  showDetail(`<h2>Your 18-company universe.</h2><p>A mock watchlist across sectors and company sizes. ${state.mode === 'demo'?'All prices below are synthetic.':'Prices reflect the last completed session.'}</p><div class="table-scroll"><table class="portfolio-table"><thead><tr><th>Company</th><th>Close ₹</th><th>Day</th><th>Volume</th><th>As of</th></tr></thead><tbody>${state.brief.market.map(m=>`<tr><td><strong>${esc(m.symbol)}</strong><br><small>${esc(m.sector)} · ${esc(m.size)} cap</small></td>${m.error?`<td colspan="4">${esc(m.error)}</td>`:`<td>${number(m.close,2)}</td><td class="${changeClass(m.change)}">${pct(m.change)}</td><td>${m.volume_ratio == null?'—':m.volume_ratio.toFixed(1)+'×'}</td><td>${esc(m.date)}${m.stale?' · stale':''}</td>`}</tr>`).join('')}</tbody></table></div><p class="table-footnote">Volume ratio uses the prior 20 completed trading sessions, excluding the current session. Demo bars omit exchange holidays; live bars use provider session dates.</p>`, 'YOUR PORTFOLIO');
}

async function openSettings() {
  try {
    const data = await api('/api/settings');
    $('#price-rule').value = data.preferences.price_threshold; $('#volume-rule').value = data.preferences.volume_threshold;
    updateRuleLabels();
    $('#category-options').innerHTML = data.categories.map(c=>`<label><input type="checkbox" name="category" value="${esc(c.id)}" ${data.preferences.categories.includes(c.id)?'checked':''}> ${esc(c.label)}</label>`).join('');
    $('#settings-error').textContent = ''; $('#settings-dialog').showModal();
  } catch(e) {toast(e.message);}
}
function updateRuleLabels() { $('#price-output').textContent = `${$('#price-rule').value}%`; $('#volume-output').textContent = `${$('#volume-rule').value}×`; }

function setResearch(symbol) {
  if ($('#detail-dialog').open) $('#detail-dialog').close();
  $('#research-symbol').value = symbol;
  const questions = {ASIANPAINT:'Where do the growth narrative and the numbers diverge?', TCS:'What do the annual report and call say about growth and margins?', INFY:'How well does profit convert to cash?'};
  $('#research-question').value = questions[symbol] || 'What should I understand about growth, cash and capital allocation?';
  $('#research-mode').value = ['TCS','INFY','ASIANPAINT'].includes(symbol) && state.mode === 'demo' ? 'demo' : 'live';
  if (state.route !== 'research') location.hash = 'research';
  $('#research-result').innerHTML = '<div class="research-empty"><span class="big-asterisk">✳</span><h2>Your next question starts here.</h2><p>Review the ticker, question and source mode above, then build your brief.</p></div>';
  $('#research-symbol').focus();
}

async function runResearch(event) {
  event.preventDefault(); if (researchBusy) return;
  researchBusy = true; const button = $('#research-submit'); button.disabled = true;
  $('#research-result').setAttribute('aria-busy','true');
  const mode = $('#research-mode').value;
  $('#research-result').innerHTML = `<div class="loading-card">${mode === 'live'?'Discovering annual reports and transcripts, then reading the primary evidence. This may take up to two minutes.':'Reading the historical evidence and finding relevant experience in your network…'}</div>`;
  try {
    const data = await api('/api/research',{method:'POST',body:JSON.stringify({symbol:$('#research-symbol').value,question:$('#research-question').value,mode,use_model:$('#use-model').checked})});
    state.report = data; renderReport(data);
  } catch(e) {state.report = null; $('#research-result').innerHTML = `<div class="research-report empty-state"><h3>Keep the evidence standard.</h3><p>${esc(e.message)}</p><p>Try TCS, INFY or ASIANPAINT in historical mode for a verified offline example.</p></div>`;}
  finally {researchBusy = false; button.disabled = false; $('#research-result').setAttribute('aria-busy','false');}
}

function renderReport(data) {
  const synthesis = data.synthesis ? `<div class="model-card"><p class="eyebrow">OPTIONAL MODEL SYNTHESIS</p><h3>A first interpretation</h3><ul>${data.synthesis.claims.map(c=>`<li>${esc(c.text)} ${c.source_ids.map(id=>`<a class="citation" href="#source-${esc(id)}" data-source="${esc(id)}">[source]</a>`).join('')}</li>`).join('')}</ul><small>Model interpretation: citations are validated, but factual entailment still requires human review.</small>${data.synthesis.unanswered.length?`<p class="table-footnote">Still unanswered: ${data.synthesis.unanswered.map(esc).join(' · ')}</p>`:''}</div>` : '';
  $('#research-result').innerHTML = `<article class="research-report"><div class="report-heading"><div class="research-result-header"><p class="eyebrow">${esc(data.symbol)} / EVIDENCE BRIEF</p><button class="text-button" data-action="export-report">Save brief ${icon('up-right')}</button></div><h2>${esc(data.name)}</h2><p>${esc(data.thesis)}</p><div class="report-period"><span>${esc(data.period)}</span><span class="engine-label">${esc(data.engine)}</span></div></div>${data.warnings.map(w=>`<div class="warning-box">${esc(w)}</div>`).join('')}${data.metrics.length?`<div class="report-metrics">${data.metrics.map(m=>`<div class="metric-card"><label>${esc(m.label)}</label><span class="metric-value">${number(m.value,2)}</span><small>${esc(m.unit)} · FY2025</small><br><a href="${safeUrl(m.url)}" target="_blank" rel="noopener noreferrer">${metricSourceLabel(m)} ↗</a></div>`).join('')}</div>`:''}${synthesis}<div class="research-report-layout"><div><p class="eyebrow">EVIDENCE RELEVANT TO YOUR QUESTION</p>${data.facts.length?data.facts.map(f=>`<section id="source-${esc(f.id)}" class="evidence-card"><p class="eyebrow"><span>${esc(f.kind === 'annual_report'?'ANNUAL REPORT':'CALL TRANSCRIPT')}</span><span>${f.paraphrase?'ATTRIBUTED PARAPHRASE':'SOURCE EXCERPT'}</span></p><h3>${esc(f.heading)}</h3>${f.paraphrase?`<p>${esc(f.text)}</p>`:`<blockquote>${esc(f.text)}</blockquote>`}<a class="source-link" href="${safeUrl(f.url)}" target="_blank" rel="noopener noreferrer"><span>${esc(f.title)}<small>${esc(f.locator)}</small></span>${icon('up-right')}</a></section>`).join(''):'<div class="empty-state">No matching passage was found. Narrow the question or change the evidence source.</div>'}</div><aside class="research-side"><p class="eyebrow">TURN RESEARCH INTO A CONVERSATION</p><h3>Who should you call?</h3><p>Experience that can help you interpret the public evidence.</p>${data.network.length?data.network.map(c=>`<div class="mini-contact"><div class="mini-contact-head"><span class="avatar">${esc(initials(c.name))}</span><strong>${esc(c.name)}</strong></div><p>${esc(c.reasons[0])}</p><button class="text-button" data-contact="${esc(c.id)}">Why this person ${icon('arrow')}</button></div>`).join(''):'<p>No relevant network overlap was found. FINN does not invent a connection.</p>'}<div class="question-card"><h4>QUESTIONS TO TAKE WITH YOU</h4>${data.questions.map(q=>`<p>“${esc(q)}”</p>`).join('')}</div><p class="table-footnote">Network profiles are synthetic and stay separate from primary financial evidence.</p></aside></div></article>`;
}

async function loadNetwork(query = '') {
  const id = ++networkSequence;
  $('#network-results').innerHTML = '<div class="loading-card">Finding the experience in your network…</div>';
  try {
    const data = await api(`/api/network?q=${encodeURIComponent(query)}`);
    if (id !== networkSequence) return;
    state.network = data;
    const people = query ? data.matches : data.contacts.map(c => ({...c, reasons:[], reconnect:(Date.now()-new Date(c.last_contact))/86400000>=90}));
    $('#network-heading').textContent = query ? `${people.length} ${people.length === 1 ? 'path' : 'paths'} to context` : 'Your circle of context';
    $('#network-results').innerHTML = people.length ? people.map(c=>contactCard(c)).join('') : '<div class="empty-state"><h3>No match, and that’s useful too.</h3><p>Try a company ticker, a sector or a different theme. FINN will not invent expertise.</p></div>';
  } catch(e) {$('#network-results').innerHTML = `<div class="empty-state">${esc(e.message)}</div>`;}
}

function contactCard(c) {
  return `<article class="contact-card"><div class="contact-card-top"><span class="avatar">${esc(initials(c.name))}</span>${c.reconnect?'<span class="reconnect-tag">A reason to reconnect</span>':''}</div><h3>${esc(c.name)}</h3><p class="contact-title">${esc(c.title)}</p>${c.reasons?.length?`<p class="contact-reason">${esc(c.reasons[0])}</p>`:''}<div class="theme-tags">${c.themes.slice(0,3).map(t=>`<span>${esc(t)}</span>`).join('')}</div><button class="text-button" data-contact="${esc(c.id)}">Explore the connection ${icon('arrow')}</button><div class="last-contact"><span>Last spoke · ${esc(new Date(c.last_contact+'T00:00:00').toLocaleDateString('en-IN',{month:'short',day:'numeric',year:'numeric'}))}</span><button data-contacted="${esc(c.id)}">Spoke today ${icon('check')}</button></div></article>`;
}

async function showContact(id) {
  const context = state.route==='research' ? (state.report?.network || []) : state.route==='network' ? (state.network?.matches || []) : allItems().flatMap(i=>i.network);
  let person = [...context,...(state.network?.contacts || [])].find(c=>c.id===id);
  if (!person) { try { state.network = await api('/api/network'); person = state.network.contacts.find(c=>c.id===id); } catch(e) {toast(e.message);return;} }
  if (!person) return;
  const c = person;
  showDetail(`<div class="source-banner">SYNTHETIC PROFILE · No real person’s information</div><h2>${esc(c.name)}</h2><p>${esc(c.title)}</p><div class="theme-tags">${c.themes.map(t=>`<span>${esc(t)}</span>`).join('')}</div><div class="detail-section"><p class="eyebrow">THE EXPERIENCE BEHIND THE CONTEXT</p>${c.roles.map(r=>`<div class="career-row"><strong>${esc(r.title)}</strong> · ${esc(r.company)}<small>${r.start}–${r.end || 'present'}</small></div>`).join('')}<p>${esc(c.education)}</p></div>${c.reasons?.length?`<div class="detail-section"><p class="eyebrow">WHY THIS CONNECTION SURFACED</p>${c.reasons.map(r=>`<p>${esc(r)}</p>`).join('')}${c.path?.length?`<div class="network-path">${c.path.map(p=>`<span>${esc(p)}</span>`).join(' → ')}</div>`:''}</div>`:''}${Object.keys(c.knows).length?`<div class="detail-section"><p class="eyebrow">ATTESTED DEMO RELATIONSHIP</p>${Object.values(c.knows).map(v=>`<p>${esc(v)}</p>`).join('')}<p class="table-footnote">This relationship is explicitly seeded, not inferred from a shared employer.</p></div>`:''}<div class="detail-section"><p class="eyebrow">A THOUGHTFUL WAY TO RECONNECT</p><p>${esc(c.suggested_question || 'What has changed in your sector that the public numbers have not yet captured?')}</p><p class="table-footnote">Last contacted ${esc(c.last_contact)}. Use conversations for context on public information.</p><button class="primary-button" data-contacted="${esc(c.id)}">Mark as spoke today ${icon('check')}</button></div>`, 'YOUR NETWORK / CONNECTION NOTES');
}

async function markContacted(id) {
  const today = new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kolkata',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  try {await api(`/api/network/${encodeURIComponent(id)}/contacted`,{method:'POST',body:JSON.stringify({last_contact:today})});for(const c of [...(state.network?.contacts||[]),...(state.network?.matches||[]),...(state.report?.network||[]),...allItems().flatMap(i=>i.network)]){if(c.id===id){c.last_contact=today;c.reconnect=false;c.days_since_contact=0;}}if(state.route==='network')await loadNetwork($('#network-query').value);toast('Conversation date updated');if($('#detail-dialog').open)await showContact(id);} catch(e) {toast(e.message);}
}

function download(filename, content, type) { const url = URL.createObjectURL(new Blob([content],{type})); const link = document.createElement('a'); link.href = url; link.download = filename; document.body.append(link); link.click(); link.remove(); setTimeout(()=>URL.revokeObjectURL(url),1000); }

function exportReport() {
  const d = state.report; if(!d)return;
  const text = [`# ${d.name} (${d.symbol}) — FINN evidence brief`,d.period,`Question: ${d.question}`,`Engine: ${d.engine}`,'',...d.warnings.map(w=>`Limit: ${w}`),'',...d.facts.flatMap(f=>[`## ${f.heading}`,f.text,`Source: ${f.title} — ${f.locator}`,f.url,'']),'## Questions to investigate',...d.questions.map(q=>`- ${q}`),'','Network profiles in the app are synthetic. This brief is not an investment recommendation.'].join('\n');
  download(`FINN-${d.symbol}-brief.md`,text,'text/markdown;charset=utf-8');toast('Evidence brief downloaded');
}

document.addEventListener('click', async event => {
  const target = event.target.closest('button,a'); if(!target)return;
  if(target.dataset.save){await saveItem(target.dataset.save);return;}
  if(target.dataset.item){await showItem(target.dataset.item);return;}
  if(target.dataset.contact){await showContact(target.dataset.contact);return;}
  if(target.dataset.contacted){await markContacted(target.dataset.contacted);return;}
  if(target.dataset.goResearch){setResearch(target.dataset.goResearch);return;}
  if(target.dataset.research){setResearch(target.dataset.research);return;}
  if(target.dataset.theme){$('#network-query').value=target.dataset.theme;await loadNetwork(target.dataset.theme);return;}
  if(target.dataset.source){event.preventDefault();document.getElementById('source-'+target.dataset.source)?.scrollIntoView({behavior:'smooth',block:'center'});return;}
  if(target.dataset.filter){state.filter=target.dataset.filter;$$('[data-filter]').forEach(b=>{const active=b.dataset.filter===state.filter;b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));});renderBrief();return;}
  switch(target.dataset.action){
    case 'settings': await openSettings();break;
    case 'close-dialog': $('#detail-dialog').close();break;
    case 'close-settings': $('#settings-dialog').close();break;
    case 'refresh': if(['brief','saved'].includes(state.route))await loadBrief();else if(state.route==='network')await loadNetwork($('#network-query').value);else toast('Submit your question to refresh the evidence brief');break;
    case 'portfolio': portfolioDialog();break;
    case 'export-report':exportReport();break;
    case 'export-network':try{const data=await api('/api/network/export');download('finn-network.json',JSON.stringify(data,null,2),'application/json');toast('Synthetic network exported');}catch(e){toast(e.message);}break;
  }
});

$('#time-window').addEventListener('change',()=>loadBrief());
$('#data-mode').addEventListener('change',async()=>{state.mode=$('#data-mode').value;$('#research-mode').value=state.mode;notice();if(['brief','saved'].includes(state.route))await loadBrief();});
$('#research-form').addEventListener('submit',runResearch);
$('#network-form').addEventListener('submit',event=>{event.preventDefault();loadNetwork($('#network-query').value);});
$('#price-rule').addEventListener('input',updateRuleLabels);$('#volume-rule').addEventListener('input',updateRuleLabels);
$('#settings-form').addEventListener('submit',async event=>{event.preventDefault();const button=$('#save-settings');button.disabled=true;$('#settings-error').textContent='';try{await api('/api/settings',{method:'PUT',body:JSON.stringify({price_threshold:Number($('#price-rule').value),volume_threshold:Number($('#volume-rule').value),categories:$$('#category-options input:checked').map(i=>i.value)})});$('#settings-dialog').close();toast('Alert preferences saved');if(['brief','saved'].includes(state.route))await loadBrief({quiet:true});}catch(e){$('#settings-error').textContent=e.message;}finally{button.disabled=false;}});
$('#auth-dialog').addEventListener('cancel',event=>event.preventDefault());
$('#auth-form').addEventListener('submit',async event=>{event.preventDefault();state.token=$('#access-token').value;try{await api('/api/settings');sessionStorage.setItem('finn-token',state.token);$('#auth-dialog').close();$('#access-token').value='';$('#auth-error').textContent='';await route();}catch(e){state.token='';sessionStorage.removeItem('finn-token');$('#auth-error').textContent=e.message;}});
window.addEventListener('hashchange',()=>{route();window.scrollTo({top:0,behavior:'instant'});});
document.addEventListener('visibilitychange',()=>{if(!document.hidden&&state.mode==='live'&&['brief','saved'].includes(state.route))loadBrief({quiet:true});});

async function init() {
  const now = new Date();$('#date-day').textContent=now.toLocaleDateString('en-IN',{weekday:'long',timeZone:'Asia/Kolkata'});$('#date-full').textContent=now.toLocaleDateString('en-IN',{day:'numeric',month:'long',year:'numeric',timeZone:'Asia/Kolkata'});
  refreshTimer=setInterval(()=>{if(!document.hidden&&state.mode==='live'&&['brief','saved'].includes(state.route))loadBrief({quiet:true});},300000);
  try{const health=await api('/api/health');state.modelAvailable=health.model_available;$('#use-model').disabled=!health.model_available;$('#model-label').textContent=health.model_available?'· server configured':'· configure a server API key to enable';if(health.auth_required&&!state.token){$('#auth-dialog').showModal();return;}}catch(e){toast('The server is not reachable. Start FINN with python run.py.');}
  await route();
}
init();
