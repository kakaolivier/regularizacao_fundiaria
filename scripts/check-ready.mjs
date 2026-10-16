import assert from 'node:assert/strict';
const base=process.env.CHECK_URL||'http://127.0.0.1:3000';
const request=async p=>{const r=await fetch(base+p);assert.ok(r.ok,`${p}: HTTP ${r.status}`);return r;};
const health=await (await request('/api/health')).json();assert.equal(health.ok,true);
const data=await (await request('/api/bootstrap')).json();assert.ok(Array.isArray(data.cases));assert.equal(health.cases,data.cases.length);
const html=await (await request('/')).text();assert.ok(html.includes('Território'));const script=html.match(/src="([^\"]+\.js)"/);if(script)await request(script[1]);
if(data.cases.length){const item=await (await request(`/api/cases/${data.cases[0].id}`)).json();assert.ok(Array.isArray(item.sources));assert.ok(Array.isArray(item.events));assert.ok(Array.isArray(item.documents));}
const map=await (await request('/maps/goias-municipios.geojson')).json();assert.equal(map.type,'FeatureCollection');assert.equal(map.features.length,246);
console.log(`READY: interface, assets, API, ${data.cases.length} cadastros, ${data.meta.summary?.records||0} registros de origem e mapa municipal local.`);
