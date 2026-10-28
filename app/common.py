import json
import logging
import os
import time
import psycopg
from psycopg.rows import dict_row
from paho.mqtt import client as mqtt

logging.basicConfig(level=logging.INFO, format='%(message)s')
def log(event, **fields):
    logging.info(json.dumps({'event': event, **fields}, default=str, ensure_ascii=False))

def connect():
    return psycopg.connect(host=os.getenv('POSTGRES_HOST','localhost'),
        port=int(os.getenv('POSTGRES_PORT','5432')),
        dbname=os.getenv('POSTGRES_DB','iot_industrial'),
        user=os.getenv('POSTGRES_USER','iot_app'), password=os.environ['POSTGRES_PASSWORD'],
        connect_timeout=3, row_factory=dict_row, options='-c timezone=UTC -c statement_timeout=5000')

def mqtt_client(name, manual_ack=False):
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=name,
                    clean_session=False, manual_ack=manual_ack)
    c.reconnect_delay_set(min_delay=1, max_delay=15)
    c.max_queued_messages_set(10000)
    c.on_disconnect = lambda client, data, flags, reason, props: log('mqtt_disconnected', client=name, reason=str(reason))
    return c

def start_mqtt(c, timeout=30):
    c.connect_async(os.getenv('MQTT_HOST','localhost'), int(os.getenv('MQTT_PORT','1883')),60)
    c.loop_start()
    deadline = time.monotonic()+timeout
    while not c.is_connected():
        if time.monotonic() > deadline:
            c.loop_stop()
            raise TimeoutError('MQTT indisponível')
        time.sleep(.1)
