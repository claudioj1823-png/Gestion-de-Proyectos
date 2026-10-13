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

def limpiar_nombre_columnas(df):
    if df is not None and not df.empty:
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    return df

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
                if clave == 'contratistas':
                    try:
                        df = pd.read_excel(ruta, sheet_name="Actividades con materiales")
                    except Exception:
                        df = pd.read_excel(ruta, sheet_name=0)
                else:
                    df = pd.read_excel(ruta)
                dfs[clave] = limpiar_nombre_columnas(df)
            except Exception as e:
                dfs[clave] = None
        else:
            dfs[clave] = None
    return dfs

datos = cargar_datos()

st.sidebar.markdown("### 🎯 Selección de Proyecto")
df_codigos = datos.get('codigos')

if df_codigos is not None and not df_codigos.empty:
    col_codigo = next((c for c in df_codigos.columns if 'proyecto' in c.lower() or 'código' in c.lower() or 'codigo' in c.lower()), df_codigos.columns[0])
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

if menu == "Panel Ejecutivo por Proyecto":
    st.subheader(f"📌 Proyecto Seleccionado: {codigo_seleccionado}")
    
    if codigo_seleccionado != "Todos":
        cod_clean = str(codigo_seleccionado).strip()
        
        # 1. Mano de Obra Ejecutada del Proyecto
        monto_mo = 0.0
        df_mo_proy = pd.DataFrame()
        if df_mo is not None and not df_mo.empty:
            col_proy_mo = next((c for c in df_mo.columns if 'proyecto' in c.lower() or 'código' in c.lower() or 'codigo' in c.lower()), df_mo.columns[-3])
            col_costo_mo = next((c for c in df_mo.columns if 'costo total' in c.lower() or 'total' in c.lower()), df_mo.columns[5])
            
            df_mo['Clean_Proy'] = df_mo[col_proy_mo].astype(str).str.strip()
            df_mo_proy = df_mo[df_mo['Clean_Proy'] == cod_clean].copy()
            monto_mo = pd.to_numeric(df_mo_proy[col_costo_mo], errors='coerce').sum()

        # 2. Presupuesto Planificado
        presupuesto_plan = 0.0
        if df_metas is not None and not df_metas.empty:
            col_proy_meta = next((c for c in df_metas.columns if 'proyecto' in c.lower() or 'código' in c.lower() or 'codigo' in c.lower()), df_metas.columns[0])
            col_presupuesto = next((c for c in df_metas.columns if 'presupuesto' in c.lower()), df_metas.columns[-1])
            
            df_metas['Clean_Proy'] = df_metas[col_proy_meta].astype(str).str.strip()
            df_meta_proy = df_metas[df_metas['Clean_Proy'] == cod_clean]
            
            val_presupuesto = pd.to_numeric(df_meta_proy[col_presupuesto], errors='coerce').dropna()
            if not val_presupuesto.empty:
                presupuesto_plan = val_presupuesto.iloc[0]

        # 3. Lógica IDP Blindada: Agrupar MO -> Deduplicar Maestro Contratistas -> Cruce Universal -> Agrupar SAP
        costo_materiales_total = 0.0
        df_materiales_calculados = pd.DataFrame()
        df_mo_agrupado = pd.DataFrame()
        
        fuente_mat = df_contratistas.copy() if (df_contratistas is not None and not df_contratistas.empty) else (df_familia.copy() if df_familia is not None else None)
        
        if fuente_mat is not None and not fuente_mat.empty and df_sap is not None and not df_sap.empty and not df_mo_proy.empty:
            # A. Agrupar mano de obra del proyecto por Actividad
            col_act_mo = next((c for c in df_mo_proy.columns if 'actividad' in c.lower()), df_mo_proy.columns[0])
            col_cant_mo = next((c for c in df_mo_proy.columns if c.lower() == 'cantidad' or 'cant' in c.lower()), df_mo_proy.columns[4])
            
            df_mo_proy['Actividad_Clean'] = df_mo_proy[col_act_mo].fillna("").astype(str).str.strip().str.upper()
            df_mo_proy['Cantidad_Num'] = pd.to_numeric(df_mo_proy[col_cant_mo], errors='coerce').fillna(0)
            
            df_mo_agrupado = df_mo_proy.groupby('Actividad_Clean', as_index=False)['Cantidad_Num'].sum()
            df_mo_agrupado.rename(columns={'Actividad_Clean': 'Actividad', 'Cantidad_Num': 'Cantidad Total Ejecutada'}, inplace=True)
            
            dict_cant_mo = dict(zip(df_mo_agrupado['Actividad'], df_mo_agrupado['Cantidad Total Ejecutada']))
            
            # B. Identificar columnas y DEDUPLICAR el maestro de contratistas para evitar duplicidad por contrata
            col_act_mat = next((c for c in fuente_mat.columns if 'actividad' in c.lower()), fuente_mat.columns[0])
            col_sap_mat = next((c for c in fuente_mat.columns if 'sap' in c.lower() or 'código sap' in c.lower() or 'codigo sap' in c.lower()), fuente_mat.columns[4])
            desc_mat_col = next((c for c in fuente_mat.columns if 'descripci' in c.lower() or ('mat' in c.lower() and c != col_sap_mat)), fuente_mat.columns[5])
            und_col = next((c for c in fuente_mat.columns if 'unid' in c.lower()), None)
            
            cols_candidatas_cant = [c for c in fuente_mat.columns if ('cant' in c.lower() or 'und' in c.lower()) and c != col_act_mat and c != col_sap_mat]
            col_cant_mat = cols_candidatas_cant[-1] if cols_candidatas_cant else fuente_mat.columns[-1]
            
            fuente_mat['Actividad_Clean'] = fuente_mat[col_act_mat].fillna("").astype(str).str.strip().str.upper()
            fuente_mat['Clean_SAP'] = fuente_mat[col_sap_mat].
