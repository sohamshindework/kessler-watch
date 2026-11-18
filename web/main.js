import './style.css';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import * as satellite from 'satellite.js';
const $ = id => document.getElementById(id);
let data, selected, points, highlight, records=[], timeOffset=0;
const host=$('globe'), scene=new THREE.Scene(), camera=new THREE.PerspectiveCamera(38,1,.01,100);
camera.position.set(0,1.3,4.4);
let renderer;
try { renderer=new THREE.WebGLRenderer({antialias:true,alpha:true}); renderer.setPixelRatio(Math.min(devicePixelRatio,2)); host.prepend(renderer.domElement); }
catch { const note=document.createElement('p');note.className='empty';note.textContent='The 3D view needs WebGL. Catalogue and encounter data are still available below.';host.append(note); }
const earth=new THREE.Group(); scene.add(earth);
const globe=new THREE.Mesh(new THREE.SphereGeometry(1,64,48),new THREE.MeshPhongMaterial({color:0x122839,emissive:0x06111c,shininess:20,transparent:true,opacity:.95}));earth.add(globe);
const grid=new THREE.LineSegments(new THREE.WireframeGeometry(new THREE.SphereGeometry(1.002,40,22)),new THREE.LineBasicMaterial({color:0x33566e,transparent:true,opacity:.15}));earth.add(grid);
scene.add(new THREE.AmbientLight(0x819ab6,1.4));const sun=new THREE.DirectionalLight(0xbbd7e9,2);sun.position.set(5,3,5);scene.add(sun);
const atmosphere=new THREE.Mesh(new THREE.SphereGeometry(1.025,48,32),new THREE.MeshBasicMaterial({color:0x467ca0,transparent:true,opacity:.07,side:THREE.BackSide}));earth.add(atmosphere);
// Simplified continent outlines, intentionally a lightweight orientation aid.
const outlines=[[-168,65,-145,70,-125,60,-128,48,-122,35,-105,22,-88,20,-80,27,-67,45,-52,50,-60,62,-85,70,-115,73,-168,65],[-81,10,-70,12,-51,1,-35,-8,-43,-24,-55,-52,-70,-55,-76,-25,-81,10],[-18,35,10,37,34,31,51,12,43,-12,32,-30,18,-35,9,-20,-4,4,-18,16,-18,35],[-10,36,-10,58,10,70,40,69,70,75,110,74,160,60,180,65,160,45,140,36,120,22,105,4,80,8,70,25,45,30,35,42,15,45,-10,36],[112,-11,135,-12,153,-26,146,-39,122,-35,112,-22,112,-11],[-55,60,-43,60,-20,78,-40,83,-60,75,-55,60]];
function ll(lon,lat,r=1.006){let a=lat*Math.PI/180,b=lon*Math.PI/180;return new THREE.Vector3(r*Math.cos(a)*Math.cos(b),r*Math.sin(a),-r*Math.cos(a)*Math.sin(b));}
for(const outline of outlines){const vertices=[];for(let i=0;i<outline.length;i+=2)vertices.push(ll(outline[i],outline[i+1]));earth.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(vertices),new THREE.LineBasicMaterial({color:0x668f9c,transparent:true,opacity:.65})));}
const stars=[];let seed=42;function random(){seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;}for(let i=0;i<900;i++){const v=new THREE.Vector3(random()-.5,random()-.5,random()-.5).normalize().multiplyScalar(15);stars.push(v.x,v.y,v.z);}const starGeo=new THREE.BufferGeometry();starGeo.setAttribute('position',new THREE.Float32BufferAttribute(stars,3));scene.add(new THREE.Points(starGeo,new THREE.PointsMaterial({size:.015,color:0x8da2b8,transparent:true,opacity:.5})));
const controls=renderer?new OrbitControls(camera,renderer.domElement):null;
if(controls){controls.enableDamping=true;controls.enablePan=false;controls.minDistance=2;controls.maxDistance=10;controls.autoRotate=true;controls.autoRotateSpeed=.3;}
function resize(){camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();renderer?.setSize(host.clientWidth,host.clientHeight);}new ResizeObserver(resize).observe(host);
$('rotate').onclick=()=>{if(!controls)return;controls.autoRotate=!controls.autoRotate;$('rotate').setAttribute('aria-pressed',String(controls.autoRotate));$('rotate').textContent=controls.autoRotate?'Ⅱ':'▶';};
$('reset').onclick=()=>{camera.position.set(0,1.3,4.4);controls?.target.set(0,0,0);};
function toView(p){return [p.x/6371,p.z/6371,-p.y/6371];}
function plot(){if(!data)return;const date=new Date(Date.now()+timeOffset*3600000),coords=[];
for(const r of records){try{const result=satellite.propagate(r.sat,date);if(result.position&&Number.isFinite(result.position.x))coords.push(...toView(result.position));}catch{/* Invalid or decayed orbits are omitted. */}}
if(points){points.geometry.dispose();points.material.dispose();scene.remove(points);}const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(coords,3));points=new THREE.Points(geo,new THREE.PointsMaterial({size:.012,color:0xb9ef79,transparent:true,opacity:.8,sizeAttenuation:true}));scene.add(points);
// TEME is inertial; rotate only Earth to approximate terrestrial orientation.
earth.rotation.y=satellite.gstime(date);
$('position-label').textContent=`${coords.length/3} propagated positions · TEME`;
$('view-time').textContent=timeOffset?`+${timeOffset} H`:'NOW';}
$('time').oninput=e=>{timeOffset=Number(e.target.value);plot();};
function text(tag,cls,value){const e=document.createElement(tag);e.className=cls;e.textContent=value;return e;}
function showEvents(){const query=$('search').value.toLowerCase();let events=data.events.filter(e=>`${e.primaryName} ${e.secondaryName} ${e.primary} ${e.secondary}`.toLowerCase().includes(query));events.sort((a,b)=>$('sort').value==='time'?new Date(a.tca)-new Date(b.tca):a.missDistanceKm-b.missDistanceKm);$('encounters').replaceChildren();$('list-count').textContent=`/ ${events.length}`;
for(const event of events){const button=text('button','encounter'+(event.id===selected?.id?' selected':''),'');const left=text('div','names',event.primaryName);left.append(text('span','',`↳ ${event.secondaryName}`),text('small','',`${new Date(event.tca).toISOString().replace('T',' ').slice(0,16)} UTC`));const right=text('div','distance',event.missDistanceKm.toFixed(2));right.append(text('span','',' km'));button.append(left,right);button.onclick=()=>selectEvent(event);$('encounters').append(button);}
if(!events.length)$('encounters').append(text('div','empty',query?'No encounters match your search.':'No approaches within 10 km were found in this screening run. This is not a guarantee of safe separation.'));}
function selectEvent(event){selected=event;showEvents();const detail=$('detail');detail.replaceChildren();const left=text('div','','');left.append(text('span','eyebrow','ENCOUNTER INSPECTOR / PUBLIC ELEMENTS'),text('h2','',`${event.primaryName} × ${event.secondaryName}`),text('p','',`NORAD ${event.primary} / ${event.secondary} · ${new Date(event.tca).toUTCString()}`));const stats=text('div','detail-stats','');for(const [name,value] of [['MISS DISTANCE',`${event.missDistanceKm.toFixed(3)} km`],['RELATIVE SPEED',`${event.relativeSpeedKms.toFixed(2)} km/s`],['COLLISION PROBABILITY','Unavailable']]){const col=text('div','','');col.append(text('span','',name),text('strong','',value));stats.append(col);}detail.append(left,stats);
const lead=(new Date(event.tca)-Date.now())/1000;if(lead>0){const lower=Math.max(0,10-event.missDistanceKm)*1000/lead;left.append(text('p','',`Toy displacement estimate to 10 km: ≥ ${lower.toPrecision(3)} m/s over ${(lead/3600).toFixed(1)} h. Straight-line lower bound only; not a manoeuvre solution.`));}
if(highlight){scene.remove(highlight);highlight.geometry.dispose();highlight.material.dispose();}const p=event.positionTemeKm;highlight=new THREE.Mesh(new THREE.SphereGeometry(.035,16,16),new THREE.MeshBasicMaterial({color:0xffab6b}));highlight.position.set(...toView({x:p[0],y:p[1],z:p[2]}));scene.add(highlight);}
$('search').oninput=()=>data&&showEvents();$('sort').onchange=()=>data&&showEvents();
async function load(){try{$('status').textContent='UPDATING CATALOGUE';const response=await fetch(`${import.meta.env.BASE_URL}data/latest.json?t=${Date.now()}`);if(!response.ok)throw Error(`Snapshot HTTP ${response.status}`);data=await response.json();records=data.objects.flatMap(object=>{try{return [{sat:satellite.json2satrec(object.omm)}];}catch{return [];}});$('object-count').textContent=data.catalogueCount.toLocaleString();$('screened-count').textContent=data.screenedCount.toLocaleString();$('event-count').textContent=data.events.length;$('horizon').textContent=`${data.horizonDays} days`;$('catalogue-label').textContent=`CelesTrak · ${data.catalogueGroup} catalogue`;$('coverage-label').textContent=`${(data.screenedCount/data.catalogueCount*100).toFixed(1)}% of this snapshot`;
const age=(Date.now()-new Date(data.generatedAt))/3600000;$('status').textContent=data.mode==='demo'?'DEMONSTRATION DATA':age>36?'STALE SNAPSHOT':'PUBLIC CATALOGUE';$('data-mode').textContent=data.mode==='demo'?'DEMO / NOT LIVE':age>36?'STALE DATA':'SGP4 / LIVE POSITIONS';$('updated').textContent=`Snapshot ${new Date(data.generatedAt).toUTCString()}`;
$('screen-note').textContent=`${data.coverage.stepSeconds}s grid; ${data.coverage.candidateRadiusKm} km candidate radius. ${data.coverage.failedObjectSamples} failed propagation samples.`;
if(data.forecast.status==='evaluated')$('forecast-state').textContent=`Held-out public-element consistency RMSE: SGP4 ${data.forecast.baselineRmseKm.toFixed(2)} km; ridge correction ${data.forecast.modelRmseKm.toFixed(2)} km. ${data.forecast.testSamples} test samples. This is not position ground truth.`;
else $('forecast-state').textContent=`Baseline status: ${data.forecast.status.replaceAll('-',' ')}. Daily history is accumulating; no improvement is claimed before a held-out evaluation.`;
$('manoeuvre-state').textContent=`${data.manoeuvres.length} unvalidated discontinuity candidates in the latest history comparison. Changes in drag and element fitting can also explain these signals.`;
showEvents();plot();if(data.events.length)selectEvent(data.events[0]);}catch(error){$('status').textContent='SNAPSHOT UNAVAILABLE';$('updated').textContent=error.message;$('encounters').replaceChildren(text('div','empty','The snapshot could not be loaded. Refresh to try again.'));}}
$('refresh').onclick=load;$('export').onclick=()=>{if(!data)return;const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='kessler-watch-snapshot.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
function animate(){requestAnimationFrame(animate);controls?.update();renderer?.render(scene,camera);}animate();load();setInterval(plot,30000);
