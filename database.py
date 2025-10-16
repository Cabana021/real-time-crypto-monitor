from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import config

Base = declarative_base()

class CryptoPrice(Base):
    __tablename__ = 'crypto_prices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    crypto_id = Column(String(50), nullable=False)
    price_usd = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    
    def __repr__(self):
        return f"<CryptoPrice(crypto_id={self.crypto_id}, price={self.price_usd}, timestamp={self.timestamp})>"

# Cria a engine e sessão
engine = create_engine(config.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Inicializa o banco de dados criando as tabelas"""
    Base.metadata.create_all(engine)
    print("✅ Banco de dados inicializado!")

def get_session():
    """Retorna uma nova sessão do banco"""
    return SessionLocal()

if __name__ == "__main__":
    init_db()
