import streamlit as st
import pandas as pd
import plotly.express as px
from google_play_scraper import Sort, reviews_all
from datetime import datetime, timedelta
import io
import os

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Executive VoC Dashboard | Grido",
    page_icon="🍦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS con forzado estricto sobre clases internas de Streamlit
st.markdown("""
    <style>
    /* 1. OCULTAR BOTÓN DE COLAPSO DEL SIDEBAR */
    button[data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapseButton"],
    div[data-testid="collapsedControl"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* 2. FONDO Y ESTRUCTURA GENERAL */
    .stApp {
        background-color: #f8fafc !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #cbd5e1 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #002169 !important;
    }
    
    /* 3. TIPOGRAFÍA Y ENCABEZADOS DE ALTO CONTRASTE */
    h1, h2, h3, h4, h5, h6 {
        color: #002169 !important;
        font-family: 'Segoe UI', Roboto, sans-serif !important;
        font-weight: 800 !important;
    }
    p, span, label {
        color: #1e293b !important;
        font-family: 'Segoe UI', Roboto, sans-serif !important;
    }

    /* 4. TARJETAS DE KPIS */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        padding: 16px !important;
        border-radius: 12px !important;
        border: 2px solid #cbd5e1 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    }
    div[data-testid="stMetricLabel"] > div {
        color: #002169 !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricValue"] > div {
        color: #e30613 !important;
        font-weight: 800 !important;
    }

    /* 5. BOTONES PRIMARIOS Y DESCARGA EXCEL */
    div.stButton > button, div.stDownloadButton > button {
        background-color: #00a0e9 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        font-size: 0.95rem !important;
        padding: 0.6rem 1.2rem !important;
    }

    /* 6. SOBRESCRITURA DE INPUTS Y BUSCADORES (FORZADO MODO CLARO) */
    .stTextInput input, .stSelectbox div, .stMultiSelect div {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border-color: #94a3b8 !important;
    }
    div[data-baseweb="select"] span {
        color: #0f172a !important;
    }
    div[data-baseweb="tag"] {
        background-color: #e2e8f0 !important;
    }
    div[data-baseweb="tag"] span {
        color: #0f172a !important;
    }

    /* 7. ESTILO TABLA HTML NATIVA BLANCA */
    .tabla-blanca-container {
        background-color: #ffffff !important;
        border-radius: 10px;
        border: 1px solid #cbd5e1;
        padding: 10px;
        overflow-x: auto;
    }
    .tabla-blanca {
        width: 100%;
        border-collapse: collapse;
        background-color: #ffffff !important;
        color: #0f172a !important;
        font-family: sans-serif;
        font-size: 0.9rem;
    }
    .tabla-blanca th {
        background-color: #f1f5f9 !important;
        color: #002169 !important;
        font-weight: 700;
        text-align: left;
        padding: 12px;
        border-bottom: 2px solid #cbd5e1;
    }
    .tabla-blanca td {
        padding: 10px 12px;
        border-bottom: 1px solid #e2e8f0;
        color: #0f172a !important;
    }
    .tabla-blanca tr:hover {
        background-color: #f8fafc !important;
    }

    /* 8. PESTAÑAS (TABS) */
    button[data-baseweb="tab"] {
        color: #475569 !important;
        font-weight: 700 !important;
    }
    button[aria-selected="true"] {
        color: #e30613 !important;
        border-bottom-color: #e30613 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado Principal con Logo
RUTA_LOGO = "logo grido.png"

col_h_logo, col_h_title = st.columns([1, 5])

with col_h_logo:
    if os.path.exists(RUTA_LOGO):
        st.image(RUTA_LOGO, width=130)
    else:
        st.markdown("## 🍦")

with col_h_title:
    st.title("Tablero Ejecutivo: Monitoreo Voz del Cliente (VdC)")
    st.markdown("**Grido Argentina** | Análisis automatizado de experiencia de usuario y fricción - App Store")

# ==========================================
# 2. BARRA LATERAL
# ==========================================
if os.path.exists(RUTA_LOGO):
    st.sidebar.image(RUTA_LOGO, use_container_width=True)
else:
    st.sidebar.markdown("# **GRIDO - Voz del Cliente**")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🕹️ Panel de Control")

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

with st.spinner("Descargando datos de Google Play Store..."):
    df = cargar_datos(APP_ID)

if df.empty:
    st.error("No se pudieron recuperar datos de Play Store.")
    st.stop()

# ==========================================
# 4. SEGMENTACIÓN TEMPORAL Y CATEGORIZACIÓN
# ==========================================
ahora = datetime.now()
fecha_corte_actual = ahora - timedelta(days=dias_analisis)
fecha_corte_anterior = fecha_corte_actual - timedelta(days=dias_analisis)

df_actual = df[(df['at'] >= fecha_corte_actual) & (df['at'] <= ahora)].copy()
df_anterior = df[(df['at'] >= fecha_corte_anterior) & (df['at'] < fecha_corte_actual)].copy()

fecha_mes_actual = ahora - timedelta(days=30)
fecha_mes_anterior = ahora - timedelta(days=60)
df_mes_anterior = df[(df['at'] >= fecha_mes_anterior) & (df['at'] < fecha_mes_actual)].copy()

def categorizar_reclamo(texto):
    texto = str(texto).lower()
    if any(k in texto for k in ['tarjeta', 'pago', 'cobro', 'mercado', 'dinero', 'precio', 'descuento']):
        return 'Pagos y Promociones'
    elif any(k in texto for k in ['clave', 'contraseña', 'ingresar', 'login', 'mail', 'registro', 'cuenta']):
        return 'Acceso y Cuenta'
    elif any(k in texto for k in ['abrir', 'cierra', 'traba', 'lenta', 'error', 'pantalla', 'bug', 'funciona']):
        return 'Estabilidad App'
    elif any(k in texto for k in ['local', 'sucursal', 'pedido', 'demora', 'atencion', 'delivery', 'helado']):
        return 'Servicio y Pedidos'
    else:
        return 'Otros / General'

df_actual['categoria'] = df_actual['content'].apply(categorizar_reclamo)

color_map = {'Positivo': '#00a0e9', 'Neutro': '#94a3b8', 'Negativo': '#e30613'}

def aplicar_estilo_grafico(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#0f172a', size=12),
        xaxis=dict(title_font=dict(color='#002169', size=13), tickfont=dict(color='#0f172a')),
        yaxis=dict(title_font=dict(color='#002169', size=13), tickfont=dict(color='#0f172a')),
        legend=dict(font=dict(color='#0f172a'))
    )
    return fig

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
# 6. PESTAÑAS Y GRÁFICOS INTERACTIVOS
# ==========================================
tab_volumen, tab_sentimiento, tab_categorias, tab_explorador = st.tabs([
    "📈 Tendencia y Volumen", 
    "📊 Comparativa de Sentimiento", 
    "🎯 Pilares de Fricción",
    "💬 Explorador de Comentarios"
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
        fig_line = aplicar_estilo_grafico(fig_line)
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
        fig_pie_h = aplicar_estilo_grafico(fig_pie_h)
        fig_pie_h.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie_h, use_container_width=True)

    with col_g2:
        st.markdown("##### 📅 Mes Anterior (30-60 días atrás)")
        if not df_mes_anterior.empty:
            fig_pie_m = px.pie(
                df_mes_anterior, names='sentimiento', color='sentimiento',
                color_discrete_map=color_map, hole=0.4, template="plotly_white"
            )
            fig_pie_m = aplicar_estilo_grafico(fig_pie_m)
            fig_pie_m.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie_m, use_container_width=True)

    with col_g3:
        st.markdown(f"##### 🚀 Periodo Actual ({dias_analisis} días)")
        if not df_actual.empty:
            fig_pie_s = px.pie(
                df_actual, names='sentimiento', color='sentimiento',
                color_discrete_map=color_map, hole=0.4, template="plotly_white"
            )
            fig_pie_s = aplicar_estilo_grafico(fig_pie_s)
            fig_pie_s.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_pie_s, use_container_width=True)

# --- TAB 3: CATEGORÍAS DE FRICCIÓN ---
with tab_categorias:
    st.subheader("Categorización de Temas Recurrentes en el Periodo")
    col_cat1, col_cat2 = st.columns(2)
    
    with col_cat1:
        st.markdown("##### 🔍 Distribución por Categoría de Reclamo/Tema")
        df_cat_count = df_actual['categoria'].value_counts().reset_index()
        df_cat_count.columns = ['Categoría', 'Cantidad']
        
        fig_cat = px.bar(
            df_cat_count, x='Cantidad', y='Categoría', orientation='h',
            color='Categoría', color_discrete_sequence=px.colors.qualitative.Bold,
            template="plotly_white"
        )
        fig_cat = aplicar_estilo_grafico(fig_cat)
        fig_cat.update_layout(showlegend=False)
        st.plotly_chart(fig_cat, use_container_width=True)
        
    with col_cat2:
        st.markdown("##### ⭐ Desglose Estricto por Calificación (Estrellas)")
        df_score_count = df_actual['score'].value_counts().reset_index()
        df_score_count.columns = ['Estrellas', 'Cantidad']
        df_score_count['Estrellas'] = df_score_count['Estrellas'].astype(str) + " ⭐"
        
        fig_score = px.bar(
            df_score_count, x='Estrellas', y='Cantidad',
            color='Estrellas', color_discrete_sequence=['#e30613', '#f39c12', '#00a0e9', '#2ecc71', '#002169'],
            template="plotly_white"
        )
        fig_score = aplicar_estilo_grafico(fig_score)
        fig_score.update_layout(showlegend=False)
        st.plotly_chart(fig_score, use_container_width=True)

# --- TAB 4: EXPLORADOR DE COMENTARIOS CON TABLA HTML BLANCA PURA ---
with tab_explorador:
    st.subheader("Explorador Directo de Reseñas de Clientes")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_sent = st.multiselect("Filtrar por Sentimiento:", options=['Positivo', 'Neutro', 'Negativo'], default=['Negativo', 'Neutro'])
    with col_f2:
        busqueda_texto = st.text_input("Buscar por palabra clave (ej. 'Mercado Pago', 'caja', 'demora'):")
        
    df_filtrado = df_actual[df_actual['sentimiento'].isin(filtro_sent)]
    if busqueda_texto:
        df_filtrado = df_filtrado[df_filtrado['content'].str.contains(busqueda_texto, case=False, na=False)]
        
    # Selección y formato de columnas
    df_tabla = df_filtrado[['at', 'userName', 'score', 'sentimiento', 'categoria', 'content']].sort_values(by='at', ascending=False).head(50).copy()
    df_tabla['at'] = df_tabla['at'].dt.strftime('%Y-%m-%d %H:%M')
    df_tabla.columns = ['Fecha', 'Usuario', 'Rating', 'Sentimiento', 'Categoría', 'Comentario Completo']

    # Renderizado mediante Tabla HTML nativa para romper el Shadow DOM oscuro
    html_tabla = df_tabla.to_html(classes='tabla-blanca', index=False, escape=True)
    st.markdown(f'<div class="tabla-blanca-container">{html_tabla}</div>', unsafe_allow_html=True)

# ==========================================
# 7. EXPORTACIÓN
# ==========================================
st.markdown("---")

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Historico_Completo', index=False)
    df_actual.to_excel(writer, sheet_name='Periodo_Actual', index=False)
    df_anterior.to_excel(writer, sheet_name='Periodo_Anterior_Eq', index=False)

st.download_button(
    label="📄 Descargar Dataset Completo en Excel (.xlsx)",
    data=buffer.getvalue(),
    file_name=f"Reporte_VoC_Grido_Comparativo_{datetime.now().strftime('%Y%m%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
