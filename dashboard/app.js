const $=id=>document.getElementById(id);
const names={temperature:'Temperatura',vibration:'Vibração',pressure:'Pressão',current:'Corrente',flow:'Vazão'};
const labels={NORMAL:'Normal',WARN:'Atenção',CRITICAL:'Crítico',OFFLINE:'Indisponível',OPEN:'Aberto',ACK:'Reconhecido',CLOSED:'Encerrado'};
let snapshot=null,chart=null,configured=false,loading=false,again=false,connected=false,health={database:false,mqtt:false};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const num=v=>v==null?'—':Number(v).toLocaleString('pt-BR',{maximumFractionDigits:2});
const date=t=>t?new Date(t).toLocaleString('pt-BR',{hour:'2-digit',minute:'2-digit',second:'2-digit',day:'2-digit',month:'2-digit'}):'Sem leitura';
const unit=s=>s.unit==='C'?'°C':s.unit;
const badge=s=>`<span class="badge ${esc(s)}">${labels[s]||esc(s)}</span>`;
function fresh(s){return connected&&s.enabled&&s.quality>0&&s.time&&(Date.now()-new Date(s.time).getTime())<(s.sample_seconds*3+2)*1000;}
function status(s){return fresh(s)?(s.severity||'NORMAL'):'OFFLINE';}
function configure(){
 if(!configured){$('asset-filter').innerHTML='<option value="">Todos os equipamentos</option>'+snapshot.assets.map(a=>`<option value="${esc(a.id)}">${esc(a.id)} · ${esc(a.production_line)}</option>`).join('');configured=true;configureSensors();}
}
function configureSensors(){let old=$('sensor-filter').value;const sensors=snapshot.sensors.filter(s=>!$('asset-filter').value||s.asset_id===$('asset-filter').value);$('sensor-filter').innerHTML=sensors.map(s=>`<option value="${esc(s.id)}">${esc(s.asset_id)} · ${names[s.sensor_type]||esc(s.sensor_type)}</option>`).join('');if(sensors.some(s=>s.id===old))$('sensor-filter').value=old;}
function render(){
 const d=snapshot;const freshCount=d.sensors.filter(fresh).length;const levels=d.sensors.map(status);const state=levels.includes('CRITICAL')?'CRITICAL':levels.includes('WARN')?'WARN':freshCount<d.sensors.length?'OFFLINE':'NORMAL';
 $('asset-count').textContent=d.assets.length;$('sensor-count').textContent=`${freshCount} / ${d.sensors.length}`;$('sensor-detail').textContent=`${d.sensors.length-freshCount} sem leitura atual`;$('alarm-count').textContent=d.open_alarms;$('plant-state').textContent=labels[state];$('plant-detail').textContent=state==='NORMAL'?'Todos os sensores com leitura atual':'Verifique sensores e ocorrências';
 $('assets').innerHTML=d.assets.map(a=>`<article class="asset"><div class="asset-head"><div><h3>${esc(a.id)}</h3><small>${esc(a.production_line)} · criticidade ${esc(a.criticality)}</small></div><span aria-hidden="true">◈</span></div>${d.sensors.filter(s=>s.asset_id===a.id).map(s=>`<div class="sensor"><span class="type">${names[s.sensor_type]||esc(s.sensor_type)}</span><span class="value">${num(s.value)}<small>${esc(unit(s))}</small></span><time datetime="${esc(s.time||'')}">${date(s.time)}</time><div class="sensor-state">${badge(status(s))}</div></div>`).join('')}</article>`).join('');
 const th=d.thresholds.find(t=>t.sensor_id==='S-M07-TEMP-01');$('threshold-note').textContent=th?`Temperatura MOTOR-07: atenção > ${num(th.warn_high)} °C · crítico > ${num(th.critical_high)} °C. Leituras históricas não alteram o estado atual.`:'Sem limites de temperatura cadastrados para MOTOR-07.';
 renderAlarms();$('total').textContent=num(d.total);const lags=d.sensors.filter(s=>s.time).map(s=>(new Date(s.received_at)-new Date(s.time))/1000);$('lag').textContent=lags.length?`${num(Math.max(...lags))} s`:'Sem dados';
 $('db-health').textContent=health.database?'Disponível':'Indisponível';$('mqtt-health').textContent=health.mqtt?'Disponível':'Indisponível';
}
function renderAlarms(){const rows=snapshot.alarms.filter(a=>!$('alarm-filter').value||a.state===$('alarm-filter').value);$('alarm-rows').innerHTML=rows.length?rows.map(a=>`<tr><td>#${esc(a.id)}<small>${esc(a.sensor_id)}</small></td><td>${badge(a.severity)}</td><td>${num(a.value)} ${esc(unit(snapshot.sensors.find(s=>s.id===a.sensor_id)||{unit:""}))}</td><td>${date(a.opened_at)}</td><td>${a.closed_at?date(a.closed_at):'—'}</td><td>${badge(a.state)}</td></tr>`).join(''):'<tr><td colspan="6">Nenhuma ocorrência neste filtro.</td></tr>';}
async function get(path){const r=await fetch(path,{signal:AbortSignal.timeout(6000),cache:'no-store'});if(!r.ok)throw Error(`Serviço respondeu ${r.status}`);return r.json();}
async function history(){
 const sid=$('sensor-filter').value;if(!sid)return;
 const rows=await get(`/api/sensors/${encodeURIComponent(sid)}/history?minutes=${$('period-filter').value}`);const s=snapshot.sensors.find(s=>s.id===sid);
 $('chart-title').textContent=`${s.asset_id} · ${names[s.sensor_type]} (${unit(s)})`;
 $('chart-note').textContent=`${num(rows.length)} leituras na janela`;$('chart-empty').hidden=rows.length>0;$('chart-empty').textContent='Sem leituras neste período.';
 $('history-rows').innerHTML=rows.slice(-20).reverse().map(r=>`<tr><td>${date(r.time)}</td><td>${num(r.value)} ${esc(unit(s))}</td><td>${num(r.quality)}%</td></tr>`).join('')||'<tr><td colspan="3">Sem dados</td></tr>';
 const points=rows.map(r=>({x:new Date(r.time).getTime(),y:r.value}));
 if(!chart)chart=new Chart($('history-chart'),{type:'line',data:{datasets:[{data:[],label:'',borderColor:'#297b68',backgroundColor:'rgba(60,130,100,.08)',fill:true,borderWidth:2,pointRadius:0,pointHitRadius:10,tension:.18}]},options:{responsive:true,maintainAspectRatio:false,animation:false,parsing:false,plugins:{legend:{display:false},tooltip:{callbacks:{title:items=>new Date(items[0].parsed.x).toLocaleString('pt-BR')}}},scales:{x:{type:'linear',grid:{display:false},ticks:{maxTicksLimit:6,callback:v=>new Date(v).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})}},y:{title:{display:true,text:''},grid:{color:'#edf1e9'}}}}});
 chart.data.datasets[0].data=points;chart.data.datasets[0].label=unit(s);chart.options.scales.y.title.text=unit(s);chart.update('none');
}
async function refresh(){
 if(loading){again=true;return;}loading=true;
 try{
  snapshot=await get('/api/overview');connected=true;configure();
  try{health=await get('/health');}catch{health={database:true,mqtt:false};}
  render();$('connection').textContent=health.mqtt?'● Serviços disponíveis':'△ Broker indisponível';$('last-update').textContent='Consulta '+date(snapshot.server_time);
  const stale=snapshot.sensors.filter(s=>!fresh(s)).length;$('notice').hidden=!stale&&health.mqtt;$('notice').className='notice';$('notice').textContent=stale?`${stale} sensor(es) sem leitura atual. Verifique o simulador e a ingestão.`:'Conexão com o broker MQTT indisponível.';
  try{await history();}catch{$('chart-note').textContent='Histórico indisponível. Nova tentativa em breve.';}
 }catch(e){connected=false;$('connection').textContent='○ Sem conexão';$('notice').hidden=false;$('notice').className='notice error';$('notice').textContent='Não foi possível consultar a API. Valores anteriores podem estar desatualizados. Tentando novamente…';health={database:false,mqtt:false};if(snapshot)render();}
 finally{loading=false;if(again){again=false;refresh();}}
}
$('asset-filter').addEventListener('change',()=>{if(snapshot)configureSensors();refresh();});
$('sensor-filter').addEventListener('change',refresh);$('period-filter').addEventListener('change',refresh);$('alarm-filter').addEventListener('change',()=>snapshot&&renderAlarms());
async function poll(){await refresh();setTimeout(poll,3000);}poll();
