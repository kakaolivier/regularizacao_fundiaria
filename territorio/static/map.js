// Leaflet/Geoman run in the browser; validation, area calculations and persistence run in Python.
(() => {
  const exportJSON = (value, name) => { const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], {type:'application/geo+json'})); const a = document.createElement('a'); a.href=url; a.download=name+'.geojson'; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000); };
  document.querySelectorAll('[data-map]').forEach(root => {
    const config = JSON.parse(root.querySelector('.map-config').textContent);
    const map = L.map(root.querySelector('.map-canvas'), {zoomControl:false}).setView([-17.05,-50.15],8);
    map.pm.setLang('pt_br');
    L.control.zoom({position:'bottomright'}).addTo(map);
    const layers = L.featureGroup().addTo(map);
    const form = root.querySelector('[data-geometry-form]');
    const empty = root.querySelector('[data-map-empty]');
    const drawing = root.querySelector('[data-drawing]');
    const notice = root.querySelector('[data-map-notice]');
    let pending=null, active=null, editing=null, geometries=config.geometries;
    const showMessage = message => { notice.textContent=message; notice.hidden=false; };
    map.createPane('reference'); map.getPane('reference').style.zIndex='250';
    fetch('/maps/goias-municipios.geojson').then(r=>{if(!r.ok)throw Error();return r.json();}).then(geo=>{
      L.geoJSON(geo,{pane:'reference',pmIgnore:true,interactive:false,style:f=>({color:'#aebfa6',weight:.8,fillColor:['Aparecida de Goiânia','Trindade','Rio Verde','Jataí','Hidrolândia'].includes(f?.properties?.name)?'#c8dac0':'#e7eee0',fillOpacity:.55}),onEachFeature:(f,layer)=>{
        if(['Goiânia','Aparecida de Goiânia','Trindade','Rio Verde','Jataí','Hidrolândia'].includes(f.properties.name)){const label=document.createElement('span');label.textContent=f.properties.name;layer.bindTooltip(label,{permanent:true,direction:'center',className:'municipality-label'});}
      }}).addTo(map);map.attributionControl.addAttribution('Limites: IBGE / Geodata BR (CC0)');
    }).catch(()=>showMessage('Não foi possível carregar a camada municipal local.'));
    let tiles;
    root.querySelector('[data-streets]')?.addEventListener('click', e=>{
      const button=e.currentTarget;
      if(tiles&&map.hasLayer(tiles)){map.removeLayer(tiles);button.textContent='Carregar ruas';root.querySelector('[data-base-label]').textContent='Referência municipal';return;}
      tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a>'});
      tiles.on('tileerror',()=>{if(map.hasLayer(tiles))map.removeLayer(tiles);button.textContent='Carregar ruas';root.querySelector('[data-base-label]').textContent='Referência municipal';showMessage('Mapa de ruas indisponível nesta conexão. A camada municipal continua acessível.');});
      tiles.addTo(map);button.textContent='Ocultar ruas';root.querySelector('[data-base-label]').textContent='OpenStreetMap';
    });
    const fit=()=>layers.getLayers().length?map.fitBounds(layers.getBounds(),{padding:[35,35],maxZoom:18}):map.setView([-17.05,-50.15],8);
    root.querySelector('[data-fit]')?.addEventListener('click',fit);
    root.querySelector('[data-case-picker]')?.addEventListener('change',e=>{if(e.target.value)location.assign(e.target.value);});
    function cancel(){map.pm.disableDraw();if(active){map.removeLayer(active);active=null;}pending=null;editing=null;if(form){form.hidden=true;form.reset();}if(drawing)drawing.hidden=true;if(empty)empty.hidden=geometries.length>0;}
    function editGeometry(g){cancel();editing=g;form.elements.name.value=g.name;form.elements.kind.value=g.kind;if(form.elements.sourceId)form.elements.sourceId.value=g.sourceId||'';root.querySelector('[data-geometry-title]').textContent='Revisar geometria';active=L.geoJSON(g.feature,{style:{color:'#d4a044'}}).addTo(map);active.eachLayer(layer=>{layer.pm?.enable({allowSelfIntersection:false});layer.on('pm:edit',()=>pending=active.toGeoJSON().features[0]);});pending=g.feature;form.hidden=false;if(empty)empty.hidden=true;}
    function render(){
      layers.clearLayers();
      const list=root.querySelector('[data-geometries]');if(list)list.replaceChildren();
      geometries.forEach(g=>{
        const layer=L.geoJSON(g.feature,{style:{color:g.kind==='Limite do imóvel'?'#366e8b':'#228365',weight:2,fillOpacity:.22}});
        const popup=document.createElement('div');const title=document.createElement('strong');title.textContent=g.name;popup.append(title);const p=document.createElement('p');p.textContent=`${g.kind} · ${g.areaM2.toLocaleString('pt-BR',{maximumFractionDigits:2})} m²`;popup.append(p);
        const link=document.createElement('a');link.className='map-popup-button';link.href='/processos/'+encodeURIComponent(g.caseId)+'?tab=mapa';link.textContent='Abrir processo';popup.append(link);layer.bindPopup(popup);layers.addLayer(layer);
        if(list){const row=document.createElement('div');const span=document.createElement('span');const b=document.createElement('b');b.textContent=g.name;const small=document.createElement('small');small.textContent=`${g.kind} · ${g.areaM2.toLocaleString('pt-BR',{maximumFractionDigits:2})} m² · v${g.version}`;span.append(b,small);row.append(span);const edit=document.createElement('button');edit.className='icon-button';edit.textContent='✎';edit.setAttribute('aria-label','Editar '+g.name);edit.onclick=()=>editGeometry(g);const download=document.createElement('button');download.className='icon-button';download.textContent='↓';download.setAttribute('aria-label','Exportar '+g.name);download.onclick=()=>exportJSON(g.feature,g.name);row.append(edit,download);list.append(row);}
      });
      if(empty)empty.hidden=geometries.length>0;fit();
    }
    render();
    if(!form)return;
    root.querySelectorAll('[data-cancel-draw]').forEach(b=>b.addEventListener('click',cancel));
    root.querySelector('[data-draw]').addEventListener('click',()=>{cancel();if(empty)empty.hidden=true;drawing.hidden=false;root.querySelector('[data-geometry-title]').textContent='Vincular nova área';map.pm.enableDraw('Polygon',{allowSelfIntersection:false,pathOptions:{color:'#228365',fillOpacity:.2}});});
    map.on('pm:create',e=>{active=e.layer;pending=e.layer.toGeoJSON();form.hidden=false;drawing.hidden=true;e.layer.pm.enable({allowSelfIntersection:false});e.layer.on('pm:edit',()=>pending=e.layer.toGeoJSON());});
    root.querySelector('[data-geo-file]').addEventListener('change',async e=>{
      const file=e.target.files?.[0];if(!file)return;
      try{
        if(file.size>500000)throw Error('Limite de 500 KB por geometria.');const data=JSON.parse(await file.text());if(data.crs)throw Error('Use GeoJSON WGS84 (EPSG:4326).');const features=data.type==='FeatureCollection'?data.features:[data.type==='Feature'?data:{type:'Feature',properties:{},geometry:data}];
        if(!Array.isArray(features)||features.length!==1||!['Polygon','MultiPolygon'].includes(features[0].geometry?.type))throw Error('Importe uma área por vez: Polygon ou MultiPolygon.');
        cancel();pending=features[0];active=L.geoJSON(pending,{style:{color:'#228365'}}).addTo(map);map.fitBounds(active.getBounds(),{maxZoom:18});form.elements.name.value=file.name.replace(/\.[^.]+$/,'');form.hidden=false;if(empty)empty.hidden=true;root.querySelector('[data-geometry-title]').textContent='Vincular nova área';
      }catch(error){window.notify(error.message,true);}finally{e.target.value='';}
    });
    form.addEventListener('submit',async e=>{
      e.preventDefault();const button=form.querySelector('[type=submit]');button.disabled=true;
      try{
        const values=Object.fromEntries(new FormData(form));const response=await fetch(`/api/cases/${encodeURIComponent(config.caseId)}/geometries`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...values,feature:pending,...(editing?{id:editing.id,version:editing.version}:{})})});const result=await response.json();if(!response.ok)throw Error(result.error||'Não foi possível salvar a área.');
        geometries=geometries.filter(g=>g.id!==result.id);geometries.push(result);cancel();render();window.notify('Área salva e vinculada ao processo.');
      }catch(error){window.notify(error.message,true);}finally{button.disabled=false;}
    });
  });
})();
