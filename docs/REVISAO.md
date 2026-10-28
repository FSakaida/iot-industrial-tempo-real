# Revisão para publicação

Validação executada em ambiente separado entre `2026-10-28T23:37:49.778047+00:00` e `2026-10-28T23:38:51.987721+00:00` (UTC).

## Escopo

- Comentários de concorrência, leituras antigas e qualidade simplificados; docstring de ingestão esclarece o ACK das mensagens válidas.
- Comentário do teste de integridade corrigido: cada tentativa usa uma transação própria, sem savepoints.
- Catálogo de sensores formatado sem alterar identificadores, valores, unidades, intervalos ou ordem.
- Comparação da árvore sintática Python, desconsiderando docstrings, sem diferenças de comportamento. SQL, configuração MQTT e interface preservados byte a byte.
- README revisado com instalação, operação, alarmes, testes, backup e limitações. Avisos de terceiros mantidos; nenhuma licença foi atribuída ao código original.
- ZIP duplicado retirado da pasta do projeto; artefatos locais, credenciais, logs, relatórios e dumps excluídos do conjunto de publicação pelo `.gitignore`. Os arquivos locais de operação foram preservados.

## Instalação limpa

Foi usada uma cópia dos arquivos candidatos à publicação, sem reutilizar `.env`, ambiente virtual ou volumes de dados. `scripts/setup.py` gerou credenciais novas; um novo ambiente virtual recebeu `requirements-dev.txt`. O build Docker reutilizou camadas disponíveis no cache. As portas de teste foram 18000 (API) e 18883 (MQTT), com nome de projeto, imagem e volumes separados. A aplicação habitual na porta 8000 permaneceu independente.

Os comandos de inicialização do README foram verificados com essa alteração de portas e isolamento do Compose. Os scripts SQL inicializaram três ativos, seis sensores e a hypertable em um volume novo. Os scripts e a configuração versionados não receberam adaptações para o teste.

## Resultados

| Verificação | Resultado |
|---|---|
| Testes unitários e contratos HTTP | 56 aprovados; um aviso de depreciação de dependência |
| Integração MQTT → banco → API | 20 verificações aprovadas |
| Alarmes | Cenário 68 → 78 → 88 → 70 °C, transições, fechamento, ACK, qualidade e leituras antigas aprovados |
| Resiliência | Indisponibilidade real do banco e reconexão MQTT aprovadas |
| Restauração | 130 leituras, 5 alarmes e 6 sensores; contagens e assinaturas das cinco tabelas iguais |
| Acesso HTTP | 12 caminhos responderam HTTP 200, incluindo dashboard, arquivos estáticos, documentação e endpoints principais |
| Coleta contínua | Contagem cresceu de 88 para 96 durante a conferência |
| Arquivos publicáveis | Regras de exclusão conferidas; senhas locais e padrões de chaves/tokens não encontrados no conjunto publicado |

Etapas da suíte:

| Etapa | Resultado | Duração (s) |
|---|---|---:|
| `pytest.txt` | PASS | 5.539 |
| `compose.txt` | PASS | 0.233 |
| `pause_simulator.txt` | PASS | 0.439 |
| `e2e.txt` | PASS | 27.722 |
| `resilience.txt` | PASS | 20.174 |
| `backup_restore.txt` | PASS | 7.013 |
| `sql.txt` | PASS | 0.184 |
| `services.txt` | PASS | 0.122 |
| `logs.txt` | PASS | 0.128 |
| `resume_simulator.txt` | PASS | 0.643 |

As saídas brutas desta execução são locais e não são versionadas. O relatório acima registra o resultado efetivamente obtido; os scripts necessários para reproduzir a verificação estão no repositório.

## Limites e decisões pendentes

- As inspeções visuais em 1440 × 1000, 768 × 1024 e 390 × 844 são anteriores a esta revisão. A interface não foi alterada; não foi repetida uma validação visual completa.
- Windows, Podman, aparelhos físicos, testes de carga e falha simultânea de máquina/processo não foram validados nesta revisão.
- Definir uma licença para o código original depende dos responsáveis. As condições do TimescaleDB Community e do Docker Desktop continuam aplicáveis.
- Autenticação da API, autenticação/TLS/ACL MQTT e metas de recuperação permanecem fora da configuração local atual.
