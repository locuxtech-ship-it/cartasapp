import streamlit as st
import pandas as pd
import random
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuración de la página
st.set_page_config(page_title="Gestión Alameda del Río", layout="wide")

st.title("Sistema de Predicación - Alameda del Río")

# Conexión a Google Sheets (Base de datos persistente)
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0) # ttl=0 para que siempre lea datos frescos

# --- BARRA LATERAL (Navegación) ---
menu = st.sidebar.selectbox("Ir a:", ["Generar Cartas", "Módulo de Entrega", "Estadísticas"])

# --- LÓGICA DE SELECCIÓN ALEATORIA ---
def seleccionar_aleatorio(n_cartas):
    # Filtrar solo disponibles (estado vacío o nulo)
    disponibles = df[df['estado'].isna() | (df['estado'] == "")]
    
    if disponibles.empty:
        return pd.DataFrame()

    # Mezclar y eliminar duplicados por conjunto para que no se repitan en una misma tanda
    seleccion = disponibles.sample(frac=1).drop_duplicates(subset='conjunto')
    
    return seleccion.head(n_cartas)

# --- MÓDULO 1: GENERAR CARTAS ---
if menu == "Generar Cartas":
    st.header("Selección de Direcciones")
    
    tab1, tab2 = st.tabs(["Aleatorio", "Manual"])
    
    with tab1:
        n = st.number_input("¿Cuántas cartas vas a escribir?", min_value=1, max_value=50, value=10)
        if st.button("Sugerir Direcciones"):
            sugeridos = seleccionar_aleatorio(n)
            if not sugeridos.empty:
                st.session_state.temp_cartas = sugeridos
            else:
                st.warning("No hay más apartamentos disponibles.")

    with tab2:
        aptos_libres = df[df['estado'].isna() | (df['estado'] == "")]
        opciones = aptos_libres.apply(lambda x: f"{x['id']} - {x['conjunto']} - {x['apto']}", axis=1)
        seleccion_manual = st.multiselect("Escoge los apartamentos:", opciones)
        
        if st.button("Usar Selección Manual"):
            ids = [int(s.split(" - ")[0]) for s in seleccion_manual]
            st.session_state.temp_cartas = df[df['id'].isin(ids)]

    # Mostrar previsualización y confirmar
    if 'temp_cartas' in st.session_state:
        st.subheader("Apartamentos seleccionados:")
        st.table(st.session_state.temp_cartas[['conjunto', 'direccion', 'torre', 'apto']])
        
        if st.button("Confirmar y Marcar como 'Elaborada'"):
            for idx in st.session_state.temp_cartas.index:
                df.at[idx, 'estado'] = "elaborada"
                df.at[idx, 'fecha_elaborada'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            conn.update(data=df) # Guarda en Google Sheets
            st.success("¡Cartas registradas! Ahora aparecen en el módulo de entrega.")
            del st.session_state.temp_cartas

# --- MÓDULO 2: ENTREGA ---
elif menu == "Módulo de Entrega":
    st.header("Cartas Pendientes por Entregar")
    pendientes = df[df['estado'] == "elaborada"]
    
    if pendientes.empty:
        st.info("No hay cartas pendientes de entrega.")
    else:
        for i, row in pendientes.iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.write(f"**{row['conjunto']}** - {row['direccion']} (Apto {row['apto']})")
            col2.write(f"Escrita el: {row['fecha_elaborada']}")
            if col3.button("Marcar Entregada", key=row['id']):
                df.at[i, 'estado'] = "entregada"
                df.at[i, 'fecha_entregada'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                conn.update(data=df)
                st.rerun()

# --- MÓDULO 3: ESTADÍSTICAS ---
elif menu == "Estadísticas":
    st.header("Resumen del Territorio")
    
    total = len(df)
    elaboradas = len(df[df['estado'] == "elaborada"])
    entregadas = len(df[df['estado'] == "entregada"])
    disponibles = total - elaboradas - entregadas
    porcentaje = (entregadas / total) * 100
    
    c1, i1, c2, c3 = st.columns(4)
    c1.metric("Total Aptos", total)
    i1.metric("Disponibles", disponibles)
    c2.metric("En Proceso", elaboradas)
    c3.metric("Entregadas ✅", entregadas)
    
    st.progress(entregadas / total)
    st.write(f"Avance del territorio: **{porcentaje:.2f}%**")
    
    # Gráfico por conjunto
    st.subheader("Avance por Conjunto")
    stats_conjunto = df.groupby('conjunto')['estado'].value_counts().unstack().fillna(0)
    st.bar_chart(stats_conjunto)