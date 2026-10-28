# Evidências de execução

As capturas e os registros de inspeção manual são versionados. Relatórios de execução, saídas de comandos, logs e backups listados abaixo são gerados localmente por `python scripts/verify.py` e ignorados pelo Git. Os arquivos existentes na máquina foram preservados.
- `verification.json`: resultado do script scripts/verify.py; detalhes em cada saída abaixo.
- `pytest.xml`: relatório JUnit dos testes unitários.
- `pytest.txt`: 56 testes unitários; um aviso de depreciação de biblioteca, sem falhas.
- `e2e.txt`: 20 verificações reais MQTT → PostgreSQL → API, incluindo o cenário oficial.
- `resilience.txt`: banco temporariamente parado e broker reiniciado, com recuperação confirmada.
- `cold_start.txt`: inicialização em banco vazio separado (3 ativos, 6 sensores, role e hypertable).
- `backup_restore.json` e `.txt`: banco restaurado, contagens e hashes das cinco tabelas.
- `iot_industrial.dump`: dump lógico usado na última restauração testada.
- `sql.txt`: cadastros, hypertable/licença, leituras, agregações, alarmes e EXPLAIN ANALYZE reais.
- `services.txt`, `logs.txt`, `runtime_versions.txt`: serviços, logs e versões efetivas.
- `browser_checks.json`: verificações manuais no navegador e larguras usadas.
- `dashboard_desktop.jpg`, `dashboard_desktop_full.jpg`, `dashboard_tablet.jpg`, `dashboard_mobile.jpg`: telas com leituras da API.
- `dashboard_alarme_critico.jpg`, `anomaly_mqtt.txt`: anomalia publicada pelo MQTT real, capturada e depois normalizada.
- `dashboard_sem_conexao.jpg`: API interrompida mostra indisponibilidade e preserva valores anteriores com aviso.

As capturas mostram instantes diferentes; contagens e horários mudam durante a execução. Timestamps técnicos estão em UTC; a interface mostra o horário local de São Paulo. SQL, logs e JSON são evidência de execução; as telas não foram preenchidas com valores estáticos.

- `footer_checks.json`, `pytest_footer.txt` e `diagrama_*.jpg`: validação do rodapé explicativo com os dois diagramas, adicionado em 28/10/2026.

Nota editorial: em `pytest.txt` e `pytest_footer.txt`, caminhos absolutos da máquina foram abreviados para `<ambiente-python>` e `<projeto>`. Resultados, quantidades, avisos e durações dos testes foram preservados.
