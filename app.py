import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN TÉCNICA ---
st.set_page_config(page_title="Alameda App", page_icon="📱", layout="centered")

# --- ESTILO "DARK MODE APP" (CSS AVANZADO) ---
st.markdown("""
    <style>
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    
    /* Fondo principal */
    .stApp {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }

    /* Contenedor de la App */
    .block-container {
        padding-top: 2rem;
        max-width: 500px;
    }

    /* Tarjetas de Menú */
    .menu-btn {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 25px;
        text-align: center;
        margin-bottom: 15px;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Botones de Streamlit convertidos en botones de App */
    .stButton > button {
        width: 100%;
        border-radius: 15px;
        height: 80px;
        border: none;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        font-size: 18px;
        font-weight: 700;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
        transition: transform 0.1s;
    }
    .stButton > button:active {
        transform: scale(0.95);
    }
    
    /* Tarjetas de Apartamentos */
    .card-apto {
        background: #ffffff;
        color: #1e293b;
        padding: 20px;
        border-radius: 20px;
        margin-bottom: 15px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    .conjunto-tag {
        background: #dbeafe;
        color: #1e40af;
        padding: 4px 12px;
        border-radius: 10px;
        font-size: 12px;
        font-weight: 800;
        text-transform: uppercase;
    }

    /* Estadísticas */
    .stat-card {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 20px;
        padding: 15px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN Y DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(ttl=0)

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- LÓGICA DE NAVEGACIÓN INSTANTÁNEA ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'

def ir_a(pagina):
    st.session_state.page = pagina

# --- VISTA: HOME ---
if st.session_state.page == 'home':
    st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>Alameda del Río</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Territorio de Predicación</p>", unsafe_allow_html=True)
    
    st.write("")
    
    # Grid de Menú
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎲\nALAZAR"): ir_a('sugerir')
        if st.button("📦\nENTREGAS"): ir_a('entregar')
    with col2:
        if st.button("🖱️\nMANUAL"): ir_a('manual')
        if st.button("📊\nSTATS"): ir_a('stats')

    st.write("")
    # Mini resumen
    df = st.session_state.df
    progreso = len(df[df['estado'] == "entregada"]) / len(df)
    st.markdown(f"<div class='stat-card'>Cobertura Total: {progreso:.1%}</div>", unsafe_allow_html=True)
    st.progress(progreso)

# --- VISTA: SUGERIR (ALAZAR) ---
elif st.session_state.page == 'sugerir':
    st.markdown("### 🎲 Selección Aleatoria")
    if st.button("← VOLVER AL MENÚ"): ir_a('home')
    
    cantidad = st.select_slider("¿Cuántas cartas?", options=[1, 3, 5, 10, 15], value=5)
    
    if st.button("GENERAR SELECCIÓN"):
        libres = st.session_state.df[st.session_state.df['estado'].isna() | (st.session_state.df['estado'] == "")].copy()
        st.session_state.temp_list = libres.sample(frac=1).drop_duplicates(subset='conjunto').head(cantidad)

    if 'temp_list' in st.session_state:
        for _, row in st.session_state.temp_list.iterrows():
            st.markdown(f"""<div class='card-apto'>
                <span class='conjunto-tag'>{row['conjunto']}</span>
                <div style='font-size: 20px; font-weight: 700; margin-top: 10px;'>Torre {row['torre']} - Apto {row['apto']}</div>
                <div style='color: #64748b;'>{row['direccion']}</div>
            </div>""", unsafe_allow_html=True)
        
        if st.button("✅ REGISTRAR COMO LISTAS"):
            fecha = datetime.now().strftime("%d/%m/%Y")
            for idx in st.session_state.temp_list.index:
                st.session_state.df.at[idx, 'estado'] = "elaborada"
                st.session_state.df.at[idx, 'fecha_elaborada'] = fecha
            conn.update(data=st.session_state.df)
            st.success("Guardado!")
            del st.session_state.temp_list
            ir_a('home')

# --- VISTA: MANUAL ---
elif st.session_state.page == 'manual':
    st.markdown("### 🖱️ Selección Manual")
    if st.button("← VOLVER AL MENÚ"): ir_a('home')
    
    libres = st.session_state.df[st.session_state.df['estado'].isna() | (st.session_state.df['estado'] == "")].copy()
    libres['label'] = libres['conjunto'] + " | T" + libres['torre'].astype(str) + " | Apto " + libres['apto'].astype(str)
    
    opciones = st.multiselect("Selecciona apartamentos:", libres['label'].tolist())
    
    if opciones:
        if st.button("✅ CONFIRMAR SELECCIÓN"):
            fecha = datetime.now().strftime("%d/%m/%Y")
            indices = libres[libres['label'].isin(opciones)].index
            for idx in indices:
                st.session_state.df.at[idx, 'estado'] = "elaborada"
                st.session_state.df.at[idx, 'fecha_elaborada'] = fecha
            conn.update(data=st.session_state.df)
            ir_a('home')

# --- VISTA: ENTREGAR ---
elif st.session_state.page == 'entregar':
    st.markdown("### 🚚 Pendientes de Entrega")
    if st.button("← VOLVER AL MENÚ"): ir_a('home')
    
    pendientes = st.session_state.df[st.session_state.df['estado'] == "elaborada"]
    
    if pendientes.empty:
        st.write("---")
        st.markdown("<h4 style='text-align: center;'>No hay nada pendiente 🎉</h4>", unsafe_allow_html=True)
    else:
        for i, row in pendientes.iterrows():
            with st.container():
                st.markdown(f"""<div class='card-apto'>
                    <span class='conjunto-tag'>{row['conjunto']}</span>
                    <div style='font-size: 18px; font-weight: 700; margin-top: 5px;'>Torre {row['torre']} - Apto {row['apto']}</div>
                    <div style='font-size: 12px; color: #64748b;'>Escrita: {row['fecha_elaborada']}</div>
                </div>""", unsafe_allow_html=True)
                if st.button(f"MARCAR ENTREGADO {row['id']}", key=f"btn_{row['id']}"):
                    st.session_state.df.at[i, 'estado'] = "entregada"
                    st.session_state.df.at[i, 'fecha_entregada'] = datetime.now().strftime("%d/%m/%Y")
                    conn.update(data=st.session_state.df)
                    st.rerun()

# --- VISTA: STATS ---
elif st.session_state.page == 'stats':
    st.markdown("### 📊 Estadísticas")
    if st.button("← VOLVER AL MENÚ"): ir_a('home')
    
    df = st.session_state.df
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='stat-card'><small>LISTAS</small><h2>{len(df[df['estado']=='elaborada'])}</h2></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='stat-card'><small>ENTREGADAS</small><h2>{len(df[df['estado']=='entregada'])}</h2></div>", unsafe_allow_html=True)
    
    st.write("")
    st.markdown("<div class='stat-card'><small>TOTAL TERRITORIO</small><h3>7,000 Aptos</h3></div>", unsafe_allow_html=True)
