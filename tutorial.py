'''
==============================================================
Documentação do Projeto: Monitor de Criptomoedas em tempo real
==============================================================

Este projeto monitora preços de criptomoedas em tempo real, utilizando uma arquitetura de processamento de streams. 
A solução integra Python, Kafka (mensageria), SQLAlchemy (banco de dados) e Streamlit (dashboard), 
com a API CoinGecko como fonte de dados. Toda a infraestrutura é orquestrada com Docker Compose.

O fluxo de dados é simples:
- Producer: Coleta os dados da API e os envia para o Kafka.
- Consumer: Recebe os dados do Kafka e os salva permanentemente no banco de dados.
- Dashboard: Lê os dados do banco e os apresenta em uma interface interativa.

-----------------------------
1. O Producer (api.py)
-----------------------------
O Producer é o ponto de partida da pipeline. Sua função é buscar os dados de preço e publicá-los no Kafka.

* Coleta de Dados: A cada intervalo configurado (padrão de 60s), a função `fetch_crypto_prices()` 
faz uma requisição HTTP à API CoinGecko para obter os preços atuais das criptomoedas definidas 
em `config.py`, incluindo a variação percentual das últimas 24h.

* Envio para o Kafka: A função `send_to_kafka()` formata os dados recebidos em mensagens JSON individuais para cada criptomoeda. 
Cada mensagem contém o ID, o preço em USD, a variação e um timestamp UTC, garantindo um padrão de tempo consistente. 
As mensagens são então publicadas no tópico do Kafka.

* Robustez na Conexão: Para evitar falhas durante a inicialização (quando o Kafka pode ainda não estar pronto), a função 
`create_producer()` implementa uma lógica de retentativa, tentando se conectar ao Kafka várias vezes antes de encerrar o script.

-----------------------------
2. O Consumer (main.py)
-----------------------------
O Consumer escuta o tópico do Kafka, processa as mensagens e as persiste no banco de dados, transformando 
dados transitórios em registros permanentes.

* Consumo de Mensagens: A função `create_consumer()` se inscreve no tópico do Kafka. 
Com `auto_offset_reset='latest'`, ele processará apenas as mensagens que chegarem após sua inicialização.

* Processamento e Persistência: A função `process_message()` é o núcleo do Consumer. 
Ao receber uma mensagem, ela cria um objeto `CryptoPrice` e o salva no banco de dados usando SQLAlchemy. 
O timestamp é salvo exatamente como veio (em UTC).

* Monitoramento e Alertas: Após salvar, o Consumer exibe um log no console com o status do preço (📈 ou 📉).
Se a variação de preço for superior a 5%, um alerta especial é impresso.

* Robustez: Assim como o Producer, o Consumer possui uma lógica de retentativa de conexão. 
Além disso, o processo de escrita no banco está dentro de um bloco `try-except` que executa 
um `rollback` em caso de falha, mantendo a integridade dos dados.

---------------------------------
3. O Dashboard (dashboard.py)
---------------------------------
A interface visual do projeto, construída com Streamlit. Ela lê os dados diretamente do banco de dados, nunca do Kafka.

* **Interface Interativa**: A sidebar permite que o usuário selecione o intervalo de tempo dos dados a serem exibidos (1 a 24 horas) 
e ative um auto-refresh de 60 segundos.

* Visualização de Dados:
    * Métricas: Exibe o preço mais recente de cada criptomoeda e sua variação percentual no período selecionado.
    * Gráfico de Linhas: Um gráfico interativo da Plotly mostra a evolução dos preços ao longo do tempo.
    * Tabela de Dados: Apresenta os 5 registros mais recentes de cada criptomoeda.
* Conversão de Fuso Horário: Para exibir os horários de forma correta para o usuário, o dashboard converte os timestamps UTC
do banco de dados para o fuso horário local (ex: 'America/Sao_Paulo') antes de renderizar os gráficos e tabelas.

* Performance: A conexão com o banco de dados é otimizada com `@st.cache_resource`, que a cria uma única vez e a reutiliza, 
evitando reconexões a cada refresh.

------------------------------------------
4. Orquestração com Docker Compose
------------------------------------------
O arquivo `docker-compose.yml` define e conecta todos os serviços da aplicação, criando um ambiente isolado e consistente.

* Ordem de Inicialização: Utiliza `depends_on` para garantir uma ordem de inicialização correta: 
`zookeeper` -> `kafka` -> `producer` & `consumer` -> `dashboard`.

* Rede de Contêineres: Os serviços se comunicam através da rede interna do Docker. 
O Producer e o Consumer se conectam ao Kafka usando o nome do serviço (`kafka:9092`).

* Acesso Externo: O Dashboard é exposto na porta `8501`, permitindo que seja acessado pelo navegador em `http://localhost:8501`.

* Desenvolvimento Ágil: O código-fonte é montado como um volume dentro dos contêineres, o que permite que alterações no código 
sejam refletidas em tempo real sem a necessidade de reconstruir as imagens.
'''