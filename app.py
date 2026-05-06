import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Cartas Alameda del Río",
    page_icon="💌",
    layout="centered"
)

# --- ESTILOS AVANZADOS (INSPIRADOS EN TU ENLACE) ---
st.markdown("""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
    /* Reset y Fondo */
    .stApp {
        background-color: #f0f2f5;
    }
    /* Ocultar la barra lateral por defecto */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Títulos */
    h1 {
        font-size: 2.2em;
        font-weight: 700;
        color: #1a2a45;
        text-align: center;
    }
    
    /* Contenedores de menú */
    .menu-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin-top: 2rem;
    }

    /* Botones principales (tarjetas de menú) */
    .stButton>button {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background-color: white;
        color: #1a2a45;
        border: 1px solid #e6e8eb;
        border-radius: 12px;
        height: 120px;
        font-size: 1em;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-color: #4A90E2;
    }
    .stButton>button .material-icons {
        font-size: 2.5em;
        margin-bottom: 8px;
        color: #4A90E2;
    }
    
    /* Tarjetas de apartamentos */
    .apto-card {
        background-color: white;
        padding: 1.2rem;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #e6e8eb;
        margin-bottom: 1rem;
    }
    .conjunto-badge {
        font-weight: 600;
        font-size: 1.1em;
        color: #333;
    }

    /* Métricas */
    .metric-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.8rem;
    }
    .metric-box {
        background-color: #fff;
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid #e6e8eb;
    }
    .metric-box .label { font-size: 0.9em; color: #6c757d; }
    .metric-box .value { font-size: 1.8em; font-weight: 700; color: #1a2a45; }

    /* Botón de volver */
    .back-button {
        text-align: left;
    }

    </style>
""", unsafe_allow_html=True)

# --- CONEXIÓN DE DATOS ---
@st.cache_data(ttl=60) # Cache para no recargar constantemente
def load_data():
    return conn.read(worksheet="Sheet1", usecols=list(range(11)), ttl=0)

conn = st.connection("gsheets", type=GSheetsConnection)
df = load_data()

# --- NAVEGACIÓN BASADA EN ESTADO ---
if 'view' not in st.session_state:
    st.session_state.view = 'inicio'

def set_view(view_name):
    st.session_state.view = view_name

# --- VISTA DE INICIO (DASHBOARD) ---
if st.session_state.view == 'inicio':
    st.markdown("<h1>Cartas Alameda del Río</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#6c757d;'>Herramienta para la gestión de predicación en el territorio.</p>", unsafe_allow_html=True)

    # Menú principal
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Sugerir Apartamentos", use_container_width=True): set_view('sugerir')
    with col2:
        if st.button("Selección Manual", use_container_width=True): set_view('manual')
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("Pendientes de Entrega", use_container_width=True): set_view('entregar')
    with col4:
        if st.button("Ver Historial", use_container_width=True): set_view('historial')
    
    st.divider()

    # Estadísticas
    total_aptos = len(df)
    elaboradas = len(df[df['estado'] == "elaborada"])
    entregadas = len(df[df['estado'] == "entregada"])
    disponibles = total_aptos - elaboradas - entregadas
    
    st.markdown("<div class='metric-grid'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><div class='label'>Total</div><div class='value'>{total_aptos}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><div class='label'>Disponibles</div><div class='value'>{disponibles}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><div class='label'>En Proceso</div><div class='value' style='color:#FBC02D;'>{elaboradas}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><div class='label'>Entregadas</div><div class='value' style='color:#4CAF50;'>{entregadas}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- VISTA PARA SUGERIR CARTAS ---
elif st.session_state.view == 'sugerir':
    st.button("← Volver al inicio", on_click=set_view, args=('inicio',), type="secondary")
    st.header("Sugerencia Inteligente")
    st.info("Elige cuántas cartas y la app seleccionará apartamentos variados para ti.")

    cantidad = st.slider("Número de cartas a generar:", 1, 20, 5)
    
    if st.button("Generar Sugerencias", use_container_width=True, type="primary"):
        aptos_libres = df[df['estado'].isna() | (df['estado'] == "")].copy()
        sugerencia = aptos_libres.sample(frac=1).drop_duplicates(subset='conjunto').head(cantidad)
        st.session_state.cartas_para_confirmar = sugerencia

    # Lógica de confirmación
    if 'cartas_para_confirmar' in st.session_state:
        st.divider()
        st.subheader("Apartamentos seleccionados:")
        for _, row in st.session_state.cartas_para_confirmar.iterrows():
            st.markdown(f"""
                <div class='apto-card'>
                    <div class='conjunto-badge'>{row['conjunto']}</div>
                    <span>{row['direccion']}</span><br>
                    <small>Torre {row['torre']} - Apto {row['apto']}</small>
                </div>
            """, unsafe_allow_html=True)
        
        if st.button("✅ Confirmar y registrar", use_container_width=True):
            fecha = datetime.now().strftime("%Y-%m-%d")
            with st.spinner("Guardando..."):
                for idx in st.session_state.cartas_para_confirmar.index:
                    df.at[idx, 'estado'] = "elaborada"
                    df.at[idx, 'fecha_elaborada'] = fecha
                conn.update(data=df)
            st.success("¡Cartas registradas con éxito!")
            del st.session_state.cartas_para_confirmar
            set_view('inicio')
            st.rerun()

# --- VISTAS RESTANTES (Manual, Entregar, Historial) ---
# ... (El código para las demás vistas sería similar, con el botón "Volver" al principio)
# --- VISTA SELECCIÓN MANUAL ---
elif st.session_state.view == 'manual':
    st.button("← Volver al inicio", on_click=set_view, args=('inicio',), type="secondary")
    st.header("Selección Manual de Cartas")
    
    aptos_disponibles = df[df['estado'].isna() | (df['estado'] == "")].copy()
    aptos_disponibles['search_label'] = aptos_disponibles.apply(lambda row: f"{row['conjunto']} | T {row['torre']} | Apto {row['apto']}", axis=1)
    
    seleccion = st.multiselect("Busca y selecciona los apartamentos:", aptos_disponibles['search_label'], placeholder="Escribe el nombre del conjunto o torre...")
    
    if seleccion:
        cartas_seleccionadas = aptos_disponibles[aptos_disponibles['search_label'].isin(seleccion)]
        st.session_state.cartas_para_confirmar = cartas_seleccionadas
    
    if 'cartas_para_confirmar' in st.session_state and st.session_state.view == 'manual':
        if st.button("✅ Confirmar y registrar selección", use_container_width=True, type="primary"):
            fecha = datetime.now().strftime("%Y-%m-%d")
            with st.spinner("Guardando..."):
                for idx in st.session_state.cartas_para_confirmar.index:
                    df.at[idx, 'estado'] = "elaborada"
                    df.at[idx, 'fecha_elaborada'] = fecha
                conn.update(data=df.drop(columns=['search_label'], errors='ignore'))
            st.success("¡Cartas registradas con éxito!")
            del st.session_state.cartas_para_confirmar
            set_view('inicio')
            st.rerun()

# --- VISTA PENDIENTES DE ENTREGA ---
elif st.session_state.view == 'entregar':
    st.button("← Volver al inicio", on_click=set_view, args=('inicio',), type="secondary")
    st.header("Pendientes de Entrega")
    
    pendientes = df[df['estado'] == "elaborada"]
    
    if pendientes.empty:
        st.success("¡Excelente! No hay cartas pendientes por entregar.")
    else:
        for i, row in pendientes.iterrows():
            col1, col2 = st.columns([3,1])
            with col1:
                st.markdown(f"""
                    <div class='apto-card'>
                        <div class='conjunto-badge'>{row['conjunto']}</div>
                        <span>Torre {row['torre']} - <b>Apto {row['apto']}</b></span><br>
                        <small>Escrita el: {row['fecha_elaborada']}</small>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.write("") # Espaciador vertical
                if st.button("Entregado", key=f"ent_{row['id']}", use_container_width=True):
                    with st.spinner("Actualizando..."):
                        df.at[i, 'estado'] = "entregada"
                        df.at[i, 'fecha_entregada'] = datetime.now().strftime("%Y-%m-%d")
                        conn.update(data=df)
                    st.rerun()

# --- VISTA HISTORIAL ---
elif st.session_state.view == 'historial':
    st.button("← Volver al inicio", on_click=set_view, args=('inicio',), type="secondary")
    st.header("Historial de Entregas")
    
    historial = df[df['estado'] == "entregada"].sort_values('fecha_entregada', ascending=False)
    
    if historial.empty:
        st.info("Aún no se ha entregado ninguna carta.")
    else:
        st.dataframe(historial[['fecha_entregada', 'conjunto', 'torre', 'apto']], hide_index=True, use_container_width=True)
