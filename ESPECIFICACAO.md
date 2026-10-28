# FACAMP — IoT Industrial em Tempo Real | Especificação técnica

Esta especificação consolida as decisões e os critérios internos de implementação da prova de conceito acadêmica de monitoramento industrial. O projeto é local e reproduzível, com foco em modelagem, integridade, persistência e consultas temporais para a disciplina Tratamento e Armazenamento da Informação.

## 1. Fontes e interpretação dos requisitos

As referências didáticas são:
- `docs/references/Manual_FACAMP_IoT_Industrial_Tempo_Real_Open_Source_2026.pdf` — referência principal, especialmente as seções 6–16.
- `docs/references/facamp_tai_iot_industrial_tempo_real_animacao_interativa_v1.html` — apresentação com 15 slides, arquitetura e oito atividades de laboratório.

A matriz `docs/REQUISITOS.md` relaciona as fontes, as escolhas do projeto, a implementação e as evidências. As prioridades distinguem critérios essenciais de funcionamento (P0), complementos para a entrega (P1) e melhorias opcionais (P2). As escolhas adicionais desta especificação não devem ser atribuídas automaticamente ao material didático; divergências e limitações estão registradas na matriz.

## 2. Stack e arquitetura

Utilize:
- PostgreSQL 16 com TimescaleDB compatível.
- Eclipse Mosquitto, MQTT QoS 1.
- Python 3.11+ com paho-mqtt e psycopg 3.
- FastAPI.
- HTML/CSS/JavaScript com Chart.js.
- Compose compatível com Podman ou Docker.
- pytest.

A aplicação deve operar localmente, sem contas, APIs pagas ou serviços em nuvem.

Utilize versões compatíveis e fixadas. Evite imagens `latest` e dependências redundantes.

Implemente os serviços necessários no Compose. O FastAPI deve servir também os arquivos estáticos do dashboard, evitando um segundo servidor web e problemas desnecessários de CORS.

Use nomes de serviço na comunicação entre containers; não utilize `localhost` incorretamente dentro deles.

Dê preferência à extensão TimescaleDB. Documente PostgreSQL puro com particionamento como alternativa, sem implementar duas arquiteturas paralelas desnecessariamente.

## 3. Modelo de dados

Implemente as cinco tabelas principais:

- `assets`: equipamentos, setor, criticidade.
- `sensors`: sensor, ativo, tipo, unidade, intervalo.
- `telemetry`: timestamp UTC, sensor, valor, qualidade, sequência.
- `sensor_thresholds`: limites configuráveis.
- `alarms`: ocorrência, severidade, situação e fechamento.

Utilize os três ativos do manual: MOTOR-07, COMP-02 e BOMBA-03.

Cadastre os seis sensores originais:
- Temperatura e vibração do motor.
- Pressão e temperatura do compressor.
- Corrente e vazão da bomba.

Respeite intervalos individuais de 2 ou 5 segundos, conforme o cadastro original.

Implemente PK, FK, CHECK, restrições de qualidade, índices e hypertable. Valores numéricos devem ser finitos; timestamps precisam de timezone.

Garanta idempotência das leituras, incluindo retransmissões MQTT, com chave coerente e `ON CONFLICT`.

Implemente as consultas de último valor, histórico, agregação temporal, total de registros e alarmes. Inclua `EXPLAIN ANALYZE` e interprete os resultados sem afirmar que um índice foi utilizado quando não foi.

## 4. Simulador e comunicação MQTT

Crie um simulador para os seis sensores, com dados plausíveis, timestamps UTC, unidades corretas, sequência e publicação periódica.

Permita iniciar, interromper e configurar o simulador, além de executar um cenário determinístico de anomalia.

Implemente reconexão MQTT, logs estruturados e tratamento de falhas.

No ingestor:
- Valide JSON, identificador, unidade, timestamp, qualidade e valor.
- Rejeite dados inválidos com registro do motivo.
- Persista leituras em transações.
- Utilize batch configurável e flush por tempo, o que ocorrer primeiro.
- Não limpe o buffer antes de confirmar o commit.
- Trate falhas temporárias com retry limitado e backoff.
- Evite duplicações e decisões incorretas causadas por mensagens antigas.

Adote inicialmente um flush de aproximadamente 1–2 segundos para facilitar a visualização em tempo quase real. Mantenha limites configuráveis e teste a latência real.

Não implemente filas distribuídas ou componentes adicionais se não forem necessários.

## 5. Alarmes e comportamento determinístico

Utilize os thresholds do manual. Para a temperatura do MOTOR-07, considere atenção acima de 75 °C e criticidade acima de 85 °C, documentando a regra de comparação.

Implemente uma máquina de estados simples e testável:

NORMAL → WARN → CRITICAL → NORMAL.

Uma leitura anormal deve gerar um alarme somente quando ocorrer uma transição relevante; leituras repetidas não devem abrir dezenas de alarmes iguais.

Ao agravar de WARN para CRITICAL, encerre a ocorrência anterior e registre a nova severidade preservando o histórico.

Na normalização, feche a ocorrência ativa com timestamp.

Mantenha consistência com o estado ACK, se implementado, e não trate reconhecimento como normalização do sensor.

Use transações para manter telemetria e mudanças de alarmes coerentes. Verifique as permissões de UPDATE necessárias para fechamento.

O teste oficial deve percorrer:
68 °C → 78 °C → 88 °C → 70 °C.

A injeção da anomalia deve passar pelo MQTT real, nunca inserir diretamente no banco ou modificar apenas a interface.

## 6. API

Implemente no mínimo:

- `GET /api/assets`
- `GET /api/assets/{id}/current`
- `GET /api/sensors/{id}/history?minutes=60`
- `GET /api/alarms?state=OPEN`
- `GET /health`

Use Pydantic para validação, consultas SQL parametrizadas e contratos JSON consistentes.

Respostas de erro devem ser claras e não expor credenciais, SQL interno ou detalhes sensíveis.

Considere paginação ou limites máximos para evitar consultas de histórico excessivas.

## 7. Dashboard — UX/UI

Desenvolva uma interface em português brasileiro, moderna, sóbria, acessível e fácil de entender.

O público principal é um operador industrial ou professor que deseja compreender rapidamente a situação dos equipamentos.

Organize a interface em:
1. **Visão geral:** estado da planta, equipamentos, sensores ativos e alarmes.
2. **Monitoramento:** leituras atuais e séries temporais com filtros de ativo, sensor e período.
3. **Alarmes:** eventos ativos, severidade e histórico.
4. **Informações do sistema:** conexão, última atualização e saúde dos serviços.

Diretrizes visuais:
- Identidade técnica e profissional, sem visual de template genérico.
- Hierarquia clara e espaçamento consistente.
- Cards moderados, sem excesso de informação.
- Tipografia legível.
- Cores semânticas: normal, atenção, crítico e indisponível.
- Não depender exclusivamente de cores: usar texto e ícones.
- Gráficos com unidade, eixo temporal e legendas corretas.
- Não misturar grandezas incompatíveis em um mesmo eixo.
- Layout responsivo em desktop, tablet e smartphone.
- Interações com teclado e estados de foco visíveis.

Inclua estados explícitos de carregamento, ausência de dados, perda de conexão e leituras desatualizadas.

Cada sensor deve mostrar a última leitura e horário correspondente. Não exiba “online” apenas porque a página está aberta.

Atualize os dados com polling de 2–5 segundos. Evite requisições sobrepostas, chamadas redundantes e recriação desnecessária dos gráficos.

Todo número operacional deve vir da API. Não copie valores estáticos dos slides para o dashboard funcional.

O HTML de referência é uma demonstração visual; não reutilize seu simulador JavaScript como fonte de verdade.

Não mostre consumo energético da planta sem cadastrar e implementar o sensor correspondente.

Prefira CSS e JavaScript simples, sem frameworks pesados. O dashboard deve funcionar localmente sem depender de CDN em tempo de execução.

## 8. Segurança e operação

- Credenciais apenas em variáveis de ambiente.
- `.env.example` sem segredos reais.
- `.gitignore` adequado.
- Broker MQTT de laboratório restrito ao ambiente local.
- PostgreSQL não exposto à rede pública.
- Usuário da aplicação com permissões mínimas suficientes.
- Consultas parametrizadas.
- Logs sem credenciais.
- Healthchecks e inicialização reproduzível.
- Backup e restauração testados em banco separado.

Documente as limitações de segurança da prova de conceito. Não configure autenticação corporativa ou TLS completo se isso comprometer desnecessariamente o escopo local.

## 9. Testes e critérios de aceitação

Utilize pytest e testes de integração sempre que possível.

Critérios P0 — indispensáveis:
- Ambiente inicializa.
- Três ativos e seis sensores cadastrados.
- Seis sensores publicam via MQTT.
- Ingestão automática e sem duplicações.
- Banco preserva histórico e integridade.
- API consulta os dados persistidos.
- Dashboard atualiza com leituras reais.
- Cenário NORMAL/WARN/CRITICAL/NORMAL funciona.
- Alarmes possuem histórico e fechamento.
- README permite reproduzir a execução.

Critérios P1 — entrega completa:
- Layout validado nas três larguras.
- Evidências reais de banco, MQTT e alarmes.
- Backup/restore executado e conferido.
- Logs e tratamento de falhas.
- Documentação de ferramentas e licenças.
- Guia de demonstração de 10–12 minutos.

Critérios P2 — somente após P0/P1:
- Teste de carga progressivo.
- Ajustes de desempenho mensurados.
- Melhorias visuais não essenciais.

Inclua testes de mensagem malformada, sensor desconhecido, duplicidade, indisponibilidade temporária do banco e reconexão.

Nunca declare um teste aprovado sem executá-lo.

## 10. Etapas de desenvolvimento

- Fase A: infraestrutura, esquema e cadastro.
- Fase B: simulador, MQTT e ingestão.
- Fase C: API, dashboard e alarmes.
- Fase D: testes integrados, documentação e acabamento visual.

As convenções do projeto incluem timestamps UTC no transporte e no banco, interface em português brasileiro, SQL parametrizado e credenciais em variáveis de ambiente. O histórico de validação e as limitações ficam em `docs/PROGRESS.md`. As evidências devem distinguir testes unitários, execução integrada e inspeção visual.

## 11. Entregáveis finais

Produza código-fonte completo, Compose, SQL, configurações, testes, README, matriz de requisitos, evidências e roteiro de apresentação.

Use nomes claros e estrutura simples.

Na entrega final, apresente:
- O que foi implementado.
- O que foi efetivamente testado.
- O que permanece pendente.
- Os comandos exatos de inicialização.
- Onde encontrar as evidências.

**Definição de concluído:** um usuário consegue iniciar o sistema localmente, observar a telemetria real, provocar uma falha via MQTT e comprovar a ocorrência e normalização do alarme no PostgreSQL e no dashboard.

Não considere o projeto concluído com protótipos estáticos, arquivos vazios, componentes desconectados ou testes apenas simulados.
