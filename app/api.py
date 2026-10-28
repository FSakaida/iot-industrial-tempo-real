from datetime import datetime,timezone
from pathlib import Path
import os
import socket
from typing import Literal
from fastapi import FastAPI,HTTPException,Query,Request
from fastapi.responses import JSONResponse,FileResponse
from fastapi.staticfiles import StaticFiles
import psycopg
from app.common import connect,log

app=FastAPI(title='FACAMP | IoT Industrial',version='1.0.0')
ROOT=Path(__file__).resolve().parents[1]/'dashboard'
app.mount('/static',StaticFiles(directory=ROOT),name='static')

@app.exception_handler(psycopg.Error)
def db_error(request:Request,exc):
    log('api_db_error',kind=type(exc).__name__)
    return JSONResponse(status_code=503,content={'detail':'Banco temporariamente indisponível. Tente novamente.'})

@app.get('/')
def index(): return FileResponse(ROOT/'index.html')

@app.get('/health')
def health():
    with connect() as c: c.execute('SELECT 1').fetchone()
    try:
        with socket.create_connection((os.getenv('MQTT_HOST','localhost'),int(os.getenv('MQTT_PORT','1883'))),timeout=1): pass
        mqtt=True
    except OSError: mqtt=False
    return JSONResponse(status_code=200 if mqtt else 503,content={'database':True,'mqtt':mqtt,'time':datetime.now(timezone.utc).isoformat()})

@app.get('/api/assets')
def assets():
    with connect() as c: return c.execute('SELECT * FROM assets ORDER BY id').fetchall()

CURRENT="""SELECT s.*,t.time,t.value,t.quality,t.seq,t.received_at,
 a.severity,a.state AS alarm_state
 FROM sensors s LEFT JOIN LATERAL
 (SELECT * FROM telemetry WHERE sensor_id=s.id ORDER BY time DESC LIMIT 1) t ON true
 LEFT JOIN alarms a ON a.sensor_id=s.id AND a.state IN ('OPEN','ACK')"""

def sensor_exists(c,sid):
    if not c.execute('SELECT id FROM sensors WHERE id=%s',(sid,)).fetchone():
        raise HTTPException(404,'Sensor não encontrado')

@app.get('/api/assets/{asset_id}/current')
def current(asset_id:str):
    with connect() as c:
        if not c.execute('SELECT id FROM assets WHERE id=%s',(asset_id,)).fetchone(): raise HTTPException(404,'Ativo não encontrado')
        return c.execute(CURRENT+' WHERE s.asset_id=%s ORDER BY s.id',(asset_id,)).fetchall()

@app.get('/api/overview')
def overview():
    with connect() as c:
        # Snapshot consistente das várias consultas.
        c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        readings=c.execute(CURRENT+' ORDER BY s.id').fetchall()
        count=c.execute('SELECT count(*) AS total FROM telemetry').fetchone()['total']
        alarms=c.execute('SELECT * FROM alarms ORDER BY opened_at DESC,id DESC LIMIT 200').fetchall()
        return dict(assets=c.execute('SELECT * FROM assets ORDER BY id').fetchall(),sensors=readings,
                    alarms=alarms,total=count,thresholds=c.execute('SELECT * FROM sensor_thresholds ORDER BY sensor_id').fetchall(),server_time=datetime.now(timezone.utc),
                    open_alarms=c.execute("SELECT count(*) AS total FROM alarms WHERE state IN ('OPEN','ACK')").fetchone()['total'])

@app.get('/api/sensors/{sensor_id}/history')
def history(sensor_id:str,minutes:int=Query(60,ge=1,le=1440),limit:int=Query(2000,ge=1,le=5000)):
    with connect() as c:
        sensor_exists(c,sensor_id)
        return c.execute("""SELECT * FROM (SELECT time,value,quality FROM telemetry
          WHERE sensor_id=%s AND time>=now()-(%s*interval '1 minute') ORDER BY time DESC LIMIT %s) h ORDER BY time""",
          (sensor_id,minutes,limit)).fetchall()

@app.get('/api/sensors/{sensor_id}/aggregate')
def aggregate(sensor_id:str,minutes:int=Query(60,ge=1,le=1440)):
    with connect() as c:
        sensor_exists(c,sensor_id)
        return c.execute("""SELECT time_bucket('1 minute',time) AS time,avg(value) AS avg,min(value) AS min,max(value) AS max,count(*) AS points
        FROM telemetry WHERE sensor_id=%s AND time>=now()-(%s*interval '1 minute') GROUP BY 1 ORDER BY 1""",(sensor_id,minutes)).fetchall()

@app.get('/api/alarms')
def alarms(state:Literal['OPEN','ACK','CLOSED']|None=None,limit:int=Query(200,ge=1,le=1000),offset:int=Query(0,ge=0)):
    with connect() as c:
        return c.execute('SELECT * FROM alarms WHERE (%s::text IS NULL OR state=%s) ORDER BY opened_at DESC,id DESC LIMIT %s OFFSET %s',
                         (state,state,limit,offset)).fetchall()
