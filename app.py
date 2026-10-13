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
df_contratistas = datos.get('contratistas')
df_sap = datos.get('sap')
df_metas = datos.get('metas')

# Vista 1: Panel Ejecutivo por Proyecto
if menu == "Panel Ejecutivo por Proyecto":
    st.subheader(f"📌 Proyecto Seleccionado: {codigo_seleccionado}")
    
    if codigo_seleccionado != "Todos":
        cod_clean = str(codigo_seleccionado).strip()
        
        # 1. Mano de Obra Ejecutada
        monto_mo = 0.0
        df_mo_proy = pd.DataFrame()
        if df_mo is not None and not df_mo.empty:
            col_proy_mo = 'Código Proyecto' if 'Código Proyecto' in df_mo.columns else df_mo.columns[-3]
            col_costo_mo = 'Costo Total' if 'Costo Total' in df_mo.columns else df_mo.columns[5]
            
            df_mo['Clean_Proy'] = df_mo[col_proy_mo].astype(str).str.strip()
            df_mo_proy = df_mo[df_mo['Clean_Proy'] == cod_clean]
            monto_mo = pd.to_numeric(df_mo_proy[col_costo_mo], errors='coerce').sum()

        # 2. Presupuesto Planificado
        presupuesto_plan = 0.0
        if df_metas is not None and not df_metas.empty:
            col_proy_meta = 'Código Proyecto' if 'Código Proyecto' in df_metas.columns else df_metas.columns[0]
            col_presupuesto = 'PRESUPUESTO' if 'PRESUPUESTO' in df_metas.columns else df_metas.columns[-1]
            
            df_metas['Clean_Proy'] = df_metas[col_proy_meta].astype(str).str.strip()
            df_meta_proy = df_metas[df_metas['Clean_Proy'] == cod_clean]
            
            val_presupuesto = pd.to_numeric(df_meta_proy[col_presupuesto], errors='coerce').dropna()
            if not val_presupuesto.empty:
                presupuesto_plan = val_presupuesto.iloc[0]

        # 3. Cruce Directo y Robusto de Materiales (Mano de Obra ➔ Contratistas ➔ Precios SAP)
        costo_materiales_total = 0.0
        df_materiales_calculados = pd.DataFrame()
        
        fuente_mat = df_contratistas if (df_contratistas is not None and not df_contratistas.empty) else df_familia
        
        if fuente_mat is not None and not fuente_mat.empty and df_sap is not None and not df_sap.empty and not df_mo_proy.empty:
            # Extraer todas las actividades ejecutadas en la mano de obra de este proyecto
            acts_mo = df_mo_proy['Actividad'].astype(str).str.strip().unique()
            
            col_act_cont = fuente_mat.columns[0] # Columna 'Actividad' en contratistas
            df_mat_filtrado = fuente_mat[fuente_mat[col_act_cont].astype(str).str.strip().isin(acts_mo)].copy()
            
            if not df_mat_filtrado.empty:
                # Detectar columnas clave de forma dinámica en la tabla de contratistas y SAP
                col_sap_mat = next((c for c in fuente_mat.columns if 'sap' in c.lower() or 'codigo' in c.lower()), 'Codigo SAP')
                col_cant_mat = fuente_mat.columns[-1] # La cantidad suele ser la última columna
                
                col_sap_prec = df_sap.columns[0]
                col_precio_final = next((c for c in df_sap.columns if 'precio' in c.lower()), df_sap.columns[-1])
                
                df_sap['Clean_SAP'] = df_sap[col_sap_prec].astype(str).str.strip()
                df_mat_filtrado['Clean_SAP'] = df_mat_filtrado[col_sap_mat].astype(str).str.strip()
                
                # Hacer el merge con los precios SAP
                df_merge = pd.merge(df_mat_filtrado, df_sap, on='Clean_SAP', how='inner')
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
                cols_show = [c for c in [fuente_mat.columns[0], 'Descripción_MAT', fuente_mat.columns[-1], 'Precio Final', 'Costo_Material'] if c in df_materiales_calculados.columns]
                st.dataframe(df_materiales_calculados[cols_show].head(15), use_container_width=True)
            else:
                st.info("No se encontraron materiales vinculados para las actividades de este proyecto.")
                
        st.markdown("#### 📋 Detalle de Mano de Obra del Proyecto")
        if not df_mo_proy.empty:
            cols_mo = [c for c in ['Actividad', 'DETALLE', 'Costo Unit.', 'Cantidad', 'Costo Total', 'Contrata', 'Supervisor'] if c in df_mo_proy.columns]
            st.dataframe(df_mo_proy[cols_mo].head(15), use_container_width=True)
        else:
            st.warning(f"⚠️ No se encontraron registros de mano de obra para el código '{codigo_seleccionado}'.")
    else:
        st.info("👈 Por favor seleccione un Código de Proyecto en el menú lateral.")

elif menu == "Relación Mano de Obra y Materiales":
    st.subheader("🧩 Matriz Relacional: Actividades, Materiales y Precios SAP")
    if df_contratistas is not None:
        st.dataframe(df_contratistas, use_container_width=True)
    else:
        st.warning("No se encontró el archivo de contratistas.")

else:
    st.subheader("🗺️ Ubicación Geográfica del Proyecto en Zona de Concesión EDEESTE")
    map_data = pd.DataFrame({
        'lat': [18.4861, 18.5123, 18.4500, 18.5500],
        'lon': [-69.8500, -69.8000, -69.6500, -69.7800],
        'Proyecto': ['Proyecto Redes La Javilla', 'Ciudad Juan Bosch', 'Circuito SPER01', 'Rehabilitación LM3802R']
    })
    st.map(map_data)
    st.caption("Ubicación satelital y puntos de ejecución del proyecto.")
