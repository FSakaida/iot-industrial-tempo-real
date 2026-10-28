# Matriz única de requisitos
Fontes: ESPECIFICACAO.md (critérios internos de implementação); manual PDF §§1–19; HTML (15 slides e 8 atividades). Os dois materiais didáticos estão preservados em docs/references. Os exemplos são dados de referência e foram corrigidos quando conflitam com integridade ou operação segura.

| ID | Prioridade | Requisito e origem | Implementação | Verificação/evidência |
|---|---|---|---|---|
| R01 | P0 obrigatório | Local, gratuito, reproduzível; especificação §2, manual §§4,7 | Compose; Python, banco pg16/Timescale, broker; sem nuvem | compose up; evidence/services.txt |
| R02 | P0 | 3 ativos e 6 sensores originais, intervalos 2/5 s; manual §6 | sql/02_seed.sql; app/catalog.py | e2e cadastro + 6 tópicos; evidence/sql.txt |
| R03 | P0 | 5 tabelas, PK/FK/CHECK, UTC, valores finitos; manual §8, especificação §3 | sql/01_schema.sql, models.py | testes unitários + e2e checks |
| R04 | P0 | Hypertable, índice, consultas/EXPLAIN; manual §8 | schema e scripts/queries.sql | evidence/sql.txt; docs/DESEMPENHO.md |
| R05 | P0 | MQTT QoS 1, seis sensores, controle e cenário; manual §§9–10 | simulator.py; Compose stop/start; CLI --scenario | e2e seis_sensores_mqtt e cenário |
| R06 | P0 | Validar JSON/cadastro/unidade/qualidade/ts; manual §11 | models.py + conferência de cadastro na transação | tests/test_rules.py; e2e rejeições |
| R07 | P0 | Batch tamanho/tempo; buffer até commit; retry; especificação §4 | ingestor.py; ACK manual após commit, flush 1 s | unitário retry; scripts/resilience.py |
| R08 | P0 | Idempotência e eventos antigos; manual §11/especificação §5 | PK(sensor_id,time), ON CONFLICT; lock por sensor | e2e duplicidade, ACK e fora de ordem |
| R09 | P0 | Máquina NORMAL/WARN/CRITICAL/NORMAL; especificação §5, manual §13 | storage.py em uma transação; histórico e fechamento | e2e valores 68/78/88/70 pela rede MQTT |
| R10 | P0 | API mínima parametrizada, limites; manual §12 | api.py; overview, aggregate e health adicionais | unitário contratos + e2e API |
| R11 | P0 | Dashboard consumindo API; especificação §7 | FastAPI serve HTML/CSS/Chart.js local; polling 3 s | inspeção visual + testes em navegador |
| R12 | P1 obrigatório entrega completa | Português, foco, responsividade; especificação §7/manual §12 | CSS 3 larguras, sem CDN; tabela acessível do gráfico | evidence/dashboard_*.jpg |
| R13 | P1 | Sem dados, carregando, conexão perdida, stale; especificação §7 | JS compara timestamp e qualidade, mostra alertas | navegador; desconexão real |
| R14 | P1 | Credenciais no ambiente, menor privilégio, rede local; manual §14 | setup.py; .env ignorado; roles; db sem porta host | e2e privilégios; compose config --quiet |
| R15 | P1 | Backup restaurado e conferido separado; manual §14 | scripts/backup_restore.py | evidence/backup_restore.json |
| R16 | P1 | Evidências banco/MQTT/alarme; manual §16 | e2e, SQL, logs, screenshots | pasta evidence/ |
| R17 | P1 | README, licenças, roteiro 10–12 min; especificação §11 | README; LICENCAS.md; DEMONSTRACAO.md | revisão de documentação |
| R18 | P1 | Falha temporária DB, reconexão MQTT, logs; especificação §9 | retries/backoff, sessão persistente, logs JSON | evidence/resilience.txt |
| R19 | P2 opcional | Carga progressiva e ajuste medido; manual §15 | Fora do MVP; seis sensores a 1,8 pontos/s nominal | Não executado; sem alegação de escala |
| R20 | Recomendado | Retenção hot/warm/cold; HTML slide 8/manual §8.5 | Política proposta em README; sem remoção automática | Documentação; evita apagar evidência |

## Decisões e ambiguidades
- O guia ensina instalação no Windows; esta implementação usa o macOS existente e Docker instalado.
- Dashboard próprio com Chart.js; sem Grafana, framework JS, autenticação corporativa ou segundo servidor.
- Usa TimescaleDB Community self-hosted (partes Apache 2 e TSL). Gratuito local; não é integralmente OSI. Alternativa estritamente aberta: PostgreSQL 16 particionado (§17.1), descrita sem segunda arquitetura paralela.
- Manual tem thresholds só para temperatura/vibração do motor e pressão do compressor. Não inventamos limites para os demais sensores; recebem telemetria sem regras configuradas.
- Comparação estrita: valor =75 é NORMAL; =85 é WARN; >85 é CRITICAL. Sem histerese no MVP. Qualidade zero persiste, mas não gera transição.
- Seq é diagnóstico por execução; pode reiniciar. Idempotência usa sensor+instante, chave compatível com hypertable e retransmissão MQTT.
- Leitura com timestamp anterior ao último recebido persiste, mas não altera alarme atual. Empates com mesma PK conservam a primeira amostra confirmada.
- Alarme ativo tem índice único parcial. WARN→CRITICAL fecha WARN e abre CRITICAL; retorno a NORMAL fecha ativo. ACK não significa normalização. Sem botão de reconhecimento no dashboard.
- API entrega até 5.000 pontos por chamada (padrão 2.000); UI informa que mostra as últimas 2.000 leituras. Alarmes UI mostra últimos 200; API possui limit/offset.
- Atualidade: até 3 intervalos+2 s e qualidade >0; não usa página aberta como sinal de sensor online.
- Com frequência original, taxa nominal é 2/2 + 4/5 = 1,8 pontos/s. Não há sensor energético cadastrado; não há KPI energético.
- Health é disponibilidade de DB e conexão TCP com broker; atualidade de sensores é calculada separadamente. Sem pretensão de observabilidade corporativa.
- Falhas por processo/máquina além de laboratório: buffer Python em memória; QoS 1 e sessão persistente ajudam, mas não prometem exactly-once nem garantia durável de ponta a ponta. Retentativa da transação usa idempotência.
