import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Alameda App", page_icon="🏢", layout="centered")

# --- CSS AVANZADO PARA INTERFAZ DE APP ---
st.markdown("""
    <style>
    /* Ocultar basura de Streamlit */
    [data-testid="stHeader"], footer, #MainMenu {display: none;}
    
    .stApp {
        background-color: #f0f2f5;
        color: #1e293b;
    }

    /* Contenedor principal */
    .block-container {
        padding-top: 1rem;
        max-width: 500px;
    }

    /* CUADRÍCULA DE BOTONES UNIFORMES */
    .stButton > button {
        width: 100% !important;
        height: 100px !important; /* Altura fija para uniformidad */
        border-radius: 20px !important;
        border: none !important;
        background: white !important;
        color: #1e293b !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 10px !important;
    }
    
    .stButton > button:hover {
        border: 1px solid #10b981 !important;
        color: #10b981 !important;
    }

    /* TARJETAS DE APARTAMENTOS */
    .card-apto {
        background: white;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #10b981;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* ESTILO DASHBOARD */
    .stat-card {
        background: white;
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    
    .progress-label {
        font-size: 12px;
        font-weight: 600;
        color: #64748b;
        margin-bottom: 5px;
        display: flex;
        justify-content: space-between;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN Y CARGA DE DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10) # Cache corto para fluidez
def load_data():
    return conn.read(ttl=0)

# Cargar datos en el estado de la sesión
if 'df' not in st.session_state or st.sidebar.button("Refrescar Datos"):
    st.session_state.df = load_data()

df = st.session_state.df

# --- NAVEGACIÓN ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'

def nav(page_name):
    st.session_state.page = page_name

# --- VISTA: INICIO (MENU PRINCIPAL) ---
if st.session_state.page == 'home':
    st.markdown("<h1 style='text-align: center; color: #10b981;'>Alameda App</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; margin-top:-15px;'>Territorio de Predicación</p>", unsafe_allow_html=True)

    # Cuadrícula de botones 2x2
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎲\nAL AZAR"): nav('sugerir')
        if st.button("📦\nENTREGAS"): nav('entregar')
    with col2:
        if st.button("🖱️\nMANUAL"): nav('manual')
        if st.button("📊\nAVANCE"): nav('stats')

    st.write("---")
    
    # Resumen rápido
    total = len(df)
    hechas = len(df[df['estado'].isin(['elaborada', 'entregada'])])
    progreso_val = hechas/total if total > 0 else 0
    
    st.markdown(f"""
        <div class='stat-card'>
            <div class='progress-label'>
                <span>Progreso General</span>
                <span>{progreso_val:.1%}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.progress(progreso_val)

# --- VISTA: ESTADÍSTICAS (DASHBOARD REAL) ---
elif st.session_state.page == 'stats':
    st.markdown("### 📊 Avance por Conjuntos")
    if st.button("← VOLVER"): nav('home')

    # Cálculos por conjunto
    stats = df.copy()
    stats['completado'] = stats['estado'].apply(lambda x: 1 if x == 'entregada' else 0)
    resumen = stats.groupby('conjunto').agg(
        total=('id', 'count'),
        entregados=('completado', 'sum')
    )
    resumen['porcentaje'] = (resumen['entregados'] / resumen['total'])
    resumen = resumen.sort_values('porcentaje', ascending=False)

    for conjunto, row in resumen.iterrows():
        pct = row['porcentaje']
        color = "#10b981" if pct > 0.5 else "#f59e0b"
        st.markdown(f"""
            <div class='stat-card' style='text-align: left; padding: 10px 20px;'>
                <div class='progress-label'>
                    <span style='color:#1e293b; font-size:14px;'>{conjunto}</span>
                    <span>{int(row['entregados'])} / {int(row['total'])}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.progress(pct)

# --- VISTA: SUGERIR (AL AZAR) ---
elif st.session_state.page == 'sugerir':
    st.markdown("### 🎲 Selección Aleatoria")
    if st.button("← VOLVER"): nav('home')
    
    cantidad = st.number_input("¿Cuántas cartas vas a escribir?", 1, 20, 5)
    
    if st.button("GENERAR NUEVA LISTA", type="primary"):
        libres = df[df['estado'].isna() | (df['estado'] == "")].copy()
        st.session_state.temp_list = libres.sample(frac=1).drop_duplicates(subset='conjunto').head(cantidad)

    if 'temp_list' in st.session_state:
        st.write("---")
        for _, row in st.session_state.temp_list.iterrows():
            st.markdown(f"""<div class='card-apto'>
                <small style='color:#10b981; font-weight:bold;'>{row['conjunto']}</small><br>
                <b>Torre {row['torre']} - Apto {row['apto']}</b>
            </div>""", unsafe_allow_html=True)
        
        if st.button("✅ REGISTRAR ESTAS CARTAS"):
            fecha = datetime.now().strftime("%d/%m/%Y")
            for idx in st.session_state.temp_list.index:
                df.at[idx, 'estado'] = "elaborada"
                df.at[idx, 'fecha_elaborada'] = fecha
            conn.update(data=df)
            st.session_state.df = df # Actualizar sesión
            st.success("¡Cartas registradas!")
            del st.session_state.temp_list
            nav('home')
            st.rerun()

# --- VISTA: MANUAL ---
elif st.session_state.page == 'manual':
    st.markdown("### 🖱️ Selección Manual")
    if st.button("← VOLVER"): nav('home')
    
    libres = df[df['estado'].isna() | (df['estado'] == "")].copy()
    libres['label'] = libres['conjunto'] + " | T" + libres['torre'].astype(str) + " | Apto " + libres['apto'].astype(str)
    
    opciones = st.multiselect("Busca apartamentos:", libres['label'].tolist())
    
    if opciones:
        if st.button("✅ CONFIRMAR SELECCIÓN", type="primary"):
            fecha = datetime.now().strftime("%d/%m/%Y")
            indices = libres[libres['label'].isin(opciones)].index
            for idx in indices:
                df.at[idx, 'estado'] = "elaborada"
                df.at[idx, 'fecha_elaborada'] = fecha
            conn.update(data=df)
            st.session_state.df = df
            nav('home')
            st.rerun()

# --- VISTA: ENTREGAR ---
elif st.session_state.page == 'entregar':
    st.markdown("### 🚚 Pendientes de Entrega")
    if st.button("← VOLVER"): nav('home')
    
    pendientes = df[df['estado'] == "elaborada"]
    
    if pendientes.empty:
        st.markdown("<p style='text-align:center;'>No hay cartas pendientes 🎉</p>", unsafe_allow_html=True)
    else:
        for i, row in pendientes.iterrows():
            with st.container():
                st.markdown(f"""<div class='card-apto'>
                    <small>{row['conjunto']}</small><br>
                    <b>Torre {row['torre']} - Apto {row['apto']}</b><br>
                    <span style='font-size:10px; color:gray;'>Escrita: {row['fecha_elaborada']}</span>
                </div>""", unsafe_allow_html=True)
                if st.button(f"MARCAR ENTREGADO", key=f"btn_{row['id']}"):
                    df.at[i, 'estado'] = "entregada"
                    df.at[i, 'fecha_entregada'] = datetime.now().strftime("%d/%m/%Y")
                    conn.update(data=df)
                    st.session_state.df = df
                    st.rerun()
