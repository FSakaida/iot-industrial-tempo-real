from datetime import datetime,timezone,timedelta
from unittest.mock import Mock
import json
import pytest
import psycopg
from pydantic import ValidationError
from fastapi.testclient import TestClient
from app.models import Reading,severity
from app.catalog import SENSORS
from app.ingestor import BatchWriter
from app.api import app

@pytest.fixture
def payload():
    return dict(sensor_id='S-M07-TEMP-01',asset_id='MOTOR-07',ts=datetime.now(timezone.utc).isoformat(),value=68,unit='C',quality=100,seq=1)

@pytest.mark.parametrize('value,expected',[(68,'NORMAL'),(75,'NORMAL'),(75.01,'WARN'),(78,'WARN'),(85,'WARN'),(85.01,'CRITICAL'),(88,'CRITICAL'),(70,'NORMAL')])
def test_threshold_boundaries(value,expected):
    assert severity(value,{'warn_high':75,'critical_high':85})==expected

@pytest.mark.parametrize('value,expected',[(11,'NORMAL'),(10,'NORMAL'),(9,'WARN'),(5,'WARN'),(4,'CRITICAL')])
def test_low_thresholds(value,expected):
    assert severity(value,{'warn_low':10,'critical_low':5})==expected

@pytest.mark.parametrize('key,value',[
 ('value',float('nan')),('value',float('inf')),('value',float('-inf')),('value',True),('value','68'),
 ('quality',-1),('quality',101),('quality',True),('quality',50.5),('seq',-1),('seq',True),('seq',2**63),
 ('ts','2026-01-01T12:00:00'),('ts','inválido'),('ts',1793147000),('ts','1793147000')])
def test_reject_bad_payload(payload,key,value):
    payload[key]=value
    with pytest.raises(ValidationError): Reading.model_validate(payload)

def test_future_rejected(payload):
    payload['ts']=(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat()
    with pytest.raises(ValidationError): Reading.model_validate(payload)

@pytest.mark.parametrize('key,value',[('sensor_id','desconhecido'),('asset_id','BOMBA-03'),('unit','F')])
def test_catalog_mismatch(payload,key,value):
    payload[key]=value
    with pytest.raises(ValueError):Reading.model_validate(payload).validate_catalog(SENSORS['S-M07-TEMP-01']['topic'])

def test_bad_json():
    with pytest.raises(ValidationError):Reading.model_validate_json(b'{bad')

def test_bad_topic(payload):
    with pytest.raises(ValueError):Reading.model_validate(payload).validate_catalog('outro')

def test_timezone_normalized(payload):
    payload['ts']='2026-01-01T12:00:00-03:00'
    assert Reading.model_validate(payload).ts.hour==15

def test_retry_buffer_ack_after_commit(payload):
    reading=Reading.model_validate(payload);client=Mock();events=[]
    def writer(rows):
        events.append('write')
        assert client.ack.call_count==0
        if len(events)==1:raise psycopg.OperationalError('temporary')
        return len(rows)
    b=BatchWriter(writer,sleep=lambda _:None);b.buffer=[(reading,42,1)]
    assert b.flush(client)
    assert events==['write','write'];client.ack.assert_called_once_with(42,1);assert not b.buffer

def test_retry_exhaustion_keeps_buffer(payload,monkeypatch):
    monkeypatch.setenv('DB_RETRIES','2')
    writer=Mock(side_effect=psycopg.OperationalError('offline'));client=Mock()
    b=BatchWriter(writer,sleep=lambda _:None);b.buffer=[(Reading.model_validate(payload),1,1)]
    assert not b.flush(client);assert len(b.buffer)==1;client.ack.assert_not_called();assert writer.call_count==2

def test_api_input_validation():
    client=TestClient(app)
    for path in ['/api/sensors/test/history?minutes=0','/api/sensors/test/history?minutes=1441','/api/alarms?state=INVALID','/api/alarms?limit=5000','/api/alarms?offset=-1']:
        assert client.get(path).status_code==422

def test_six_sensors_and_intervals():
    assert len(SENSORS)==6
    assert [s['sample_seconds'] for s in SENSORS.values()].count(2)==2
    assert len({s['asset_id'] for s in SENSORS.values()})==3
