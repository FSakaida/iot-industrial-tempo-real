"""Gera segredos de laboratório sem sobrescrever configuração existente."""
from pathlib import Path
import secrets
root = Path(__file__).resolve().parents[1]
p = root / '.env'
if p.exists():
    print('.env existente preservado.')
else:
    text = (root / '.env.example').read_text()
    text = text.replace('POSTGRES_PASSWORD=\n', 'POSTGRES_PASSWORD=' + secrets.token_hex(24) + '\n')
    text = text.replace('APP_DB_PASSWORD=\n', 'APP_DB_PASSWORD=' + secrets.token_hex(24) + '\n')
    p.write_text(text)
    p.chmod(0o600)
    print('.env criado; senhas não exibidas.')
