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

        # 3. Lógica IDP Robusta: Detección Dinámica de Columnas y Doble Agregación
        costo_materiales_total = 0.0
        df_materiales_calculados = pd.DataFrame()
        df_mo_agrupado = pd.DataFrame()
        
        fuente_mat = df_contratistas.copy() if (df_contratistas is not None and not df_contratistas.empty) else (df_familia.copy() if df_familia is not None else None)
        
        if fuente_mat is not None and not fuente_mat.empty and df_sap is not None and not df_sap.empty and not df_mo_proy.empty:
            # A. Agrupar mano de obra por Actividad buscando nombres de columna inteligentes
            col_act_mo = next((c for c in df_mo_proy.columns if 'actividad' in c.lower()), df_mo_proy.columns[0])
            col_cant_mo = next((c for c in df_mo_proy.columns if c.lower() == 'cantidad' or 'cant' in c.lower()), df_mo_proy.columns[4])
            
            df_mo_proy['Actividad_Clean'] = df_mo_proy[col_act_mo].fillna("").astype(str).str.strip().str.upper()
            df_mo_proy['Cantidad_Num'] = pd.to_numeric(df_mo_proy[col_cant_mo], errors='coerce').fillna(0)
            
            df_mo_agrupado = df_mo_proy.groupby('Actividad_Clean', as_index=False)['Cantidad_Num'].sum()
            df_mo_agrupado.rename(columns={'Actividad_Clean': 'Actividad', 'Cantidad_Num': 'Cantidad Total Ejecutada'}, inplace=True)
            
            dict_cant_mo = dict(zip(df_mo_agrupado['Actividad'], df_mo_agrupado['Cantidad Total Ejecutada']))
            
            # B. Identificar columnas dinámicas en el maestro de contratistas
            col_act_mat = next((c for c in fuente_mat.columns if 'actividad' in c.lower()), fuente_mat.columns[0])
            col_sap_mat = next((c for c in fuente_mat.columns if 'sap' in c.lower() or 'código sap' in c.lower() or 'codigo sap' in c.lower()), fuente_mat.columns[4])
            desc_mat_col = next((c for c in fuente_mat.columns if 'descripci' in c.lower() or ('mat' in c.lower() and c != col_sap_mat)), fuente_mat.columns[5])
            und_col = next((c for c in fuente_mat.columns if 'unid' in c.lower()), None)
            
            # Columna de cantidad unitaria del material (buscando explícitamente columnas numéricas o de cantidad que no sean actividad/sap)
            cols_candidatas_cant = [c for c in fuente_mat.columns if ('cant' in c.lower() or 'und' in c.lower()) and c != col_act_mat and c != col_sap_mat]
            col_cant_mat = cols_candidatas_cant[-1] if cols_candidatas_cant else fuente_mat.columns[-1]
            
            fuente_mat['Actividad_Clean'] = fuente_mat[col_act_mat].fillna("").astype(str).str.strip().str.upper()
            df_filtrado = fuente_mat[fuente_mat['Actividad_Clean'].isin(dict_cant_mo.keys())].copy()
            
            if not df_filtrado.empty:
                df_filtrado['Cant_IDP'] = df_filtrado['Actividad_Clean'].map(dict_cant_mo)
                df_filtrado["Cantidad_Unitaria"] = pd.to_numeric(df_filtrado[col_cant_mat], errors="coerce").fillna(0)
                df_filtrado["Cantidad_Total_Material"] = df_filtrado["Cantidad_Unitaria"] * df_filtrado['Cant_IDP']
                
                # C. Normalizar códigos SAP preservando ceros a la izquierda (como texto limpio)
                col_sap_prec = next((c for c in df_sap.columns if 'sap' in c.lower() or 'código' in c.lower() or 'codigo' in c.lower()), df_sap.columns[0])
                col_precio_final = next((c for c in df_sap.columns if 'precio material' in c.lower() or 'precio' in c.lower() or 'costo' in c.lower()), df_sap.columns[-1])
                
                df_sap_copy = df_sap.copy()
                df_sap_copy['Clean_SAP'] = df_sap_copy[col_sap_prec].fillna("").astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
                df_filtrado['Clean_SAP'] = df_filtrado[col_sap_mat].fillna("").astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
                
                # Cruce con SAP (usando left join para no perder materiales)
                df_merge_sap = pd.merge(df_filtrado, df_sap_copy, on='Clean_SAP', how='left')
                df_merge_sap['Precio_Unitario_SAP'] = pd.to_numeric(df_merge_sap[col_precio_final].astype(str).str.replace("$", "").str.replace(",", ""), errors="coerce").fillna(0.0)
                
                # D. Doble Agrupación por Código SAP
                cols_agrupar = ['Clean_SAP', desc_mat_col]
                if und_col and und_col in df_merge_sap.columns:
                    cols_agrupar.append(und_col)
                    
                df_resumen_mat = df_merge_sap.groupby(cols_agrupar, as_index=False).agg({
                    "Cantidad_Total_Material": "sum",
                    "Precio_Unitario_SAP": "first"
                })
                
                df_resumen_mat['Costo_Material'] = df_resumen_mat['Cantidad_Total_Material'] * df_resumen_mat['Precio_Unitario_SAP']
                
                renombres = {
                    'Clean_SAP': "Código SAP",
                    desc_mat_col: "Descripción de Material",
                    "Cantidad_Total_Material": "Cantidad Total",
                    "Costo_Material": "Costo Total"
                }
                if und_col and und_col in df_resumen_mat.columns:
                    renombres[und_col] = "Unidad"
                    
                df_resumen_mat = df_resumen_mat.rename(columns=renombres)
                
                costo_materiales_total = df_resumen_mat['Costo Total'].sum()
                df_materiales_calculados = df_resumen_mat

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
            st.markdown("#### 🛠️ Requerimiento Consolidado de Materiales (Doble Agrupación SAP)")
            if not df_materiales_calculados.empty:
                st.dataframe(df_materiales_calculados.head(15), use_container_width=True)
            else:
                st.info("No se encontraron materiales vinculados para este proyecto.")
                
        st.markdown("#### 📋 Mano de Obra Agrupada por Actividad")
        if not df_mo_agrupado.empty:
            st.dataframe(df_mo_agrupado.head(15), use_container_width=True)
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
