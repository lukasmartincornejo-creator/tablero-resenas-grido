import streamlit as st
import pandas as pd
import plotly.express as px
from google_play_scraper import Sort, reviews_all
from datetime import datetime, timedelta
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import io

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y MARCA GRIDO
# ==========================================
st.set_page_config(
    page_title="VoC Dashboard | Grido",
    page_icon="https://upload.wikimedia.org/wikipedia/commons/2/22/Logo_Grido.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados basados en la UI de Grido
st.markdown("""
    <style>
    /* Fondo principal y fuentes */
    .stApp {
        background-color: #f4f6f9;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Encabezados y títulos */
    h1, h2, h3 {
        color: #002169 !important; /* Azul Grido */
        font-weight: 700 !important;
    }
    
    /* Tarjetas de Métricas (KPIs) */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        padding: 18px !important;
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 12px rgba(0, 33, 105, 0.05) !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #002169 !important;
        font-size: 0.9rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricValue"] {
        color: #e30613 !important; /* Rojo Grido */
        font-weight: 800 !important;
    }
    
    /* Botones primarios (Celeste Grido) */
    div.stButton > button {
        background-color: #00a0e9 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #0080c0 !important;
        box-shadow: 0 4px 8px rgba(0, 160, 233, 0.3) !important;
    }

    /* Pestañas (Tabs) */
    button[data-baseweb="tab"] {
        color: #002169 !important;
        font-weight: 600 !important;
    }
    button[aria-selected="true"] {
        border-bottom-color: #e30613 !important; /* Línea roja Grido */
    }
    </style>
""", unsafe_allow_html=True)

# Header con Logo Oficial de Grido
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/22/Logo_Grido.png", width=120)
with col_titulo:
    st.title("Dashboard Ejecutivo: Monitoreo Voz del Cliente (VoC)")
    st.caption("Plataforma de análisis de experiencia de usuario y sentimiento en tiempo real")

# ==========================================
# 2. BARRA LATERAL (CONTROLES)
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/2/22/Logo_Grido.png", width=140)
st.sidebar.markdown("---")
st.sidebar.header("🕹️ Panel de Control")

APP_ID = 'com.grido.app'
dias_analisis = st.sidebar.slider("Periodo a analizar (Días):", min_value=7, max_value=60, value=15)

if st.sidebar.button("🔄 Actualizar datos on-demand", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ==========================================
# 3. EXTRACCIÓN Y CACHÉ DE DATOS
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

with st.spinner("Descargando información de Google Play Store..."):
    df = cargar_datos(APP_ID)

if df.empty:
    st.error("No se pudieron recuperar datos de Play Store.")
    st.stop()

# ==========================================
# 4. SEGMENTACIÓN TEMPORAL COMPARATIVA
# ==========================================
ahora = datetime.now()
fecha_corte_actual = ahora - timedelta(days=dias_analisis)
fecha_corte_anterior = fecha_corte_actual - timedelta(days=dias_analisis)

df_actual = df[(df['at'] >= fecha_corte_actual) & (df['at'] <= ahora)].copy()
df_anterior = df[(df['at'] >= fecha_corte_anterior) & (df['at'] < fecha_corte_actual)].copy()

fecha_mes_actual = ahora - timedelta(days=30)
fecha_mes_anterior = ahora - timedelta(days=60)
df_mes_anterior = df[(df['at'] >= fecha_mes_anterior) & (df['at'] < fecha_mes_actual)].copy()

# Paleta de colores ajustada a la marca
color_map = {'Positivo': '#00a0e9', 'Neutro': '#a0aec0', 'Negativo': '#e30613'}

# ==========================================
# 5. TARJETAS DE KPIS COMPARATIVAS
# ==========================================
st.markdown("---")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_historico = len(df)
vol_actual = len(df_actual)
vol_anterior = len(df_anterior)
delta_vol = vol_actual - vol_anterior

rating_actual = df_actual['score'].mean() if not df_actual.empty else 0
rating_anterior = df_anterior['score'].mean() if not df_anterior.empty else 0
delta_rating = rating_actual - rating_anterior

csat_actual = (df_actual['sentimiento'] == 'Positivo').mean() * 100 if not df_actual.empty else 0
csat_anterior = (df_anterior['sentimiento'] == 'Positivo').mean() * 100 if not df_anterior.empty else 0
delta_csat = csat_actual - csat_anterior

kpi1.metric("Reseñas Históricas", f"{total_historico:,}")
kpi2.metric(f"Reseñas ({dias_analisis}d)", f"{vol_actual:,}", delta=f"{delta_vol:+} vs p. anterior")
kpi3.metric("Rating Promedio", f"{rating_actual:.2f} ⭐", delta=f"{delta_rating:+.2f} ⭐ vs p. anterior")
kpi4.metric("CSAT Reciente", f"{csat_actual:.1f}%", delta=f"{delta_csat:+.1f}% vs p. anterior")

st.markdown("---")

# ==========================================
# 6. PESTAÑAS Y GRÁFICOS
# ==========================================
tab_volumen, tab_sentimiento, tab_palabras = st.tabs([
    "📈 Tendencia y Volumen", 
    "📊 Comparativa de Sentimiento", 
    "☁️ Diagnóstico Cualitativo (Nubes)"
])

# --- TAB 1: TENDENCIA ---
with tab_volumen:
    st.subheader(f"Evolución Diaria de Opiniones (Últimos {dias_analisis} días)")
    if not df_actual.empty:
        df_actual['fecha'] = df_actual['at'].dt.date
        df_time = df_actual.groupby(['fecha', 'sentimiento']).size().reset_index(name='cantidad')
        
        fig_line = px.bar(
            df_time, x='fecha', y='cantidad', color='sentimiento',
            color_discrete_map=color_map,
            barmode='stack', template="plotly_white"
        )
        fig_line.update_layout(xaxis_title="Fecha", yaxis_title="Cantidad de Reseñas", legend_title="Sentimiento")
        st.plotly_chart(fig_line, use_container_width=True)

# --- TAB 2: COMPARATIVA ---
with tab_sentimiento:
    st.subheader("Análisis Comparativo por Periodos")
    col_g1, col_g2, col_g3 = st.columns(3)
    
    with col_g1:
        st.markdown("##### 📜 Histórico Completo")
        fig_pie_h = px.pie(
            df, names='sentimiento', color='sentimiento',
            color_discrete_map=color_map, hole=0.4, template="plotly_white"
        )
        fig_pie_h.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie_h, use_container_width=True)

    with col_g2:
        st.markdown("##### 📅 Mes Anterior (30-60 días atrás)")
        if not df_mes_anterior.empty:
            fig_pie_m = px.pie(
                df_mes_anterior, names='sentimiento', color='sentimiento',
                color_discrete_map=color_map, hole=0.4, template="plotly_white"
            )
            fig_pie_m.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie_m, use_container_width=True)

    with col_g3:
        st.markdown(f"##### 🚀 Periodo Actual ({dias_analisis} días)")
        if not df_actual.empty:
            fig_pie_s = px.pie(
                df_actual, names='sentimiento', color='sentimiento',
                color_discrete_map=color_map, hole=0.4, template="plotly_white"
            )
            fig_pie_s.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie_s, use_container_width=True)

# --- TAB 3: NUBES DE PALABRAS ---
with tab_palabras:
    st.subheader("Análisis Semántico del Periodo Actual")
    
    stopwords_pro = set(STOPWORDS)
    stopwords_pro.update([
        "que", "la", "el", "de", "en", "para", "una", "un", "es", "por", "si", "app", 
        "grido", "pero", "con", "me", "al", "lo", "como", "las", "y", "se", "te", "ni", 
        "creo", "tengo", "puedo", "muy", "mas", "mi", "ya", "bien", "mal", "hola", "hacer",
        "todo", "nada", "dia", "favor", "pido", "version", "actualizacion", "hace"
    ])
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("##### 💙 Atributos Positivos Valorados")
        df_p = df_actual[df_actual['sentimiento'] == 'Positivo']
        if not df_p.empty and df_p['content'].dropna().str.len().sum() > 0:
            txt_p = " ".join(review for review in df_p['content'].dropna().astype(str))
            wc_p = WordCloud(width=800, height=450, background_color='white', stopwords=stopwords_pro, colormap='Blues').generate(txt_p)
            
            fig_wc1, ax_wc1 = plt.subplots(figsize=(8, 4.5))
            ax_wc1.imshow(wc_p, interpolation='bilinear')
            ax_wc1.axis("off")
            st.pyplot(fig_wc1)

    with c2:
        st.markdown("##### 🔴 Puntos de Fricción (Atención Requerida)")
        df_n = df_actual[df_actual['sentimiento'] == 'Negativo']
        if not df_n.empty and df_n['content'].dropna().str.len().sum() > 0:
            txt_n = " ".join(review for review in df_n['content'].dropna().astype(str))
            wc_n = WordCloud(width=800, height=450, background_color='white', stopwords=stopwords_pro, colormap='Reds').generate(txt_n)
            
            fig_wc2, ax_wc2 = plt.subplots(figsize=(8, 4.5))
            ax_wc2.imshow(wc_n, interpolation='bilinear')
            ax_wc2.axis("off")
            st.pyplot(fig_wc2)

# ==========================================
# 7. EXPORTACIÓN
# ==========================================
st.markdown("---")
st.subheader("📥 Exportar Datos")

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Historico_Completo', index=False)
    df_actual.to_excel(writer, sheet_name='Periodo_Actual', index=False)
    df_anterior.to_excel(writer, sheet_name='Periodo_Anterior_Eq', index=False)

st.download_button(
    label="📄 Descargar Dataset Comparativo (.xlsx)",
    data=buffer.getvalue(),
    file_name=f"Reporte_VoC_Grido_Comparativo_{datetime.now().strftime('%Y%m%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
