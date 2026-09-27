// 线上实跑一条 hitl 链并逐帧截图：npm i puppeteer-core 后 node capture_demo.mjs（默认打开线上站，URL 环境变量可改）。
import puppeteer from 'puppeteer-core';
import fs from 'fs';
const URL = process.env.URL || 'https://liangyi-five.vercel.app/';
const b = await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless:true, args:['--no-first-run','--lang=zh-CN']});
const p = await b.newPage();
await p.setViewport({width:1200, height:2600, deviceScaleFactor:2});
await p.goto(URL, {waitUntil:'networkidle0'});
const log = []; let n = 0; const t0 = Date.now();
const sec = () => Math.round((Date.now()-t0)/1000);
const rect = sel => p.evaluate(s => { const e=document.querySelector(s); if(!e) return null; const r=e.getBoundingClientRect(); return {top:r.top+scrollY, h:r.height}; }, sel);
async function frame(mode, anchorSel, before=420) {
  await p.evaluate(()=>window.scrollTo({top:0, behavior:'instant'}));
  let y;
  if (mode==='progress') {
    // 默认从输入框往下拍；进行到的步骤滑出画面时（第 2 轮），镜头跟着往下走
    y = (await rect('#seed')).top - 30;
    const cur = await p.evaluate(() => { const e = document.querySelector('.step.doing, .step.await') || [...document.querySelectorAll('.step.done')].pop();
      if (!e) return null; const r = e.getBoundingClientRect(); return {top: r.top + scrollY, h: r.height}; });
    if (cur && cur.top + cur.h > y + 1120) y = cur.top + cur.h - 1120;
  }
  else { const r = await rect(anchorSel); y = Math.max(0, r.top - before); }
  n++; const f = `frames/${String(n).padStart(4,'0')}.png`;
  await p.screenshot({path:f, clip:{x:0, y, width:1200, height:1200}});
  const st = await p.evaluate(()=>({step:document.querySelector('#s-step')?.textContent, time:document.querySelector('#s-time')?.textContent, cost:document.querySelector('#s-cost')?.textContent, state}));
  log.push({n, f, mode, t:sec(), ...st});
  fs.writeFileSync('frames.json', JSON.stringify(log, null, 1));
}
const on = sel => p.evaluate(s => document.querySelector(s)?.classList.contains('on'), sel);
// 准备：填示例、选 hitl
await frame('progress');
await (await p.$$('.chip'))[0].click(); await new Promise(r=>setTimeout(r,600));
for (let k=0;k<3;k++) await frame('progress');
await p.evaluate(()=>document.querySelector('.tier input[value=hitl]').closest('label').click());
for (let k=0;k<3;k++) await frame('progress');
await p.click('#go');
let decisions = 0, retries = 0, done = false;
const deadline = Date.now() + 30*60*1000;
while (Date.now() < deadline) {
  await new Promise(r=>setTimeout(r,4000));
  if (await on('#result')) { for (let k=0;k<6;k++) await frame('result', '#result', 260);
    await (await p.$('#result')).screenshot({path:'stills/result.png'}); done = true; break; }
  if (await on('#err')) {
    const m = await p.evaluate(()=>document.querySelector('#err').textContent);
    console.log('ERR', sec(), m); await frame('progress');
    if (/429|次数|上限|limit/i.test(m) || retries >= 2) break;
    retries++; await p.click('#go'); continue;
  }
  if (await on('#decide')) {
    decisions++;
    await new Promise(r=>setTimeout(r,1500));
    const pos = await p.evaluate(()=>awaiting?.position);
    console.log('DECIDE', sec(), pos);
    await p.evaluate(()=>window.scrollTo({top:0, behavior:'instant'}));
    await (await p.$('#decide')).screenshot({path:`stills/decide-${pos}.png`});
    for (let k=0;k<8;k++) await frame('decide', '#decide', 380);
    await p.click('#d-go');   // 第一项「接受」默认选中
    continue;
  }
  await frame('progress');
}
console.log(JSON.stringify({done, decisions, retries, frames:n, secs:sec(), final: log.at(-1)}));
await p.evaluate(()=>window.scrollTo({top:0, behavior:'instant'}));
await p.screenshot({path:'stills/page-end.png', fullPage:true});
await b.close();
