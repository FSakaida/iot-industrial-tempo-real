import argparse
from datetime import datetime,timezone
import json
import os
import random
import signal
import threading
import time
from app.catalog import SENSORS
from app.common import log,mqtt_client,start_mqtt

def publish(c,s,value,seq):
    payload = dict(sensor_id=s['id'],asset_id=s['asset_id'],ts=datetime.now(timezone.utc).isoformat(),
                   value=round(value,3),unit=s['unit'],quality=100,seq=seq)
    info=c.publish(s['topic'],json.dumps(payload),qos=1)
    info.wait_for_publish(timeout=10)
    if not info.is_published(): raise TimeoutError('MQTT não confirmou publicação')
    log('published',topic=s['topic'],**payload)
    return payload

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--scenario',action='store_true')
    parser.add_argument('--step-seconds',type=float,default=4)
    args=parser.parse_args()
    stop=threading.Event()
    signal.signal(signal.SIGTERM,lambda *_:stop.set())
    signal.signal(signal.SIGINT,lambda *_:stop.set())
    c=mqtt_client('facamp-scenario' if args.scenario else 'facamp-simulator')
    start_mqtt(c)
    try:
        if args.scenario:
            for seq,value in enumerate((68,78,88,70),1):
                publish(c,SENSORS['S-M07-TEMP-01'],value,seq)
                stop.wait(args.step_seconds)
                if stop.is_set(): break
        else:
            due={sid:0 for sid in SENSORS}; seq={sid:0 for sid in SENSORS}
            factor=float(os.getenv('SIM_INTERVAL_FACTOR','1'))
            if factor<=0: raise ValueError('SIM_INTERVAL_FACTOR deve ser positivo')
            while not stop.is_set():
                for sid,s in SENSORS.items():
                    if time.monotonic()>=due[sid]:
                        seq[sid]+=1
                        try:
                            publish(c,s,random.gauss(s['base'],s['sigma']),seq[sid])
                        except (RuntimeError,TimeoutError,ValueError): log('publish_retry',sensor_id=sid)
                        due[sid]=time.monotonic()+s['sample_seconds']*factor
                stop.wait(.05)
    finally:
        c.disconnect(); c.loop_stop()

if __name__=='__main__': main()
