from app.common import connect,log
from app.models import severity

INSERT = """INSERT INTO telemetry(time,sensor_id,value,quality,seq)
VALUES(%s,%s,%s,%s,%s) ON CONFLICT(sensor_id,time) DO NOTHING RETURNING time"""

def persist_batch(readings):
    inserted = 0
    with connect() as conn:
        # Bloqueia sensores em ordem fixa para serializar alarmes e evitar deadlocks.
        for sid in sorted({r.sensor_id for r in readings}):
            conn.execute('SELECT id FROM sensors WHERE id=%s FOR UPDATE',(sid,)).fetchone()
        for r in sorted(readings,key=lambda r:(r.ts,r.sensor_id)):
            sensor = conn.execute('SELECT * FROM sensors WHERE id=%s',(r.sensor_id,)).fetchone()
            if not sensor or not sensor['enabled'] or sensor['unit'] != r.unit or sensor['asset_id'] != r.asset_id:
                log('message_rejected',reason='cadastro do banco incompatível',sensor_id=r.sensor_id)
                continue
            latest = conn.execute('SELECT time FROM telemetry WHERE sensor_id=%s ORDER BY time DESC LIMIT 1',(r.sensor_id,)).fetchone()
            added = conn.execute(INSERT,(r.ts,r.sensor_id,r.value,r.quality,r.seq)).fetchone()
            if not added: continue
            inserted += 1
            # Leituras antigas e de qualidade zero ficam apenas no histórico.
            if (latest and r.ts <= latest['time']) or r.quality == 0: continue
            threshold = conn.execute('SELECT * FROM sensor_thresholds WHERE sensor_id=%s',(r.sensor_id,)).fetchone()
            level = severity(r.value,threshold)
            active = conn.execute("SELECT * FROM alarms WHERE sensor_id=%s AND state IN ('OPEN','ACK')",(r.sensor_id,)).fetchone()
            if active and active['severity'] == level: continue
            if active:
                conn.execute("UPDATE alarms SET state='CLOSED',closed_at=%s WHERE id=%s",(r.ts,active['id']))
            if level != 'NORMAL':
                conn.execute('INSERT INTO alarms(sensor_id,opened_at,severity,value,message) VALUES(%s,%s,%s,%s,%s)',
                    (r.sensor_id,r.ts,level,r.value,f'{r.sensor_id}: {level}, {r.value} {r.unit}'))
    return inserted
