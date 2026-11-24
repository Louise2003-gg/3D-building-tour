// Fullscreen the app rather than the WebGL canvas so the elevator and touch pad remain usable.
export function installFullscreen(app,button,hint){
  const current=()=>document.fullscreenElement||document.webkitFullscreenElement;
  let timer;
  function sync(){
    const on=current()===app;
    button.textContent=on?'Exit fullscreen':'Fullscreen';
    button.setAttribute('aria-pressed',String(on));
    hint.hidden=true;
  }
  button.addEventListener('click',async()=>{
    try{
      if(current()===app)await (document.exitFullscreen||document.webkitExitFullscreen).call(document);
      else await (app.requestFullscreen||app.webkitRequestFullscreen).call(app);
    }catch{
      hint.textContent='Fullscreen is unavailable here. Open the tour in a browser window to use fullscreen.';
      hint.hidden=false;clearTimeout(timer);timer=setTimeout(()=>hint.hidden=true,5500);
    }
  });
  document.addEventListener('fullscreenchange',sync);
  document.addEventListener('webkitfullscreenchange',sync);
  sync();
}
