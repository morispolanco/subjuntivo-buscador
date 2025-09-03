# app_subjuntivo.py
import streamlit as st
import spacy
import pandas as pd
from collections import defaultdict
import re
import io

# Configuración de la página
st.set_page_config(
    page_title="Analizador de Subjuntivo",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título de la aplicación
st.title("🔍 Analizador de Verbos en Subjuntivo")
st.markdown("""
Esta aplicación identifica formas verbales del modo subjuntivo en textos en español 
y genera un informe detallado en formato Excel.
""")

# Clase principal del analizador
class AnalizadorSubjuntivo:
    def __init__(self):
        # Cargar el modelo de spaCy para español
        try:
            self.nlp = spacy.load("es_core_news_sm")
        except OSError:
            st.error("Modelo de spaCy no encontrado. Ejecuta: `python -m spacy download es_core_news_sm`")
            st.stop()
        
        # Patrones de verbos irregulares y formas comunes del subjuntivo
        self.patrones_subjuntivo = [
            r'\b(?:quisier|pudier|vinier|fuer|tuvier|hicier|dijer|supier|anduvier|estuvier)a[mn]?o?s?\b',
            r'\b(?:quier|pued|veng|se|teng|hag|dig|sep|and|esté?)a[mn]?o?s?\b',
            r'\b(?:habl|com|viv|am|tem|part)iera[mn]?o?s?\b',
            r'\b(?:habl|com|viv|am|tem|part)iere[mn]?o?s?\b',
            r'\b(?:habl|com|viv|am|tem|part)ase[mn]?o?s?\b',
            r'\b(?:habl|com|viv|am|tem|part)are[mn]?o?s?\b',
            r'\b(?:sea|seas|sea|seamos|seáis|sean)\b',
            r'\b(?:fuera|fueras|fuera|fuéramos|fuerais|fueran)\b',
            r'\b(?:fuese|fueses|fuese|fuésemos|fueseis|fuesen)\b',
            r'\b(?:haya|hayas|haya|hayamos|hayáis|hayan)\b',
            r'\b(?:hubiera|hubieras|hubiera|hubiéramos|hubierais|hubieran)\b',
            r'\b(?:hubiese|hubieses|hubiese|hubiésemos|hubieseis|hubiesen)\b'
        ]
        
        self.regex_subjuntivo = re.compile('|'.join(self.patrones_subjuntivo), re.IGNORECASE)
    
    def es_verbo_subjuntivo(self, token):
        """Verifica si un token es un verbo en subjuntivo usando análisis morfológico"""
        if token.pos_ == 'VERB' or token.pos_ == 'AUX':
            # Verificar características morfológicas del subjuntivo
            morph_features = token.morph.to_dict()
            if 'Mood' in morph_features and morph_features['Mood'] == 'Sub':
                return True
            
            # Verificación adicional con patrones regex
            if self.regex_subjuntivo.search(token.text.lower()):
                return True
        
        return False
    
    def analizar_texto(self, texto):
        """Analiza el texto y encuentra verbos en subjuntivo"""
        doc = self.nlp(texto)
        resultados = []
        
        for sent in doc.sents:
            for token in sent:
                if self.es_verbo_subjuntivo(token):
                    # Obtener información morfológica detallada
                    morph_info = token.morph.to_dict()
                    
                    resultado = {
                        'Texto Original': token.text,
                        'Lema': token.lemma_,
                        'Oración Completa': sent.text.strip(),
                        'Tiempo Verbal': morph_info.get('Tense', 'Desconocido'),
                        'Persona': morph_info.get('Person', 'Desconocido'),
                        'Número': morph_info.get('Number', 'Desconocido'),
                        'Modo': 'Subjuntivo',
                        'Posición Inicio': token.idx,
                        'Posición Fin': token.idx + len(token.text)
                    }
                    resultados.append(resultado)
        
        return resultados

# Inicializar el analizador
@st.cache_resource
def cargar_analizador():
    return AnalizadorSubjuntivo()

analizador = cargar_analizador()

# Sidebar con información
with st.sidebar:
    st.header("ℹ️ Información")
    st.markdown("""
    Esta herramienta identifica:
    - Presente de subjuntivo (hable, comas, viva)
    - Imperfecto de subjuntivo (hablara, comieras, viviese)
    - Perfecto de subjuntivo (haya hablado)
    - Pluscuamperfecto de subjuntivo (hubiera hablado)
    """)
    
    st.header("📊 Estadísticas")
    if 'resultados' in st.session_state:
        st.metric("Verbos encontrados", len(st.session_state.resultados))

# Selección de modo de entrada
modo_entrada = st.radio(
    "Selecciona el modo de entrada:",
    ["Texto directo", "Subir archivo"],
    horizontal=True
)

texto_analizar = ""

if modo_entrada == "Texto directo":
    texto_analizar = st.text_area(
        "Ingresa el texto a analizar:",
        height=200,
        placeholder="Ej: Espero que vengas a la fiesta. Ojalá que tengas un buen día..."
    )
else:
    archivo_subido = st.file_uploader(
        "Sube un archivo de texto (.txt)",
        type=["txt"]
    )
    
    if archivo_subido is not None:
        texto_analizar = archivo_subido.getvalue().decode("utf-8")
        st.text_area("Texto extraído del archivo:", texto_analizar, height=200)

# Botón para analizar
if st.button("🔍 Analizar texto", type="primary"):
    if texto_analizar.strip():
        with st.spinner("Analizando texto..."):
            resultados = analizador.analizar_texto(texto_analizar)
            st.session_state.resultados = resultados
            
        st.success(f"Análisis completado. Se encontraron {len(resultados)} verbos en subjuntivo.")
    else:
        st.warning("Por favor, ingresa algún texto para analizar.")

# Mostrar resultados si existen
if 'resultados' in st.session_state and st.session_state.resultados:
    resultados = st.session_state.resultados
    
    # Mostrar estadísticas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de verbos", len(resultados))
    with col2:
        lemas_unicos = len(set(r['Lema'] for r in resultados))
        st.metric("Lemas únicos", lemas_unicos)
    with col3:
        oraciones_unicas = len(set(r['Oración Completa'] for r in resultados))
        st.metric("Oraciones con subjuntivo", oraciones_unicas)
    
    # Mostrar tabla de resultados
    st.subheader("📋 Resultados detallados")
    df = pd.DataFrame(resultados)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Preparar archivo Excel para descarga
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Verbos Subjuntivo', index=False)
        
        # Ajustar el ancho de las columnas
        worksheet = writer.sheets['Verbos Subjuntivo']
        for idx, col in enumerate(df.columns):
            max_len = max(
                df[col].astype(str).map(len).max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_len, 50)
    
    output.seek(0)
    
    # Botón de descarga
    st.download_button(
        label="📥 Descargar informe en Excel",
        data=output,
        file_name="informe_subjuntivo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # Mostrar ejemplos en el texto
    st.subheader("🔍 Ejemplos en contexto")
    
    # Limitar a 5 ejemplos para no saturar la interfaz
    for i, resultado in enumerate(resultados[:5]):
        with st.expander(f"Ejemplo {i+1}: {resultado['Texto Original']} ({resultado['Lema']})"):
            st.write("**Oración completa:**")
            st.write(resultado['Oración Completa'])
            
            # Resaltar el verbo en la oración
            inicio = resultado['Posición Inicio']
            fin = resultado['Posición Fin']
            texto_antes = resultado['Oración Completa'][:inicio]
            texto_verbo = resultado['Oración Completa'][inicio:fin]
            texto_despues = resultado['Oración Completa'][fin:]
            
            st.write("**Verbo resaltado:**")
            st.markdown(f"{texto_antes} :red[**{texto_verbo}**] {texto_despues}")
            
            st.write("**Información morfológica:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**Tiempo:** {resultado['Tiempo Verbal']}")
            with col2:
                st.info(f"**Persona:** {resultado['Persona']}")
            with col3:
                st.info(f"**Número:** {resultado['Número']}")

# Texto de ejemplo para probar
with st.expander("💡 ¿Necesitas un texto de ejemplo?"):
    texto_ejemplo = """
    Espero que vengas a la fiesta. Ojalá que tengas un buen día.
    Quisiera que hicieras el trabajo. Es importante que estudies.
    Dudo que ella sepa la verdad. No creo que puedan venir.
    Me gustaría que fuéramos al cine. Sería bueno que lloviera.
    """
    st.text_area("Texto de ejemplo", texto_ejemplo, height=150)
    
    if st.button("Usar texto de ejemplo"):
        st.session_state.texto_ejemplo = texto_ejemplo
        st.rerun()

# Ejecutar con: streamlit run app_subjuntivo.py
