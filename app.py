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

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Panel de Control Ejecutivo - Gestión de Proyectos EDEESTE")
st.markdown("---")

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
                df = pd.read_excel(ruta)
                # Limpiar espacios en los nombres de las columnas
                df.columns = [str(c).strip() for c in df.columns]
                dfs[clave] = df
            except Exception as e:
                dfs[clave] = None
        else:
            dfs[clave] = None
    return dfs

datos = cargar_datos()

# Sidebar: Selección de Proyecto
st.sidebar.markdown("### 🎯 Selección de Proyecto")

df_codigos = datos.get('codigos')

if df_codigos is not None and not df_codigos.empty:
    col_codigo = df_codigos.columns[0]
    lista_codigos = df_codigos[col_codigo].dropna().astype(str).str.strip().unique().tolist()
    codigo_seleccionado = st.sidebar.selectbox("Seleccione Código de Proyecto:", ["Todos"] + lista_codigos)
else:
    st.sidebar.warning("No se encontró 'Codigos de proyectos.xlsx'")
    codigo_seleccionado = "Todos"

menu = st.sidebar.radio("🧭 Vista General", ["Panel Ejecutivo por Proyecto", "Relación Mano de Obra y Materiales", "Mapas de Ubicación"])

st.sidebar.markdown("---")
st.sidebar.caption("EDEESTE - Sistema de Control Presupuestario y Ejecución")

df_mo = datos.get('mo')
df_familia = datos.get('familia')
df_sap = datos.get('sap')
df_metas = datos.get('metas')

# Vista 1: Panel Ejecutivo por Proyecto
if menu == "Panel Ejecutivo por Proyecto":
    st.subheader(f"📌 Proyecto Seleccionado: {codigo_seleccionado}")
    
    if codigo_seleccionado != "Todos":
        col1, col2, col3, col4 = st.columns(4)
        
        monto_mo = 0.0
        if df_mo is not None and not df_mo.empty:
            # Buscar columna de código de proyecto de forma flexible
            col_proy_mo = next((c for c in df_mo.columns if 'proy' in c.lower() or 'código' in c.lower()), None)
            col_costo = next((c for c in df_mo.columns if 'costo total' in c.lower() or 'total' in c.lower()), None)
            
            if col_proy_mo and col_costo:
                df_mo[col_proy_mo] = df_mo[col_proy_mo].astype(str).str.strip()
                df_mo_proy = df_mo[df_mo[col_proy_mo] == str(codigo_seleccionado).strip()]
                monto_mo = pd.to_numeric(df_mo_proy[col_costo], errors='coerce').sum()
        
        presupuesto_plan = 0.0
        if df_metas is not None and not df_metas.empty:
            # Buscar columna de código y presupuesto de forma flexible
            col_proy_meta = next((c for c in df_metas.columns if 'codigo' in c.lower() or 'proy' in c.lower()), None)
            col_presupuesto = next((c for c in df_metas.columns if 'presupuesto' in c.lower()), None)
            
            if col_proy_meta and col_presupuesto:
                df_metas[col_proy_meta] = df_metas[col_proy_meta].astype(str).str.strip()
                df_meta_proy = df_metas[df_metas[col_proy_meta] == str(codigo_seleccionado).strip()]
                val_presupuesto = pd.to_numeric(df_meta_proy[col_presupuesto], errors='coerce').dropna()
                if not val_presupuesto.empty:
                    presupuesto_plan = val_presupuesto.iloc[0]

        col1.metric("Mano de Obra Ejecutada (RD$)", f"{monto_mo:,.2f}")
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
                'Concepto': ['Mano de Obra Ejec.', 'Presupuesto Planificado'],
                'Monto (RD$)': [monto_mo, presupuesto_plan]
            })
            fig_bar = px.bar(df_grafico, x='Concepto', y='Monto (RD$)', color='Concepto', title="Comparativo Presupuestario del Proyecto")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_g2:
            st.markdown("#### 🛠️ Metas y Actividades del Proyecto")
            if df_metas is not None:
                col_proy_meta = next((c for c in df_metas.columns if 'codigo' in c.lower() or 'proy' in c.lower()), None)
                if col_proy_meta:
                    df_meta_proy = df_metas[df_metas[col_proy_meta] == str(codigo_seleccionado).strip()]
                    cols_mostrar = [c for c in ['Actividad / Partida', 'Cantidad Planificada', 'Unidad'] if c in df_meta_proy.columns]
                    if cols_mostrar:
                        st.dataframe(df_meta_proy[cols_mostrar], use_container_width=True)
                    else:
                        st.dataframe(df_meta_proy.head(5), use_container_width=True)
            else:
                st.info("No se encontró información de metas.")
    else:
        st.info("👈 Por favor seleccione un Código de Proyecto en el menú lateral para ver el desglose ejecutivo completo.")

# Vista 2: Relación Mano de Obra y Materiales
elif menu == "Relación Mano de Obra y Materiales":
    st.subheader("🧩 Matriz Relacional: Mano de Obra ➔ Actividad ➔ Materiales ➔ Precios SAP")
    if df_familia is not None:
        st.dataframe(df_familia, use_container_width=True)
    else:
        st.warning("No se encontró el archivo 'Actividades con su familia.xlsx'.")

# Vista 3: Mapas de Ubicación
else:
    st.subheader("🗺️ Ubicación Geográfica del Proyecto en Zona de Concesión EDEESTE")
    map_data = pd.DataFrame({
        'lat': [18.4861, 18.5123, 18.4500, 18.5500],
        'lon': [-69.8500, -69.8000, -69.6500, -69.7800],
        'Proyecto': ['Proyecto Redes La Javilla', 'Ciudad Juan Bosch', 'Circuito SPER01', 'Rehabilitación LM3802R']
    })
    st.map(map_data)
    st.caption("Ubicación satelital y puntos de ejecución del proyecto.")
