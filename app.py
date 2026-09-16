import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google_play_scraper import Sort, reviews_all
from datetime import datetime, timedelta
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import io

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Tablero Ejecutivo | Reviews de Grido App",
    page_icon="🍦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado en CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

st.title("🍦 Dashboard Ejecutivo: Monitoreo de Voz del Cliente (VoC)")
st.caption("Análisis automatizado de experiencia de usuario y sentimiento en Google Play Store")

# ==========================================
# 2. BARRA LATERAL (CONTROLES)
# ==========================================
st.sidebar.image("https://img.icons8.com/color/96/ice-cream-cone.png", width=60)
st.sidebar.header("🕹️ Panel de Control")

APP_ID = 'com.grido.app'
dias_analisis = st.sidebar.slider("Periodo reciente (Días):", min_value=7, max_value=90, value=14)

if st.sidebar.button("🔄 Actualizar datos on-demand", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ==========================================
# 3. EXTRACCIÓN Y CACHÉ
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def cargar_datos(app_id):
    resenas = reviews_all(
        app_id,
        sleep_milliseconds=0,
        lang='es',
        country='ar',
        sort=Sort.NEWEST
    )
    df = pd.DataFrame(resenas)
    if not df.empty:
        df['at'] = pd.to_datetime(df['at'])
        def clasificar(score):
            if score <= 2: return 'Negativo'
            if score == 3: return 'Neutro'
            return 'Positivo'
        df['sentimiento'] = df['score'].apply(clasificar)
        df = df.drop(columns=['reviewId', 'userImage', 'replyContent', 'repliedAt'], errors='ignore')
    return df

with st.spinner("Descargando e indexando reseñas..."):
    df = cargar_datos(APP_ID)

if df.empty:
    st.error("No se pudieron recuperar datos.")
    st.stop()

# Filtros de fecha
fecha_corte = datetime.now() - timedelta(days=dias_analisis)
df_reciente = df[df['at'] >= fecha_corte].copy()

color_map = {'Positivo': '#2ecc71', 'Neutro': '#f39c12', 'Negativo': '#e74c3c'}

# ==========================================
# 4. TARJETAS DE KPIS SUPERIORES
# ==========================================
st.markdown("---")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_historico = len(df)
total_reciente = len(df_reciente)
rating_prom = df_reciente['score'].mean() if not df_reciente.empty else 0

# CSAT Estimado (% Positivos)
csat = (df_reciente['sentimiento'] == 'Positivo').mean() * 100 if not df_reciente.empty else 0

kpi1.metric("Reseñas Históricas", f"{total_historico:,}")
kpi2.metric(f"Reseñas ({dias_analisis} días)", f"{total_reciente:,}")
kpi3.metric("Rating Promedio", f"{rating_prom:.2f} ⭐")
kpi4.metric("CSAT Reciente", f"{csat:.1f}%")

st.markdown("---")

# ==========================================
# 5. ESTRUCTURA EN PESTAÑAS (TABS)
# ==========================================
tab1, tab2, tab3 = st.columns(3)
tab_volumen, tab_sentimiento, tab_palabras = st.tabs([
    "📈 Tendencia y Volumen", 
    "📊 Distribución de Sentimiento", 
    "☁️ Diagnóstico Cualitativo (Nubes)"
])

# --- TAB 1: TENDENCIA ---
with tab_volumen:
    st.subheader("Evolución Diaria del Sentimiento")
    if not df_reciente.empty:
        df_reciente['fecha'] = df_reciente['at'].dt.date
        df_time = df_reciente.groupby(['fecha', 'sentimiento']).size().reset_index(name='cantidad')
        
        fig_line = px.bar(
            df_time, x='fecha', y='cantidad', color='sentimiento',
            color_discrete_map=color_map,
            title=f"Volumen diario de opiniones en los últimos {dias_analisis} días",
            barmode='stack', template="plotly_white"
        )
        fig_line.update_layout(xaxis_title="Fecha", yaxis_title="Cantidad de Reseñas", legend_title="Sentimiento")
        st.plotly_chart(fig_line, use_container_width=True)

# --- TAB 2: DISTRIBUCIÓN ---
with tab_sentimiento:
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("Histórico General")
        fig_pie_h = px.pie(
            df, names='sentimiento', color='sentimiento',
            color_discrete_map=color_map, hole=0.5, template="plotly_white"
        )
        fig_pie_h.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie_h, use_container_width=True)

    with col_g2:
        st.subheader(f"Últimos {dias_analisis} días")
        if not df_reciente.empty:
            fig_pie_s = px.pie(
                df_reciente, names='sentimiento', color='sentimiento',
                color_discrete_map=color_map, hole=0.5, template="plotly_white"
            )
            fig_pie_s.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie_s, use_container_width=True)

# --- TAB 3: NUBES DE PALABRAS MEJORADAS ---
with tab_palabras:
    st.subheader("Análisis Semántico de la Experiencia de Usuario")
    
    # Stopwords ampliadas para limpiar ruido de negocio
    stopwords_pro = set(STOPWORDS)
    stopwords_pro.update([
        "que", "la", "el", "de", "en", "para", "una", "un", "es", "por", "si", "app", 
        "grido", "pero", "con", "me", "al", "lo", "como", "las", "y", "se", "te", "ni", 
        "creo", "tengo", "puedo", "muy", "mas", "mi", "ya", "bien", "mal", "hola", "hacer",
        "todo", "nada", "dia", "favor", "pido", "version", "actualizacion", "hace"
    ])
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("##### 🟢 Atributos Positivos Valorados")
        df_p = df_reciente[df_reciente['sentimiento'] == 'Positivo']
        if not df_p.empty and df_p['content'].dropna().str.len().sum() > 0:
            txt_p = " ".join(review for review in df_p['content'].dropna().astype(str))
            wc_p = WordCloud(width=800, height=450, background_color='white', stopwords=stopwords_pro, colormap='Greens').generate(txt_p)
            
            fig_wc1, ax_wc1 = plt.subplots(figsize=(8, 4.5))
            ax_wc1.imshow(wc_p, interpolation='bilinear')
            ax_wc1.axis("off")
            st.pyplot(fig_wc1)
        else:
            st.info("Sin datos suficientes.")

    with c2:
        st.markdown("##### 🔴 Puntos de Dolor (Puntos de Ficción)")
        df_n = df_reciente[df_reciente['sentimiento'] == 'Negativo']
        if not df_n.empty and df_n['content'].dropna().str.len().sum() > 0:
            txt_n = " ".join(review for review in df_n['content'].dropna().astype(str))
            wc_n = WordCloud(width=800, height=450, background_color='white', stopwords=stopwords_pro, colormap='Reds').generate(txt_n)
            
            fig_wc2, ax_wc2 = plt.subplots(figsize=(8, 4.5))
            ax_wc2.imshow(wc_n, interpolation='bilinear')
            ax_wc2.axis("off")
            st.pyplot(fig_wc2)
        else:
            st.info("Sin datos suficientes.")

# ==========================================
# 6. EXPORTACIÓN Y DESCARGA
# ==========================================
st.markdown("---")
st.subheader("📥 Exportación Ejecutiva")

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Historico', index=False)
    df_reciente.to_excel(writer, sheet_name='Periodo_Analizado', index=False)

st.download_button(
    label="📄 Descargar Dataset Completo en Excel (.xlsx)",
    data=buffer.getvalue(),
    file_name=f"Reporte_VoC_Grido_{datetime.now().strftime('%Y%m%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
