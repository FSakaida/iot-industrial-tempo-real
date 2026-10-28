# Ferramentas e licenças

O código original do projeto não recebeu uma licença de distribuição nesta revisão. A definição de uma licença depende da autorização dos responsáveis. As licenças abaixo se aplicam aos componentes de terceiros e não concedem automaticamente uma licença ao projeto inteiro.

| Ferramenta | Versão fixada | Licença/condição | Fonte |
|---|---|---|---|
| PostgreSQL | 16, imagem Timescale | PostgreSQL License | https://www.postgresql.org/about/licence/ |
| TimescaleDB | 2.18.2-pg16 | Apache 2 + Timescale License (Community); gratuito self-hosted, não todo OSI | https://github.com/timescale/timescaledb/tree/2.18.2 |
| Eclipse Mosquitto | 2.0.21 | EPL 2.0 / EDL 1.0 | https://mosquitto.org/ |
| Python | 3.12.10 em container | PSF | https://docs.python.org/3/license.html |
| Paho MQTT | 2.1.0 | EPL 2.0 / EDL 1.0 | https://github.com/eclipse-paho/paho.mqtt.python |
| psycopg | 3.2.9 | LGPL 3 | https://www.psycopg.org/psycopg3/docs/basic/install.html |
| FastAPI | 0.115.12 | MIT | https://github.com/fastapi/fastapi |
| Uvicorn | 0.34.2 | BSD 3-Clause | https://github.com/encode/uvicorn |
| Pydantic | 2.12.3 | MIT | https://github.com/pydantic/pydantic |
| Chart.js | 4.4.8, vendorizado | MIT; licença junto ao arquivo | https://github.com/chartjs/Chart.js/tree/v4.4.8 |
| pytest | 8.3.5 | MIT | https://github.com/pytest-dev/pytest |
| Docker Desktop | instalado pelo usuário | Termos próprios; gratuidade depende do enquadramento | https://www.docker.com/legal/docker-subscription-service-agreement/ |
| Podman (alternativa) | não usado nos testes | Apache 2.0 | https://podman.io/ |

As bibliotecas conservam suas licenças. O projeto não incorpora código dos exemplos sem adaptação e não usa imagens da apresentação no dashboard. O material de aula original é mantido como referência didática, sem atribuir licença nova. A aplicação funciona localmente, sem serviços pagos ou APIs externas.

Documentação técnica consultada na implementação: Paho Client manual_ack/ack https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html ; imagem Timescale https://hub.docker.com/r/timescale/timescaledb .

As dependências de desenvolvimento adicionais são httpx 0.28.1 (BSD de três cláusulas) e PyYAML 6.0.2 (MIT). A versão do Compose deve ser conferida com `docker compose version`; o componente é distribuído sob Apache 2.0. Fontes: https://github.com/encode/httpx/blob/0.28.1/LICENSE.md , https://github.com/yaml/pyyaml/blob/6.0.2/LICENSE e https://github.com/docker/compose/blob/v5.5.1/LICENSE . As dependências transitivas estão fixadas em `requirements.lock` e mantêm seus respectivos avisos de licença.
