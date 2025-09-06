import streamlit as st
import pandas as pd
import re
from io import BytesIO
import requests
import json

# Configuración de la página
st.set_page_config(
    page_title="Analizador de Subjuntivo Español con Gemini",
    page_icon="📝",
    layout="wide"
)

# Título y descripción
st.title("🔍 Analizador de Modo Subjuntivo en Español con Gemini AI")
st.markdown("""
Esta aplicación utiliza la inteligencia artificial de **Google Gemini** para identificar 
y analizar todas las formas verbales en modo subjuntivo en textos en español con máxima precisión.
""")

# Configuración de la API de Gemini
st.sidebar.header("🔑 Configuración de API")
api_key = st.sidebar.text_input("Introduce tu API Key de Google Gemini", type="password")
gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Almacenar la API key en session state
if api_key:
    st.session_state.gemini_api_key = api_key
    st.sidebar.success("✅ API Key configurada correctamente")
else:
    if 'gemini_api_key' not in st.session_state:
        st.sidebar.warning("⚠️ Introduce tu API Key para usar Gemini AI")

# Función para analizar texto con Gemini
def analizar_con_gemini(texto):
    """Analiza el texto usando la API de Gemini"""
    if 'gemini_api_key' not in st.session_state:
        return None
    
    prompt = f"""
    Analiza el siguiente texto en español e identifica TODOS los verbos en modo subjuntivo.
    Para cada verbo en subjuntivo, proporciona:
    1. La forma verbal exacta
    2. El lema (infinitivo)
    3. El tiempo verbal
    4. La persona y número
    5. La cláusula completa donde aparece
    
    Devuelve la respuesta en formato JSON con esta estructura:
    {{
        "verbos_subjuntivo": [
            {{
                "verbo": "string",
                "lema": "string",
                "tiempo": "string",
                "persona": "string",
                "clausula": "string"
            }}
        ]
    }}
    
    Texto a analizar:
    "{texto}"
    """
    
    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': st.session_state.gemini_api_key
    }
    
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(gemini_url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        if 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0]['content']['parts'][0]['text']
            
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                st.error("No se pudo extraer JSON de la respuesta de Gemini")
                return None
        else:
            st.error("Error en la respuesta de Gemini")
            return None
            
    except Exception as e:
        st.error(f"Error al conectar con Gemini API: {str(e)}")
        return None

# Función alternativa para cuando no hay API key
def analizar_texto_local(texto):
    """Analiza el texto usando métodos locales cuando Gemini no está disponible"""
    # Lista de terminaciones de verbos en subjuntivo
    subjuntivo_terminaciones = [
        'ara', 'aras', 'áramos', 'aran',  # Pretérito imperfecto (-ar)
        'are', 'ares', 'áremos', 'aren',  # Futuro simple (-ar)
        'iera', 'ieras', 'iéramos', 'ieran',  # Pretérito imperfecto (-er/-ir)
        'iere', 'ieres', 'iéremos', 'ieren',  # Futuro simple (-er/-ir)
        'era', 'eras', 'éramos', 'eran',  # Variante (-er)
        'ese', 'eses', 'ésemos', 'esen',  # Pretérito imperfecto (variante)
        'a', 'as', 'amos', 'an',  # Presente (-ar)
        'e', 'es', 'emos', 'en',  # Presente (-er)
        'a', 'as', 'amos', 'an',  # Presente (-ir)
        'se', 'ses', 'semos', 'sen'  # Otra variante
    ]

    # Verbos irregulares comunes en subjuntivo
    verbos_irregulares = [
        'sea', 'seas', 'seamos', 'sean',  # ser
        'vaya', 'vayas', 'vayamos', 'vayan',  # ir
        'haya', 'hayas', 'hayamos', 'hayan',  # haber
        'esté', 'estés', 'estemos', 'estén',  # estar
        'dé', 'des', 'demos', 'den',  # dar
        'sepa', 'sepas', 'sepamos', 'sepan',  # saber
        'quepa', 'quepas', 'quepamos', 'quepan',  # caber
        'haga', 'hagas', 'hagamos', 'hagan',  # hacer
        'pueda', 'puedas', 'podamos', 'puedan',  # poder
        'quiera', 'quieras', 'queramos', 'quieran',  # querer
        'tenga', 'tengas', 'tengamos', 'tengan',  # tener
        'venga', 'vengas', 'vengamos', 'vengan',  # venir
        'digas', 'diga', 'digamos', 'digan',  # decir
        'oyas', 'oiga', 'oigamos', 'oigan'  # oír
    ]

    # Conectores que suelen introducir subjuntivo
    conectores_subjuntivo = [
        'que', 'cuando', 'si', 'aunque', 'para que', 'a fin de que', 
        'como si', 'a menos que', 'con tal de que', 'en caso de que',
        'sin que', 'antes de que', 'ojalá', 'espero que', 'dudo que',
        'no creo que', 'es posible que', 'es probable que', 'quizás',
        'tal vez', 'a no ser que', 'salvo que', 'excepto que'
    ]

    def es_verbo_subjuntivo(palabra):
        palabra_limpia = re.sub(r'[^\w]', '', palabra.lower())
        
        # Verificar verbos irregulares
        if palabra_limpia in verbos_irregulares:
            return True
        
        # Verificar por terminaciones
        for terminacion in subjuntivo_terminaciones:
            if palabra_limpia.endswith(terminacion):
                return True
        
        return False

    def obtener_lema(palabra):
        # Diccionario básico de lemas
        lemas = {
            'sea': 'ser', 'seas': 'ser', 'seamos': 'ser', 'sean': 'ser',
            'vaya': 'ir', 'vayas': 'ir', 'vayamos': 'ir', 'vayan': 'ir',
            'haya': 'haber', 'hayas': 'haber', 'hayamos': 'haber', 'hayan': 'haber',
            'esté': 'estar', 'estés': 'estar', 'estemos': 'estar', 'estén': 'estar',
            'dé': 'dar', 'des': 'dar', 'demos': 'dar', 'den': 'dar',
            'sepa': 'saber', 'sepas': 'saber', 'sepamos': 'saber', 'sepan': 'saber',
            'haga': 'hacer', 'hagas': 'hacer', 'hagamos': 'hacer', 'hagan': 'hacer',
            'pueda': 'poder', 'puedas': 'poder', 'podamos': 'poder', 'puedan': 'poder',
            'quiera': 'querer', 'quieras': 'querer', 'queramos': 'querer', 'quieran': 'querer',
            'tenga': 'tener', 'tengas': 'tener', 'tengamos': 'tener', 'tengan': 'tener',
            'venga': 'venir', 'vengas': 'venir', 'vengamos': 'venir', 'vengan': 'venir'
        }
        
        palabra_limpia = re.sub(r'[^\w]', '', palabra.lower())
        return lemas.get(palabra_limpia, palabra_limpia)

    def determinar_tiempo(palabra):
        palabra_limpia = re.sub(r'[^\w]', '', palabra.lower())
        
        if any(palabra_limpia.endswith(t) for t in ['a', 'as', 'amos', 'an', 'e', 'es', 'emos', 'en']):
            return 'Presente'
        elif any(palabra_limpia.endswith(t) for t in ['ara', 'aras', 'áramos', 'aran', 'iera', 'ieras', 'iéramos', 'ieran', 'era', 'eras', 'éramos', 'eran', 'ese', 'eses', 'ésemos', 'esen']):
            return 'Pretérito imperfecto'
        elif any(palabra_limpia.endswith(t) for t in ['are', 'ares', 'áremos', 'aren', 'iere', 'ieres', 'iéremos', 'ieren']):
            return 'Futuro simple'
        else:
            return 'Indeterminado'

    def determinar_persona(palabra):
        palabra_limpia = re.sub(r'[^\w]', '', palabra.lower())
        
        if palabra_limpia.endswith(('o', 'a', 'e')):
            return '1ª persona singular'
        elif palabra_limpia.endswith(('as', 'es')):
            return '2ª persona singular'
        elif palabra_limpia.endswith(('a', 'e')):
            return '3ª persona singular'
        elif palabra_limpia.endswith(('amos', 'emos', 'imos')):
            return '1ª persona plural'
        elif palabra_limpia.endswith(('áis', 'éis', 'ís')):
            return '2ª persona plural'
        elif palabra_limpia.endswith(('an', 'en')):
            return '3ª persona plural'
        else:
            return 'Indeterminada'

    def encontrar_clausula(texto, posicion):
        inicio = max(0, posicion - 100)
        fin = min(len(texto), posicion + 100)
        
        for conector in conectores_subjuntivo:
            idx = texto.rfind(conector, inicio, posicion)
            if idx != -1:
                inicio = idx
                break
        
        for puntuacion in ['.', '!', '?', ';']:
            idx = texto.find(puntuacion, posicion)
            if idx != -1 and idx < fin:
                fin = idx + 1
                break
        
        return texto[inicio:fin].strip()

    # Análisis del texto
    resultados = []
    palabras = re.findall(r'\b[a-záéíóúñ]+\b', texto.lower())
    posiciones = []
    
    for match in re.finditer(r'\b[a-záéíóúñ]+\b', texto.lower()):
        posiciones.append((match.group(), match.start()))
    
    for palabra, posicion in posiciones:
        if es_verbo_subjuntivo(palabra):
            clausula = encontrar_clausula(texto, posicion)
            
            resultados.append({
                "verbo": texto[posicion:posicion+len(palabra)],
                "lema": obtener_lema(palabra),
                "tiempo": determinar_tiempo(palabra),
                "persona": determinar_persona(palabra),
                "clausula": clausula
            })
    
    return {"verbos_subjuntivo": resultados}

def crear_excel(resultados):
    """Crea un archivo Excel con los resultados"""
    if not resultados or 'verbos_subjuntivo' not in resultados or not resultados['verbos_subjuntivo']:
        return None
    
    df = pd.DataFrame(resultados['verbos_subjuntivo'])
    
    # Crear el archivo Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Subjuntivos', index=False)
        
        # Obtener el libro y la hoja de trabajo para aplicar formato
        workbook = writer.book
        worksheet = writer.sheets['Subjuntivos']
        
        # Formato para los encabezados
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#366092',
            'font_color': 'white',
            'border': 1
        })
        
        # Aplicar formato a los encabezados
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Ajustar el ancho de las columnas
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, max_len)
    
    output.seek(0)
    return output

def crear_csv(resultados):
    """Crea un archivo CSV con los resultados"""
    if not resultados or 'verbos_subjuntivo' not in resultados or not resultados['verbos_subjuntivo']:
        return None
    
    df = pd.DataFrame(resultados['verbos_subjuntivo'])
    
    # Crear el archivo CSV en memoria
    output = BytesIO()
    
    # Escribir el CSV con codificación UTF-8 para caracteres especiales
    output.write(df.to_csv(index=False, encoding='utf-8').encode('utf-8'))
    
    output.seek(0)
    return output

# Sidebar con información
with st.sidebar:
    st.header("ℹ️ Información")
    st.markdown("""
    **Características:**
    - Identificación precisa de verbos en subjuntivo
    - Análisis de tiempo y persona verbal
    - Extracción de cláusulas completas
    - Generación de informes en Excel y CSV
    
    **Tecnología:**
    - **Google Gemini AI**: Modelo de lenguaje avanzado
    - Análisis gramatical de alta precisión
    - Reconocimiento contextual de verbos
    """)
    
    st.markdown("---")
    st.markdown("""
    **Cómo obtener una API Key:**
    1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
    2. Inicia sesión con tu cuenta de Google
    3. Crea una nueva API Key
    4. Copia y pega la key en el campo de arriba
    """)

# Área de texto para entrada
col1, col2 = st.columns([2, 1])

with col1:
    texto = st.text_area(
        "Introduce el texto a analizar:",
        height=300,
        placeholder="Ejemplo: Es necesario que estudies más para el examen. Ojalá que tengas suerte en tu viaje..."
    )

with col2:
    st.markdown("### 📊 Estadísticas")
    if texto:
        # Contar palabras (considerando acentos españoles)
        palabras = re.findall(r'\b[a-záéíóúñ]+\b', texto.lower())
        total_palabras = len(palabras)
        total_oraciones = len(re.split(r'[.!?]+', texto))
        
        st.metric("Palabras", total_palabras)
        st.metric("Oraciones", total_oraciones)
        
        # Estadísticas básicas
        if 'gemini_api_key' in st.session_state:
            st.success("✅ Gemini AI disponible")
        else:
            st.info("ℹ️ Usando análisis local")
    else:
        st.info("Introduce texto para ver estadísticas")

# Botón para analizar
if st.button("🔍 Analizar Subjuntivo con Gemini", type="primary"):
    if not texto.strip():
        st.warning("Por favor, introduce un texto para analizar.")
    else:
        with st.spinner("Analizando texto con Gemini AI..."):
            if 'gemini_api_key' in st.session_state:
                resultados = analizar_con_gemini(texto)
            else:
                st.info("ℹ️ Usando análisis local (sin API Key)")
                resultados = analizar_texto_local(texto)
        
        if resultados and 'verbos_subjuntivo' in resultados and resultados['verbos_subjuntivo']:
            st.success(f"✅ Se encontraron {len(resultados['verbos_subjuntivo'])} verbos en subjuntivo")
            
            # Mostrar resultados en tabla
            st.subheader("📋 Resultados del Análisis")
            df = pd.DataFrame(resultados['verbos_subjuntivo'])
            st.dataframe(df, use_container_width=True)
            
            # Crear columnas para los botones de descarga
            col_download1, col_download2 = st.columns(2)
            
            with col_download1:
                # Generar y descargar Excel
                excel_file = crear_excel(resultados)
                
                if excel_file:
                    st.download_button(
                        label="📥 Descargar Informe Excel",
                        data=excel_file,
                        file_name="analisis_subjuntivo.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            
            with col_download2:
                # Generar y descargar CSV
                csv_file = crear_csv(resultados)
                
                if csv_file:
                    st.download_button(
                        label="📄 Descargar Informe CSV",
                        data=csv_file,
                        file_name="analisis_subjuntivo.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            # Mostrar estadísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total subjuntivos", len(resultados['verbos_subjuntivo']))
            with col2:
                tiempos = df['tiempo'].value_counts()
                st.metric("Tiempo más común", tiempos.index[0] if len(tiempos) > 0 else "N/A")
            with col3:
                st.metric("Verbos únicos", df['lema'].nunique())
            
        else:
            st.info("ℹ️ No se encontraron verbos en modo subjuntivo en el texto.")

# Ejemplos predefinidos
st.subheader("💡 Ejemplos para probar")
ejemplos = {
    "Ejemplo 1": "Es importante que estudies para el examen. Ojalá que tengas buena suerte.",
    "Ejemplo 2": "Quiero que vengas a la fiesta. Dudo que ella pueda asistir.",
    "Ejemplo 3": "Sería bueno que lloviera pronto. Temo que se sequen las plantas."
}

cols = st.columns(3)
for i, (nombre, ejemplo) in enumerate(ejemplos.items()):
    with cols[i]:
        if st.button(f"📌 {nombre}"):
            texto = ejemplo
            st.rerun()

# Información adicional
with st.expander("📚 Acerca del análisis con Gemini AI"):
    st.markdown("""
    **Google Gemini** es un modelo de lenguaje de IA avanzado que ofrece:
    
    - Comprensión contextual profunda del español
    - Análisis gramatical preciso
    - Identificación de matices lingüísticos
    - Reconocimiento de estructuras complejas
    
    **Ventajas sobre métodos tradicionales:**
    - Mayor precisión en la identificación de verbos
    - Mejor comprensión del contexto
    - Detección de usos figurados y excepciones
    - Análisis de estructuras gramaticales complejas
    
    **Cómo funciona:**
    1. El texto se envía a la API de Gemini
    2. Gemini analiza el texto y identifica verbos en subjuntivo
    3. Se extrae información morfológica y contextual
    4. Los resultados se presentan en formato estructurado
    """)

# Pie de página
st.markdown("---")
st.caption("Analizador de Modo Subjuntivo v5.0 | Desarrollado con Google Gemini AI")

# Advertencia si no hay API key
if 'gemini_api_key' not in st.session_state:
    st.info("""
    💡 **Para usar la versión completa con Gemini AI:**
    1. Obtén una API Key gratuita de Google AI Studio
    2. Ingrésala en la barra lateral
    3. Disfruta de análisis más precisos con IA
    """)
