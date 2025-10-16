import requests
import json
import time
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import sys
from datetime import datetime
import config

def create_producer():
    """Cria um producer do Kafka com retentativas de conexão."""
    retries = 10
    delay = 5
    for i in range(retries):
        try:
            print(f"Tentando conectar ao Kafka... Tentativa {i + 1}/{retries}")
            producer = KafkaProducer(
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("✅ Conectado ao Kafka com sucesso!")
            return producer
        except NoBrokersAvailable:
            print(f"Broker do Kafka indisponível. Tentando novamente em {delay}s...")
            time.sleep(delay)
    
    print("❌ Não foi possível conectar ao Kafka após várias tentativas. Encerrando.")
    sys.exit(1)

def fetch_crypto_prices():
    """Busca preços das criptomoedas da API CoinGecko"""
    try:
        params = {
            'ids': ','.join(config.CRYPTO_IDS),
            'vs_currencies': config.CURRENCIES,
            'include_24hr_change': 'true'
        }
        
        response = requests.get(config.API_URL, params=params, timeout=10)
        response.raise_for_status()
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao buscar dados da API: {e}")
        return None

def send_to_kafka(producer, data):
    """Envia dados para o Kafka"""
    if not data:
        return
    
    timestamp = datetime.utcnow().isoformat()
    
    for crypto_id, price_data in data.items():
        message = {
            'crypto_id': crypto_id,
            'price_usd': price_data.get('usd', 0),
            'change_24h': price_data.get('usd_24h_change', 0),
            'timestamp': timestamp
        }
        
        producer.send(config.KAFKA_TOPIC, value=message)
        print(f"📤 Enviado: {crypto_id} = ${message['price_usd']:.2f}")
    
    producer.flush()

def main():
    """Função principal do producer"""
    print("🚀 Iniciando Producer...")
    print(f"📊 Monitorando: {', '.join(config.CRYPTO_IDS)}")
    print(f"⏱️  Intervalo: {config.FETCH_INTERVAL}s\n")
    
    producer = create_producer()
    
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Buscando preços...")
            
            prices = fetch_crypto_prices()
            send_to_kafka(producer, prices)
            
            time.sleep(config.FETCH_INTERVAL)
    
    except KeyboardInterrupt:
        print("\n\n⛔ Producer encerrado pelo usuário")
    
    finally:
        producer.close()
        print("👋 Conexão com Kafka fechada")

if __name__ == "__main__":
    main()
