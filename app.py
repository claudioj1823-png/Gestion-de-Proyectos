import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Sistema de Gestión de Proyectos - EDEESTE",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; color: #212529; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stMetric label { color: #6c757d !important; font-weight: 600; font-size: 14px; }
    .stMetric [data-testid="stMetricValue"] { color: #0d6efd !important; font-size: 24px; font-weight: bold; }
    h1, h2, h3, h4, h5, h6 { color: #212529 !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("## ⚡ EDEESTE • Sistema de Gestión de Proyectos")
st.markdown("<h4 style='color: #6c757d; font-weight: 500;'>GERENCIA EJECUCIÓN DE PROYECTOS • PANEL EJECUTIVO</h4>", unsafe_allow_html=True)
st.markdown("---")

def limpiar_nombre_columnas(df):
    if df is not None and not df.empty:
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    return df

def normalizar_texto(txt):
    if not isinstance(txt, str):
        return ""
    import unicodedata
    nfkd_form = unicodedata.normalize('NFKD', txt)
    solo_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    clean = solo_ascii.upper().strip()
    if clean.endswith('ES'):
        clean = clean[:-2]
    elif clean.endswith('S') and not clean in ['PUESTA A TIERRA', 'TENDIDO DE CONDUCTOR']:
        clean = clean[:-1]
    return clean

def cargar_datos():
    archivos = {
        'codigos': 'Codigos de proyectos.xlsx',
        'familia': 'Actividades con sus familia.xlsx',
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
            if clave == 'familia' and os.path.exists('Actividades con sus familia.xlsx'):
                try:
                    dfs[clave] = limpiar_nombre_columnas(pd.read_excel('Actividades con sus familia.xlsx'))
                except:
                    dfs[clave] = None
            else:
                dfs[clave] = None
    return dfs

datos = cargar_datos()

df_codigos = datos.get('codigos')
df_mo = datos.get('mo')
df_familia = datos.get('familia')
df_contratistas = datos.get('contratistas')
df_sap = datos.get('sap')
df_metas = datos.get('metas')

# Mapeo Actividad -> Familia
dict_familia = {}
if df_familia is not None and not df_familia.empty:
    col_act_f = next((c for c in df_familia.columns if 'actividad' in c.lower()), df_familia.columns[0])
    col_fam_f = next((c for c in df_familia.columns if 'familia' in c.lower()), df_familia.columns[-1])
    
    for _, row in df_familia.iterrows():
        act_raw = str(row[col_act_f]).strip().upper()
        fam_raw = str(row[col_fam_f]).strip()
        dict_familia[act_raw] = fam_raw

st.sidebar.markdown("### 🎛️ FILTROS EJECUTIVOS")
anos_disponibles = ["Todos"]
meses_disponibles = ["Todos", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

if df_mo is not None and not df_mo.empty:
    cols_fecha = [c for c in df_mo.columns if 'fecha' in c.lower() or 'date' in c.lower() or 'periodo' in c.lower()]
    if cols_fecha:
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
menu = st.sidebar.radio("🧭 MÓDULOS", ["Panel Ejecutivo por Proyecto", "Relación Mano de Obra y Materiales", "Mapas de Ubicación"])

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refrescar Datos en Vivo"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.caption("EDEESTE - Control Presupuestario y Operativo")

if menu == "Panel Ejecutivo por Proyecto":
    if codigo_seleccionado != "Todos":
        cod_clean = str(codigo_seleccionado).strip()
        
        nombre_proyecto_str = cod_clean
        if df_codigos is not None and not df_codigos.empty:
            col_codigo_p = df_codigos.columns[0]
            cols_desc_p = [c for c in df_codigos.columns if 'nombre' in c.lower() or 'descripci' in c.lower() or ('proyecto' in c.lower() and c != col_codigo_p)]
            if cols_desc_p:
                col_desc_p = cols_desc_p[0]
                df_codigos['Clean_Cod'] = df_codigos[col_codigo_p].astype(str).str.strip()
                match_p = df_codigos[df_codigos['Clean_Cod'] == cod_clean]
                if not match_p.empty:
                    nombre_proyecto_str = f"{cod_clean} - {match_p.iloc[0][col_desc_p]}"
        
        st.markdown(f"<h4 style='color: #212529; margin-bottom: 15px;'>📌 PROYECTO: <b style='color: #0d6efd;'>{nombre_proyecto_str}</b></h4>", unsafe_allow_html=True)
        
        # 1. Mano de Obra Ejecutada filtrada
        monto_mo = 0.0
        df_mo_proy = pd.DataFrame()
        if df_mo is not None and not df_mo.empty:
            col_proy_mo = next((c for c in df_mo.columns if 'proyecto' in c.lower() or 'código' in c.lower() or 'codigo' in c.lower()), df_mo.columns[-3])
            col_costo_mo = next((c for c in df_mo.columns if 'costo total' in c.lower() or 'total' in c.lower()), df_mo.columns[5])
            
            df_mo['Clean_Proy'] = df_mo[col_proy_mo].astype(str).str.strip()
            df_mo_proy = df_mo[df_mo['Clean_Proy'] == cod_clean].copy()
            
            if 'Fecha_Parsed' in df_mo_proy.columns:
                if ano_sel != "Todos":
                    df_mo_proy = df_mo_proy[df_mo_proy['Fecha_Parsed'].dt.year == int(ano_sel)]
                if mes_sel != "Todos":
                    meses_dict = {"Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12}
                    df_mo_proy = df_mo_proy[df_mo_proy['Fecha_Parsed'].dt.month == meses_dict.get(mes_sel, 0)]
            
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

        # 3. Procesamiento y Materiales (Forzando lectura de Columna E / Precio Final)
        costo_materiales_total = 0.0
        df_materiales_calculados = pd.DataFrame()
        df_mo_agrupado = pd.DataFrame()
        
        fuente_mat = df_contratistas.copy() if (df_contratistas is not None and not df_contratistas.empty) else (df_familia.copy() if df_familia is not None else None)
        
        if fuente_mat is not None and not fuente_mat.empty and df_sap is not None and not df_sap.empty and not df_mo_proy.empty:
            col_act_mo = next((c for c in df_mo_proy.columns if 'actividad' in c.lower()), df_mo_proy.columns[0])
            col_cant_mo = next((c for c in df_mo_proy.columns if c.lower() == 'cantidad' or 'cant' in c.lower()), df_mo_proy.columns[4])
            
            df_mo_proy['Actividad_Clean'] = df_mo_proy[col_act_mo].fillna("").astype(str).str.strip().str.upper()
            df_mo_proy['Cantidad_Num'] = pd.to_numeric(df_mo_proy[col_cant_mo], errors='coerce').fillna(0)
            
            df_mo_proy['Familia_Accion'] = df_mo_proy['Actividad_Clean'].map(dict_familia).fillna("OTRA")
            
            df_mo_agrupado = df_mo_proy.groupby(['Familia_Accion', 'Actividad_Clean'], as_index=False)['Cantidad_Num'].sum()
            df_mo_agrupado.rename(columns={'Familia_Accion': 'Familia / Acción', 'Actividad_Clean': 'Actividad', 'Cantidad_Num': 'Cantidad Ejecutada'}, inplace=True)
            
            dict_cant_mo = dict(zip(df_mo_agrupado['Actividad'], df_mo_agrupado['Cantidad Ejecutada']))
            
            col_act_mat = next((c for c in fuente_mat.columns if 'actividad' in c.lower()), fuente_mat.columns[0])
            col_sap_mat = next((c for c in fuente_mat.columns if 'sap' in c.lower() or 'código sap' in c.lower() or 'codigo sap' in c.lower()), fuente_mat.columns[4])
            und_col = next((c for c in fuente_mat.columns if 'unid' in c.lower()), None)
            
            cols_candidatas_cant = [c for c in fuente_mat.columns if ('cant' in c.lower() or 'und' in c.lower()) and c != col_act_mat and c != col_sap_mat]
            col_cant_mat = cols_candidatas_cant[-1] if cols_candidatas_cant else fuente_mat.columns[-1]
            
            fuente_mat['Actividad_Clean'] = fuente_mat[col_act_mat].fillna("").astype(str).str.strip().str.upper()
            fuente_mat['Clean_SAP'] = fuente_mat[col_sap_mat].fillna("").astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
            fuente_mat['Cantidad_Unitaria_Num'] = pd.to_numeric(fuente_mat[col_cant_mat], errors='coerce').fillna(0)
            
            fuente_mat_clean = fuente_mat.drop_duplicates(subset=['Actividad_Clean', 'Clean_SAP']).copy()
            df_filtrado = fuente_mat_clean[fuente_mat_clean['Actividad_Clean'].isin(dict_cant_mo.keys())].copy()
            
            if not df_filtrado.empty:
                df_filtrado['Cant_IDP'] = df_filtrado['Actividad_Clean'].map(dict_cant_mo)
                df_filtrado["Cantidad_Total_Material"] = df_filtrado["Cantidad_Unitaria_Num"] * df_filtrado['Cant_IDP']
                
                # Leer Precio SAP tomando directamente la columna de precio final o la columna E (índice 4)
                col_sap_prec = df_sap.columns[0]
                col_desc_sap = df_sap.columns[1]
                col_precio_final = df_sap.columns[4] if len(df_sap.columns) > 4 else df_sap.columns[-1]
                
                df_sap_copy = df_sap.copy()
                df_sap_copy['Clean_SAP'] = df_sap_copy[col_sap_prec].fillna("").astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
                df_sap_copy['Descripcion_Oficial'] = df_sap_copy[col_desc_sap].fillna("").astype(str)
                df_sap_copy['Precio_Oficial'] = pd.to_numeric(df_sap_copy[col_precio_final].astype(str).str.replace("$", "").str.replace(",", ""), errors="coerce").fillna(0.0)
                
                df_sap_limpio = df_sap_copy[['Clean_SAP', 'Descripcion_Oficial', 'Precio_Oficial']].drop_duplicates(subset=['Clean_SAP'])
                df_merge_sap = pd.merge(df_filtrado, df_sap_limpio, on='Clean_SAP', how='left')
                
                cols_agrupar = ['Clean_SAP', 'Descripcion_Oficial']
                if und_col and und_col in df_merge_sap.columns:
                    cols_agrupar.append(und_col)
                    
                df_resumen_mat = df_merge_sap.groupby(cols_agrupar, as_index=False).agg({
                    "Cantidad_Total_Material": "sum",
                    "Precio_Oficial": "first"
                })
                
                df_resumen_mat['Costo_Material'] = df_resumen_mat['Cantidad_Total_Material'] * df_resumen_mat['Precio_Oficial']
                
                renombres = {
                    'Clean_SAP': "Código SAP",
                    'Descripcion_Oficial': "Descripción de Material",
                    "Cantidad_Total_Material": "Cantidad Total",
                    "Precio_Oficial": "Precio_Unitario_SAP",
                    "Costo_Material": "Costo Total"
                }
                if und_col and und_col in df_resumen_mat.columns:
                    renombres[und_col] = "Unidad"
                    
                df_resumen_mat = df_resumen_mat.rename(columns=renombres)
                costo_materiales_total = df_resumen_mat['Costo Total'].sum()
                df_materiales_calculados = df_resumen_mat

        # 4. Cruce de Metas y Ejecutado
        df_avance_acciones = pd.DataFrame()
        if df_metas is not None and not df_metas.empty:
            col_proy_m = next((c for c in df_metas.columns if 'proyecto' in c.lower() or 'código' in c.lower() or 'codigo' in c.lower()), df_metas.columns[0])
            df_metas['Clean_P_Meta'] = df_metas[col_proy_m].astype(str).str.strip()
            df_metas_proy = df_metas[df_metas['Clean_P_Meta'] == cod_clean].copy()
            
            if not df_metas_proy.empty:
                col_accion_meta = next((c for c in df_metas_proy.columns if 'accion' in c.lower() or 'actividad' in c.lower()), df_metas_proy.columns[3])
                col_cant_plan = next((c for c in df_metas_proy.columns if 'cantidad' in c.lower() or 'planifica' in c.lower()), df_metas_proy.columns[4])
                
                df_metas_proy['Acción'] = df_metas_proy[col_accion_meta].fillna("").astype(str).str.strip()
                df_metas_proy['Acción_Key'] = df_metas_proy['Acción'].apply(normalizar_texto)
                df_metas_proy['Planificado'] = pd.to_numeric(df_metas_proy[col_cant_plan], errors='coerce').fillna(0)
                
                if not df_mo_proy.empty:
                    df_mo_proy['Familia_Key'] = df_mo_proy['Familia_Accion'].apply(normalizar_texto)
                    df_ejec_fam = df_mo_proy.groupby('Familia_Key', as_index=False)['Cantidad_Num'].sum()
                    df_ejec_fam.rename(columns={'Familia_Key': 'Acción_Key', 'Cantidad_Num': 'Ejecutado'}, inplace=True)
                else:
                    df_ejec_fam = pd.DataFrame(columns=['Acción_Key', 'Ejecutado'])
                
                df_avance_acciones = pd.merge(
                    df_metas_proy[['Acción', 'Acción_Key', 'Planificado']],
                    df_ejec_fam[['Acción_Key', 'Ejecutado']],
                    on='Acción_Key',
                    how='left'
                ).fillna(0)
                
                df_avance_acciones = df_avance_acciones[['Acción', 'Planificado', 'Ejecutado']]
                df_avance_acciones['% Avance'] = df_avance_acciones.apply(
                    lambda r: f"{(r['Ejecutado'] / r['Planificado'] * 100):.1f}%" if r['Planificado'] > 0 else "0.0%",
                    axis=1
                )

        total_ejecutado = monto_mo + costo_materiales_total
        porcentaje_ejecutado = (total_ejecutado / presupuesto_plan * 100) if presupuesto_plan > 0 else 0

        # Tarjetas Métricas
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Mano de Obra (RD$)", f"{monto_mo:,.2f}")
        c2.metric("Materiales SAP (RD$)", f"{costo_materiales_total:,.2f}")
        c3.metric("Total Ejecutado (RD$)", f"{total_ejecutado:,.2f}")
        c4.metric("Presupuesto Plan. (RD$)", f"{presupuesto_plan:,.2f}")
        c5.metric("% Ejecución", f"{porcentaje_ejecutado:.1f}%")

        st.markdown("---")
        st.markdown("### 📊 Desglose Financiero y Operativo")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            df_grafico = pd.DataFrame({
                'Concepto': ['Mano de Obra', 'Materiales SAP', 'Total Ejecutado', 'Presupuesto Plan.'],
                'Monto (RD$)': [monto_mo, costo_materiales_total, total_ejecutado, presupuesto_plan]
            })
            fig_bar = px.bar(df_grafico, x='Concepto', y='Monto (RD$)', color='Concepto', title="Comparativo Financiero del Proyecto")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_g2:
            st.markdown("#### 🛠️ Materiales Instalados")
            if not df_materiales_calculados.empty:
                st.dataframe(df_materiales_calculados.head(15), use_container_width=True)
            else:
                st.info("No se encontraron materiales vinculados para este proyecto.")

        # Tabla y Gráfico de Avance por Acción
        st.markdown("#### 🎯 Avance Total por Acción (Planificado vs Ejecutado)")
        if not df_avance_acciones.empty:
            st.dataframe(df_avance_acciones[['Acción', 'Planificado', 'Ejecutado', '% Avance']], use_container_width=True, hide_index=True)
            
            fig_comb = go.Figure()
            fig_comb.add_trace(go.Bar(x=df_avance_acciones['Acción'], y=df_avance_acciones['Planificado'], name='Planificado', marker_color='#1f77b4'))
            fig_comb.add_trace(go.Bar(x=df_avance_acciones['Acción'], y=df_avance_acciones['Ejecutado'], name='Ejecutado', marker_color='#2ca02c'))
            fig_comb.update_layout(title=f"Avance Gráfico por Acción - {nombre_proyecto_str}", barmode='group', xaxis_title="Acciones", yaxis_title="Cantidades")
            st.plotly_chart(fig_comb, use_container_width=True)
        else:
            st.info("No se encontraron metas planificadas para este proyecto.")
                
        # Detalle de Mano de Obra en Expansor Limpio (Opción A)
        with st.expander("📋 Ver Auditoría Detallada de Mano de Obra (Ejecución en Campo)"):
            if not df_mo_agrupado.empty:
                st.dataframe(
                    df_mo_agrupado,
                    column_config={
                        "Familia / Acción": st.column_config.TextColumn("Familia / Acción", width="medium"),
                        "Actividad": st.column_config.TextColumn("Actividad", width="medium"),
                        "Cantidad Ejecutada": st.column_config.NumberColumn("Cantidad Ejecutada", width="small", format="%.2f")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.warning(f"⚠️ No se encontraron registros de mano de obra para el código '{codigo_seleccionado}'.")
    else:
        st.info("👈 Por favor seleccione un Código de Proyecto en el menú lateral.")

elif menu == "Relación Mano de Obra y Materiales":
    st.subheader("🧩 Matriz Relacional Unificada con Familias de Actividades")
    if df_contratistas is not None and df_sap is not None:
        df_c_mat = df_contratistas.copy()
        col_act = next((c for c in df_c_mat.columns if 'actividad' in c.lower()), df_c_mat.columns[0])
        col_sap = next((c for c in df_c_mat.columns if 'sap' in c.lower() or 'código sap' in c.lower()), df_c_mat.columns[4])
        
        df_c_mat['Clean_Act'] = df_c_mat[col_act].fillna("").astype(str).str.strip().str.upper()
        df_c_mat['Familia'] = df_c_mat['Clean_Act'].map(dict_familia).fillna("OTRA")
        df_c_mat['Clean_SAP'] = df_c_mat[col_sap].fillna("").astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        
        col_sap_prec = df_sap.columns[0]
        col_desc_sap = df_sap.columns[1]
        col_precio_final = df_sap.columns[4] if len(df_sap.columns) > 4 else df_sap.columns[-1]
        
        df_sap_c = df_sap.copy()
        df_sap_c['Clean_SAP'] = df_sap_c[col_sap_prec].fillna("").astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        df_sap_c['Descripcion_Oficial'] = df_sap_c[col_desc_sap].fillna("").astype(str)
        df_sap_c['Precio_Oficial'] = pd.to_numeric(df_sap_c[col_precio_final].astype(str).str.replace("$", "").str.replace(",", ""), errors="coerce").fillna(0.0)
        
        df_sap_limpio = df_sap_c[['Clean_SAP', 'Descripcion_Oficial', 'Precio_Oficial']].drop_duplicates(subset=['Clean_SAP'])
        df_c_dedup = df_c_mat.drop_duplicates(subset=[col_act, 'Clean_SAP']).copy()
        df_matriz_final = pd.merge(df_c_dedup, df_sap_limpio, on='Clean_SAP', how='left')
        
        st.dataframe(df_matriz_final, use_container_width=True)
    else:
        st.warning("No se encontraron los archivos de contratistas o precios SAP.")

else:
    st.subheader("🗺️ Ubicación Geográfica del Proyecto en Zona de Concesión EDEESTE")
    map_data = pd.DataFrame({
        'lat': [18.4861, 18.5123, 18.4500, 18.5500],
        'lon': [-69.8500, -69.8000, -69.6500, -69.7800],
        'Proyecto': ['Proyecto Redes La Javilla', 'Ciudad Juan Bosch', 'Circuito SPER01', 'Rehabilitación LM3802R']
    })
    st.map(map_data)
    st.caption("Ubicación satelital y puntos de ejecución del proyecto.")
