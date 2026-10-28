# Desempenho observado

Os arquivos brutos de execução citados neste documento ficam em `evidence/` na máquina de validação e não são versionados. Podem ser produzidos novamente com `python scripts/verify.py`. Os resultados históricos abaixo não representam uma nova execução.

Execução local em Docker Desktop, PostgreSQL 16.7 / TimescaleDB 2.18.2. A consulta e o plano completos estão em evidence/sql.txt. Os números são observações deste conjunto pequeno, sem teste de carga nem promessa de SLA.

Na execução automatizada de 28/10/2026, o banco continha **5.620 leituras**. A consulta da temperatura MOTOR-07 na última hora, ORDER BY time DESC LIMIT 100, retornou **54 registros** em **0,079 ms**, com planejamento de **0,270 ms**. O plano usou `Custom Scan (ChunkAppend)` e `Index Scan` sobre `_hyper_1_1_chunk_telemetry_time_idx`. O filtro de tempo entrou no Index Cond; sensor_id foi aplicado depois, removendo 106 linhas. Houve 6 hits em buffers compartilhados e nenhuma exclusão de chunks.

**O otimizador não escolheu o índice secundário sensor+time nessa execução.** Não se deve afirmar que a existência de um índice prova seu uso. Estatísticas, tamanho da janela e seletividade afetam essa escolha. O tempo observado já é pequeno; comparar estratégias com volume maior é trabalho futuro, sem forçar planos artificialmente para gerar uma evidência favorável.

O lag médio entre envio e persistência dos últimos cinco minutos foi **1,135 s** naquele snapshot. O cenário oficial registra a latência observada de cada etapa em evidence/e2e.txt; ela inclui polling de teste. Durante queda real do banco, é esperado atraso superior ao nominal.

A UI consulta novamente a cada três segundos após a consulta anterior terminar. Sua latência visual acrescenta até esse intervalo e tempo das requisições. Não há WebSocket nem promessa de tempo real rígido.

O teste de carga progressivo (20/100 sensores e variação de batch) é P2, fora do MVP, e **não foi executado**. Antes de aumentar escala, medir CPU, memória, buffers, p95 de queries, latência de ingestão e crescimento de disco. Não há evidência para afirmar capacidade industrial.
