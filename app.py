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
                # Limpiar espacios en nombres de columnas
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
st.sidebar.caption("EDEESTE - Sistema de Control Presupuestario")

df_mo = datos.get('mo')
df_familia = datos.get('familia')
df_sap = datos.get('sap')
df_metas = datos.get('metas')

# Vista 1: Panel Ejecutivo por Proyecto
if menu == "Panel Ejecutivo por Proyecto":
    st.subheader(f"📌 Proyecto Seleccionado: {codigo_seleccionado}")
    
    if codigo_seleccionado != "Todos":
        cod_clean = str(codigo_seleccionado).strip().lower()
        
        # 1. Mano de Obra Ejecutada
        monto_mo = 0.0
        df_mo_proy = pd.DataFrame()
        if df_mo is not None and not df_mo.empty:
            # Buscar columna que tenga 'proy' o 'código'
            col_proy_mo = next((c for c in df_mo.columns if 'proy' in c.lower() or 'código' in c.lower()), df_mo.columns[-1])
            col_costo = next((c for c in df_mo.columns if 'costo total' in c.lower() or 'total' in c.lower()), df_mo.columns[5])
            
            df_mo['Clean_Proy'] = df_mo[col_proy_mo].astype(str).str.strip().str.lower()
            df_mo_proy = df_mo[df_mo['Clean_Proy'] == cod_clean]
            monto_mo = pd.to_numeric(df_mo_proy[col_costo], errors='coerce').sum()

        # 2. Presupuesto Planificado
        presupuesto_plan = 0.0
        df_meta_proy = pd.DataFrame()
        if df_metas is not None and not df_metas.empty:
            col_proy_meta = next((c for c in df_metas.columns if 'proyecto' in c.lower() or 'código' in c.lower()), df_metas.columns[0])
            col_presupuesto = next((c for c in df_metas.columns if 'presupuesto' in c.lower()), df_metas.columns[-1])
            
            df_metas['Clean_Proy'] = df_metas[col_proy_meta].astype(str).str.strip().str.lower()
            df_meta_proy = df_metas[df_metas['Clean_Proy'] == cod_clean]
            
            val_presupuesto = pd.to_numeric(df_meta_proy[col_presupuesto], errors='coerce').dropna()
            if not val_presupuesto.empty:
                presupuesto_plan = val_presupuesto.iloc[0]

        # 3. Cruce de Actividades y Precios SAP
        costo_materiales_total = 0.0
        df_materiales_calculados = pd.DataFrame()
        if df_familia is not None and not df_familia.empty and df_sap is not None and not df_sap.empty:
            col_act_fam = next((c for c in df_familia.columns if 'actividad' in c.lower()), df_familia.columns[0])
            col_sap_fam = next((c for c in df_familia.columns if 'sap' in c.lower()), df_familia.columns[3])
            col_cant_mat = next((c for c in df_familia.columns if 'cantidad' in c.lower()), df_familia.columns[-1])
            
            col_sap_prec = next((c for c in df_sap.columns if 'sap' in c.lower()), df_sap.columns[0])
            col_precio_final = next((c for c in df_sap.columns if 'precio' in c.lower()), df_sap.columns[-1])
            
            if not df_meta_proy.empty:
                col_act_meta = next((c for c in df_meta_proy.columns if 'actividad' in c.lower() or 'partida' in c.lower()), df_meta_proy.columns[3])
                acts_proy = df_meta_proy[col_act_meta].astype(str).str.strip().unique()
                
                df_fam_filtrado = df_familia[df_familia[col_act_fam].astype(str).str.strip().isin(acts_proy)].copy()
                
                df_sap['Clean_SAP'] = df_sap[col_sap_prec].astype(str).str.strip()
                df_fam_filtrado['Clean_SAP'] = df_fam_filtrado[col_sap_fam].astype(str).str.strip()
                
                df_merge = pd.merge(df_fam_filtrado, df_sap, on='Clean_SAP', how='inner')
                df_merge['Costo_Material'] = pd.to_numeric(df_merge[col_cant_mat], errors='coerce') * pd.to_numeric(df_merge[col_precio_final], errors='coerce')
                costo_materiales_total = df_merge['Costo_Material'].sum()
                df_materiales_calculados = df_merge

        # Tarjetas de Indicadores
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Mano de Obra Ejecutada (RD$)", f"{monto_mo:,.2f}")
        col2.metric("Presupuesto Planificado (RD$)", f"{presupuesto_plan:,.2f}")
        col3.metric("Costo Materiales (SAP) (RD$)", f"{costo_materiales_total:,.2f}")
        
        porcentaje_ejecutado = (monto_mo / presupuesto_plan * 100) if presupuesto_plan > 0 else 0
        col4.metric("% Ejecución Presupuestaria", f"{porcentaje_ejecutado:.1f}%")

        st.markdown("---")
        st.markdown("### 📊 Desglose Financiero y Materiales Vinculados")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            df_grafico = pd.DataFrame({
                'Concepto': ['Mano de Obra', 'Materiales SAP', 'Presupuesto Plan.'],
                'Monto (RD$)': [monto_mo, costo_materiales_total, presupuesto_plan]
            })
            fig_bar = px.bar(df_grafico, x='Concepto', y='Monto (RD$)', color='Concepto', title="Comparativo Financiero del Proyecto")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_g2:
            st.markdown("#### 🛠️ Materiales Asociados por Actividad")
            if not df_materiales_calculados.empty:
                st.dataframe(df_materiales_calculados.head(10), use_container_width=True)
            else:
                st.info("No se encontraron materiales vinculados para este proyecto.")
                
        st.markdown("#### 📋 Detalle de Mano de Obra del Proyecto")
        if not df_mo_proy.empty:
            st.dataframe(df_mo_proy.head(15), use_container_width=True)
        else:
            st.warning(f"⚠️ No se encontraron registros de mano de obra para el código '{codigo_seleccionado}' en el archivo de Mano de Obra.")
    else:
        st.info("👈 Por favor seleccione un Código de Proyecto en el menú lateral.")

elif menu == "Relación Mano de Obra y Materiales":
    st.subheader("🧩 Matriz Relacional: Actividades, Materiales y Precios SAP")
    if df_familia is not None:
        st.dataframe(df_familia, use_container_width=True)
    else:
        st.warning("No se encontró el archivo 'Actividades con su familia.xlsx'.")

else:
    st.subheader("🗺️ Ubicación Geográfica del Proyecto en Zona de Concesión EDEESTE")
    map_data = pd.DataFrame({
        'lat': [18.4861, 18.5123, 18.4500, 18.5500],
        'lon': [-69.8500, -69.8000, -69.6500, -69.7800],
        'Proyecto': ['Proyecto Redes La Javilla', 'Ciudad Juan Bosch', 'Circuito SPER01', 'Rehabilitación LM3802R']
    })
    st.map(map_data)
    st.caption("Ubicación satelital y puntos de ejecución del proyecto.")
