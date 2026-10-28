"""Teste real dentro da rede Compose. Execute com simulador parado."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datetime import datetime,timezone,timedelta
import json
import time
import urllib.request
import urllib.error
import threading
from urllib.parse import quote
import psycopg
from paho.mqtt import client as mqtt
from app.common import connect,mqtt_client,start_mqtt
from app.catalog import SENSORS
from app.models import Reading
from app.storage import persist_batch

results=[]
def record(name,**data):
    results.append(dict(test=name,result='PASS',**data))
    print(json.dumps(results[-1],default=str),flush=True)

def wait(predicate,timeout=20):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        value=predicate()
        if value:return value
        time.sleep(.15)
    raise AssertionError('Tempo excedido aguardando persistência')

def scalar(sql,params=()):
    with connect() as c:return next(iter(c.execute(sql,params).fetchone().values()))

def api(path):
    with urllib.request.urlopen('http://api:8000'+path,timeout=5) as r:return json.load(r)

def row_count(): return scalar('SELECT count(*) FROM telemetry')

# Teste não deve receber backlog de execuções anteriores nem deixar uma sessão assinante.
client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id='facamp-e2e',clean_session=True)
received=[];subscribed=threading.Event()
client.on_connect=lambda c,u,f,r,p:c.subscribe('facamp/industrial/#',qos=1)
client.on_subscribe=lambda *args:subscribed.set()
client.on_message=lambda c,u,m:received.append(dict(topic=m.topic,payload=m.payload.decode(errors='replace')))
start_mqtt(client);assert subscribed.wait(5)
seq=10000

def publish(value=68,sid='S-M07-TEMP-01',**changes):
    global seq
    seq+=1;s=SENSORS[sid]
    payload=dict(sensor_id=sid,asset_id=s['asset_id'],ts=datetime.now(timezone.utc).isoformat(),value=value,unit=s['unit'],quality=100,seq=seq)
    payload.update(changes)
    send(payload,s['topic'])
    return payload

def send(payload,topic):
    i=client.publish(topic,json.dumps(payload),qos=1);i.wait_for_publish(timeout=5);assert i.is_published()

def persisted(p):
    return scalar('SELECT count(*) FROM telemetry WHERE sensor_id=%s AND time=%s',(p['sensor_id'],p['ts']))==1

def active():
    with connect() as c:return c.execute("SELECT * FROM alarms WHERE sensor_id='S-M07-TEMP-01' AND state IN ('OPEN','ACK')").fetchall()

try:
    assert len(api('/api/assets'))==3
    assert scalar('SELECT count(*) FROM sensors')==6
    record('cadastro',assets=3,sensors=6)
    for sid,s in SENSORS.items():
        p=publish(s['base'],sid);wait(lambda:persisted(p))
    record('seis_sensores_mqtt',topics=len({m['topic'] for m in received}))
    for value,expected in [(68,'NORMAL'),(78,'WARN'),(88,'CRITICAL'),(70,'NORMAL')]:
        started=time.monotonic();p=publish(value);wait(lambda:persisted(p))
        current=active()
        assert (current[0]['severity'] if current else 'NORMAL')==expected
        rows=api('/api/assets/MOTOR-07/current');s=next(s for s in rows if s['id']=='S-M07-TEMP-01')
        assert s['value']==value
        record('cenario_'+expected,value=value,latency_seconds=round(time.monotonic()-started,3),api=s)
    with connect() as c:
        closed=c.execute("SELECT * FROM alarms WHERE sensor_id='S-M07-TEMP-01' ORDER BY id DESC LIMIT 2").fetchall()
    assert len(closed)==2 and all(a['state']=='CLOSED' and a['closed_at'] for a in closed)
    record('historico_fechamento',alarms=closed)
    p=publish(78);wait(lambda:persisted(p));alarm=active()[0]['id']
    p2=publish(79);wait(lambda:persisted(p2));assert active()[0]['id']==alarm
    record('sem_alarmes_repetidos')
    try:
        with connect() as c:
            c.execute("""INSERT INTO alarms(sensor_id,opened_at,severity,value,message)
                VALUES('S-M07-TEMP-01',clock_timestamp(),'WARN',79,'teste de unicidade')""")
        raise AssertionError('Esperado bloqueio de segunda ocorrência ativa')
    except psycopg.errors.UniqueViolation:
        pass
    assert len(active())==1 and active()[0]['id']==alarm
    record('indice_unico_alarme_ativo')
    # ACK é reconhecimento, não normalização.
    with connect() as c:c.execute("UPDATE alarms SET state='ACK' WHERE id=%s",(alarm,))
    p=publish(80);wait(lambda:persisted(p));assert active()[0]['state']=='ACK'
    # Mais antiga que o último evento: persiste sem agravar o presente.
    p=publish(99,ts=(datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat())
    wait(lambda:persisted(p));assert active()[0]['id']==alarm and active()[0]['state']=='ACK'
    record('ack_e_fora_de_ordem')
    p=publish(70);wait(lambda:persisted(p));assert not active()
    p=publish(88,quality=0);wait(lambda:persisted(p));assert not active()
    record('qualidade_zero_nao_abre_alarme')
    p=publish(88);wait(lambda:persisted(p));critical_id=active()[0]['id']
    p=publish(70,quality=0);wait(lambda:persisted(p))
    assert active()[0]['id']==critical_id and active()[0]['severity']=='CRITICAL'
    record('qualidade_zero_nao_normaliza_alarme')
    p=publish(78);wait(lambda:persisted(p))
    assert active()[0]['severity']=='WARN' and active()[0]['id']!=critical_id
    assert scalar('SELECT state FROM alarms WHERE id=%s',(critical_id,))=='CLOSED'
    record('critical_para_warn_preserva_historico')
    p=publish(70);wait(lambda:persisted(p));assert not active()
    # Injeção direta somente neste teste da atomicidade SQL. Cenário oficial usa MQTT.
    base=Reading.model_validate(p).model_copy(update={'ts':datetime.now(timezone.utc),'value':78})
    invalid=base.model_copy(update={'ts':base.ts+timedelta(microseconds=1),'quality':101})
    before=row_count()
    try:
        persist_batch([base,invalid])
        raise AssertionError('Esperado CHECK na segunda linha do lote')
    except psycopg.errors.CheckViolation:
        pass
    assert row_count()==before and not active()
    assert scalar('SELECT count(*) FROM telemetry WHERE sensor_id=%s AND time=%s',
                  (base.sensor_id,base.ts))==0
    record('rollback_atomico_telemetria_e_alarme')
    before=row_count();send(p,SENSORS[p['sensor_id']]['topic']);send(p,SENSORS[p['sensor_id']]['topic']);time.sleep(2.3)
    assert row_count()==before
    record('idempotencia',count=before)
    before=row_count();topic=SENSORS['S-M07-TEMP-01']['topic']
    for raw in [b'{bad',b'[]',b'{"sensor_id":"unknown"}']:
        i=client.publish(topic,raw,qos=1);i.wait_for_publish(timeout=5)
    publish(70,sensor_id='unknown');publish(70,unit='F');publish(70,quality=101)
    publish(70,ts='2026-01-01T12:00:00');publish(70,ts=1793147000);publish(70,seq=-1)
    send(p,'facamp/industrial/topico-incorreto')
    time.sleep(2.5);assert row_count()==before
    record('rejeicao_malformado_desconhecido_unidade_qualidade')
    for path in ['/api/sensors/unknown/history','/api/assets/unknown/current']:
        try:api(path);raise AssertionError('Esperado 404')
        except urllib.error.HTTPError as e:assert e.code==404
    assert api('/api/sensors/S-M07-TEMP-01/aggregate')
    assert api('/api/sensors/S-M07-TEMP-01/history')
    assert api('/health')['mqtt']
    thresholds=api('/api/overview')['thresholds']
    assert len(thresholds)==3 and next(t for t in thresholds if t['sensor_id']=='S-M07-TEMP-01')['warn_high']==75
    record('api_historico_agregacao_saude_404')
    history=api('/api/sensors/S-M07-TEMP-01/history?limit=3')
    assert len(history)==3
    times=[datetime.fromisoformat(r['time']) for r in history]
    assert times==sorted(times)
    assert times[-1]==datetime.fromisoformat(p['ts'])
    for row in api('/api/alarms?state=CLOSED&limit=2&offset=1'):
        assert row['state']=='CLOSED'
    try:
        api('/api/assets/'+quote("' OR 1=1 --",safe='')+'/current')
        raise AssertionError('Identificador malicioso deve ser tratado como dado')
    except urllib.error.HTTPError as e:
        assert e.code==404
    record('api_limites_ordenacao_filtro_e_injecao_sql')
    # Cada tentativa usa uma transação separada e deve falhar sem persistir.
    import psycopg
    for value in (float('nan'),float('inf'),float('-inf')):
        try:
            with connect() as c:c.execute("INSERT INTO telemetry(time,sensor_id,value,quality,seq) VALUES(clock_timestamp(),'S-M07-TEMP-01',%s,100,1)",(value,))
            raise AssertionError('Esperado CHECK')
        except psycopg.errors.CheckViolation:pass
    record('checks_valores_finitos')
    with connect() as c:
        assert not c.execute("SELECT has_table_privilege(current_user,'telemetry','DELETE') AS allowed").fetchone()['allowed']
        assert c.execute("SELECT has_table_privilege(current_user,'alarms','UPDATE') AS allowed").fetchone()['allowed']
    record('menor_privilegio')
    print(json.dumps(dict(summary='PASS',tests=len(results),mqtt_samples=received[:10]),default=str))
finally:
    client.disconnect();client.loop_stop()
