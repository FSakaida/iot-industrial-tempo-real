# Progresso

Os arquivos brutos de execução citados neste documento ficam em `evidence/` na máquina de validação e não são versionados. Podem ser produzidos novamente com `python scripts/verify.py`. Os resultados históricos abaixo não representam uma nova execução.

## Rodapé explicativo adicionado em 28/10/2026
- Dois diagramas no final do dashboard: estrutura das cinco tabelas com PK/FK e cardinalidades, e fluxo simulador → MQTT → ingestor → banco → API → dashboard.
- Esquema conferido com sql/01_schema.sql; limites opcionais por sensor e unicidade de ocorrência ativa explicados.
- Diagramas em HTML/CSS/SVG locais, com explicações textuais e organização vertical no celular; sem bibliotecas ou serviços adicionais.
- 56 testes pytest aprovados (`evidence/pytest_footer.txt`). Conferência visual e de largura no navegador em 1440, 768 e 390 pixels; sem transbordamento horizontal.
- Aplicação local atualizada; banco, ingestão e contratos da API preservados. Integração completa anterior não foi repetida para esta mudança visual.

## Atualização de 28/10/2026: testes automatizados
- Execução integral de `scripts/verify.py`: PASS em todas as etapas.
- 56 testes pytest aprovados, com relatório JUnit em `evidence/pytest.xml`.
- 20 verificações integradas MQTT/DB/API aprovadas, incluindo qualidade zero, CRITICAL→WARN, unicidade do alarme ativo, rollback conjunto de leituras/alarme, paginação e tentativa de injeção SQL.
- Recuperação real após parada do PostgreSQL e reinício do MQTT aprovada.
- Backup restaurado em outro banco com 5.620 leituras, 15 alarmes e 6 sensores; contagens e hashes das cinco tabelas iguais.
- Relatório JSON agora registra RUNNING/PASS/FAIL, horários e duração por etapa; não conserva PASS de uma execução anterior se houver erro.
- Sessão MQTT do teste é limpa, evitando receber o backlog de testes anteriores.
- Simulador retomado ao final; API e banco saudáveis. Código da aplicação não precisou de correções.
- Cobertura e reprodução: `docs/TESTES.md`. Automação de navegador e carga permanecem fora desta suíte; verificações visuais anteriores são manuais.

Fase D concluída para o MVP P0/P1, com limitações abaixo. scripts/verify.py executado integralmente com resultado PASS; última mudança da API novamente validada com as 14 verificações MQTT/DB/API. Ambiente validado no macOS, Docker Desktop, containers Linux arm64. Execução local em 27/10/2026 (evidências técnicas guardam timestamps UTC de 28/10).

## Implementado
Compose; PostgreSQL16/TimescaleDB; 5 tabelas, hypertable, checks e seed; broker Mosquitto; simulador de 6 sensores a 2/5 s; ingestor QoS1 com batch/retry/idempotência e alarmes transacionais; FastAPI; dashboard Chart.js local em português; configuração sem segredos no código; testes, backup/restore, matriz, licenças e roteiro de 12 min.

## Histórico da entrega de 27/10
- 40 testes pytest: validação, fusos, qualidade, valores finitos, fronteiras de limites, falha temporária, buffer preservado/ACK após commit e contratos de parâmetros.
- 14 verificações integradas em rede MQTT/DB/API reais, incluindo cadastro, seis tópicos, quatro etapas do cenário oficial, histórico e fechamento, repetição, ACK, fora de ordem, duplicidade, inválidos, API e menor privilégio. `evidence/e2e.txt`.
- Queda real do PostgreSQL com mensagem publicada durante a indisponibilidade, depois persistida; parada e reconexão do Mosquitto; `evidence/resilience.txt`.
- Instalação em volume vazio separado: 3 ativos, 6 sensores, role iot_app e hypertable presentes; `evidence/cold_start.txt`. Ambiente temporário removido após teste.
- Backup lógico restaurado em outro banco; contagens e hashes de conteúdo comparados nas cinco tabelas; `evidence/backup_restore.json`. Banco principal preservado.
- SQL real, histórico, agregação, contagem, alarmes e EXPLAIN ANALYZE; `evidence/sql.txt`, interpretação em DESEMPENHO.md.
- Interface inspecionada em 1440x1000, 768x1024 e 390x844; sem transbordamento da página após estabilizar o gráfico. Filtros de equipamento/sensor, alarmes ativos, gráfico com unidade e perda de conexão API verificados no navegador.
- Captura de estado crítico produzido via MQTT real, seguida de normalização e retomada do simulador; `evidence/dashboard_alarme_critico.jpg` e `anomaly_mqtt.txt`.

## Pendências e limites
- P2 opcional: carga progressiva, ajuste de desempenho em escala e políticas automáticas hot/warm/cold não executados.
- Podman e Windows não foram testados; Compose validado com Docker Desktop/macOS.
- Sem integração com DBeaver: SQL foi verificado com psql e há evidências equivalentes em texto. Capturas do dashboard são de navegador em três viewports, não de aparelhos físicos.
- Sem garantia de durabilidade em falha simultânea de máquina/processo: buffer Python e parte do estado Paho são em memória. MQTT QoS1 não equivale a exactly-once.
- TimescaleDB Community inclui licença TSL em parte dos recursos; gratuito self-hosted, não integralmente OSI. Alternativa PostgreSQL puro documentada.

Bloqueios: nenhum para uso local testado. Próxima ação do usuário: abrir http://localhost:8000 e seguir DEMONSTRACAO.md. Para retomar em outra máquina: README e REQUISITOS.md.
