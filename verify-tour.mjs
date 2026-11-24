// Integration check against a running viewer. Set CHROME_PATH to use another Chromium binary.
import {spawn} from 'node:child_process';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import assert from 'node:assert/strict';
const profile=await mkdtemp(join(tmpdir(),'atrium-tour-'));
const chrome=spawn(process.env.CHROME_PATH||'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  ['--headless=new','--no-first-run','--disable-extensions','--enable-unsafe-swiftshader','--remote-debugging-pipe',`--user-data-dir=${profile}`],
  {stdio:['ignore','ignore','ignore','pipe','pipe']});
const pending=new Map(),errors=[];let id=0,buffer='';
chrome.stdio[4].setEncoding('utf8').on('data',data=>{
  buffer+=data;let end;
  while((end=buffer.indexOf('\0'))>=0){
    const msg=JSON.parse(buffer.slice(0,end));buffer=buffer.slice(end+1);
    if(msg.method==='Runtime.exceptionThrown')errors.push(msg.params.exceptionDetails.exception?.description||msg.params.exceptionDetails.text);
    if(msg.method==='Runtime.consoleAPICalled'&&msg.params.type==='error')errors.push(msg.params.args.map(a=>a.value||a.description).join(' '));
    if(pending.has(msg.id)){pending.get(msg.id)(msg);pending.delete(msg.id);}
  }
});
function send(method,params={},sessionId){
  return new Promise((resolve,reject)=>{
    const n=++id,timer=setTimeout(()=>reject(Error(method+' timed out')),45000);
    pending.set(n,m=>{clearTimeout(timer);if(m.error)reject(Error(m.error.message));else resolve(m.result);});
    chrome.stdio[3].write(JSON.stringify({id:n,method,params,sessionId})+'\0');
  });
}
try{
  const {targetId}=await send('Target.createTarget',{url:'about:blank'});
  const {sessionId}=await send('Target.attachToTarget',{targetId,flatten:true});
  const page=(m,p)=>send(m,p,sessionId);
  await page('Runtime.enable');
  await page('Emulation.setDeviceMetricsOverride',{width:1440,height:900,deviceScaleFactor:1.5,mobile:false});
  await page('Page.navigate',{url:(process.argv[2]||'http://127.0.0.1:4196/')+'?tour=1&stats'});
  async function ev(expression){
    const r=await page('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true,userGesture:true});
    if(r.exceptionDetails)throw Error(r.exceptionDetails.exception?.description||r.exceptionDetails.text);
    return r.result.value;
  }
  await ev(`new Promise(r=>{function check(){if(window.atriumStats&&document.querySelector('#loading.hidden'))r(true);else requestAnimationFrame(check)}check()})`);
  async function toggle(){
    return ev(`new Promise((resolve,reject)=>{const tm=setTimeout(()=>reject(Error('fullscreenchange missing')),3000);
      document.addEventListener('fullscreenchange',()=>{clearTimeout(tm);resolve(!!document.fullscreenElement)},{once:true});document.querySelector('#fullscreen').click()})`);
  }
  assert.equal(await toggle(),true);
  const sample=await ev(`(async()=>{let n=0,extra=0,prev;const start=window.atriumStats.position.slice();
    window.dispatchEvent(new KeyboardEvent('keydown',{code:'KeyW'}));
    try{await new Promise((resolve,reject)=>{const tm=setTimeout(()=>reject(Error('walk stalled')),18000);
      function sample(){const s=window.atriumStats;if(s!==prev&&s.motion){prev=s;n++;extra+=Number(s.reflectionPass)}
        if(n>=10){clearTimeout(tm);resolve()}else requestAnimationFrame(sample)}sample()});
    }finally{window.dispatchEvent(new KeyboardEvent('keyup',{code:'KeyW'}))}
    const end=window.atriumStats.position,c=document.querySelector('canvas');
    return {motionFrames:n,extraReflectionPasses:extra,metres:Math.hypot(end[0]-start[0],end[2]-start[2]),pixelRatio:window.atriumStats.pixelRatio,native:devicePixelRatio};})()`);
  assert.equal(sample.extraReflectionPasses,0);assert.ok(sample.metres>.05);assert.equal(sample.pixelRatio,sample.native);
  assert.equal(await toggle(),false);
  assert.equal(await ev(`document.body.classList.contains('walking')`),true);
  for(const key of ['first','second','third']){
    const size=await ev(`(async()=>{const f=document.querySelector('#floor');f.value='${key}';await f.onchange();
      const c=document.querySelector('canvas');return [!document.querySelector('#loading').classList.contains('error'),c.width,c.height,Math.floor(c.clientWidth*devicePixelRatio),Math.floor(c.clientHeight*devicePixelRatio)]})()`);
    assert.ok(size[0]);assert.deepEqual(size.slice(1,3),size.slice(3));
  }
  console.log('Fullscreen entry/exit and walking passed:',sample);
  // Start a true touch session so that initial texture selection and gesture handling also run.
  await page('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:5});
  await page('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:2,mobile:true});
  await page('Page.navigate',{url:(process.argv[2]||'http://127.0.0.1:4196/')+'?visit=lockers&stats'});
  const waitPage=code=>ev(`new Promise((resolve,reject)=>{const tm=setTimeout(()=>reject(Error('Timed out: '+${JSON.stringify(code)})),28000);function test(){if(${code}){clearTimeout(tm);resolve(true)}else requestAnimationFrame(test)}test()})`);
  await waitPage(`window.atriumStats?.locker && document.querySelector('#loading.hidden') && !document.querySelector('#locker-action').hidden`);
  async function point(selector){
    return ev(`(()=>{const r=document.querySelector(${JSON.stringify(selector)}).getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()`);
  }
  async function touch(selector){
    await page('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[await point(selector)]});
    await page('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  }
  await touch('#locker-action');
  await waitPage('window.atriumStats.locker.angle>1.3');
  await page('Input.dispatchKeyEvent',{type:'keyDown',key:'e',code:'KeyE'});
  await page('Input.dispatchKeyEvent',{type:'keyUp',key:'e',code:'KeyE'});
  await waitPage('window.atriumStats.locker.id===0');
  const before=await ev('window.atriumStats.position');
  await page('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[await point('[data-step=KeyS]')]});
  try{await waitPage(`Math.abs(window.atriumStats.position[2]-(${before[2]}))>.1`);}
  finally{await page('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});}
  for(const [width,height] of [[320,568],[844,390],[768,1024],[1024,768],[1440,900]]){
    await page('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<1200});
    await waitPage(`document.querySelector('canvas').width===${width}&&document.querySelector('canvas').height===${height}`);
    const clipped=await ev(`(()=>{let bad=[];for(let e of document.querySelectorAll('.topbar button,.topbar select,.tour-guide,.step-pad button')){
      if(!e.getClientRects().length)continue;const r=e.getBoundingClientRect();if(r.left<-.5||r.right>innerWidth+.5||r.top<0||r.bottom>innerHeight+.5)bad.push(e.id||e.textContent)
    }return bad})()`);
    assert.deepEqual(clipped,[],`Clipped controls at ${width}×${height}`);
    if(width<=1180){
      await touch('#view-menu');assert.equal(await ev(`document.querySelector('#view-menu').getAttribute('aria-expanded')`),'true');
      assert.equal(await ev(`document.querySelector('#visit-gallery').getBoundingClientRect().height>=44`),true);
      await touch('#visit-gallery');await waitPage(`!document.querySelector('#view-options').classList.contains('expanded')&&document.querySelector('#loading.hidden')`);
    }
  }
  console.log('Locker opening/closing, touch movement and five viewport layouts passed.');
  assert.deepEqual(errors,[],'The tour reported a script or WebGL shader error: '+errors.join('\n').slice(0,4000));
}finally{
  const closed=new Promise(r=>chrome.once('exit',r));chrome.kill();await closed;
  await rm(profile,{recursive:true,force:true,maxRetries:5,retryDelay:200});
}
