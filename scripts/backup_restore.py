"""Backup restaurado em banco separado; mantém o banco restaurado para inspeção."""
import json
from pathlib import Path
import subprocess
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def run(*args,**kw):return subprocess.run(['docker','compose',*args],cwd=ROOT,check=True,**kw)
def query(db,query):
    return subprocess.check_output(['docker','compose','exec','-T','db','sh','-c','psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$1" -At -c "$2"','sh',db,query],cwd=ROOT,text=True).strip()
# Dump de toda a base tem snapshot consistente; simulador parado pelo operador/script.
name='facamp_restore_'+datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
source='iot_industrial'
# Obtém nome efetivo sem exibir ambiente/credenciais.
source=subprocess.check_output(['docker','compose','exec','-T','db','sh','-c','printf %s "$POSTGRES_DB"'],cwd=ROOT,text=True).strip()
run('stop','simulator')
try:
    import time;time.sleep(3)
    fingerprints={}
    for table in ('assets','sensors','telemetry','sensor_thresholds','alarms'):
        fingerprints[table]=query(source,"SELECT md5(coalesce(string_agg(row_to_json(t)::text,'' ORDER BY row_to_json(t)::text),'')) FROM "+table+" t")
    counts=query(source,"SELECT json_build_object('telemetry',(SELECT count(*) FROM telemetry),'alarms',(SELECT count(*) FROM alarms),'sensors',(SELECT count(*) FROM sensors))")
    dump=ROOT/'evidence'/'iot_industrial.dump'
    with dump.open('wb') as f:run('exec','-T','db','sh','-c','pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc',stdout=f)
    run('exec','-T','db','sh','-c','createdb -U "$POSTGRES_USER" "$1"','sh',name)
    query(name,'CREATE EXTENSION timescaledb; SELECT timescaledb_pre_restore();')
    with dump.open('rb') as f:run('exec','-T','db','sh','-c','pg_restore --exit-on-error -U "$POSTGRES_USER" -d "$1"','sh',name,stdin=f)
    query(name,'SELECT timescaledb_post_restore();')
    restored=query(name,"SELECT json_build_object('telemetry',(SELECT count(*) FROM telemetry),'alarms',(SELECT count(*) FROM alarms),'sensors',(SELECT count(*) FROM sensors))")
    assert json.loads(counts)==json.loads(restored),(counts,restored)
    restored_fingerprints={}
    for table in fingerprints:
        restored_fingerprints[table]=query(name,"SELECT md5(coalesce(string_agg(row_to_json(t)::text,'' ORDER BY row_to_json(t)::text),'')) FROM "+table+" t")
    assert fingerprints==restored_fingerprints,(fingerprints,restored_fingerprints)
    result=dict(result='PASS',database=name,source=json.loads(counts),restored=json.loads(restored),dump_bytes=dump.stat().st_size, fingerprints=fingerprints,restored_fingerprints=restored_fingerprints)
    (ROOT/'evidence'/'backup_restore.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))
finally:run('start','simulator')
