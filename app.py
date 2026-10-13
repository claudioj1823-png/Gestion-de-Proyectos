import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="Gestión de Proyectos - EDEESTE",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Panel de Control Ejecutivo - Proyectos EDEESTE")
st.markdown("---")

# Menú lateral de navegación estilo Power BI
st.sidebar.markdown("### Menú de Navegación")
menu = st.sidebar.radio(
    "Seleccione una vista:", 
    ["Resumen Global", "Presupuestos y Metas SAP", "Seguimiento de Contratistas y Mano de Obra"]
)

# Función segura para leer archivos si están disponibles localmente o en el repo
@st.cache_data
def cargar_datos(nombre_archivo):
    if os.path.exists(nombre_archivo):
        try:
            return pd.read_excel(nombre_archivo)
        except Exception as e:
            return None
    return None

# Carga de archivos base disponibles
df_codigos = cargar_datos("Codigos de proyectos.xlsx")
df_contratistas = cargar_datos("Actividades contratistas.xlsx")
df_familia = cargar_datos("Actividades con su familia.xlsx")

if menu == "Resumen Global":
    st.subheader("📊 Resumen Ejecutivo y Catálogo de Proyectos")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Proyectos Registrados", value="180+" if df_codigos is not None else "Cargando...")
    with col2:
        st.metric(label="Familias de Actividades", value="Activas" if df_familia is not None else "Pendiente")
    with col3:
        st.metric(label="Estado del Sistema", value="Conectado 🟢")

    st.markdown("---")
    st.markdown("### 🔍 Vista Rápida de Códigos de Proyectos")
    
    if df_codigos is not None:
        st.dataframe(df_codigos, use_container_width=True)
    else:
        st.info("Sube o mantén los archivos en la raíz del repositorio para visualizarlos de forma automática.")
        archivo_subido = st.file_uploader("Cargar 'Codigos de proyectos.xlsx'", type=["xlsx"])
        if archivo_subido:
            st.dataframe(pd.read_excel(archivo_subido), use_container_width=True)

elif menu == "Presupuestos y Metas SAP":
    st.subheader("🎯 Control de Metas, Presupuestos y Precios SAP")
    st.markdown("Análisis financiero y cumplimiento de metas físicas orientadas a la planificación de EDEESTE.")
    
    # Espacio para Precios SAP y Metas
    st.info("Módulo configurado para integrar 'Precios Sap.xlsx' y 'Proyectos con sus metas.xlsx'.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 💰 Precios Unitarios SAP")
        file_sap = st.file_uploader("Cargar Precios Sap.xlsx", type=["xlsx"], key="sap")
        if file_sap:
            st.dataframe(pd.read_excel(file_sap), use_container_width=True)
            
    with col_b:
        st.markdown("#### 🎯 Metas de Proyectos")
        file_metas = st.file_uploader("Cargar Proyectos con sus metas.xlsx", type=["xlsx"], key="metas")
        if file_metas:
            st.dataframe(pd.read_excel(file_metas), use_container_width=True)

else:
    st.subheader("👷 Seguimiento de Contratistas y Mano de Obra")
    st.markdown("Control operacional de cuadrillas y ejecución en campo.")
    
    if df_contratistas is not None:
        st.markdown("#### Actividades de Contratistas")
        st.dataframe(df_contratistas, use_container_width=True)
    
    file_mo = st.file_uploader("Cargar 'Mano de Obra por proyecto.xlsx'", type=["xlsx"], key="mo")
    if file_mo:
        st.markdown("#### Mano de Obra Registrada")
        st.dataframe(pd.read_excel(file_mo), use_container_width=True)
