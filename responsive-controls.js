export function responsiveControls(){
  const toggle=document.querySelector('#view-menu'),options=document.querySelector('#view-options');
  const compact=matchMedia('(max-width:1180px), (max-height:500px)');
  function close(restore=false){
    if(restore&&options.contains(document.activeElement))toggle.focus();
    options.classList.remove('expanded');toggle.setAttribute('aria-expanded','false');
  }
  toggle.onclick=()=>{
    const open=options.classList.toggle('expanded');toggle.setAttribute('aria-expanded',String(open));
    if(open)[...options.querySelectorAll('button,select')].find(el=>el.getClientRects().length)?.focus();
  };
  options.addEventListener('click',e=>{if(e.target.closest('button'))close(compact.matches);});
  options.addEventListener('change',()=>close(compact.matches));
  document.addEventListener('pointerdown',e=>{if(!options.contains(e.target)&&!toggle.contains(e.target))close();});
  document.addEventListener('focusin',e=>{if(!options.contains(e.target)&&e.target!==toggle)close();});
  document.addEventListener('keydown',e=>{
    if(e.code==='Escape'&&options.classList.contains('expanded')){e.preventDefault();e.stopImmediatePropagation();close(true);}
  },true);
  compact.addEventListener('change',()=>close());
  return (walking,floor)=>{
    close();
    toggle.hidden=walking&&floor!=='third';
  };
}
