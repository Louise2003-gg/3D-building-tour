// Some mobile browsers disable WebGL. Keep floor navigation useful on those devices too.
import('./reference-viewer.js').catch(err=>{
  if(!/WebGL.*context|creating.*context/i.test(String(err))){
    document.querySelector('#loading').textContent='The tour could not start. Please refresh to retry.';console.error(err);return;
  }
  const app=document.querySelector('.app'),host=document.querySelector('#viewer'),floor=document.querySelector('#floor');
  const previews={
    first:['Store & nursery',new URL('./models/Atrium/Architectural/Reception.png',import.meta.url)],
    second:['Print, study & dining',new URL('./models/Atrium/Architectural/Workstations.png',import.meta.url)],
    third:['Locker gallery',new URL('./models/Atrium/Gallery/Locker_gallery.png',import.meta.url)],
    building:['Atrium Building',new URL('./models/Atrium/Atrium_Building_preview.png',import.meta.url)]
  };
  app.classList.add('preview-mode');
  const image=new Image(),caption=document.createElement('p');
  caption.textContent='Floor previews · Interactive walking requires WebGL 2.';
  host.replaceChildren(image,caption);
  function show(){
    const [title,url]=previews[floor.value];image.src=url;image.alt=title+' architectural render';
    document.querySelector('h1').textContent=title;document.querySelector('.eyebrow').textContent='BUILDING PREVIEWS';
  }
  floor.value=new URLSearchParams(location.search).has('visit')?'third':'building';
  floor.onchange=show;show();document.querySelector('#loading').hidden=true;
});
