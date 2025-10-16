import os
from dotenv import load_dotenv
from datetime import timezone, timedelta

load_dotenv()

# Configuração do Kafka
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'crypto-prices')

# Configuração da API
API_URL = 'https://api.coingecko.com/api/v3/simple/price'
CRYPTO_IDS = ['bitcoin', 'ethereum', 'cardano', 'solana', 'ripple']
CURRENCIES = 'usd'
FETCH_INTERVAL = int(os.getenv('FETCH_INTERVAL', 60))  # segundos

# Configuração do banco de dados
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///crypto_prices.db')

# Configuração do consumer
CONSUMER_GROUP_ID = os.getenv('CONSUMER_GROUP_ID', 'crypto-consumer-group')

# Configuração de Timezone
TIMEZONE_OFFSET_HOURS = int(os.getenv('TIMEZONE_OFFSET_HOURS', -3))
TIMEZONE = timezone(timedelta(hours=TIMEZONE_OFFSET_HOURS))