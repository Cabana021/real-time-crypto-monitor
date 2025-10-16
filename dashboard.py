import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import config
from datetime import datetime

st.set_page_config(
    page_title="Crypto Real-Time Dashboard",
    page_icon="📊",
    layout="wide"
)

@st.cache_resource
def get_engine():
    """Cria engine do banco de dados"""
    return create_engine(config.DATABASE_URL)

def load_data(hours=1):
    """Carrega dados do banco"""
    engine = get_engine()
    
    query = f"""
    SELECT crypto_id, price_usd, "timestamp"
    FROM crypto_prices
    WHERE "timestamp" >= datetime('now', '-{hours} hours', 'utc')
    ORDER BY "timestamp" DESC
    """
    
    df = pd.read_sql(query, engine)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def get_latest_prices():
    """Pega os preços mais recentes de cada crypto"""
    engine = get_engine()
    
    query = """
    SELECT crypto_id, price_usd, "timestamp"
    FROM crypto_prices
    WHERE id IN (
        SELECT MAX(id)
        FROM crypto_prices
        GROUP BY crypto_id
    )
    """
    
    df = pd.read_sql(query, engine)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def main():
    st.title("📊 Crypto Real-Time Dashboard")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.header("⚙️ Configurações")
    time_range = st.sidebar.selectbox(
        "Intervalo de tempo",
        options=[1, 3, 6, 12, 24],
        format_func=lambda x: f"{x} hora(s)"
    )
    
    auto_refresh = st.sidebar.checkbox("Auto-refresh (60s)", value=True)
    
    if auto_refresh:
        st.sidebar.info("Dashboard atualizando automaticamente...")
    
    # Carregar dados
    df = load_data(hours=time_range)
    latest_prices = get_latest_prices()
    
    if df.empty:
        st.warning("⚠️ Nenhum dado disponível. Certifique-se de que o Producer e Consumer estão rodando!")
        return
    
    # Converte a coluna de timestamp para o fuso horário local
    try:
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
        latest_prices['timestamp'] = latest_prices['timestamp'].dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
    except TypeError:
        # Lida com o caso onde a coluna já tem timezone, evitando erro em re-runs
        df['timestamp'] = df['timestamp'].dt.tz_convert('America/Sao_Paulo')
        latest_prices['timestamp'] = latest_prices['timestamp'].dt.tz_convert('America/Sao_Paulo')
        
    # Métricas atuais
    st.subheader("💰 Preços Atuais")
    cols = st.columns(len(config.CRYPTO_IDS))
    
    for idx, crypto in enumerate(config.CRYPTO_IDS):
        crypto_data = latest_prices[latest_prices['crypto_id'] == crypto]
        
        if not crypto_data.empty:
            current_price = crypto_data.iloc[0]['price_usd']
            
            # Calcular variação
            historical = df[df['crypto_id'] == crypto].sort_values('timestamp')
            if len(historical) > 1:
                old_price = historical.iloc[0]['price_usd']
                change = ((current_price - old_price) / old_price) * 100
                delta = f"{change:+.2f}%"
            else:
                delta = "N/A"
            
            with cols[idx]:
                st.metric(
                    label=crypto.upper(),
                    value=f"${current_price:,.2f}",
                    delta=delta
                )
    
    st.markdown("---")
    
    # Gráfico de linhas
    st.subheader("📈 Variação de Preços")
    
    fig = px.line(
        df,
        x='timestamp',
        y='price_usd',
        color='crypto_id',
        title=f"Preços das Últimas {time_range} Hora(s)",
        labels={'price_usd': 'Preço (USD)', 'timestamp': 'Horário Local', 'crypto_id': 'Criptomoeda'}
    )
    
    fig.update_layout(
        hovermode='x unified',
        height=500,
        legend_title_text='Criptomoeda'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela de dados recentes
    st.subheader("📋 Dados Recentes")
    
    # Pega os 5 registros mais recentes de cada cripto
    recent_data = df.sort_values('timestamp', ascending=False).groupby('crypto_id').head(5)
    
    # Formata o timestamp para exibição 
    recent_data['timestamp'] = recent_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Renderiza o dataframe final
    st.dataframe(
        recent_data[['crypto_id', 'price_usd', 'timestamp']],
        hide_index=True,
        use_container_width=True
    )
    
    # Info
    st.sidebar.markdown("---")
    
    # Usa o timestamp do dado mais recente para a "Última atualização"
    last_update_time = df['timestamp'].max().strftime('%H:%M:%S')
    st.sidebar.info(
        f"📅 Última atualização: {last_update_time}\n\n"
        f"📊 Registros na janela: {len(df)}"
    )
    
    # Auto refresh
    if auto_refresh:
        import time
        time.sleep(60)
        st.rerun()

if __name__ == "__main__":
    main()
