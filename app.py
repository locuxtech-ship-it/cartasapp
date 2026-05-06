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

# --- ESTILOS CSS (INSPIRADOS EN EL ENLACE) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { display: none; } /* Ocultar sidebar */
    
    /* Botones del Menú Principal */
    .stButton>button {
        border-radius: 12px;
        height: 100px;
        font-size: 18px;
        font-weight: 600;
        border: 1px solid #e0e0e0;
        background-color: white;
        color: #1a2a45;
        transition: all 0.3s;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stButton>button:hover {
        border-color: #4A90E2;
        color: #4A90E2;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* Tarjetas de Apartamentos */
    .apto-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 6px solid #4A90E2;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .conjunto-name { font-size: 1.2em; font-weight: 700; color: #333; }
    .apto-info { color: #666; font-size: 1em; }

    /* Métricas */
    .metric-box {
        background-color: white;
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #eee;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONEXIÓN DE DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Eliminamos el nombre específico de la pestaña para evitar errores
    return conn.read(ttl=0)

df = load_data()

# --- NAVEGACIÓN ---
if 'view' not in st.session_state:
    st.session_state.view = 'inicio'

def change_view(view_name):
    st.session_state.view = view_name

# --- VISTA: INICIO ---
if st.session_state.view == 'inicio':
    st.markdown("<h1 style='text-align: center; color: #1a2a45;'>Alameda del Río</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Gestión de Cartas para Predicación</p>", unsafe_allow_html=True)
    
    st.write("") # Espacio
    
    # Menú de botones grandes
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎲 Sugerir\nAleatorio", use_container_width=True): change_view('sugerir')
        if st.button("🚚 Pendientes\nde Entrega", use_container_width=True): change_view('entregar')
    with col2:
        if st.button("🖱️ Selección\nManual", use_container_width=True): change_view('manual')
        if st.button("📊 Ver\nEstadísticas", use_container_width=True): change_view('stats')

    st.write("")
    st.divider()
    
    # Resumen rápido abajo
    total = len(df)
    entregadas = len(df[df['estado'] == "entregada"])
    st.markdown(f"<p style='text-align: center;'>Progreso del territorio: <b>{entregadas} de {total}</b></p>", unsafe_allow_html=True)
    st.progress(entregadas/total if total > 0 else 0)

# --- VISTA: SUGERIR ALEATORIO ---
elif st.session_state.view == 'sugerir':
    if st.button("← Volver"): change_view('inicio'); st.rerun()
    st.subheader("Sugerencia de apartamentos")
    
    cantidad = st.number_input("¿Cuántas cartas vas a hacer?", 1, 30, 5)
    
    if st.button("Generar Lista", type="primary", use_container_width=True):
        libres = df[df['estado'].isna() | (df['estado'] == "")].copy()
        # Regla: No más de uno por conjunto en esta tanda
        st.session_state.temp_list = libres.sample(frac=1).drop_duplicates(subset='conjunto').head(cantidad)

    if 'temp_list' in st.session_state:
        st.write("---")
        for _, row in st.session_state.temp_list.iterrows():
            st.markdown(f"""<div class='apto-card'>
                <div class='conjunto-name'>{row['conjunto']}</div>
                <div class='apto-info'>Torre {row['torre']} - Apto {row['apto']}</div>
            </div>""", unsafe_allow_html=True)
        
        if st.button("✅ Confirmar: Marcar como Elaboradas", use_container_width=True):
            fecha = datetime.now().strftime("%d/%m/%Y")
            for idx in st.session_state.temp_list.index:
                df.at[idx, 'estado'] = "elaborada"
                df.at[idx, 'fecha_elaborada'] = fecha
            conn.update(data=df)
            st.success("¡Cartas guardadas!")
            del st.session_state.temp_list
            change_view('inicio')
            st.rerun()

# --- VISTA: MANUAL ---
elif st.session_state.view == 'manual':
    if st.button("← Volver"): change_view('inicio'); st.rerun()
    st.subheader("Selección Manual")
    
    libres = df[df['estado'].isna() | (df['estado'] == "")].copy()
    libres['selector'] = libres['conjunto'] + " | Torre " + libres['torre'].astype(str) + " | Apto " + libres['apto'].astype(str)
    
    elegidos = st.multiselect("Busca los apartamentos:", libres['selector'].tolist())
    
    if elegidos:
        if st.button("✅ Registrar Selección", type="primary", use_container_width=True):
            fecha = datetime.now().strftime("%d/%m/%Y")
            indices = libres[libres['selector'].isin(elegidos)].index
            for idx in indices:
                df.at[idx, 'estado'] = "elaborada"
                df.at[idx, 'fecha_elaborada'] = fecha
            conn.update(data=df)
            st.success("Registrados correctamente")
            change_view('inicio')
            st.rerun()

# --- VISTA: ENTREGAR ---
elif st.session_state.view == 'entregar':
    if st.button("← Volver"): change_view('inicio'); st.rerun()
    st.subheader("Cartas listas para entregar")
    
    pendientes = df[df['estado'] == "elaborada"]
    
    if pendientes.empty:
        st.info("No hay nada pendiente por ahora.")
    else:
        for i, row in pendientes.iterrows():
            with st.container():
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"""<div class='apto-card'>
                    <div class='conjunto-name'>{row['conjunto']}</div>
                    <div class='apto-info'>Apto {row['apto']} (Escrita: {row['fecha_elaborada']})</div>
                </div>""", unsafe_allow_html=True)
                if c2.button("LISTO ✅", key=f"ent_{row['id']}"):
                    df.at[i, 'estado'] = "entregada"
                    df.at[i, 'fecha_entregada'] = datetime.now().strftime("%d/%m/%Y")
                    conn.update(data=df)
                    st.rerun()

# --- VISTA: ESTADÍSTICAS ---
elif st.session_state.view == 'stats':
    if st.button("← Volver"): change_view('inicio'); st.rerun()
    st.subheader("Estadísticas del Territorio")
    
    col1, col2 = st.columns(2)
    elaboradas = len(df[df['estado'] == "elaborada"])
    entregadas = len(df[df['estado'] == "entregada"])
    libres = len(df) - elaboradas - entregadas
    
    col1.metric("Pendientes Entrega", elaboradas)
    col2.metric("Total Entregadas", entregadas)
    st.metric("Disponibles para escribir", libres)
    
    st.write("### Avance por Conjunto")
    con_stats = df[df['estado'] == "entregada"].groupby('conjunto').size()
    if not con_stats.empty:
        st.bar_chart(con_stats)
    else:
        st.write("Sin datos de entregas aún.")
