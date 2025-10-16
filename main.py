import json
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import time
import sys
from datetime import datetime, timezone, timedelta
import config
from database import get_session, CryptoPrice, init_db

def create_consumer():
    """Cria um consumer do Kafka com retentativas de conexão"""
    retries = 10
    delay = 5
    for i in range(retries):
        try:
            print(f"Tentando conectar ao Kafka... Tentativa {i + 1}/{retries}")
            consumer = KafkaConsumer(
                config.KAFKA_TOPIC,
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=config.CONSUMER_GROUP_ID,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            print("✅ Conectado ao Kafka com sucesso!")
            return consumer
        except NoBrokersAvailable:
            print(f"Broker do Kafka indisponível. Tentando novamente em {delay}s...")
            time.sleep(delay)
    
    print("❌ Não foi possível conectar ao Kafka após várias tentativas. Encerrando.")
    sys.exit(1)

def process_message(message_value, session):
    """Processa a mensagem recebida e salva no banco"""
    try:
        timestamp_utc = datetime.fromisoformat(message_value['timestamp'])
        crypto_price = CryptoPrice(
            crypto_id=message_value['crypto_id'],
            price_usd=message_value['price_usd'],
            timestamp=timestamp_utc
        )
        
        session.add(crypto_price)
        session.commit()
        
        change = message_value.get('change_24h', 0)
        change_icon = "📈" if change >= 0 else "📉"
        
        print(f"💾 Salvo: {crypto_price.crypto_id.upper()} = "
              f"${crypto_price.price_usd:.2f} "
              f"{change_icon} {change:.2f}%")
        
        if abs(change) > 5:
            print(f"⚠️  ALERTA: {crypto_price.crypto_id.upper()} com variação de {change:.2f}% nas últimas 24h!")
    
    except Exception as e:
        print(f"❌ Erro ao processar mensagem: {e}")
        session.rollback()

def main():
    """Função principal do consumer"""
    print("🚀 Iniciando Consumer...")
    print(f"📥 Aguardando mensagens do tópico: {config.KAFKA_TOPIC}\n")
    
    # Inicializa banco de dados
    init_db()
    
    consumer = create_consumer()
    session = get_session()
    
    try:
        for message in consumer:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Mensagem recebida")
            process_message(message.value, session)
    
    except KeyboardInterrupt:
        print("\n\n⛔ Consumer encerrado pelo usuário")
    
    finally:
        session.close()
        consumer.close()
        print("👋 Conexões fechadas")

if __name__ == "__main__":
    main()
