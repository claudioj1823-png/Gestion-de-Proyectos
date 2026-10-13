import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="Panel de Proyectos - EDEESTE",
    page_icon="⚡",
    layout="wide"
)

# Estilo visual ejecutivo similar al diseño mostrado
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .metric-card { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Panel de Control Ejecutivo de Proyectos - EDEESTE")
st.markdown("---")

# Barra lateral de navegación y filtros
st.sidebar.markdown("### 🧭 Navegación")
menu = st.sidebar.radio(
    "Seleccione una vista:", 
    ["Resumen Ejecutivo", "Presupuestos SAP", "Seguimiento Contratistas", "Mano de Obra"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filtros Globales")
busqueda_codigo = st.sidebar.text_input("Buscar Código Proyecto", placeholder="Ej. O-PE-16-002")

# Función para cargar datos de manera segura
@st.cache_data
def cargar_excel(nombre):
    if os.path.exists(nombre):
        try:
            return pd.read_excel(nombre)
        except:
            return None
    return None

df_codigos = cargar_excel("Codigos de proyectos.xlsx")
df_contratistas = cargar_excel("Actividades contratistas.xlsx")

if menu == "Resumen Ejecutivo":
    # Sección de Filtros superiores en la interfaz
    st.markdown("### 📋 Filtros y Controles")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        cat_proyecto = st.selectbox("Categoría del Proyecto", ["Todos", "Redes de Distribución", "Alumbrado Público", "Subestaciones"])
    with col_f2:
        gerencia = st.selectbox("Gerencia Responsable", ["Todas", "Gerencia Norte", "Gerencia Este", "Gerencia Sur"])
    with col_f3:
        rango_avance = st.slider("Rango de Avance (%)", 0, 100, (0, 100))

    st.markdown("---")

    # Tarjetas de KPIs y Gráficos simulados ejecutivos
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    
    with col_kpi1:
        st.markdown("### 📊 Total Proyectos en Curso")
        st.metric(label="Activos", value="185", delta="+12 vs. Mes Anterior")
        # Simulación visual de distribución por estado
        chart_data_donut = pd.DataFrame({'Estado': ['Activo', 'Finalizado', 'Demorado'], 'Cantidad': [120, 45, 20]})
        st.bar_chart(chart_data_donut.set_index('Estado'))

    with col_kpi2:
        st.markdown("### 💰 Presupuesto y Ejecución Sap")
        st.metric(label="Ejecución Presupuestaria", value="82%", delta="-4%")
        chart_data_bar = pd.DataFrame({
            'Concepto': ['Presupuesto Inicial', 'Gasto Real', 'Proyección'],
            'Monto (M RD$)': [6.5, 4.2, 5.8]
        })
        st.bar_chart(chart_data_bar.set_index('Concepto'))

    with col_kpi3:
        st.markdown("### 🎯 Avance de Metas por Proyecto")
        st.metric(label="Cumplimiento Global", value="78%")
        chart_metas = pd.DataFrame({
            'Proyecto': ['O-PE-04', 'O-PE-05', 'O-PE-06', 'O-PE-07'],
            'Meta Física': [90, 85, 95, 80],
            'Avance Real': [75, 70, 90, 65]
        })
        st.bar_chart(chart_metas.set_index('Proyecto'))

    st.markdown("---")
    st.markdown("### 📑 Lista Completa y Filtros Dinámicos")
    
    if df_codigos is not None:
        # Filtrar si el usuario escribió un código en la barra lateral
        df_mostrar = df_codigos
        if busqueda_codigo:
            df_mostrar = df_codigos[df_codigos.astype(str).apply(lambda x: x.str.contains(busqueda_codigo, case=False)).any(axis=1)]
        st.dataframe(df_mostrar, use_container_width=True)
    else:
        st.info("Coloque o cargue 'Codigos de proyectos.xlsx' para ver el listado completo.")
        file_sub = st.file_uploader("Subir Codigos de proyectos.xlsx", type=["xlsx"])
        if file_sub:
            st.dataframe(pd.read_excel(file_sub), use_container_width=True)

elif menu == "Presupuestos SAP":
    st.subheader("🎯 Control de Presupuestos y Precios SAP")
    st.markdown("Análisis financiero detallado por partida y costos unitarios.")
    file_sap = st.file_uploader("Cargar 'Precios Sap.xlsx' y 'Proyectos con sus metas.xlsx'", type=["xlsx"], accept_multiple_files=True)
    if file_sap:
        for f in file_sap:
            st.write(f"Archivo: {f.name}")
            st.dataframe(pd.read_excel(f), use_container_width=True)

elif menu == "Seguimiento Contratistas":
    st.subheader("👷 Actividades de Contratistas")
    if df_contratistas is not None:
        st.dataframe(df_contratistas, use_container_width=True)
    else:
        file_cont = st.file_uploader("Cargar 'Actividades contratistas.xlsx'", type=["xlsx"])
        if file_cont:
            st.dataframe(pd.read_excel(file_cont), use_container_width=True)

else:
    st.subheader("👥 Control de Mano de Obra por Proyecto")
    file_mo = st.file_uploader("Cargar 'Mano de Obra por proyecto.xlsx'", type=["xlsx"])
    if file_mo:
        st.dataframe(pd.read_excel(file_mo), use_container_width=True)
