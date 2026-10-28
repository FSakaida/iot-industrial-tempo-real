"""Valida mensagens e grava lotes; leituras válidas recebem ACK após o commit."""
import os
import queue
import signal
import threading
import time
from pydantic import ValidationError
import psycopg
from app.common import log, mqtt_client, start_mqtt
from app.models import Reading
from app.storage import persist_batch

class BatchWriter:
    def __init__(self, writer=persist_batch, sleep=time.sleep):
        self.buffer = []
        self.writer, self.sleep = writer, sleep

    def flush(self, client):
        if not self.buffer: return True
        for attempt in range(int(os.getenv('DB_RETRIES','4'))):
            try:
                count = self.writer([r for r,mid,qos in self.buffer])
                for r,mid,qos in self.buffer: client.ack(mid,qos)
                log('batch_committed', received=len(self.buffer), inserted=count)
                self.buffer.clear()
                return True
            except (psycopg.OperationalError,psycopg.InterfaceError,psycopg.errors.DeadlockDetected):
                log('db_retry',attempt=attempt+1,pending=len(self.buffer))
                self.sleep(min(2**attempt,8))
        log('db_unavailable',pending=len(self.buffer))
        return False

def main():
    inbox = queue.Queue(maxsize=10000)
    stop = threading.Event()
    signal.signal(signal.SIGTERM,lambda *_: stop.set())
    signal.signal(signal.SIGINT,lambda *_: stop.set())
    client = mqtt_client('facamp-ingestor',manual_ack=True)
    def connected(c,u,f,reason,p):
        if reason == 0:
            c.subscribe('facamp/industrial/#',qos=1)
            log('mqtt_subscribed',topic='facamp/industrial/#')
    client.on_connect = connected
    def message(c,u,msg):
        try:
            if len(msg.payload)>4096: raise ValueError('payload muito grande')
            reading = Reading.model_validate_json(msg.payload).validate_catalog(msg.topic)
            inbox.put_nowait((reading,msg.mid,msg.qos))
        except (ValidationError,ValueError) as e:
            reason = e.errors(include_input=False)[0]['type'] if isinstance(e,ValidationError) else str(e)
            log('message_rejected',reason=reason,topic=msg.topic)
            c.ack(msg.mid,msg.qos)
        except queue.Full:
            log('buffer_full',action='reiniciar para retransmissão; mensagem sem ACK')
            stop.set()
    client.on_message = message
    start_mqtt(client)
    batch = BatchWriter()
    deadline = time.monotonic()+float(os.getenv('FLUSH_SECONDS','1'))
    try:
        while not stop.is_set():
            try: batch.buffer.append(inbox.get(timeout=.1))
            except queue.Empty: pass
            if len(batch.buffer)>=int(os.getenv('BATCH_MAX','100')) or time.monotonic()>=deadline:
                if not batch.flush(client):
                    # Não consome mais mensagens enquanto o lote está pendente.
                    while not stop.is_set() and not batch.flush(client): stop.wait(2)
                deadline = time.monotonic()+float(os.getenv('FLUSH_SECONDS','1'))
        while not inbox.empty(): batch.buffer.append(inbox.get_nowait())
        batch.flush(client)
    finally:
        client.disconnect()
        client.loop_stop()

if __name__ == '__main__': main()
