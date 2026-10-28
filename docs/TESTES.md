# Testes automatizados

Antes, execute `python3 scripts/setup.py`. Com Docker em execução e o ambiente virtual ativado:

```sh
pip install -r requirements-dev.txt
docker compose up -d --build --wait
python3 scripts/verify.py
```

O comando termina com código 0 somente se todas as etapas passarem. Grava `evidence/verification.json` com resultado, horários e duração por etapa; `evidence/pytest.xml` é um relatório JUnit importável por ferramentas de CI. A execução começa com estado RUNNING e grava FAIL se ocorrer erro, evitando reaproveitar um resultado PASS anterior.

## Cobertura
- `tests/test_rules.py`: limites de alarme, fuso, JSON, valores finitos, qualidade, sequência, cadastro, retry, preservação do buffer e ACK após commit.
- `tests/test_contracts.py`: campos obrigatórios, campos extras, arquivos do dashboard acessíveis sem banco e erros HTTP 503 sem exposição de detalhes internos.
- `scripts/e2e.py`: usa MQTT, PostgreSQL e API reais. Confere os seis sensores, cenário 68/78/88/70, fechamento e histórico, reconhecimento, mensagens antigas, deduplicação, mensagens inválidas e privilégios. Também valida qualidade zero, redução CRITICAL→WARN, índice único para alarme ativo, rollback conjunto de telemetria e alarme, paginação e identificadores com tentativa de injeção SQL.
- `scripts/resilience.py`: para temporariamente o banco, publica uma mensagem real e confirma a recuperação; reinicia o broker e confirma reconexão e persistência.
- `scripts/backup_restore.py`: restaura em banco separado e compara contagens e hashes das cinco tabelas.
- `scripts/queries.sql`: consultas e EXPLAIN ANALYZE reais com parada em qualquer erro SQL.

O simulador contínuo é interrompido durante os testes para não competir com o cenário determinístico e é retomado ao final. O histórico recebe leituras e alarmes de teste; o banco principal não é apagado. A restauração cria outro banco, sem sobrescrever o original.

O teste de rollback chama a camada de persistência diretamente para provocar uma violação de CHECK na segunda linha do lote; o cenário oficial e os testes de qualidade/anomalia passam pelo broker MQTT real.

## Limites
A suíte não automatiza navegador, dispositivos físicos nem teste de carga. As capturas e verificações de layout existentes foram feitas por inspeção do navegador na entrega anterior. Falha simultânea da máquina e dos processos não foi simulada. Há um aviso de depreciação em uma dependência do cliente de teste, separado de falhas de asserção.

## Arquivos publicados

O repositório inclui os scripts e as capturas selecionadas. Logs, relatórios JSON/JUnit, dumps e saídas operacionais são locais e estão no `.gitignore`. A revisão de instalação limpa e os resultados correspondentes estão em `REVISAO.md`.
