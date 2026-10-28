"""Contratos externos e falhas: evita regressões na validação e exposição de erros."""
from datetime import datetime, timezone

import psycopg
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import app.api as api_module
from app.models import Reading


@pytest.fixture
def reading_payload():
    return dict(sensor_id='S-M07-TEMP-01', asset_id='MOTOR-07',
                ts=datetime.now(timezone.utc).isoformat(), value=68,
                unit='C', quality=100, seq=1)


@pytest.mark.parametrize('field', ['sensor_id', 'asset_id', 'ts', 'value', 'unit', 'quality', 'seq'])
def test_required_payload_fields(reading_payload, field):
    del reading_payload[field]
    with pytest.raises(ValidationError):
        Reading.model_validate(reading_payload)


def test_unexpected_payload_fields_rejected(reading_payload):
    reading_payload['unexpected'] = 'untrusted'
    with pytest.raises(ValidationError):
        Reading.model_validate(reading_payload)


@pytest.mark.parametrize('path,content_type', [
    ('/', 'text/html'), ('/static/style.css', 'text/css'),
    ('/static/app.js', 'javascript'), ('/static/vendor/chart.umd.js', 'javascript'),
])
def test_dashboard_assets_available_without_database(monkeypatch, path, content_type):
    def forbidden_connection():
        raise AssertionError('Arquivos estáticos devem abrir mesmo com o banco indisponível')
    monkeypatch.setattr(api_module, 'connect', forbidden_connection)
    response = TestClient(api_module.app).get(path)
    assert response.status_code == 200
    assert content_type in response.headers['content-type']
    assert response.content


@pytest.mark.parametrize('path', ['/health', '/api/assets', '/api/overview', '/api/alarms'])
def test_database_outage_has_safe_error_response(monkeypatch, path):
    private_error = 'password=TEST_PRIVATE_VALUE SELECT private_table'
    def unavailable():
        raise psycopg.OperationalError(private_error)
    monkeypatch.setattr(api_module, 'connect', unavailable)
    response = TestClient(api_module.app).get(path)
    assert response.status_code == 503
    assert response.json() == {'detail': 'Banco temporariamente indisponível. Tente novamente.'}
    assert 'TEST_PRIVATE_VALUE' not in response.text
    assert 'private_table' not in response.text
