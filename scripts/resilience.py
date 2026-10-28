"""Executado no host; controla apenas os containers deste projeto."""
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
def compose(*args,check=True):
    return subprocess.run(['docker','compose',*args],cwd=ROOT,check=check,capture_output=True,text=True)

def sql(query):
    return compose('exec','-T','db','sh','-c','psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "$1"','sh',query).stdout.strip()

def publish(seq):
    code="from app.common import mqtt_client,start_mqtt; from app.simulator import publish; from app.catalog import SENSORS; c=mqtt_client('facamp-resilience'); start_mqtt(c); publish(c,SENSORS['S-M07-TEMP-01'],70,"+str(seq)+"); c.disconnect(); c.loop_stop()"
    return compose('run','--rm','--no-deps','api','python','-c',code).stdout

def wait_for(seq,timeout=70):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if sql('SELECT count(*) FROM telemetry WHERE seq='+str(seq))=='1':return
        time.sleep(1)
    raise AssertionError('Leitura não persistida após recuperação')

marker=int(time.time()*1000000)
try:
    compose('stop','simulator')
    compose('stop','db');print(publish(marker),flush=True)
    time.sleep(4)
    compose('start','db')
    wait_for(marker)
    print(json.dumps({'test':'indisponibilidade_real_banco','result':'PASS','seq':marker}),flush=True)
    compose('stop','mosquitto');time.sleep(3);compose('start','mosquitto');time.sleep(4)
    print(publish((marker+1)),flush=True);wait_for((marker+1))
    print(json.dumps({'test':'reconexao_real_mqtt','result':'PASS','seq':(marker+1)}),flush=True)
finally:
    compose('start','db','mosquitto','simulator',check=False)
