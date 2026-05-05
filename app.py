import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN E INTERFAZ ---
st.set_page_config(page_title="Alameda del Río - Predicación", layout="wide", page_icon="✉️")

# CSS personalizado para mejorar la estética
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #4CAF50; color: white; border: none; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .card { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 15px; 
        border-left: 5px solid #4CAF50; 
        margin-bottom: 10px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        color: #31333F;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # ttl=0 para asegurar que los datos se recarguen de la nube cada vez
    return conn.read(ttl=0)

df = load_data()

# --- NAVEGACIÓN ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3062/3062634.png", width=100)
    st.title("Menú Principal")
    menu = st.radio("Acciones:", ["📊 Estadísticas", "✍️ Generar Cartas", "🚚 Entregar Cartas"])
    st.info("Gestión de territorio Alameda del Río.")

# --- MÓDULO 1: ESTADÍSTICAS ---
if menu == "📊 Estadísticas":
    st.title("Dashboard de Progreso")
    
    total = len(df)
    # Manejar posibles valores nulos en el estado
    elaboradas = len(df[df['estado'] == "elaborada"])
    entregadas = len(df[df['estado'] == "entregada"])
    disponibles = total - elaboradas - entregadas
    porcentaje = (entregadas / total) if total > 0 else 0

    # Métricas principales
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Apartamentos", f"{total:,}")
    c2.metric("Disponibles", f"{disponibles:,}")
    c3.metric("En Proceso ✍️", f"{elaboradas}")
    c4.metric("Entregadas ✅", f"{entregadas}", f"{porcentaje:.2%}")

    st.subheader("Progreso de Cobertura Total")
    st.progress(porcentaje)

    # Gráfico por conjunto
    st.subheader("Avance por Conjunto Residencial")
    chart_df = df[df['estado'].isin(['elaborada', 'entregada'])]
    if not chart_df.empty:
        chart_data = chart_df.groupby(['conjunto', 'estado']).size().unstack().fillna(0)
        st.bar_chart(chart_data)
    else:
        st.info("Aún no hay cartas procesadas para mostrar en el gráfico.")

# --- MÓDULO 2: GENERAR CARTAS ---
elif menu == "✍️ Generar Cartas":
    st.title("Generar Nuevas Cartas")
    
    # Filtrar disponibles
    aptos_libres = df[(df['estado'].isna()) | (df['estado'] == "")].copy()

    if aptos_libres.empty:
        st.warning("¡Increíble! No quedan apartamentos disponibles en el territorio.")
    else:
        tab_auto, tab_manual = st.tabs(["🎲 Selección Aleatoria", "🖱️ Selección Manual"])

        with tab_auto:
            n = st.number_input("¿Cuántas cartas vas a escribir?", min_value=1, max_value=40, value=5)
            if st.button("Sugerir Apartamentos"):
                # Máximo uno por conjunto para variar
                seleccion = aptos_libres.sample(frac=1).drop_duplicates(subset='conjunto').head(n)
                st.session_state.temp_cartas = seleccion

        with tab_manual:
            st.write("Busca apartamentos por nombre de conjunto o número:")
            aptos_libres['label'] = aptos_libres['conjunto'] + " - Torre " + aptos_libres['torre'].astype(str) + " - Apto " + aptos_libres['apto'].astype(str)
            seleccion_manual = st.multiselect("Selecciona los apartamentos:", aptos_libres['label'].tolist())
            
            if st.button("Usar Selección Manual"):
                st.session_state.temp_cartas = aptos_libres[aptos_libres['label'].isin(seleccion_manual)]

        # Confirmación de guardado
        if 'temp_cartas' in st.session_state and not st.session_state.temp_cartas.empty:
            st.subheader("Lista para escribir:")
            for i, row in st.session_state.temp_cartas.iterrows():
                st.markdown(f"""
                    <div class="card">
                    <b>Conjunto:</b> {row['conjunto']}<br>
                    <b>Dirección:</b> {row['direccion']}<br>
                    <b>Ubicación:</b> Torre {row['torre']} - Apto {row['apto']}
                    </div>
                """, unsafe_allow_html=True)
            
            if st.button("Confirmar y Marcar como 'Elaborada'"):
                fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
                for idx in st.session_state.temp_cartas.index:
                    df.at[idx, 'estado'] = "elaborada"
                    df.at[idx, 'fecha_elaborada'] = fecha_hoy
                
                # Quitar columna auxiliar si existe
                if 'label' in df.columns: df.drop(columns=['label'], inplace=True)
                
                conn.update(data=df)
                st.success("¡Cartas registradas correctamente!")
                st.balloons()
                del st.session_state.temp_cartas
                st.rerun()

# --- MÓDULO 3: ENTREGA ---
elif menu == "🚚 Entregar Cartas":
    st.title("Cartas Pendientes por Entregar")
    
    pendientes = df[df['estado'] == "elaborada"]
    
    if pendientes.empty:
        st.info("No hay cartas pendientes de entrega.")
    else:
        st.write(f"Tienes **{len(pendientes)}** cartas listas para llevar.")
        
        for i, row in pendientes.iterrows():
            with st.container():
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    st.markdown(f"""
                        <div class="card">
                        <span style="font-size: 1.1em; color: #1f77b4;"><b>{row['conjunto']}</b></span><br>
                        📍 {row['direccion']} | Torre {row['torre']} - <b>Apto {row['apto']}</b><br>
                        <small>Elaborada el: {row['fecha_elaborada']}</small>
                        </div>
                    """, unsafe_allow_html=True)
                with col_btn:
                    st.write(" ")
                    if st.button("Entregada", key=f"entrega_{row['id']}"):
                        df.at[i, 'estado'] = "entregada"
                        df.at[i, 'fecha_entregada'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        conn.update(data=df)
                        st.toast(f"Apto {row['apto']} marcado como entregado")
                        st.rerun()
