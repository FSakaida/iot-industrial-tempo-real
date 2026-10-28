"""Verificação automatizada com relatórios JSON/JUnit; requer Docker e requirements-dev."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'evidence'
E.mkdir(exist_ok=True)
report = {'result': 'RUNNING', 'started_at': datetime.now(timezone.utc).isoformat(), 'checks': []}

def save_report():
    (E / 'verification.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')

def step(name, cmd, stdin=None):
    check = {'name': name, 'result': 'RUNNING'}
    report['checks'].append(check)
    save_report()
    started = time.monotonic()
    try:
        with (E / name).open('w') as output:
            subprocess.run(cmd, cwd=ROOT, stdin=stdin, stdout=output,
                           stderr=subprocess.STDOUT, timeout=300, check=True)
        check['result'] = 'PASS'
        print(f'PASS {name}', flush=True)
    except (subprocess.SubprocessError, OSError):
        check['result'] = 'FAIL'
        raise RuntimeError(f'Falhou {name}. Consulte evidence/{name}') from None
    finally:
        check['duration_seconds'] = round(time.monotonic() - started, 3)
        save_report()

save_report()
try:
    step('pytest.txt', [sys.executable, '-m', 'pytest', '-q', '--junitxml=evidence/pytest.xml'])
    suites = ET.parse(E / 'pytest.xml').getroot().iter('testsuite')
    report['unit_tests'] = sum(int(s.attrib['tests']) for s in suites)
    step('compose.txt', ['docker', 'compose', 'config', '--quiet'])
    step('pause_simulator.txt', ['docker', 'compose', 'stop', 'simulator'])
    step('e2e.txt', ['docker', 'compose', 'run', '--rm', '--no-deps', 'api', 'python', 'scripts/e2e.py'])
    for line in (E / 'e2e.txt').read_text().splitlines():
        if line.startswith('{'):
            event = json.loads(line)
            if event.get('summary') == 'PASS':
                report['integration_checks'] = event['tests']
    if 'integration_checks' not in report:
        raise RuntimeError('Teste integrado não produziu resumo de aprovação')
    step('resilience.txt', [sys.executable, 'scripts/resilience.py'])
    step('backup_restore.txt', [sys.executable, 'scripts/backup_restore.py'])
    with (ROOT / 'scripts/queries.sql').open() as sql:
        step('sql.txt', ['docker', 'compose', 'exec', '-T', 'db', 'sh', '-c',
                        'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'], stdin=sql)
    step('services.txt', ['docker', 'compose', 'ps'])
    step('logs.txt', ['docker', 'compose', 'logs', '--tail=50', 'ingestor', 'simulator', 'mosquitto'])
    report['result'] = 'PASS'
except Exception as exc:
    report['result'] = 'FAIL'
    report['error'] = str(exc)
finally:
    try:
        step('resume_simulator.txt', ['docker', 'compose', 'start', 'simulator'])
    except Exception as exc:
        report['result'] = 'FAIL'
        report['restore_error'] = str(exc)
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    save_report()

print(json.dumps(report, ensure_ascii=False), flush=True)
if report['result'] != 'PASS':
    sys.exit(1)
