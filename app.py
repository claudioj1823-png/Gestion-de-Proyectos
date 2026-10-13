import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

st.set_page_config(
    page_title="Panel de Control Ejecutivo - EDEESTE",
    page_icon="⚡",
    layout="wide"
)

# Estilo visual limpio y profesional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Panel de Control Ejecutivo - Gestión de Proyectos EDEESTE")
st.markdown("---")

# Función optimizada para cargar los archivos del repositorio en GitHub
@st.cache_data
def cargar_datos():
    archivos = {
        'codigos': 'Codigos de proyectos.xlsx',
        'familia': 'Actividades con su familia.xlsx',
        'contratistas': 'Actividades contratistas.xlsx',
        'sap': 'Precios Sap.xlsx',
        'metas': 'Proyectos con sus metas.xlsx',
        'mo': 'Mano de Obra por proyecto.xlsx'
    }
    dfs = {}
    for clave, ruta in archivos.items():
        if os.path.exists(ruta):
            try:
                dfs[clave] = pd.read_excel(ruta)
            except Exception as e:
                dfs[clave] = None
        else:
            dfs[clave] = None
    return dfs

datos = cargar_datos()

# Sidebar: Búsqueda y Selección de Proyecto
st.sidebar.markdown("### 🎯 Selección de Proyecto")

df_codigos = datos.get('codigos')

if df_codigos is not None and not df_codigos.empty:
    col_codigo = df_codigos.columns[0]
    lista_codigos = df_codigos[col_codigo].dropna().astype(str).unique().tolist()
    codigo_seleccionado = st.sidebar.selectbox("Seleccione Código de Proyecto:", ["Todos"] + lista_codigos)
else:
    st.sidebar.warning("No se encontró 'Codigos de proyectos.xlsx'")
    codigo_seleccionado = "Todos"

# Filtro por búsqueda rápida
busqueda_texto = st.sidebar.text_input("🔍 Buscar por Código o Nombre", "")

# VISTAS EN EL MENÚ PRINCIPAL
menu = st.sidebar.radio("🧭 Vista General", ["Panel Ejecutivo por Proyecto", "Relación Mano de Obra y Materiales", "Mapas de Ubicación"])

st.sidebar.markdown("---")
st.sidebar.caption("EDEESTE - Sistema de Control Presupuestario y Ejecución")

# LOGICA DE FILTRADO Y CRUCE
df_mo = datos.get('mo')
df_familia = datos.get('familia')
df_sap = datos.get('sap')
df_metas = datos.get('metas')

# Vista 1: Panel Ejecutivo por Proyecto
if menu == "Panel Ejecutivo por Proyecto":
    st.subheader(f"📌 Proyecto Seleccionado: {codigo_seleccionado}")
    
    if codigo_seleccionado != "Todos":
        col1, col2, col3, col4 = st.columns(4)
        
        # Filtro de Mano de Obra para el proyecto
        monto_mo = 0.0
        if df_mo is not None and not df_mo.empty:
            cols_mo = df_mo.columns
            # Intentar filtrar por código de proyecto
            df_mo_proy = df_mo[df_mo.astype(str).apply(lambda x: x.str.contains(codigo_seleccionado, case=False)).any(axis=1)]
            num_cols = df_mo_proy.select_dtypes(include=[np.number]).columns
            if len(num_cols) > 0:
                monto_mo = df_mo_proy[num_cols[0]].sum()
        
        # Cálculo de Presupuesto Planificado y Materiales
        presupuesto_plan = 0.0
        if df_metas is not None and not df_metas.empty:
            df_meta_proy = df_metas[df_metas.astype(str).apply(lambda x: x.str.contains(codigo_seleccionado, case=False)).any(axis=1)]
            num_cols_meta = df_meta_proy.select_dtypes(include=[np.number]).columns
            if len(num_cols_meta) > 0:
                presupuesto_plan = df_meta_proy[num_cols_meta[0]].sum()

        col1.metric("Mano de Obra (RD$)", f"{monto_mo:,.2f}")
        col2.metric("Presupuesto Planificado (RD$)", f"{presupuesto_plan:,.2f}")
        
        diferencia = presupuesto_plan - monto_mo
        porcentaje_ejecutado = (monto_mo / presupuesto_plan * 100) if presupuesto_plan > 0 else 0
        
        col3.metric("Variación / Saldo (RD$)", f"{diferencia:,.2f}")
        col4.metric("% Ejecución Presupuestaria", f"{porcentaje_ejecutado:.1f}%")

        st.markdown("---")
        
        st.markdown("### 📊 Gráficos de Ejecución vs Presupuesto")
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            df_grafico = pd.DataFrame({
                'Concepto': ['Mano de Obra Exec.', 'Presupuesto Planificado'],
                'Monto (RD$)': [monto_mo, presupuesto_plan]
            })
            fig_bar = px.bar(df_grafico, x='Concepto', y='Monto (RD$)', color='Concepto', title="Comparativo Presupuestario")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_g2:
            st.markdown("#### 🛠️ Resumen de Materiales Vinculados por Familia")
            if df_familia is not None:
                st.dataframe(df_familia.head(10), use_container_width=True)
            else:
                st.info("Cargue 'Actividades con su familia.xlsx' para ver la relación de materiales.")
    else:
        st.info("👈 Por favor seleccione un Código de Proyecto en el menú lateral para ver el desglose ejecutivo completo.")

# Vista 2: Relación Mano de Obra y Materiales
elif menu == "Relación Mano de Obra y Materiales":
    st.subheader("🧩 Matriz Relacional: Mano de Obra ➔ Actividad ➔ Materiales ➔ Precios SAP")
    st.markdown("Esta tabla refleja la combinación automática de las actividades con su familia de materiales y sus cantidades exactas.")
    
    if df_familia is not None:
        st.dataframe(df_familia, use_container_width=True)
    else:
        st.warning("No se encontró el archivo 'Actividades con su familia.xlsx' en el repositorio.")

# Vista 3: Mapas de Ubicación
else:
    st.subheader("🗺️ Ubicación Geográfica del Proyecto en Zona de Concesión EDEESTE")
    
    # Coordenadas por defecto (Zona Este / Santo Domingo Este, República Dominicana)
    map_data = pd.DataFrame({
        'lat': [18.4861, 18.5123, 18.4500, 18.5500],
        'lon': [-69.8500, -69.8000, -69.6500, -69.7800],
        'Proyecto': ['Proyecto Redes La Javilla', 'Ciudad Juan Bosch', 'Circuito SPER01', 'Rehabilitación LM3802R']
    })
    
    st.map(map_data)
    st.caption("Ubicación satelital y puntos de ejecución del proyecto.")
