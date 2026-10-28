# Roteiro de demonstração (12 minutos)
Antes: Docker em execução; `python3 scripts/setup.py`; `docker compose up -d --build`. Abra dashboard, terminal de logs e cliente SQL (`docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'`).

| Tempo | Ação | O que explicar |
|---|---|---|
| 0–1 min | Mostrar arquitetura no README | Produtor → broker → validação → banco → API → tela |
| 1–3 min | Mostrar assets JOIN sensors e schema | Integridade cadastral e série temporal; 3 ativos, 6 sensores, 2/5 s |
| 3–5 min | `docker compose logs --tail=8 simulator ingestor` e subscriber | Payload com ts/seq/unidade; MQTT QoS 1; batch e commit |
| 5–7 min | Consultas SQL e EXPLAIN | Hypertable/chunks, histórico, agregados; interpretar plano real |
| 7–9 min | Dashboard e filtros | Uma grandeza por eixo, dados da API, timestamp; três larguras |
| 9–11 min | Parar simulador, executar cenário abaixo | 68 → 78 → 88 → 70; abertura, agravamento e fechamento persistidos |
| 11–12 min | Mostrar backup_restore.json e licenças | Restauração conferida; gratuito local; Timescale Community inclui TSL |

Cenário: interromper o simulador contínuo evita que uma leitura normal concorrente encerre o alarme durante a apresentação.
```sh
docker compose stop simulator
docker compose run --rm --no-deps api python -m app.simulator --scenario --step-seconds 8
docker compose start simulator
```
Durante o cenário, consulte `/api/alarms` e a tabela `alarms`. Para observar o estado crítico antes da normalização, use os 8 segundos entre as etapas. Não insira anomalias diretamente no SQL.

Subscriber real (encerrar com Ctrl+C):
```sh
docker compose exec mosquitto mosquitto_sub -t 'facamp/industrial/#' -q 1 -v
```
