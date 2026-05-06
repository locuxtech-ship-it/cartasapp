import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Alameda del Río | Predicación",
    page_icon="🏠",
    layout="centered"
)

# --- ESTILOS CSS PERSONALIZADOS (MODERNO) ---
st.markdown("""
    <style>
    /* Fondo y fuente */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E0E0E0;
    }

    /* Tarjetas de Apartamentos */
    .apto-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #F0F2F6;
        margin-bottom: 15px;
        transition: transform 0.2s;
    }
    .apto-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }

    /* Badge de Conjunto */
    .conjunto-badge {
        background-color: #E3F2FD;
        color: #1976D2;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
        margin-bottom: 10px;
        display: inline-block;
    }

    /* Estadísticas */
    .metric-container {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #E0E0E0;
        text-align: center;
    }

    /* Botones */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #262730;
        font-family: 'Inter', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN Y DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(ttl=0)

df = load_data()

# --- BARRA LATERAL (NAVEGACIÓN) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>📋 Menú</h2>", unsafe_allow_html=True)
    menu = st.radio(
        "",
        ["🏠 Inicio", "✍️ Escribir Cartas", "📦 Pendientes Entrega", "📊 Historial"],
        label_visibility="collapsed"
    )
    st.divider()
    st.caption("Alameda del Río - Gestión de Territorio")

# --- MÓDULO 1: INICIO Y ESTADÍSTICAS ---
if menu == "🏠 Inicio":
    st.markdown("# Bienvenido 👋")
    st.markdown("Gestión de cartas para el territorio de Alameda del Río.")
    
    # Cálculos
    total_aptos = len(df)
    elaboradas = len(df[df['estado'] == "elaborada"])
    entregadas = len(df[df['estado'] == "entregada"])
    porcentaje = (entregadas / total_aptos) if total_aptos > 0 else 0
    
    # Layout de métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='metric-container'><small>Total</small><h3>{total_aptos:,}</h3></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-container'><small>Escritas</small><h3 style='color:#FBC02D;'>{elaboradas}</h3></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-container'><small>Entregadas</small><h3 style='color:#4CAF50;'>{entregadas}</h3></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Progreso del territorio")
    st.progress(porcentaje)
    st.write(f"Avance actual: **{porcentaje:.2%}**")

# --- MÓDULO 2: ESCRIBIR CARTAS ---
elif menu == "✍️ Escribir Cartas":
    st.subheader("✍️ Generar nuevas cartas")
    
    aptos_disponibles = df[df['estado'].isna() | (df['estado'] == "")].copy()
    
    tab_auto, tab_manual = st.tabs(["Selección Inteligente", "Selección Manual"])
    
    with tab_auto:
        st.info("Esta opción elige apartamentos al azar, asegurando que sean de conjuntos distintos.")
        cantidad = st.select_slider("¿Cuántas cartas vas a escribir?", options=[1, 2, 5, 10, 15, 20])
        
        if st.button("🎲 Sugerir Apartamentos", use_container_width=True):
            # Lógica: Mezclar, quitar duplicados por conjunto y tomar N
            sugerencia = aptos_disponibles.sample(frac=1).drop_duplicates(subset='conjunto').head(cantidad)
            st.session_state.cartas_hoy = sugerencia

    with tab_manual:
        aptos_disponibles['search_label'] = aptos_disponibles['conjunto'] + " - Torre " + aptos_disponibles['torre'].astype(str) + " - Apto " + aptos_disponibles['apto'].astype(str)
        seleccionados = st.multiselect("Busca apartamentos específicos:", aptos_disponibles['search_label'].tolist())
        
        if st.button("📌 Confirmar Selección Manual", use_container_width=True):
            st.session_state.cartas_hoy = aptos_disponibles[aptos_disponibles['search_label'].isin(seleccionados)]

    # Mostrar para confirmar
    if 'cartas_hoy' in st.session_state and not st.session_state.cartas_hoy.empty:
        st.divider()
        st.markdown("### 📋 Lista para escribir:")
        for _, row in st.session_state.cartas_hoy.iterrows():
            st.markdown(f"""
                <div class="apto-card">
                    <span class="conjunto-badge">{row['conjunto']}</span><br>
                    <b>Dirección:</b> {row['direccion']}<br>
                    <b>Ubicación:</b> Torre {row['torre']} - Apto {row['apto']}
                </div>
            """, unsafe_allow_html=True)
            
        if st.button("✅ MARCAR COMO REALIZADAS", type="primary", use_container_width=True):
            fecha = datetime.now().strftime("%Y-%m-%d")
            for idx in st.session_state.cartas_hoy.index:
                df.at[idx, 'estado'] = "elaborada"
                df.at[idx, 'fecha_elaborada'] = fecha
            
            # Quitar columna auxiliar si existe
            cols_to_save = [c for c in df.columns if c != 'search_label']
            conn.update(data=df[cols_to_save])
            
            st.success("¡Cartas registradas!")
            del st.session_state.cartas_hoy
            st.rerun()

# --- MÓDULO 3: ENTREGAR ---
elif menu == "📦 Pendientes Entrega":
    st.subheader("🚚 Cartas por entregar")
    pendientes = df[df['estado'] == "elaborada"]
    
    if pendientes.empty:
        st.info("No hay cartas pendientes de entrega.")
    else:
        for i, row in pendientes.iterrows():
            with st.container():
                col_text, col_action = st.columns([3, 1])
                with col_text:
                    st.markdown(f"""
                        <div class="apto-card">
                            <span class="conjunto-badge">{row['conjunto']}</span><br>
                            <b>Apto {row['apto']}</b> - Torre {row['torre']}<br>
                            <small>Escrita el: {row['fecha_elaborada']}</small>
                        </div>
                    """, unsafe_allow_html=True)
                with col_action:
                    st.write("") # Espaciador
                    if st.button("Entregado ✅", key=f"ent_{row['id']}", use_container_width=True):
                        df.at[i, 'estado'] = "entregada"
                        df.at[i, 'fecha_entregada'] = datetime.now().strftime("%Y-%m-%d")
                        conn.update(data=df)
                        st.rerun()

# --- MÓDULO 4: HISTORIAL ---
elif menu == "📊 Historial":
    st.subheader("📜 Últimas cartas entregadas")
    historial = df[df['estado'] == "entregada"].sort_values(by='fecha_entregada', ascending=False)
    
    if historial.empty:
        st.write("Aún no hay historial de entregas.")
    else:
        st.dataframe(
            historial[['fecha_entregada', 'conjunto', 'torre', 'apto']],
            use_container_width=True,
            hide_index=True
        )
