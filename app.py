# ==========================================
# 1. INSTALACIÓN DE LIBRERÍAS
# ==========================================
!pip install google_play_scraper pandas openpyxl wordcloud

import pandas as pd
import matplotlib.pyplot as plt
from google_play_scraper import Sort, reviews_all
from datetime import datetime, timedelta
from wordcloud import WordCloud, STOPWORDS
from google.colab import files

# ==========================================
# 2. CONFIGURACIÓN Y EXTRACCIÓN
# ==========================================
APP_ID = 'com.grido.app'
print(f"Iniciando proceso para {APP_ID}...")

resenas = reviews_all(
    APP_ID,
    sleep_milliseconds=0,
    lang='es',
    country='ar',
    sort=Sort.NEWEST
)

df = pd.DataFrame(resenas)
df['at'] = pd.to_datetime(df['at'])

# ==========================================
# 3. LIMPIEZA Y PROCESAMIENTO
# ==========================================
def clasificar(score):
    if score <= 2: return 'Negativo'
    if score == 3: return 'Neutro'
    return 'Positivo'

df['sentimiento'] = df['score'].apply(clasificar)
df = df.drop(columns=['reviewId', 'userImage', 'replyContent', 'repliedAt'], errors='ignore')

hace_una_semana = datetime.now() - timedelta(days=7)
df_semana = df[df['at'] >= hace_una_semana].copy()

# ==========================================
# 4. GENERACIÓN DEL TABLERO VISUAL
# ==========================================
fig = plt.figure(figsize=(20, 22))
grid = plt.GridSpec(3, 2, wspace=0.3, hspace=0.3)

# --- [Gráfico Superior] Tendencia Temporal ---
ax_time = fig.add_subplot(grid[0, :])
df_time = df_semana.groupby([df_semana['at'].dt.date, 'sentimiento']).size().unstack(fill_value=0)
for col in ['Positivo', 'Neutro', 'Negativo']:
    if col not in df_time.columns: df_time[col] = 0

df_time[['Positivo', 'Neutro', 'Negativo']].plot(
    kind='bar', stacked=True, ax=ax_time,
    color=['#66ff66', '#d3d3d3', '#ff6666'], edgecolor='white'
)
ax_time.set_title('Tendencia Semanal por Sentimiento', fontsize=18, fontweight='bold')
ax_time.tick_params(axis='x', rotation=45)

# --- [Fila 2] Tortas Histórica y Semanal ---
ax_pie_h = fig.add_subplot(grid[1, 0])
conteo_total = df['sentimiento'].value_counts()
ax_pie_h.pie(conteo_total, labels=conteo_total.index, autopct='%1.1f%%', startangle=140,
            colors=[('#66ff66' if s=='Positivo' else '#ff6666' if s=='Negativo' else '#d3d3d3') for s in conteo_total.index])
ax_pie_h.set_title(f'Histórico Total ({len(df)} reseñas)')

ax_pie_s = fig.add_subplot(grid[1, 1])
if not df_semana.empty:
    conteo_semana = df_semana['sentimiento'].value_counts()
    ax_pie_s.pie(conteo_semana, labels=conteo_semana.index, autopct='%1.1f%%', startangle=140,
                colors=[('#66ff66' if s=='Positivo' else '#ff6666' if s=='Negativo' else '#d3d3d3') for s in conteo_semana.index])
    ax_pie_s.set_title(f'Última Semana ({len(df_semana)} reseñas)')

# --- [Fila 3] Nubes de Palabras ---
mis_stopwords = set(STOPWORDS)
mis_stopwords.update(["que", "la", "el", "de", "en", "para", "una", "un", "es", "por", "si", "app", "grido", "pero", "con", "me", "al", "lo", "como", "las", "y", "se", "te", "ni", "creo", "tengo", "puedo"])

ax_wc_p = fig.add_subplot(grid[2, 0])
df_pos = df_semana[df_semana['sentimiento'] == 'Positivo']
if not df_pos.empty:
    texto_pos = " ".join(review for review in df_pos.content.astype(str))
    wc_pos = WordCloud(width=800, height=400, background_color='white', stopwords=mis_stopwords, colormap='Greens').generate(texto_pos)
    ax_wc_p.imshow(wc_pos, interpolation='bilinear')
    ax_wc_p.set_title('Temas POSITIVOS (Semanal)')
ax_wc_p.axis("off")

ax_wc_n = fig.add_subplot(grid[2, 1])
df_neg = df_semana[df_semana['sentimiento'] == 'Negativo']
if not df_neg.empty:
    texto_neg = " ".join(review for review in df_neg.content.astype(str))
    wc_neg = WordCloud(width=800, height=400, background_color='white', stopwords=mis_stopwords, colormap='Reds').generate(texto_neg)
    ax_wc_n.imshow(wc_neg, interpolation='bilinear')
    ax_wc_n.set_title('Temas NEGATIVOS (Semanal)')
ax_wc_n.axis("off")

# --- GUARDAR IMAGEN ---
fecha_str = datetime.now().strftime("%Y-%m-%d")
nombre_imagen = f'Tablero_Grido_{fecha_str}.png'
plt.savefig(nombre_imagen, bbox_inches='tight', dpi=300) # dpi=300 asegura alta calidad
plt.show()

# ==========================================
# 5. EXPORTACIÓN Y DESCARGA
# ==========================================
nombre_excel = f'Reporte_Grido_{fecha_str}.xlsx'
with pd.ExcelWriter(nombre_excel, engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Historico_Completo', index=False)
    df_semana.to_excel(writer, sheet_name='Ultima_Semana', index=False)

print(f"✅ Archivos generados: {nombre_excel} y {nombre_imagen}")

# Descargar ambos archivos
files.download(nombre_excel)
files.download(nombre_imagen)
