import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Control de Proyecto - EDEESTE",
    page_icon="⚡",
    layout="wide"
)

# Estilos CSS globales y semáforos corporativos
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; color: #212529; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stMetric label { color: #6c757d !important; font-weight: 600; font-size: 14px; }
    .stMetric [data-testid="stMetricValue"] { color: #0d6efd !important; font-size: 24px; font-weight: bold; }
    h1, h2, h3, h4, h5, h6 { color: #212529 !important; }
    
    /* Cajas de Resumen Ejecutivo y Narrativa */
    .resumen-gerencial-box {
        background: #ffffff;
        border-left: 5px solid #0d6efd;
        padding: 18px 22px;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .resumen-gerencial-box h4 {
        margin-top: 0;
        color: #0b2240 !important;
        font-size: 16px;
        font-weight: 700;
    }
    .resumen-gerencial-box p {
        color: #333333;
        font-size: 14px;
        line-height: 1.5;
        margin-bottom: 0;
    }

    /* Estilo HTML exacto para tablas ejecutivas EDEESTE */
    .tabla-ejecutiva-container {
        width: 100%;
        overflow-x: auto;
        margin-bottom: 15px;
        border: 1px solid #d0d7de;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    table.tabla-ejecutiva {
        width: 100%;
        border-collapse: collapse;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        font-size: 13px;
        background-color: #ffffff;
    }
    table.tabla-ejecutiva thead tr {
        background-color: #0b2240 !important;
        color: #ffffff !important;
        text-align: left;
    }
    table.tabla-ejecutiva th {
        padding: 11px 14px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        border-right: 1px solid #1a365d;
        white-space: nowrap;
    }
    table.tabla-ejecutiva td {
        padding: 9px 14px !important;
        border-bottom: 1px solid #e1e4e8;
        border-right: 1px solid #e1e4e8;
        color: #24292e;
    }
    table.tabla-ejecutiva tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    table.tabla-ejecutiva tr:hover {
        background-color: #f1f3f5;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("## ⚡ EDEESTE • Control de Proyecto (Panel Gerencial)")
st.markdown("---")

def limpiar_nombre_columnas(df):
    if df is not None and not df.empty:
        df = df.copy()
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    return df

@st.cache_data(ttl=0)
def cargar_datos_seguros():
    dfs = {}
    
    if os.path.exists('Codigos de proyectos.xlsx'):
        dfs['codigos'] = limpiar_nombre_columnas(pd.read_excel('Codigos de proyectos.xlsx'))
    else:
        dfs['codigos'] = None

    ruta_fam = 'Actividades con su familia.xlsx' if os.path.exists('Actividades con su familia.xlsx') else 'Actividades con sus familia.xlsx'
    if os.path.exists(ruta_fam):
        try:
            xls_f = pd.ExcelFile(ruta_fam)
            sheet_f = 'Mano de Obra con su Familia' if 'Mano de Obra con su Familia' in xls_f.sheet_names else xls_f.sheet_names[0]
            dfs['familia'] = limpiar_nombre_columnas(pd.read_excel(ruta_fam, sheet_name=sheet_f))
        except Exception:
            dfs['familia'] = None
    else:
        dfs['familia'] = None

    if os.path.exists('Actividades contratistas.xlsx'):
        try:
            xls_c = pd.ExcelFile('Actividades contratistas.xlsx')
            sheet_c = 'Actividades con materiales' if 'Actividades con materiales' in xls_c.sheet_names else xls_c.sheet_names[0]
            dfs['contratistas'] = limpiar_nombre_columnas(pd.read_excel('Actividades contratistas.xlsx', sheet_name=sheet_c))
        except Exception:
            dfs['contratistas'] = None
    else:
        dfs['contratistas'] = None

    if os.path.exists('Precios Sap.xlsx'):
        try:
            dfs['sap'] = limpiar_nombre_columnas(pd.read_excel('Precios Sap.xlsx', sheet_name='Hoja3'))
        except Exception as e:
            st.error(f"Error al leer la Hoja 3 de Precios Sap.xlsx: {e}")
            dfs['sap'] = None
    else:
        dfs['sap'] = None

    if os.path.exists('Proyectos con sus metas.xlsx'):
        dfs['metas'] = limpiar_nombre_columnas(pd.read_excel('Proyectos con sus metas.xlsx', skiprows=1))
    else:
        dfs['metas'] = None

    if os.path.exists('Mano de Obra por proyecto.xlsx'):
        dfs['mo'] = limpiar_nombre_columnas(pd.read_excel('Mano de Obra por proyecto.xlsx'))
    else:
        dfs['mo'] = None

    return dfs

datos = cargar_datos_seguros()

df_codigos = datos.get('codigos')
df_mo = datos.get('mo')
df_familia = datos.get('familia')
df_contratistas = datos.get('contratistas')
df_sap = datos.get('sap')
df_metas = datos.get('metas')

dict_familia = {}
if df_familia is not None and not df_familia.empty:
    col_act_f = next((c for c in df_familia.columns if 'actividad' in c.lower() or 'código' in c.lower() or 'codigo' in c.lower()), df_familia.columns[0])
    col_fam_f = next((c for c in df_familia.columns if 'familia' in c.lower()), df_familia.columns[2])
    for _, row in df_familia.iterrows():
        act_raw = str(row[col_act_f]).strip().upper()
        fam_raw = str(row[col_fam_f]).strip()
        if act_raw and fam_raw and fam_raw != "nan":
            dict_familia[act_raw] = fam_raw

st.sidebar.markdown("### 🎛️ FILTROS EJECUTIVOS")
anos_disponibles = ["Todos"]
meses_disponibles = ["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

if df_mo is not None and not df_mo.empty:
    cols_fecha = [c for c in df_mo.columns if 'fecha' in c.lower() or 'date' in c.lower() or 'periodo' in c.lower()]
    if cols_fecha:
        df_mo = df_mo.copy()
        df_mo['Fecha_Parsed'] = pd.to_datetime(df_mo[cols_fecha[0]], errors='coerce')
        anos_encontrados = df_mo['Fecha_Parsed'].dt.year.dropna().unique()
        if len(anos_encontrados) > 0:
            anos_disponibles = ["Todos"] + sorted([str(int(a)) for a in anos_encontrados])

ano_sel = st.sidebar.selectbox("📅 AÑO", anos_disponibles)
mes_sel = st.sidebar.selectbox("📅 MES", meses_disponibles)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 SELECCIÓN DE PROYECTO")

lista_codigos = []
if df_codigos is not None and not df_codigos.empty:
    col_codigo = next((c for c in df_codigos.columns if 'proyecto' in c.lower() or 'código' in c.lower() or 'codigo' in c.lower()), df_codigos.columns[0])
    lista_codigos = df_codigos[col_codigo].dropna().astype(str).str.strip().unique().tolist()

codigo_seleccionado = st.sidebar.selectbox("Código de Proyecto:", ["Todos"] + lista_codigos)
menu = st.sidebar.radio("🧭 MÓDULOS", ["Panel Ejecutivo por Proyecto", "Mapa Interactivo de Proyectos"])

st.sidebar.markdown("---")
if st.sidebar.button("🔄 RECARGAR DATOS"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.caption("EDEESTE - Control Presupuestario y Operativo")

def mostrar_tabla_html_ejecutiva(df_mostrar):
    html_str = df_mostrar.to_html(index=False, classes='tabla-ejecutiva', escape=False)
    st.markdown(f'<div class="tabla-ejecutiva-container">{html_str}</div>', unsafe_allow_html=True)

def calcular_inversion_proyecto_completa(p_cod, df_mo_input, df_contratistas_input, df_sap_input, dict_fam):
    monto_mo = 0.0
    monto_mat = 0.0
    
    if df_mo_input is not None and not df_mo_input.empty:
        col_proy_m = next((c for c in df_mo_input.columns if 'código proyecto' in c.lower() or 'codigo proyecto' in c.lower() or 'proyecto' in c.lower()), df_mo_input.columns[-2])
        col_costo_m = next((c for c in df_mo_input.columns if c.lower().strip() == 'costo total'), None)
        if not col_costo_m:
            col_costo_m = next((c for c in df_mo_input.columns if 'costo total' in c.lower()), df_mo_input.columns[5])
        
        sub_mo = df_mo_input[df_mo_input[col_proy_m].astype(str).str.strip() == str(p_cod).strip()].copy()
        
        if not sub_mo.empty:
            serie_c = sub_mo[col_costo_m].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
            monto_mo = pd.to_numeric(serie_c, errors='coerce').sum()
            
            if df_contratistas_input is not None and not df_contratistas_input.empty and df_sap_input is not None and not df_sap_input.empty:
                col_act_mo = next((c for c in sub_mo.columns if c.lower().strip() == 'código' or 'actividad' in c.lower() or 'código' in c.lower()), sub_mo.columns[0])
                col_cant_mo = next((c for c in sub_mo.columns if c.lower().strip() == 'cantidad' or 'cant' in c.lower()), sub_mo.columns[4])
                
                sub_mo['Actividad_Clean'] = sub_mo[col_act_mo].fillna("").astype(str).str.strip().str.upper()
                sub_mo['Cantidad_Num'] = pd.to_numeric(sub_mo[col_cant_mo], errors='coerce').fillna(0)
                
                cant_por_act = sub_mo.groupby('Actividad_Clean', as_index=False)['Cantidad_Num'].sum()
                dict_cant = dict(zip(cant_por_act['Actividad_Clean'], cant_por_act['Cantidad_Num']))
                
                col_act_mat = next((c for c in df_contratistas_input.columns if 'actividad' in c.lower()), df_contratistas_input.columns[0])
                col_sap_mat = next((c for c in df_contratistas_input.columns if 'sap' in c.lower() or 'código sap' in c.lower() or 'codigo sap' in c.lower()), df_contratistas_input.columns[4])
                col_cant_mat = next((c for c in df_contratistas_input.columns if 'cantidad' in c.lower() or 'cant' in c.lower()), df_contratistas_input.columns[7])
                
                f_mat = df_contratistas_input.copy()
                f_mat['Actividad_Clean'] = f_mat[col_act_mat].fillna("").astype(str).str.strip().str.upper()
                f_mat['Clean_SAP'] = f_mat[col_sap_mat].fillna("").astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
                f_mat['Cantidad_Unitaria_Num'] = pd.to_numeric(f_mat[col_cant_mat], errors='coerce').fillna(0)
                
                f_mat = f_mat[~f_mat['Clean_SAP'].isin(['', 'NAN', 'NONE', '0'])]
                f_mat_clean = f_mat.groupby(['Actividad_Clean', 'Clean_SAP'], as_index=False)['Cantidad_Unitaria_Num'].first()
                
                df_filt = f_mat_clean[f_mat_clean['Actividad_Clean'].isin(dict_cant.keys())].copy()
                if not df_filt.empty:
                    df_filt['Cant_IDP'] = df_filt['Actividad_Clean'].map(dict_cant)
                    cond = (df_filt['Actividad_Clean'] == '1VA-MT') & (df_filt['Clean_SAP'] == '1000130')
                    df_filt["Cantidad_Total_Material"] = np.where(cond, df_filt['Cant_IDP'], df_filt['Cantidad_Unitaria_Num'] * df_filt['Cant_IDP'])
                    
                    col_sap_prec = next((c for c in df_sap_input.columns if 'sap' in c.lower() or 'código' in c.lower() or 'codigo' in c.lower()), df_sap_input.columns[0])
                    col_desc_sap = next((c for c in df_sap_input.columns if 'descripci' in c.lower()), df_sap_input.columns[1])
                    col_precio_final = next((c for c in df_sap_input.columns if 'precio' in c.lower() or 'costo' in c.lower()), df_sap_input.columns[2])
                    
                    s_copy = df_sap_input.copy()
                    s_copy['Clean_SAP'] = s_copy[col_sap_prec].fillna("").astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
                    s_copy['Precio_Oficial'] = pd.to_numeric(s_copy[col_precio_final].astype(str).str.replace("$", "").str.replace(",", ""), errors="coerce").fillna(0.0)
                    
                    s_clean = s_copy[['Clean_SAP', 'Precio_Oficial']].drop_duplicates(subset=['Clean_SAP'])
                    m_merge = pd.merge(df_filt, s_clean, on='Clean_SAP', how='left')
                    m_merge['Costo_Mat'] = m_merge['Cantidad_Total_Material'] * m_merge['Precio_Oficial']
                    monto_mat = m_merge['Costo_Mat'].sum()

    return monto_mo, monto_mat, (monto_mo + monto_mat)

if menu == "Panel Ejecutivo por Proyecto":
    if codigo_seleccionado != "Todos":
        cod_clean = str(codigo_seleccionado).strip()
        
        nombre_proyecto_str = cod_clean
        if df_codigos is not None and not df_codigos.empty:
            col_codigo_p = df_codigos.columns[0]
            cols_desc_p = [c for c in df_codigos.columns if 'nombre' in c.lower() or 'descripci' in c.lower() or ('proyecto' in c.lower() and c != col_codigo_p)]
            if cols_desc_p:
                col_desc_p = cols_desc_p[0]
                df_codigos_copy = df_codigos.copy()
                df_codigos_copy['Clean_Cod'] = df_codigos_copy[col_codigo_p].astype(str).str.strip()
                match_p = df_codigos_copy[df_codigos_copy['Clean_Cod'] == cod_clean]
                if not match_p.empty:
                    nombre_proyecto_str = f"{cod_clean} - {match_p.iloc[0][col_desc_p]}"
        
        # 1. ENCABEZADO PRINCIPAL
        st.markdown(f"<h4 style='color: #212529; margin-bottom: 15px;'>📌 PROYECTO: <b style='color: #0d6efd;'>{nombre_proyecto_str}</b></h4>", unsafe_allow_html=True)
        
        # Procesamiento de Datos de Mano de Obra
        monto_mo = 0.0
        df_mo_proy = pd.DataFrame()
        if df_mo is not None and not df_mo.empty:
            col_proy_mo = next((c for c in df_mo.columns if 'código proyecto' in c.lower() or 'codigo proyecto' in c.lower() or 'proyecto' in c.lower()), df_mo.columns[-2])
            col_costo_mo = next((c for c in df_mo.columns if c.lower().strip() == 'costo total'), None)
            if not col_costo_mo:
                col_costo_mo = next((c for c in df_mo.columns if 'costo total' in c.lower()), df_mo.columns[5])
            
            df_mo_proy = df_mo[df_mo[col_proy_mo].astype(str).str.strip() == cod_clean].copy()
            
            if 'Fecha_Parsed' in df_mo_proy.columns:
                if ano_sel != "Todos":
                    df_mo_proy = df_mo_proy[df_mo_proy['Fecha_Parsed'].dt.year == int(ano_sel)]
                if mes_sel != "Todos":
                    meses_dict = {"Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12}
                    df_mo_proy = df_mo_proy[df_mo_proy['Fecha_Parsed'].dt.month == meses_dict.get(mes_sel, 0)]
            
            serie_costos = df_mo_proy[col_costo_mo].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
            monto_mo = pd.to_numeric(serie_costos, errors='coerce').sum()

        # Presupuesto Planificado
        presupuesto_plan = 0.0
        if df_metas is not None and not df_metas.empty:
            col_proy_meta = next((c for c in df_metas.columns if 'proyecto' in c.lower() or 'código' in c.lower() or 'codigo' in c.lower()), df_metas.columns[0])
            col_presupuesto = next((c for c in df_metas.columns if 'presupuesto' in c.lower()), df_metas.columns[-1])
            
            df_metas_copy = df_metas.copy()
            df_metas_copy['Clean_Proy'] = df_metas_copy[col_proy_meta].astype(str).str.strip()
            df_meta_proy = df_metas_copy[df_metas_copy['Clean_Proy'] == cod_clean]
            
            val_presupuesto = pd.to_numeric(df_meta_proy[col_presupuesto], errors='coerce').dropna()
            if not val_presupuesto.empty:
                presupuesto_plan = val_presupuesto.iloc[0]

        # Materiales
        costo_materiales_total = 0.0
        df_materiales_mostrador = pd.DataFrame()
        df_mo_agrupado = pd.DataFrame()
        df_mo_fisico = pd.DataFrame()
        df_resumen_mat = pd.DataFrame()
        
        if df_contratistas is not None and not df_contratistas.empty and df_sap is not None and not df_sap.empty and not df_mo_proy.empty:
            fuente_mat = df_contratistas.copy()
            
            col_act_mo = next((c for c in df_mo_proy.columns if c.lower().strip() == 'código' or 'actividad' in c.lower() or 'código' in c.lower()), df_mo_proy.columns[0])
            col_cant_mo = next((c for c in df_mo_proy.columns if c.lower().strip() == 'cantidad' or 'cant' in c.lower()), df_mo_proy.columns[4])
            col_unds_mo = next((c for c in df_mo_proy.columns if c.lower().strip() == 'unds.' or 'und' in c.lower() or 'unidad' in c.lower()), None)
            
            df_mo_proy = df_mo_proy.copy()
            df_mo_proy['Actividad_Clean'] = df_mo_proy[col_act_mo].fillna("").astype(str).str.strip().str.upper()
            df_mo_proy['Cantidad_Num'] = pd.to_numeric(df_mo_proy[col_cant_mo], errors='coerce').fillna(0)
            df_mo_proy['Familia_Accion'] = df_mo_proy['Actividad_Clean'].map(dict_familia).fillna("OTRA")
            
            if col_unds_mo:
                df_mo_proy['Unds_Clean'] = df_mo_proy[col_unds_mo].fillna("").astype(str).str.strip().str.upper()
                df_mo_fisico = df_mo_proy[~df_mo_proy['Unds_Clean'].str.contains('HORA|HR')].copy()
            else:
                df_mo_fisico = df_mo_proy[~df_mo_proy['Actividad_Clean'].str.startswith(('HNBR', 'DFAC'))].copy()

            df_mo_agrupado = df_mo_fisico.groupby(['Familia_Accion', 'Actividad_Clean'], as_index=False)['Cantidad_Num'].sum()
            df_mo_agrupado.rename(columns={'Familia_Accion': 'Familia / Acción', 'Actividad_Clean': 'Actividad', 'Cantidad_Num': 'Cantidad Ejecutada'}, inplace=True)
            
            dict_cant_mo = dict(zip(df_mo_agrupado['Actividad'], df_mo_agrupado['Cantidad Ejecutada']))
            
            col_act_mat = next((c for c in fuente_mat.columns if 'actividad' in c.lower()), fuente_mat.columns[0])
            col_sap_mat = next((c for c in fuente_mat.columns if 'sap' in c.lower() or 'código sap' in c.lower() or 'codigo sap' in c.lower()), fuente_mat.columns[4])
            col_cant_mat = next((c for c in fuente_mat.columns if 'cantidad' in c.lower() or 'cant' in c.lower()), fuente_mat.columns[7])
            
            fuente_mat['Actividad_Clean'] = fuente_mat[col_act_mat].fillna("").astype(str).str.strip().str.upper()
            fuente_mat['Clean_SAP'] = fuente_mat[col_sap_mat].fillna("").astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            fuente_mat['Cantidad_Unitaria_Num'] = pd.to_numeric(fuente_mat[col_cant_mat], errors='coerce').fillna(0)
            
            fuente_mat = fuente_mat[~fuente_mat['Clean_SAP'].isin(['', 'NAN', 'NONE', '0'])]
            
            fuente_mat_clean = fuente_mat.groupby(['Actividad_Clean', 'Clean_SAP'], as_index=False)['Cantidad_Unitaria_Num'].first()
            df_filtrado = fuente_mat_clean[fuente_mat_clean['Actividad_Clean'].isin(dict_cant_mo.keys())].copy()
            
            if not df_filtrado.empty:
                df_filtrado['Cant_IDP'] = df_filtrado['Actividad_Clean'].map(dict_cant_mo)
                
                condicion_especial = (df_filtrado['Actividad_Clean'] == '1VA-MT') & (df_filtrado['Clean_SAP'] == '1000130')
                df_filtrado["Cantidad_Total_Material"] = np.where(
                    condicion_especial,
                    df_filtrado['Cant_IDP'],
                    df_filtrado['Cantidad_Unitaria_Num'] * df_filtrado['Cant_IDP']
                )
                
                col_sap_prec = next((c for c in df_sap.columns if 'sap' in c.lower() or 'código' in c.lower() or 'codigo' in c.lower()), df_sap.columns[0])
                col_desc_sap = next((c for c in df_sap.columns if 'descripci' in c.lower()), df_sap.columns[1])
                col_precio_final = next((c for c in df_sap.columns if 'precio' in c.lower() or 'costo' in c.lower()), df_sap.columns[2])
                
                df_sap_copy = df_sap.copy()
                df_sap_copy['Clean_SAP'] = df_sap_copy[col_sap_prec].fillna("").astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
                df_sap_copy['Descripcion_Oficial'] = df_sap_copy[col_desc_sap].fillna("").astype(str)
                df_sap_copy['Precio_Oficial'] = pd.to_numeric(df_sap_copy[col_precio_final].astype(str).str.replace("$", "").str.replace(",", ""), errors="coerce").fillna(0.0)
                
                df_sap_limpio = df_sap_copy[['Clean_SAP', 'Descripcion_Oficial', 'Precio_Oficial']].drop_duplicates(subset=['Clean_SAP'])
                df_merge_sap = pd.merge(df_filtrado, df_sap_limpio, on='Clean_SAP', how='left')
                
                df_resumen_mat = df_merge_sap.groupby(['Clean_SAP', 'Descripcion_Oficial'], as_index=False).agg({
                    "Cantidad_Total_Material": "sum",
                    "Precio_Oficial": "first"
                })
                
                df_resumen_mat['Costo_Material'] = df_resumen_mat['Cantidad_Total_Material'] * df_resumen_mat['Precio_Oficial']
                
                costo_materiales_total = df_resumen_mat['Costo_Material'].sum()
                
                df_display = df_resumen_mat.copy()
                df_display['Cantidad Total'] = df_display['Cantidad_Total_Material'].apply(lambda x: f"{x:,.2f}")
                df_display['Precio Unitario SAP'] = df_display['Precio_Oficial'].apply(lambda x: f"RD$ {x:,.2f}")
                df_display['Costo Total'] = df_display['Costo_Material'].apply(lambda x: f"RD$ {x:,.2f}")
                
                df_display = df_display.rename(columns={
                    'Clean_SAP': "Código SAP",
                    'Descripcion_Oficial': "Descripción de Material"
                })[['Código SAP', 'Descripción de Material', 'Cantidad Total', 'Precio Unitario SAP', 'Costo Total']]
                
                df_materiales_mostrador = df_display

        # Metas vs Ejecutado
        df_avance_acciones = pd.DataFrame()
        if df_metas is not None and not df_metas.empty:
            col_proy_m = next((c for c in df_metas.columns if 'proyecto' in c.lower() or 'código' in c.lower() or 'codigo' in c.lower()), df_metas.columns[0])
            df_metas_copy2 = df_metas.copy()
            df_metas_copy2['Clean_P_Meta'] = df_metas_copy2[col_proy_m].astype(str).str.strip()
            df_meta_proy_filt = df_metas_copy2[df_metas_copy2['Clean_P_Meta'] == cod_clean].copy()
            
            if not df_meta_proy_filt.empty:
                col_accion_meta = next((c for c in df_meta_proy_filt.columns if 'accion' in c.lower() or 'actividad' in c.lower()), df_meta_proy_filt.columns[3])
                col_cant_plan = next((c for c in df_meta_proy_filt.columns if 'cantidad' in c.lower() or 'planifica' in c.lower()), df_meta_proy_filt.columns[4])
                
                df_meta_proy_filt['Acción'] = df_meta_proy_filt[col_accion_meta].fillna("").astype(str).str.strip()
                df_meta_proy_filt['Acción_Key'] = df_meta_proy_filt['Acción'].str.upper().str.strip()
                df_meta_proy_filt['Planificado'] = pd.to_numeric(df_meta_proy_filt[col_cant_plan], errors='coerce').fillna(0)
                
                if not df_mo_fisico.empty:
                    df_mo_fisico_copy = df_mo_fisico.copy()
                    df_mo_fisico_copy['Familia_Key'] = df_mo_fisico_copy['Familia_Accion'].str.upper().str.strip()
                    df_ejec_fam = df_mo_fisico_copy.groupby('Familia_Key', as_index=False)['Cantidad_Num'].sum()
                    df_ejec_fam.rename(columns={'Familia_Key': 'Acción_Key', 'Cantidad_Num': 'Ejecutado'}, inplace=True)
                else:
                    df_ejec_fam = pd.DataFrame(columns=['Acción_Key', 'Ejecutado'])
                
                df_avance_acciones = pd.merge(
                    df_meta_proy_filt[['Acción', 'Acción_Key', 'Planificado']],
                    df_ejec_fam[['Acción_Key', 'Ejecutado']],
                    on='Acción_Key',
                    how='left'
                ).fillna(0)
                
                df_avance_acciones = df_avance_acciones[['Acción', 'Planificado', 'Ejecutado']]
                
                df_avance_acciones['Num_Avance'] = np.where(
                    df_avance_acciones['Planificado'] > 0,
                    (df_avance_acciones['Ejecutado'] / df_avance_acciones['Planificado']) * 100,
                    0.0
                )
                df_avance_acciones['% Avance'] = df_avance_acciones['Num_Avance'].apply(lambda x: f"{x:.1f}%")

        total_ejecutado = monto_mo + costo_materiales_total
        porcentaje_ejecutado = (total_ejecutado / presupuesto_plan * 100) if presupuesto_plan > 0 else 0

        # Tarjetas Métricas Ejecutivas Superiores
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Mano de Obra (RD$)", f"RD$ {monto_mo:,.2f}")
        c2.metric("Materiales Instalados (RD$)", f"RD$ {costo_materiales_total:,.2f}")
        c3.metric("Monto Invertido en el Proyecto (RD$)", f"RD$ {total_ejecutado:,.2f}")
        c4.metric("Presupuesto Plan. (RD$)", f"RD$ {presupuesto_plan:,.2f}")
        c5.metric("% Ejecución Est.", f"{porcentaje_ejecutado:.1f}%")

        # -------------------------------------------------------------
        # 1. RESUMEN EJECUTIVO / NARRATIVA AUTOMÁTICA DEL PROYECTO
        # -------------------------------------------------------------
        estado_presupuesto = "en orden"
        if presupuesto_plan > 0:
            if porcentaje_ejecutado > 100:
                estado_presupuesto = "con sobreejecución presupuestaria"
            elif porcentaje_ejecutado >= 85:
                estado_presupuesto = "con ejecución avanzada cercana a la meta"
            else:
                estado_presupuesto = "con ejecución dentro de parámetros normales"

        alerta_mat_txt = "No se detectan materiales con precio $0.00."
        if not df_resumen_mat.empty:
            mat_sin_p = df_resumen_mat[df_resumen_mat['Precio_Oficial'] == 0]
            if not mat_sin_p.empty:
                alerta_mat_txt = f"⚠️ Existen {len(mat_sin_p)} material(es) en campo con precio SAP en $0.00 pendientes de actualización."

        st.markdown(f"""
            <div class="resumen-gerencial-box">
                <h4>📋 Resumen Ejecutivo y Diagnóstico Gerencial</h4>
                <p>El proyecto <b>{nombre_proyecto_str}</b> presenta una inversión acumulada de <b>RD$ {total_ejecutado:,.2f}</b>, alcanzando un <b>{porcentaje_ejecutado:.1f}%</b> del presupuesto planificado (RD$ {presupuesto_plan:,.2f}), encontrándose {estado_presupuesto}. 
                En el ámbito físico, la ejecución de actividades muestra avances consolidados en campo. {alerta_mat_txt}</p>
            </div>
        """, unsafe_allow_html=True)

        # -------------------------------------------------------------
        # 2. SISTEMA DE ALERTAS Y MATRIZ DE RIESGOS (Semáforos)
        # -------------------------------------------------------------
        alertas = []
        
        if presupuesto_plan > 0 and total_ejecutado > presupuesto_plan:
            exceso = total_ejecutado - presupuesto_plan
            alertas.append(f"🚨 **Alerta Financiera (Riesgo Alto):** El monto invertido supera el presupuesto planificado por **RD$ {exceso:,.2f}** ({porcentaje_ejecutado:.1f}%).")
        
        if not df_avance_acciones.empty:
            actividades_sobre = df_avance_acciones[df_avance_acciones['Num_Avance'] > 100]
            if not actividades_sobre.empty:
                nombres_sobr = ", ".join([f"**{r['Acción']}** ({r['% Avance']})" for _, r in actividades_sobre.iterrows()])
                alertas.append(f"⚠️ **Desvío Físico (Riesgo Moderado):** Actividades con sobreejecución mayor al 100%: {nombres_sobr}.")
        
        if not df_resumen_mat.empty:
            mat_sin_precio = df_resumen_mat[df_resumen_mat['Precio_Oficial'] == 0]
            if not mat_sin_precio.empty:
                detalles_mat = [f"**[{row['Clean_SAP']}] {row['Descripcion_Oficial']}**" for _, row in mat_sin_precio.iterrows()]
                alertas.append(f"🔍 **Auditoría de Materiales (Atención Requerida):** Precios SAP en $0.00 para: {', '.join(detalles_mat)}.")

        if alertas:
            with st.container():
                for alt in alertas:
                    st.warning(alt)

        st.markdown("---")
        
        # 3. DESGLOSE FINANCIERO Y OPERATIVO
        st.markdown("### 📊 Desglose Financiero y Operativo")
        
        df_grafico = pd.DataFrame({
            'Concepto': ['Mano de Obra', 'Materiales Instalados', 'Monto Invertido', 'Presupuesto Plan.'],
            'Monto (RD$)': [monto_mo, costo_materiales_total, total_ejecutado, presupuesto_plan]
        })
        
        df_grafico['Texto_Monto'] = df_grafico['Monto (RD$)'].apply(lambda x: f"RD$ {x:,.2f}")
        
        mapa_colores_ejecutivo = {
            'Mano de Obra': '#1b365d',
            'Materiales Instalados': '#2b5c8f',
            'Monto Invertido': '#d97706',
            'Presupuesto Plan.': '#4b5563'
        }
        
        fig_bar = px.bar(
            df_grafico, 
            x='Concepto', 
            y='Monto (RD$)', 
            color='Concepto', 
            text='Texto_Monto',
            title="Comparativo Financiero del Proyecto",
            color_discrete_map=mapa_colores_ejecutivo
        )
        fig_bar.update_traces(textposition='auto')
        fig_bar.update_layout(
            showlegend=True, 
            xaxis_title="", 
            template="plotly_white",
            margin=dict(l=20, r=20, t=40, b=20),
            height=400
        )
        st.plotly_chart(fig_bar, use_container_width=True)
            
        st.markdown("---")

        # 4. AVANCE TOTAL
        st.markdown("### 🎯 Avance Total (Planificado vs Ejecutado)")
        if not df_avance_acciones.empty:
            
            col_av_1, col_av_2 = st.columns([2.2, 1])
            
            with col_av_1:
                df_grafico_acc = df_avance_acciones.copy()
                df_grafico_acc['Es_Conductor'] = df_grafico_acc['Acción'].str.lower().str.contains('conductor')
                
                df_grafico_acc['Text_Plan'] = df_grafico_acc['Planificado'].apply(lambda x: f"{int(x):,}")
                df_grafico_acc['Text_Ejec'] = df_grafico_acc['Ejecutado'].apply(lambda x: f"{int(x):,}")
                df_grafico_acc['Porc_Texto'] = df_grafico_acc['Num_Avance'].apply(lambda x: f"{x:.0f}%")

                fig_comb = make_subplots(specs=[[{"secondary_y": True}]])
                
                df_normal = df_grafico_acc[~df_grafico_acc['Es_Conductor']]
                if not df_normal.empty:
                    fig_comb.add_trace(go.Bar(
                        x=df_normal['Acción'], y=df_normal['Planificado'], name='Planificado', 
                        marker_color='#1b365d', text=df_normal['Text_Plan'], textposition='auto'
                    ), secondary_y=False)
                    
                    fig_comb.add_trace(go.Bar(
                        x=df_normal['Acción'], y=df_normal['Ejecutado'], name='Ejecutado', 
                        marker_color='#2b5c8f', text=df_normal['Text_Ejec'], textposition='auto'
                    ), secondary_y=False)

                df_cond = df_grafico_acc[df_grafico_acc['Es_Conductor']]
                if not df_cond.empty:
                    fig_comb.add_trace(go.Bar(
                        x=df_cond['Acción'], y=df_cond['Planificado'], name='Planificado (Metros)', 
                        marker_color='#1b365d', text=df_cond['Text_Plan'], textposition='auto'
                    ), secondary_y=True)
                    
                    fig_comb.add_trace(go.Bar(
                        x=df_cond['Acción'], y=df_cond['Ejecutado'], name='Ejecutado (Metros)', 
                        marker_color='#2b5c8f', text=df_cond['Text_Ejec'], textposition='auto'
                    ), secondary_y=True)

                fig_comb.add_trace(go.Scatter(
                    x=df_grafico_acc['Acción'], 
                    y=df_grafico_acc['Num_Avance'], 
                    name='% Avance', 
                    mode='lines+markers+text',
                    line=dict(color='#d97706', width=3),
                    marker=dict(size=8, color='#d97706'),
                    text=df_grafico_acc['Porc_Texto'],
                    textposition='top center'
                ), secondary_y=True)
                
                fig_comb.update_layout(
                    title=f"Avance - {nombre_proyecto_str}",
                    barmode='group',
                    xaxis_title="",
                    template="plotly_white",
                    height=420,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                fig_comb.update_yaxes(title_text="Magnitud Unidades", secondary_y=False)
                fig_comb.update_yaxes(title_text="% Avance / Metros", secondary_y=True, range=[0, 130])

                st.plotly_chart(fig_comb, use_container_width=True)

            with col_av_2:
                prom_avance_gen = df_avance_acciones['Num_Avance'].mean()
                faltante_gen = max(0, 100 - prom_avance_gen)
                
                fig_donut = go.Figure(data=[go.Pie(
                    labels=['% Avance', '% Faltante'],
                    values=[prom_avance_gen, faltante_gen],
                    hole=0.65,
                    marker=dict(colors=['#1b365d', '#ef4444']),
                    textinfo='none'
                )])
                
                fig_donut.update_layout(
                    title=dict(text="<b>Avance Global del Proyecto</b>", x=0.5, xanchor='center'),
                    annotations=[dict(text=f"<b>{prom_avance_gen:.1f}%</b>", x=0.5, y=0.5, font_size=24, showarrow=False)],
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                    height=420,
                    margin=dict(l=10, r=10, t=50, b=10),
                    template="plotly_white"
                )
                st.plotly_chart(fig_donut, use_container_width=True)

            # Tabla resumen estructurada alineada abajo
            df_tabla_avance_clean = pd.DataFrame()
            for idx, row in df_avance_acciones.iterrows():
                df_tabla_avance_clean[row['Acción']] = [f"{int(row['Planificado']):,}", f"{int(row['Ejecutado']):,}", row['% Avance']]
            
            df_tabla_avance_clean.insert(0, 'Métrica / Concepto', ['Planificado', 'Ejecutado', '% Avance'])
            
            mostrar_tabla_html_ejecutiva(df_tabla_avance_clean)
        else:
            st.info("No se encontraron metas planificadas para este proyecto.")

        st.markdown("---")

        # 5. MÓDULOS DESPLEGABLES DE AUDITORÍA Y DETALLES AL FINAL
        with st.expander("📋 Ver Auditoría Detallada de Mano de Obra (Ejecución en Campo)"):
            if not df_mo_agrupado.empty:
                mostrar_tabla_html_ejecutiva(df_mo_agrupado)
            else:
                st.warning(f"⚠️ No se encontraron registros de mano de obra para el código '{codigo_seleccionado}'.")

        with st.expander("🛠️ Ver Detalle de Materiales Instalados (SAP)"):
            if not df_materiales_mostrador.empty:
                mostrar_tabla_html_ejecutiva(df_materiales_mostrador)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_materiales_mostrador.to_excel(writer, index=False, sheet_name='Materiales Instalados')
                
                excel_data = output.getvalue()
                
                st.download_button(
                    label="📥 Descargar Materiales en Excel Real (.xlsx)",
                    data=excel_data,
                    file_name=f"Materiales_Instalados_{cod_clean}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("No se encontraron materiales vinculados para este proyecto.")

    else:
        st.info("👈 Por favor seleccione un Código de Proyecto en el menú lateral.")

else:
    # -------------------------------------------------------------
    # MAPA INTERACTIVO CON MARCADORES RESALTADOS DE ALTO IMPACTO
    # -------------------------------------------------------------
    st.subheader("🗺️ Geoportal de Proyectos EDEESTE")
    st.caption("Cada marcador representa la ubicación geográfica del proyecto con su Inversión Total Real acumulada (Mano de Obra + Materiales SAP).")

    if df_codigos is None or df_codigos.empty:
        st.error("No se pudo cargar Codigos de proyectos.xlsx.")

    else:
        col_lat = next((c for c in df_codigos.columns if "lat" in c.lower()), None)
        col_lon = next((c for c in df_codigos.columns if "lon" in c.lower() or "lng" in c.lower()), None)
        col_cod = next((c for c in df_codigos.columns if "código" in c.lower() or "codigo" in c.lower() or "proyecto" in c.lower()), df_codigos.columns[0])
        col_nom = next((c for c in df_codigos.columns if "nombre" in c.lower() or "descripci" in c.lower()), None)

        if not col_lat or not col_lon:
            st.error("No se encontraron las columnas de Latitud y Longitud en Codigos de proyectos.xlsx.")

        else:
            df_mapa = df_codigos.copy()
            df_mapa["Código"] = df_mapa[col_cod].astype(str).str.strip()
            df_mapa["Nombre"] = df_mapa[col_nom].fillna("").astype(str).str.strip() if col_nom else ""

            df_mapa["lat"] = pd.to_numeric(df_mapa[col_lat], errors="coerce")
            df_mapa["lon"] = pd.to_numeric(df_mapa[col_lon], errors="coerce")

            df_mapa = df_mapa.dropna(subset=["lat", "lon"]).copy()
            df_mapa = df_mapa[df_mapa["lat"].between(-90, 90) & df_mapa["lon"].between(-180, 180)].copy()

            if codigo_seleccionado != "Todos":
                df_mapa = df_mapa[df_mapa["Código"] == str(codigo_seleccionado).strip()].copy()

            # Cálculo de Inversión Total Real por proyecto (Mano de Obra + Materiales SAP)
            mapa_registros = []
            for _, r_m in df_mapa.iterrows():
                p_c = r_m["Código"]
                p_n = r_m["Nombre"]
                p_la = r_m["lat"]
                p_lo = r_m["lon"]
                
                mo_v, mat_v, tot_v = calcular_inversion_proyecto_completa(p_c, df_mo, df_contratistas, df_sap, dict_familia)
                
                mapa_registros.append({
                    "Código": p_c,
                    "Nombre": p_n,
                    "lat": p_la,
                    "lon": p_lo,
                    "Proyecto": f"{p_c} - {p_n}" if p_n else p_c,
                    "Inversión MO (RD$)": mo_v,
                    "Inversión Materiales (RD$)": mat_v,
                    "Inversión Total (RD$)": tot_v,
                    "Inversión": f"RD$ {tot_v:,.2f}"
                })

            df_mapa_final = pd.DataFrame(mapa_registros)

            if df_mapa_final.empty:
                st.warning("No hay proyectos con coordenadas válidas para el filtro seleccionado.")

            else:
                lat_centro = float(df_mapa_final["lat"].mean()) if not df_mapa_final.empty else 18.52
                lon_centro = float(df_mapa_final["lon"].mean()) if not df_mapa_final.empty else -69.80
                zoom_nivel = 10 if len(df_mapa_final) == 1 else 9.2

                # Configuración de Marcadores Grandes y Color Naranja Vibrante (#D97706)
                if hasattr(px, "scatter_map"):
                    fig_map = px.scatter_map(
                        df_mapa_final,
                        lat="lat",
                        lon="lon",
                        hover_name="Proyecto",
                        hover_data={
                            "Código": True,
                            "Inversión": True,
                            "lat": False,
                            "lon": False,
                            "Inversión Total (RD$)": False,
                            "Nombre": False,
                        },
                        color_discrete_sequence=["#D97706"],  # Naranja Caluroso
                        zoom=zoom_nivel,
                        center={"lat": lat_centro, "lon": lon_centro},
                        height=600,
                    )
                    fig_map.update_traces(
                        marker=dict(
                            size=15,  # Puntos considerablemente más grandes y visibles
                            opacity=0.9,
                        )
                    )
                    fig_map.update_layout(
                        map_style="open-street-map",
                        margin=dict(l=0, r=0, t=0, b=0),
                    )
                else:
                    fig_map = px.scatter_mapbox(
                        df_mapa_final,
                        lat="lat",
                        lon="lon",
                        hover_name="Proyecto",
                        hover_data={
                            "Código": True,
                            "Inversión": True,
                            "lat": False,
                            "lon": False,
                            "Inversión Total (RD$)": False,
                            "Nombre": False,
                        },
                        color_discrete_sequence=["#D97706"],
                        zoom=zoom_nivel,
                        center={"lat": lat_centro, "lon": lon_centro},
                        height=600,
                    )
                    fig_map.update_traces(
                        marker=dict(
                            size=15,
                            opacity=0.9,
                        )
                    )
                    fig_map.update_layout(
                        mapbox_style="open-street-map",
                        mapbox=dict(
                            center={"lat": lat_centro, "lon": lon_centro},
                            zoom=zoom_nivel
                        ),
                        margin=dict(l=0, r=0, t=0, b=0),
                    )

                st.plotly_chart(
                    fig_map,
                    use_container_width=True,
                    key="mapa_proyectos_edeeste",
                )

                # Métricas Gerenciales Reales de Inversión Total
                m1, m2, m3 = st.columns(3)
                m1.metric("Proyectos visibles", len(df_mapa_final))
                m2.metric(
                    "Inversión Total Registrada",
                    f"RD$ {df_mapa_final['Inversión Total (RD$)'].sum():,.2f}"
                )
                m3.metric(
                    "Proyectos sin inversión",
                    int((df_mapa_final["Inversión Total (RD$)"] <= 0).sum())
                )

                st.caption(
                    "La inversión mostrada corresponde a la Inversión Total acumulada "
                    "(Mano de Obra ejec. + Materiales SAP valorizados en campo)."
                )
