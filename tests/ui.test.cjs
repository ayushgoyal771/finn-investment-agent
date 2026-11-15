// DOM integration tests only. No browser, network, layout engine or screenshots.
const {test,before} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const {JSDOM,VirtualConsole} = require('jsdom');
const root = path.resolve(__dirname,'..');
let fixtures;
before(() => {
  const local = path.join(root,process.platform==='win32'?'.venv/Scripts/python.exe':'.venv/bin/python');
  const python = process.env.FINN_PYTHON || (fs.existsSync(local)?local:'python');
  const result = spawnSync(python,['scripts/ui_fixtures.py'],{cwd:root,encoding:'utf8'});
  assert.equal(result.status,0,result.stderr);
  fixtures = JSON.parse(fs.readFileSync(path.join(root,'artifacts/ui-fixtures.json'),'utf8'));
});
const tick = () => new Promise(resolve=>setImmediate(resolve));
async function settled(){for(let i=0;i<5;i++)await tick();}

async function setup(options={}) {
  const errors=[],calls=[];
  const virtualConsole=new VirtualConsole();
  virtualConsole.on('jsdomError',e=>errors.push(e.message));
  const dom=new JSDOM(fs.readFileSync(path.join(root,'frontend/index.html'),'utf8'),{
    url:'http://finn.test/',runScripts:'outside-only',virtualConsole,pretendToBeVisual:true
  });
  const w=dom.window;
  w.Headers=Headers;w.AbortSignal=AbortSignal;w.scrollTo=()=>{};
  w.HTMLElement.prototype.scrollIntoView=()=>{};
  w.HTMLDialogElement.prototype.showModal=function(){this.open=true;};
  w.HTMLDialogElement.prototype.close=function(){this.open=false;};
  w.fetch=async(url,config={})=>{
    assert.ok(url.startsWith('/api/'),'UI test attempted an external fetch');
    calls.push({url,method:config.method||'GET',body:config.body?JSON.parse(config.body):null});
    let body,status=200;
    if(url==='/api/health')body={status:'ok',model_available:false,auth_required:!!options.auth};
    else if(options.fail && url.startsWith('/api/brief')){body={detail:'Provider test failure <script>alert(1)</script>'};status=503;}
    else if(options.auth && !config.headers?.get('Authorization')){body={detail:'Enter a token'};status=401;}
    else if(url.startsWith('/api/brief'))body=structuredClone(fixtures.brief);
    else if(url==='/api/settings')body=structuredClone(fixtures.settings);
    else if(url==='/api/research')body=structuredClone(fixtures.research);
    else if(url.startsWith('/api/network'))body=structuredClone(fixtures.network);
    else if(url.startsWith('/api/items/'))body={ok:true};
    else throw new Error('Unexpected API path: '+url);
    if(options.mutate)options.mutate(body,url);
    return{ok:status<400,status,json:async()=>body};
  };
  w.eval(fs.readFileSync(path.join(root,'frontend/app.js'),'utf8'));
  await settled();
  return {dom,w,document:w.document,calls,errors};
}

test('brief renders real API contract and opens the second-degree workflow',async t=>{
  const ctx=await setup();t.after(()=>ctx.dom.window.close());
  const d=ctx.document;
  assert.equal(d.querySelectorAll('.signal-card').length,fixtures.brief.priority.length);
  d.querySelector('[data-item="demo-pi-cfo"]').click();await settled();
  assert.equal(d.querySelector('#detail-dialog').open,true);
  assert.match(d.querySelector('#dialog-body').textContent,/Rohan Desai/);
  assert.match(d.querySelector('.network-path').textContent,/You.*Meera Shah.*Rohan Desai/);
  assert.ok(ctx.calls.some(c=>c.method==='PATCH'&&c.body.seen));
  assert.deepEqual(ctx.errors,[]);
});

test('bookmark, category filter and saved route are wired',async t=>{
  const ctx=await setup();t.after(()=>ctx.dom.window.close());const d=ctx.document;
  d.querySelector('[data-save="demo-pi-cfo"]').click();await settled();
  assert.equal(d.querySelector('[data-save="demo-pi-cfo"]').getAttribute('aria-pressed'),'true');
  d.querySelector('[data-filter="market"]').click();await settled();
  assert.equal(d.querySelectorAll('.signal-card').length,fixtures.brief.priority.filter(i=>i.category==='market').length);
  ctx.w.location.hash='saved';await settled();
  assert.ok(ctx.calls.some(c=>c.url.includes('saved=true')));
});

test('results detail shows all four financial comparisons',async t=>{
  const ctx=await setup();t.after(()=>ctx.dom.window.close());
  ctx.document.querySelector('[data-item="demo-asian-results"]').click();await settled();
  const table=ctx.document.querySelector('#dialog-body table');assert.ok(table);
  assert.equal(table.querySelectorAll('tbody tr').length,4);
  assert.match(table.textContent,/Revenue.*EBITDA.*PBT.*PAT/s);
  assert.match(table.textContent,/-2.2%/);
});

test('research submits the selected ticker and displays citations plus network',async t=>{
  const ctx=await setup();t.after(()=>ctx.dom.window.close());const d=ctx.document;
  ctx.w.location.hash='research';await settled();
  d.querySelector('#research-form').dispatchEvent(new ctx.w.Event('submit',{bubbles:true,cancelable:true}));await settled();
  assert.ok(ctx.calls.some(c=>c.url==='/api/research'&&c.body.symbol==='ASIANPAINT'&&c.body.mode==='demo'));
  assert.ok(d.querySelectorAll('.evidence-card').length);
  assert.ok(d.querySelectorAll('.source-link').length);
  assert.equal(d.querySelectorAll('.metric-card a')[2].textContent, 'Call transcript ↗');
  assert.match(d.querySelector('.research-side').textContent,/Vikram/);
  assert.deepEqual(ctx.errors,[]);
});

test('network theme search and contact details work',async t=>{
  const ctx=await setup();t.after(()=>ctx.dom.window.close());const d=ctx.document;
  ctx.w.location.hash='network';await settled();
  assert.equal(d.querySelectorAll('.contact-card').length,8);
  d.querySelector('[data-theme="semiconductors"]').click();await settled();
  assert.ok(ctx.calls.some(c=>c.url.includes('q=semiconductors')));
  d.querySelector('[data-contact="sana"]').click();await settled();
  assert.match(d.querySelector('#dialog-body').textContent,/DIXON/);
  assert.match(d.querySelector('#dialog-body').textContent,/SYNTHETIC PROFILE/);
});

test('alert settings save selected thresholds and categories',async t=>{
  const ctx=await setup();t.after(()=>ctx.dom.window.close());const d=ctx.document;
  d.querySelector('[data-action="settings"]').click();await settled();
  assert.equal(d.querySelector('#settings-dialog').open,true);
  d.querySelector('#price-rule').value='7';d.querySelector('#volume-rule').value='4';
  d.querySelector('#settings-form').dispatchEvent(new ctx.w.Event('submit',{bubbles:true,cancelable:true}));await settled();
  assert.ok(ctx.calls.some(c=>c.method==='PUT'&&c.body.price_threshold===7&&c.body.volume_threshold===4));
  assert.equal(d.querySelector('#settings-dialog').open,false);
});

test('source failure is visible and error strings remain text',async t=>{
  const ctx=await setup({fail:true});t.after(()=>ctx.dom.window.close());
  assert.match(ctx.document.querySelector('#signal-feed').textContent,/Provider test failure/);
  assert.equal(ctx.document.querySelector('#signal-feed script'),null);
});

test('external source and person text cannot inject HTML',async t=>{
  const ctx=await setup({mutate:(data,url)=>{if(url.startsWith('/api/brief'))data.priority[0].title='<img src=x onerror=alert(1)>';}});
  t.after(()=>ctx.dom.window.close());
  assert.match(ctx.document.querySelector('.signal-title').textContent,/<img/);
  assert.equal(ctx.document.querySelector('.signal-title img'),null);
});

test('remote access prompts for configured server token',async t=>{
  const ctx=await setup({auth:true});t.after(()=>ctx.dom.window.close());
  assert.equal(ctx.document.querySelector('#auth-dialog').open,true);
  assert.ok(!ctx.calls.some(c=>c.url.startsWith('/api/brief')));
});

test('changing source mode clears the previous prices while a new brief loads',async t=>{
  const ctx=await setup();t.after(()=>ctx.dom.window.close());const d=ctx.document;
  assert.match(d.querySelector('#radar-list').textContent,/₹/);
  d.querySelector('#data-mode').value='live';
  d.querySelector('#data-mode').dispatchEvent(new ctx.w.Event('change',{bubbles:true}));
  assert.equal(d.querySelector('#radar-list').textContent,'');
  assert.equal(d.querySelector('#brief-stats').textContent,'');
  assert.match(d.querySelector('#signal-feed').textContent,/Preparing your fieldnotes/);
  await settled();
});
