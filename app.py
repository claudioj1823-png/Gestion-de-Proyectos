import io
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(
    page_title="Control de Proyecto - EDEESTE", page_icon="⚡", layout="wide"
)

# Estilos CSS globales y semáforos corporativos
st.markdown(
    """
    <style>
    .main { background-color: #f8f9fa; color: #212529; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stMetric label { color: #6c757d !important; font-weight: 600; font-size: 14px; }
    .stMetric [data-testid="stMetricValue"] { color: #0d6efd !important; font-size: 24px; font-weight: bold; }
    h1, h2, h3, h4, h5, h6 { color: #212529 !important; }
    
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
""",
    unsafe_allow_html=True,
)

st.markdown("## ⚡ EDEESTE • Control de Proyecto (Panel Gerencial)")
st.markdown("---")


def limpiar_nombre_columnas(df):
    if df is not None and not df.empty:
        df = df.copy()
        df.columns = [str(c).strip().replace("\n", " ") for c in df.columns]
    return df


def buscar_columna_segura(df, palabras_clave):
    if df is None or df.empty:
        return None
    for col in df.columns:
        col_clean = str(col).lower().strip()
        if any(pk in col_clean for pk in palabras_clave):
            return col
    return None


def parsear_numero_seguro(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace("$", "").replace(" ", "")
    if not s or s.lower() in ["nan", "none", "null"]:
        return 0.0
    if "," in s and "." in s:
        s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


@st.cache_data(ttl=0)
def cargar_datos_seguros():
    dfs = {}

    if os.path.exists("Codigos de proyectos.xlsx"):
        dfs["codigos"] = limpiar_nombre_columnas(
            pd.read_excel("Codigos de proyectos.xlsx")
        )
    else:
        dfs["codigos"] = None

    ruta_fam = (
        "Actividades con su familia.xlsx"
        if os.path.exists("Actividades con su familia.xlsx")
        else "Actividades con sus familia.xlsx"
    )
    if os.path.exists(ruta_fam):
        try:
            xls_f = pd.ExcelFile(ruta_fam)
            sheet_f = (
                "Mano de Obra con su Familia"
                if "Mano de Obra con su Familia" in xls_f.sheet_names
                else xls_f.sheet_names[0]
            )
            dfs["familia"] = limpiar_nombre_columnas(
                pd.read_excel(ruta_fam, sheet_name=sheet_f)
            )
        except Exception:
            dfs["familia"] = None
    else:
        dfs["familia"] = None

    if os.path.exists("Actividades contratistas.xlsx"):
        try:
            xls_c = pd.ExcelFile("Actividades contratistas.xlsx")
            sheet_c = (
                "Actividades con materiales"
                if "Actividades con materiales" in xls_c.sheet_names
                else xls_c.sheet_names[0]
            )
            dfs["contratistas"] = limpiar_nombre_columnas(
                pd.read_excel("Actividades contratistas.xlsx", sheet_name=sheet_c)
            )
        except Exception:
            dfs["contratistas"] = None
    else:
        dfs["contratistas"] = None

    if os.path.exists("Precios Sap.xlsx"):
        try:
            dfs["sap"] = limpiar_nombre_columnas(
                pd.read_excel("Precios Sap.xlsx", sheet_name="Hoja3")
            )
        except Exception as e:
            st.error(f"Error al leer la Hoja 3 de Precios Sap.xlsx: {e}")
            dfs["sap"] = None
    else:
        dfs["sap"] = None

    if os.path.exists("Proyectos con sus metas.xlsx"):
        dfs["metas"] = limpiar_nombre_columnas(
            pd.read_excel("Proyectos con sus metas.xlsx", skiprows=1)
        )
    else:
        dfs["metas"] = None

    if os.path.exists("Mano de Obra por proyecto.xlsx"):
        dfs["mo"] = limpiar_nombre_columnas(
            pd.read_excel("Mano de Obra por proyecto.xlsx")
        )
    else:
        dfs["mo"] = None

    return dfs


datos = cargar_datos_seguros()

df_codigos = datos.get("codigos")
df_mo = datos.get("mo")
df_familia = datos.get("familia")
df_contratistas = datos.get("contratistas")
df_sap = datos.get("sap")
df_metas = datos.get("metas")

dict_familia = {}
if df_familia is not None and not df_familia.empty:
    col_act_f = buscar_columna_segura(df_familia, ["actividad", "código", "codigo"])
    col_fam_f = buscar_columna_segura(df_familia, ["familia"])
    if col_act_f and col_fam_f:
        for _, row in df_familia.iterrows():
            act_raw = str(row[col_act_f]).strip().upper()
            fam_raw = str(row[col_fam_f]).strip()
            if act_raw and fam_raw and fam_raw != "nan":
                dict_familia[act_raw] = fam_raw

st.sidebar.markdown("### 🎛️ FILTROS EJECUTIVOS")
anos_disponibles = ["Todos"]
meses_disponibles = [
    "Todos",
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

if df_mo is not None and not df_mo.empty:
    col_fecha_mo = buscar_columna_segura(df_mo, ["fecha", "date", "periodo"])
    if col_fecha_mo:
        df_mo = df_mo.copy()
        df_mo["Fecha_Parsed"] = pd.to_datetime(df_mo[col_fecha_mo], errors="coerce")
        anos_encontrados = df_mo["Fecha_Parsed"].dt.year.dropna().unique()
        if len(anos_encontrados) > 0:
            anos_disponibles = ["Todos"] + sorted(
                [str(int(a)) for a in anos_encontrados]
            )

ano_sel = st.sidebar.selectbox("📅 AÑO", anos_disponibles)
mes_sel = st.sidebar.selectbox("📅 MES", meses_disponibles)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 SELECCIÓN DE PROYECTO")

lista_codigos = []
if df_codigos is not None and not df_codigos.empty:
    col_codigo = buscar_columna_segura(df_codigos, ["proyecto", "código", "codigo"])
    if col_codigo:
        lista_codigos = (
            df_codigos[col_codigo]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

codigo_seleccionado = st.sidebar.selectbox(
    "Código de Proyecto:", ["Todos"] + lista_codigos
)
menu = st.sidebar.radio(
    "🧭 MÓDULOS",
    [
        "Panel Ejecutivo por Proyecto",
        "Mapa Interactivo de Proyectos",
        "Auditoría de Almacén (Coccia)",
    ],
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 RECARGAR DATOS"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.caption("EDEESTE - Control Presupuestario y Operativo")


def mostrar_tabla_html_ejecutiva(df_mostrar):
    import uuid

    tabla_id = f"tabla_{uuid.uuid4().hex[:8]}"
    html_str = df_mostrar.to_html(
        index=False, classes="tabla-ejecutiva", escape=False
    )
    
    custom_html = f"""
    <style>
    .top-scroll-wrapper {{
        width: 100%;
        overflow-x: auto;
        overflow-y: hidden;
        height: 18px;
        margin-bottom: 5px;
    }}
    .top-scroll-div {{
        height: 18px;
    }}
    </style>

    <div class="top-scroll-wrapper" id="top_{tabla_id}">
        <div class="top-scroll-div" id="top_div_{tabla_id}"></div>
    </div>
    
    <div class="tabla-ejecutiva-container" id="bot_{tabla_id}">
        {html_str}
    </div>

    <script>
    (function() {{
        const topWrapper = document.getElementById("top_{tabla_id}");
        const topDiv = document.getElementById("top_div_{tabla_id}");
        const botWrapper = document.getElementById("bot_{tabla_id}");
        const table = botWrapper.querySelector("table");

        if (table && topWrapper && botWrapper) {{
            topDiv.style.width = table.scrollWidth + "px";
            topWrapper.addEventListener("scroll", function() {{
                botWrapper.scrollLeft = topWrapper.scrollLeft;
            }});
            botWrapper.addEventListener("scroll", function() {{
                topWrapper.scrollLeft = botWrapper.scrollLeft;
            }});
        }}
    }})();
    </script>
    """
    st.components.v1.html(custom_html, height=350, scrolling=True)


def calcular_materiales_de_df_mo(df_mo_sub):
    """Función exacta que utiliza el Panel Ejecutivo para calcular materiales reales por proyecto y reportar actividades sin maestro."""
    if (
        df_contratistas is None
        or df_contratistas.empty
        or df_sap is None
        or df_sap.empty
        or df_mo_sub is None
        or df_mo_sub.empty
    ):
        return pd.DataFrame(), 0.0, []

    fuente_mat = df_contratistas.copy()
    col_act_mo = buscar_columna_segura(df_mo_sub, ["actividad", "código"])
    col_cant_mo = buscar_columna_segura(df_mo_sub, ["cantidad", "cant"])
    col_unds_mo = buscar_columna_segura(df_mo_sub, ["unds", "und", "unidad"])

    if not col_act_mo or not col_cant_mo:
        return pd.DataFrame(), 0.0, []

    df_mo_sub = df_mo_sub.copy()
    df_mo_sub["Actividad_Clean"] = (
        df_mo_sub[col_act_mo].fillna("").astype(str).str.strip().str.upper()
    )
    df_mo_sub["Cantidad_Num"] = (
        df_mo_sub[col_cant_mo].apply(parsear_numero_seguro).fillna(0)
    )

    if col_unds_mo:
        df_mo_sub["Unds_Clean"] = (
            df_mo_sub[col_unds_mo].fillna("").astype(str).str.strip().str.upper()
        )
        df_mo_fisico = df_mo_sub[
            ~df_mo_sub["Unds_Clean"].str.contains("HORA|HR")
        ].copy()
    else:
        df_mo_fisico = df_mo_sub[
            ~df_mo_sub["Actividad_Clean"].str.startswith(("HNBR", "DFAC"))
        ].copy()

    df_mo_agrupado = df_mo_fisico.groupby(
        "Actividad_Clean", as_index=False
    )["Cantidad_Num"].sum()
    dict_cant_mo = dict(
        zip(df_mo_agrupado["Actividad_Clean"], df_mo_agrupado["Cantidad_Num"])
    )

    col_act_mat = buscar_columna_segura(fuente_mat, ["actividad"])
    col_sap_mat = buscar_columna_segura(fuente_mat, ["sap", "código sap"])
    col_cant_mat = buscar_columna_segura(fuente_mat, ["cantidad", "cant"])

    if not col_act_mat or not col_sap_mat or not col_cant_mat:
        return pd.DataFrame(), 0.0, []

    fuente_mat["Actividad_Clean"] = (
        fuente_mat[col_act_mat].fillna("").astype(str).str.strip().str.upper()
    )

    # Detectar actividades en campo que NO existen en el archivo maestro de contratistas
    actividades_en_campo = set(dict_cant_mo.keys())
    actividades_en_maestro = set(fuente_mat["Actividad_Clean"].unique())
    actividades_sin_maestro = sorted(list(actividades_en_campo - actividades_en_maestro))

    fuente_mat["Clean_SAP"] = (
        fuente_mat[col_sap_mat]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )
    fuente_mat["Cantidad_Unitaria_Num"] = (
        fuente_mat[col_cant_mat].apply(parsear_numero_seguro).fillna(0)
    )

    fuente_mat = fuente_mat[
        ~fuente_mat["Clean_SAP"].isin(["", "NAN", "NONE", "0"])
    ]
    fuente_mat_clean = fuente_mat.groupby(
        ["Actividad_Clean", "Clean_SAP"], as_index=False
    )["Cantidad_Unitaria_Num"].first()

    df_filtrado = fuente_mat_clean[
        fuente_mat_clean["Actividad_Clean"].isin(dict_cant_mo.keys())
    ].copy()

    if df_filtrado.empty:
        return pd.DataFrame(), 0.0, actividades_sin_maestro

    df_filtrado["Cant_IDP"] = df_filtrado["Actividad_Clean"].map(dict_cant_mo)
    condicion_especial = (df_filtrado["Actividad_Clean"] == "1VA-MT") & (
        df_filtrado["Clean_SAP"] == "1000130"
    )
    df_filtrado["Cantidad_Total_Material"] = np.where(
        condicion_especial,
        df_filtrado["Cant_IDP"],
        df_filtrado["Cantidad_Unitaria_Num"] * df_filtrado["Cant_IDP"],
    )

    col_sap_prec = buscar_columna_segura(df_sap, ["sap", "código"])
    col_desc_sap = buscar_columna_segura(df_sap, ["descripci"])
    col_precio_final = buscar_columna_segura(df_sap, ["precio", "costo"])

    if not col_sap_prec or not col_desc_sap or not col_precio_final:
        return pd.DataFrame(), 0.0, actividades_sin_maestro

    df_sap_copy = df_sap.copy()
    df_sap_copy["Clean_SAP"] = (
        df_sap_copy[col_sap_prec]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )
    df_sap_copy["Descripcion_Oficial"] = (
        df_sap_copy[col_desc_sap].fillna("").astype(str)
    )
    df_sap_copy["Precio_Oficial"] = df_sap_copy[col_precio_final].apply(
        parsear_numero_seguro
    )

    df_sap_limpio = df_sap_copy[
        ["Clean_SAP", "Descripcion_Oficial", "Precio_Oficial"]
    ].drop_duplicates(subset=["Clean_SAP"])
    df_merge_sap = pd.merge(
        df_filtrado, df_sap_limpio, on="Clean_SAP", how="left"
    )

    df_resumen_mat = df_merge_sap.groupby(
        ["Clean_SAP", "Descripcion_Oficial"], as_index=False
    ).agg({"Cantidad_Total_Material": "sum", "Precio_Oficial": "first"})
    df_resumen_mat["Costo_Material"] = (
        df_resumen_mat["Cantidad_Total_Material"]
        * df_resumen_mat["Precio_Oficial"]
    )
    costo_total = df_resumen_mat["Costo_Material"].sum()

    return df_resumen_mat, costo_total, actividades_sin_maestro


# =====================================================================
# MÓDULO 1: PANEL EJECUTIVO POR PROYECTO (INTACTO)
# =====================================================================
if menu == "Panel Ejecutivo por Proyecto":
    if codigo_seleccionado != "Todos":
        cod_clean = str(codigo_seleccionado).strip()

        nombre_proyecto_str = cod_clean
        if df_codigos is not None and not df_codigos.empty:
            col_codigo_p = buscar_columna_segura(
                df_codigos, ["proyecto", "código", "codigo"]
            )
            col_desc_p = buscar_columna_segura(
                df_codigos, ["nombre", "descripci", "descripcion"]
            )
            if col_codigo_p and col_desc_p:
                df_codigos_copy = df_codigos.copy()
                df_codigos_copy["Clean_Cod"] = (
                    df_codigos_copy[col_codigo_p].astype(str).str.strip()
                )
                match_p = df_codigos_copy[df_codigos_copy["Clean_Cod"] == cod_clean]
                if not match_p.empty:
                    nombre_proyecto_str = (
                        f"{cod_clean} - {match_p.iloc[0][col_desc_p]}"
                    )

        st.markdown(
            f"<h4 style='color: #212529; margin-bottom: 15px;'>📌 PROYECTO: <b"
            f" style='color: #0d6efd;'>{nombre_proyecto_str}</b></h4>",
            unsafe_allow_html=True,
        )

        monto_mo = 0.0
        df_mo_proy = pd.DataFrame()
        if df_mo is not None and not df_mo.empty:
            col_proy_mo = buscar_columna_segura(
                df_mo, ["código proyecto", "codigo proyecto", "proyecto"]
            )
            col_costo_mo = buscar_columna_segura(
                df_mo, ["costo total", "monto total", "costo_total"]
            )

            if col_proy_mo and col_costo_mo:
                df_mo_proy = df_mo[
                    df_mo[col_proy_mo].astype(str).str.strip() == cod_clean
                ].copy()

                if "Fecha_Parsed" in df_mo_proy.columns:
                    if ano_sel != "Todos":
                        df_mo_proy = df_mo_proy[
                            df_mo_proy["Fecha_Parsed"].dt.year == int(ano_sel)
                        ]
                    if mes_sel != "Todos":
                        meses_dict = {
                            "Enero": 1,
                            "Febrero": 2,
                            "Marzo": 3,
                            "Abril": 4,
                            "Mayo": 5,
                            "Junio": 6,
                            "Julio": 7,
                            "Agosto": 8,
                            "Septiembre": 9,
                            "Octubre": 10,
                            "Noviembre": 11,
                            "Diciembre": 12,
                        }
                        df_mo_proy = df_mo_proy[
                            df_mo_proy["Fecha_Parsed"].dt.month
                            == meses_dict.get(mes_sel, 0)
                        ]

                monto_mo = df_mo_proy[col_costo_mo].apply(parsear_numero_seguro).sum()

        presupuesto_plan = 0.0
        if df_metas is not None and not df_metas.empty:
            col_proy_meta = buscar_columna_segura(df_metas, ["proyecto", "código"])
            col_presupuesto = buscar_columna_segura(df_metas, ["presupuesto"])

            if col_proy_meta and col_presupuesto:
                df_metas_copy = df_metas.copy()
                df_metas_copy["Clean_Proy"] = (
                    df_metas_copy[col_proy_meta].astype(str).str.strip()
                )
                df_meta_proy = df_metas_copy[df_metas_copy["Clean_Proy"] == cod_clean]
                if not df_meta_proy.empty:
                    presupuesto_plan = parsear_numero_seguro(
                        df_meta_proy.iloc[0][col_presupuesto]
                    )

        df_resumen_mat, costo_materiales_total, act_huerfanas = calcular_materiales_de_df_mo(
            df_mo_proy
        )
        
        if act_huerfanas:
            st.warning(f"🔍 **Auditoría:** Actividades reportadas en campo que NO poseen materiales en el maestro de contratistas: **{', '.join(act_huerfanas)}**")

        df_materiales_mostrador = pd.DataFrame()

        if not df_resumen_mat.empty:
            df_display = df_resumen_mat.copy()
            df_display["Cantidad Total"] = df_display["Cantidad_Total_Material"].apply(
                lambda x: f"{x:,.2f}"
            )
            df_display["Precio Unitario SAP"] = df_display["Precio_Oficial"].apply(
                lambda x: f"RD$ {x:,.2f}"
            )
            df_display["Costo Total"] = df_display["Costo_Material"].apply(
                lambda x: f"RD$ {x:,.2f}"
            )

            df_materiales_mostrador = df_display.rename(
                columns={
                    "Clean_SAP": "Código SAP",
                    "Descripcion_Oficial": "Descripción de Material",
                }
            )[
                [
                    "Código SAP",
                    "Descripción de Material",
                    "Cantidad Total",
                    "Precio Unitario SAP",
                    "Costo Total",
                ]
            ]

        df_mo_agrupado = pd.DataFrame()
        df_mo_fisico = pd.DataFrame()
        if not df_mo_proy.empty:
            col_act_mo = buscar_columna_segura(df_mo_proy, ["actividad", "código"])
            col_cant_mo = buscar_columna_segura(df_mo_proy, ["cantidad", "cant"])
            col_unds_mo = buscar_columna_segura(df_mo_proy, ["unds", "und", "unidad"])

            if col_act_mo and col_cant_mo:
                df_mo_proy["Actividad_Clean"] = (
                    df_mo_proy[col_act_mo].fillna("").astype(str).str.strip().str.upper()
                )
                df_mo_proy["Cantidad_Num"] = (
                    df_mo_proy[col_cant_mo].apply(parsear_numero_seguro).fillna(0)
                )
                df_mo_proy["Familia_Accion"] = (
                    df_mo_proy["Actividad_Clean"].map(dict_familia).fillna("OTRA")
                )

                if col_unds_mo:
                    df_mo_proy["Unds_Clean"] = (
                        df_mo_proy[col_unds_mo]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        .str.upper()
                    )
                    df_mo_fisico = df_mo_proy[
                        ~df_mo_proy["Unds_Clean"].str.contains("HORA|HR")
                    ].copy()
                else:
                    df_mo_fisico = df_mo_proy[
                        ~df_mo_proy["Actividad_Clean"].str.startswith(("HNBR", "DFAC"))
                    ].copy()

                df_mo_agrupado = df_mo_fisico.groupby(
                    ["Familia_Accion", "Actividad_Clean"], as_index=False
                )["Cantidad_Num"].sum()
                df_mo_agrupado.rename(
                    columns={
                        "Familia_Accion": "Familia / Acción",
                        "Actividad_Clean": "Actividad",
                        "Cantidad_Num": "Cantidad Ejecutada",
                    },
                    inplace=True,
                )

        df_avance_acciones = pd.DataFrame()
        if df_metas is not None and not df_metas.empty:
            col_proy_m = buscar_columna_segura(df_metas, ["proyecto", "código"])
            col_accion_meta = buscar_columna_segura(df_metas, ["accion", "actividad"])
            col_cant_plan = buscar_columna_segura(
                df_metas, ["cantidad", "planificada", "planificado"]
            )

            if col_proy_m and col_accion_meta and col_cant_plan:
                df_metas_copy2 = df_metas.copy()
                df_metas_copy2["Clean_P_Meta"] = (
                    df_metas_copy2[col_proy_m].astype(str).str.strip()
                )
                df_meta_proy_filt = df_metas_copy2[
                    df_metas_copy2["Clean_P_Meta"] == cod_clean
                ].copy()

                if not df_meta_proy_filt.empty:
                    df_meta_proy_filt["Acción"] = (
                        df_meta_proy_filt[col_accion_meta]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                    )
                    df_meta_proy_filt["Acción_Key"] = (
                        df_meta_proy_filt["Acción"].str.upper().str.strip()
                    )
                    df_meta_proy_filt["Planificado"] = (
                        df_meta_proy_filt[col_cant_plan]
                        .apply(parsear_numero_seguro)
                        .fillna(0)
                    )

                    if not df_mo_fisico.empty:
                        df_mo_fisico_copy = df_mo_fisico.copy()
                        df_mo_fisico_copy["Familia_Key"] = (
                            df_mo_fisico_copy["Familia_Accion"].str.upper().str.strip()
                        )
                        df_ejec_fam = df_mo_fisico_copy.groupby(
                            "Familia_Key", as_index=False
                        )["Cantidad_Num"].sum()
                        df_ejec_fam.rename(
                            columns={
                                "Familia_Key": "Acción_Key",
                                "Cantidad_Num": "Ejecutado",
                            },
                            inplace=True,
                        )
                    else:
                        df_ejec_fam = pd.DataFrame(columns=["Acción_Key", "Ejecutado"])

                    df_avance_acciones = pd.merge(
                        df_meta_proy_filt[["Acción", "Acción_Key", "Planificado"]],
                        df_ejec_fam[["Acción_Key", "Ejecutado"]],
                        on="Acción_Key",
                        how="left",
                    ).fillna(0)

                    df_avance_acciones = df_avance_acciones[
                        ["Acción", "Planificado", "Ejecutado"]
                    ]
                    df_avance_acciones["Num_Avance"] = np.where(
                        df_avance_acciones["Planificado"] > 0,
                        (
                            df_avance_acciones["Ejecutado"]
                            / df_avance_acciones["Planificado"]
                        )
                        * 100,
                        0.0,
                    )
                    df_avance_acciones["% Avance"] = df_avance_acciones[
                        "Num_Avance"
                    ].apply(lambda x: f"{x:.1f}%")

        total_ejecutado = monto_mo + costo_materiales_total
        porcentaje_ejecutado = (
            (total_ejecutado / presupuesto_plan * 100)
            if presupuesto_plan > 0
            else 0
        )

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Mano de Obra (RD$)", f"RD$ {monto_mo:,.2f}")
        c2.metric("Materiales Instalados (RD$)", f"RD$ {costo_materiales_total:,.2f}")
        c3.metric(
            "Monto Invertido en el Proyecto (RD$)", f"RD$ {total_ejecutado:,.2f}"
        )
        c4.metric("Presupuesto Plan. (RD$)", f"RD$ {presupuesto_plan:,.2f}")
        c5.metric("% Ejecución Est.", f"{porcentaje_ejecutado:.1f}%")

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
            mat_sin_p = df_resumen_mat[df_resumen_mat["Precio_Oficial"] == 0]
            if not mat_sin_p.empty:
                alerta_mat_txt = (
                    f"⚠️ Existen {len(mat_sin_p)} material(es) en campo con precio SAP"
                    " en $0.00 pendientes de actualización."
                )

        st.markdown(
            f"""
            <div class="resumen-gerencial-box">
                <h4>📋 Resumen Ejecutivo y Diagnóstico Gerencial</h4>
                <p>El proyecto <b>{nombre_proyecto_str}</b> presenta una inversión acumulada de <b>RD$ {total_ejecutado:,.2f}</b>, alcanzando un <b>{porcentaje_ejecutado:.1f}%</b> del presupuesto planificado (RD$ {presupuesto_plan:,.2f}), encontrándose {estado_presupuesto}. 
                En el ámbito físico, la ejecución de actividades muestra avances consolidados en campo. {alerta_mat_txt}</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        alertas = []
        if presupuesto_plan > 0 and total_ejecutado > presupuesto_plan:
            exceso = total_ejecutado - presupuesto_plan
            alertas.append(
                f"🚨 **Alerta Financiera (Riesgo Alto):** El monto invertido supera el"
                f" presupuesto planificado por **RD$ {exceso:,.2f}**"
                f" ({porcentaje_ejecutado:.1f}%)."
            )

        if not df_avance_acciones.empty:
            actividades_sobre = df_avance_acciones[
                df_avance_acciones["Num_Avance"] > 100
            ]
            if not actividades_sobre.empty:
                nombres_sobr = ", ".join([
                    f"**{r['Acción']}** ({r['% Avance']})"
                    for _, r in actividades_sobre.iterrows()
                ])
                alertas.append(
                    f"⚠️ **Desvío Físico (Riesgo Moderado):** Actividades con"
                    f" sobreejecución mayor al 100%: {nombres_sobr}."
                )

        if not df_resumen_mat.empty:
            mat_sin_precio = df_resumen_mat[df_resumen_mat["Precio_Oficial"] == 0]
            if not mat_sin_precio.empty:
                detalles_mat = [
                    f"**[{row['Clean_SAP']}] {row['Descripcion_Oficial']}**"
                    for _, row in mat_sin_precio.iterrows()
                ]
                alertas.append(
                    f"🔍 **Auditoría de Materiales (Atención Requerida):** Precios SAP"
                    f" en $0.00 para: {', '.join(detalles_mat)}."
                )

        if alertas:
            with st.container():
                for alt in alertas:
                    st.warning(alt)

        st.markdown("---")
        st.markdown("### 📊 Desglose Financiero y Operativo")

        df_grafico = pd.DataFrame({
            "Concepto": [
                "Mano de Obra",
                "Materiales Instalados",
                "Monto Invertido",
                "Presupuesto Plan.",
            ],
            "Monto (RD$)": [
                monto_mo,
                costo_materiales_total,
                total_ejecutado,
                presupuesto_plan,
            ],
        })
        df_grafico["Texto_Monto"] = df_grafico["Monto (RD$)"].apply(
            lambda x: f"RD$ {x:,.2f}"
        )

        mapa_colores_ejecutivo = {
            "Mano de Obra": "#1b365d",
            "Materiales Instalados": "#2b5c8f",
            "Monto Invertido": "#d97706",
            "Presupuesto Plan.": "#4b5563",
        }

        fig_bar = px.bar(
            df_grafico,
            x="Concepto",
            y="Monto (RD$)",
            color="Concepto",
            text="Texto_Monto",
            title="Comparativo Financiero del Proyecto",
            color_discrete_map=mapa_colores_ejecutivo,
        )
        fig_bar.update_traces(textposition="auto")
        fig_bar.update_layout(
            showlegend=True,
            xaxis_title="",
            template="plotly_white",
            margin=dict(l=20, r=20, t=40, b=20),
            height=400,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🎯 Avance Total (Planificado vs Ejecutado)")
        if not df_avance_acciones.empty:
            col_av_1, col_av_2 = st.columns([2.2, 1])

            with col_av_1:
                df_grafico_acc = df_avance_acciones.copy()
                df_grafico_acc["Es_Conductor"] = (
                    df_grafico_acc["Acción"].str.lower().str.contains("conductor")
                )

                df_grafico_acc["Text_Plan"] = df_grafico_acc["Planificado"].apply(
                    lambda x: f"{int(x):,}"
                )
                df_grafico_acc["Text_Ejec"] = df_grafico_acc["Ejecutado"].apply(
                    lambda x: f"{int(x):,}"
                )
                df_grafico_acc["Porc_Texto"] = df_grafico_acc["Num_Avance"].apply(
                    lambda x: f"{x:.0f}%"
                )

                fig_comb = make_subplots(specs=[[{"secondary_y": True}]])

                df_normal = df_grafico_acc[~df_grafico_acc["Es_Conductor"]]
                if not df_normal.empty:
                    fig_comb.add_trace(
                        go.Bar(
                            x=df_normal["Acción"],
                            y=df_normal["Planificado"],
                            name="Planificado",
                            marker_color="#1b365d",
                            text=df_normal["Text_Plan"],
                            textposition="auto",
                        ),
                        secondary_y=False,
                    )
                    fig_comb.add_trace(
                        go.Bar(
                            x=df_normal["Acción"],
                            y=df_normal["Ejecutado"],
                            name="Ejecutado",
                            marker_color="#2b5c8f",
                            text=df_normal["Text_Ejec"],
                            textposition="auto",
                        ),
                        secondary_y=False,
                    )

                df_cond = df_grafico_acc[df_grafico_acc["Es_Conductor"]]
                if not df_cond.empty:
                    fig_comb.add_trace(
                        go.Bar(
                            x=df_cond["Acción"],
                            y=df_cond["Planificado"],
                            name="Planificado (Metros)",
                            marker_color="#1b365d",
                            text=df_cond["Text_Plan"],
                            textposition="auto",
                        ),
                        secondary_y=True,
                    )
                    fig_comb.add_trace(
                        go.Bar(
                            x=df_cond["Acción"],
                            y=df_cond["Ejecutado"],
                            name="Ejecutado (Metros)",
                            marker_color="#2b5c8f",
                            text=df_cond["Text_Ejec"],
                            textposition="auto",
                        ),
                        secondary_y=True,
                    )

                fig_comb.add_trace(
                    go.Scatter(
                        x=df_grafico_acc["Acción"],
                        y=df_grafico_acc["Num_Avance"],
                        name="% Avance",
                        mode="lines+markers+text",
                        line=dict(color="#d97706", width=3),
                        marker=dict(size=8, color="#d97706"),
                        text=df_grafico_acc["Porc_Texto"],
                        textposition="top center",
                    ),
                    secondary_y=True,
                )

                fig_comb.update_layout(
                    title=f"Avance - {nombre_proyecto_str}",
                    barmode="group",
                    xaxis_title="",
                    template="plotly_white",
                    height=420,
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                    ),
                )
                fig_comb.update_yaxes(title_text="Magnitud Unidades", secondary_y=False)
                fig_comb.update_yaxes(
                    title_text="% Avance / Metros", secondary_y=True, range=[0, 130]
                )
                st.plotly_chart(fig_comb, use_container_width=True)

            with col_av_2:
                prom_avance_gen = df_avance_acciones["Num_Avance"].mean()
                faltante_gen = max(0, 100 - prom_avance_gen)

                fig_donut = go.Figure(
                    data=[
                        go.Pie(
                            labels=["% Avance", "% Faltante"],
                            values=[prom_avance_gen, faltante_gen],
                            hole=0.65,
                            marker=dict(colors=["#1b365d", "#ef4444"]),
                            textinfo="none",
                        )
                    ]
                )
                fig_donut.update_layout(
                    title=dict(
                        text="<b>Avance Global del Proyecto</b>",
                        x=0.5,
                        xanchor="center",
                    ),
                    annotations=[
                        dict(
                            text=f"<b>{prom_avance_gen:.1f}%</b>",
                            x=0.5,
                            y=0.5,
                            font_size=24,
                            showarrow=False,
                        )
                    ],
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.2,
                        xanchor="center",
                        x=0.5,
                    ),
                    height=420,
                    margin=dict(l=10, r=10, t=50, b=10),
                    template="plotly_white",
                )
                st.plotly_chart(fig_donut, use_container_width=True)

            df_tabla_avance_clean = pd.DataFrame()
            for _, row in df_avance_acciones.iterrows():
                df_tabla_avance_clean[row["Acción"]] = [
                    f"{int(row['Planificado']):,}",
                    f"{int(row['Ejecutado']):,}",
                    row["% Avance"],
                ]
            df_tabla_avance_clean.insert(
                0, "Métrica / Concepto", ["Planificado", "Ejecutado", "% Avance"]
            )
            mostrar_tabla_html_ejecutiva(df_tabla_avance_clean)
        else:
            st.info("No se encontraron metas planificadas para este proyecto.")

        st.markdown("---")
        with st.expander(
            "📋 Ver Auditoría Detallada de Mano de Obra (Ejecución en Campo)"
        ):
            if not df_mo_agrupado.empty:
                mostrar_tabla_html_ejecutiva(df_mo_agrupado)
            else:
                st.warning(
                    f"⚠️ No se encontraron registros de mano de obra para el código"
                    f" '{codigo_seleccionado}'."
                )

        with st.expander("🛠️ Ver Detalle de Materiales Instalados (SAP)"):
            if not df_materiales_mostrador.empty:
                mostrar_tabla_html_ejecutiva(df_materiales_mostrador)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df_materiales_mostrador.to_excel(
                        writer, index=False, sheet_name="Materiales Instalados"
                    )
                st.download_button(
                    label="📥 Descargar Materiales en Excel Real (.xlsx)",
                    data=output.getvalue(),
                    file_name=f"Materiales_Instalados_{cod_clean}.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    ),
                )
            else:
                st.info("No se encontraron materiales vinculados para este proyecto.")
    else:
        st.info("👈 Por favor seleccione un Código de Proyecto en el menú lateral.")


# =====================================================================
# MÓDULO 2: MAPA INTERACTIVO DE PROYECTOS (INTACTO Y SIN MODIFICACIONES)
# =====================================================================
elif menu == "Mapa Interactivo de Proyectos":
    st.subheader(
        "🗺️ Ubicación Geográfica de Proyectos en Zona de Concesión EDEESTE"
    )

    if df_codigos is not None and not df_codigos.empty:
        col_lat = buscar_columna_segura(df_codigos, ["lat", "latitud"])
        col_lon = buscar_columna_segura(df_codigos, ["lon", "longitud"])
        col_proy_map = buscar_columna_segura(
            df_codigos, ["proyecto", "código", "codigo"]
        )
        col_desc_map = buscar_columna_segura(
            df_codigos, ["nombre", "descripci", "descripcion"]
        )

        if col_lat and col_lon and col_proy_map:
            df_mapa = df_codigos.copy()
            df_mapa["Clean_Proy"] = df_mapa[col_proy_map].astype(str).str.strip()
            df_mapa["lat"] = df_mapa[col_lat].apply(parsear_numero_seguro)
            df_mapa["lon"] = df_mapa[col_lon].apply(parsear_numero_seguro)

            df_mapa = df_mapa[
                (df_mapa["lat"] != 0.0)
                & (df_mapa["lon"] != 0.0)
                & df_mapa["lat"].notna()
                & df_mapa["lon"].notna()
            ].copy()

            if not df_mapa.empty:
                monto_mo_dict = {}
                monto_mat_dict = {}

                if df_mo is not None and not df_mo.empty:
                    col_proy_mo = buscar_columna_segura(
                        df_mo, ["código proyecto", "codigo proyecto", "proyecto"]
                    )
                    col_costo_mo = buscar_columna_segura(
                        df_mo, ["costo total", "monto total", "costo_total"]
                    )

                    if col_proy_mo and col_costo_mo:
                        df_mo_copy = df_mo.copy()
                        df_mo_copy["Clean_Proy"] = (
                            df_mo_copy[col_proy_mo].astype(str).str.strip()
                        )
                        df_mo_copy["Costo_Num"] = df_mo_copy[col_costo_mo].apply(
                            parsear_numero_seguro
                        )

                        mo_group = df_mo_copy.groupby("Clean_Proy")["Costo_Num"].sum()
                        monto_mo_dict = mo_group.to_dict()

                        for pid in df_mapa["Clean_Proy"].unique():
                            df_sub_p = df_mo_copy[df_mo_copy["Clean_Proy"] == pid]
                            if not df_sub_p.empty:
                                _, c_mat, _ = calcular_materiales_de_df_mo(df_sub_p)
                                monto_mat_dict[pid] = c_mat

                df_mapa["Mano_Obra_RD"] = (
                    df_mapa["Clean_Proy"].map(monto_mo_dict).fillna(0.0)
                )
                df_mapa["Materiales_RD"] = (
                    df_mapa["Clean_Proy"].map(monto_mat_dict).fillna(0.0)
                )
                df_mapa["Inversion_Total_RD"] = (
                    df_mapa["Mano_Obra_RD"] + df_mapa["Materiales_RD"]
                )

                df_mapa["Nombre_Proyecto"] = (
                    df_mapa[col_desc_map].fillna("Sin nombre")
                    if col_desc_map
                    else df_mapa["Clean_Proy"]
                )

                def asignar_zona_por_coordenadas(lat, lon):
                    if 18.40 <= lat <= 18.50 and -69.72 <= lon <= -69.50:
                        return "Boca Chica / La Caleta"
                    elif 18.42 <= lat <= 18.52 and -69.95 <= lon <= -69.72:
                        return "Santo Domingo Este (SDE)"
                    elif 18.45 <= lat <= 18.58 and -69.83 <= lon <= -69.72:
                        return "San Luis / Guerra"
                    elif 18.43 <= lat <= 18.55 and -69.52 <= lon <= -69.25:
                        return "San Pedro de Macorís"
                    elif 18.50 <= lat <= 18.75 and -69.95 <= lon <= -69.70:
                        return "Santo Domingo Norte / Villa Mella"
                    elif 18.60 <= lat <= 19.10 and -70.15 <= lon <= -69.50:
                        return "Monte Plata / Yamasá"
                    elif 18.35 <= lat <= 18.55 and -69.25 <= lon <= -68.80:
                        return "La Romana / Higüey"
                    else:
                        return "Zona EDEESTE (General)"

                df_mapa["Zona_Nombre"] = df_mapa.apply(
                    lambda r: asignar_zona_por_coordenadas(r["lat"], r["lon"]), axis=1
                )

                if codigo_seleccionado != "Todos":
                    df_mapa = df_mapa[
                        df_mapa["Clean_Proy"] == str(codigo_seleccionado).strip()
                    ]

                if not df_mapa.empty:
                    df_mapa["Hover_Txt"] = df_mapa.apply(
                        lambda r: (
                            f"<b>Proyecto:</b> {r['Clean_Proy']} - {r['Nombre_Proyecto']}<br>"
                            f"<b>Zona Detectada:</b> {r['Zona_Nombre']}<br>"
                            f"<b>Mano de Obra:</b> RD$ {r['Mano_Obra_RD']:,.2f}<br>"
                            f"<b>Materiales SAP:</b> RD$ {r['Materiales_RD']:,.2f}<br>"
                            f"<b>Inversión Total:</b> RD$"
                            f" {r['Inversion_Total_RD']:,.2f}"
                        ),
                        axis=1,
                    )

                    lat_center = (
                        df_mapa["lat"].mean()
                        if codigo_seleccionado == "Todos"
                        else df_mapa["lat"].iloc[0]
                    )
                    lon_center = (
                        df_mapa["lon"].mean()
                        if codigo_seleccionado == "Todos"
                        else df_mapa["lon"].iloc[0]
                    )
                    zoom_level = 9.2 if codigo_seleccionado == "Todos" else 13.0

                    fig_map = go.Figure(
                        go.Scattermap(
                            lat=df_mapa["lat"],
                            lon=df_mapa["lon"],
                            mode="markers",
                            marker=dict(size=16, color="#0d6efd", opacity=0.9),
                            hoverinfo="text",
                            text=df_mapa["Hover_Txt"],
                        )
                    )

                    fig_map.update_layout(
                        map=dict(
                            style="open-street-map",
                            center=dict(lat=lat_center, lon=lon_center),
                            zoom=zoom_level,
                        ),
                        margin={"r": 0, "t": 10, "l": 0, "b": 0},
                        height=550,
                    )

                    st.plotly_chart(fig_map, use_container_width=True)

                    st.markdown("---")
                    st.markdown(
                        "### 🏙️ Resumen de Inversión Presupuestaria por Zona (Geolocalizada)"
                    )

                    df_resumen_zona = (
                        df_mapa.groupby("Zona_Nombre", as_index=False)
                        .agg({
                            "Clean_Proy": "count",
                            "Mano_Obra_RD": "sum",
                            "Materiales_RD": "sum",
                            "Inversion_Total_RD": "sum",
                        })
                        .rename(
                            columns={
                                "Zona_Nombre": "Zona / Municipio Detectado",
                                "Clean_Proy": "Cantidad de Proyectos",
                            }
                        )
                    )

                    df_resumen_zona_disp = df_resumen_zona.copy()
                    df_resumen_zona_disp["Mano de Obra"] = df_resumen_zona_disp[
                        "Mano_Obra_RD"
                    ].apply(lambda x: f"RD$ {x:,.2f}")
                    df_resumen_zona_disp["Materiales SAP"] = df_resumen_zona_disp[
                        "Materiales_RD"
                    ].apply(lambda x: f"RD$ {x:,.2f}")
                    df_resumen_zona_disp["Inversión Total"] = df_resumen_zona_disp[
                        "Inversion_Total_RD"
                    ].apply(lambda x: f"RD$ {x:,.2f}")

                    df_resumen_zona_disp = df_resumen_zona_disp[
                        [
                            "Zona / Municipio Detectado",
                            "Cantidad de Proyectos",
                            "Mano de Obra",
                            "Materiales SAP",
                            "Inversión Total",
                        ]
                    ]

                    mostrar_tabla_html_ejecutiva(df_resumen_zona_disp)
                else:
                    st.warning(
                        f"⚠️ El proyecto '{codigo_seleccionado}' no posee coordenadas"
                        " geográficas para graficar."
                    )
            else:
                st.warning("⚠️ No se encontraron coordenadas válidas en el archivo.")
        else:
            st.error(
                "⚠️ Faltan columnas de Latitud, Longitud o Código en 'Codigos de"
                " proyectos.xlsx'."
            )
    else:
        st.warning("⚠️ Archivo de Códigos de Proyecto no cargado.")

# =====================================================================
# MÓDULO 3: AUDITORÍA DE ALMACÉN (COCCIA) — MATRIZ CRUZADA Y AUDITORÍA
# =====================================================================
elif menu == "Auditoría de Almacén (Coccia)":
    st.subheader(
        "📦 Auditoría de Materiales por Almacén — Contratista COCCIA (Desglose por"
        " Proyecto)"
    )
    st.markdown(
        "Este módulo presenta de manera limpia y estructurada la mano de obra"
        " ejecutada exclusivamente por **COCCIA** por cada proyecto, sus"
        " materiales calculados, y la **Matriz Cruzada Global** consolidada."
    )

    if df_mo is not None and df_contratistas is not None and df_sap is not None:
        col_contratista = buscar_columna_segura(
            df_mo, ["contrata", "contratista", "empresa", "proveedor"]
        )

        if col_contratista is None:
            st.error(
                "⚠️ No se encontró la columna de Contratista/Contrata en el archivo"
                " de Mano de Obra."
            )
            st.stop()

        df_mo_coccia_puro = df_mo[
            df_mo[col_contratista]
            .astype(str)
            .str.upper()
            .str.strip()
            .eq("COCCIA")
        ].copy()

        if "Fecha_Parsed" in df_mo_coccia_puro.columns:
            if ano_sel != "Todos":
                df_mo_coccia_puro = df_mo_coccia_puro[
                    df_mo_coccia_puro["Fecha_Parsed"].dt.year == int(ano_sel)
                ]
            if mes_sel != "Todos":
                meses_dict = {
                    "Enero": 1,
                    "Febrero": 2,
                    "Marzo": 3,
                    "Abril": 4,
                    "Mayo": 5,
                    "Junio": 6,
                    "Julio": 7,
                    "Agosto": 8,
                    "Septiembre": 9,
                    "Octubre": 10,
                    "Noviembre": 11,
                    "Diciembre": 12,
                }
                df_mo_coccia_puro = df_mo_coccia_puro[
                    df_mo_coccia_puro["Fecha_Parsed"].dt.month
                    == meses_dict.get(mes_sel, 0)
                ]

        if df_mo_coccia_puro.empty:
            st.warning(
                "⚠️ No se encontraron registros de mano de obra exclusivos para"
                " COCCIA con los filtros seleccionados."
            )
            st.stop()

        col_proy_mo = buscar_columna_segura(
            df_mo_coccia_puro, ["código proyecto", "codigo proyecto", "proyecto"]
        )
        if not col_proy_mo:
            col_proy_mo = df_mo_coccia_puro.columns[-2]

        col_desc_proy_mo = buscar_columna_segura(
            df_mo_coccia_puro, ["nombre proyect", "nombre proyecto", "descripcion"]
        )

        proyectos_de_coccia = sorted(
            df_mo_coccia_puro[col_proy_mo]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )

        st.markdown("---")
        st.markdown(
            "### 🏗️ Desglose por Proyecto de Coccia (Mano de Obra y Materiales)"
        )

        lista_df_materiales_todos = []
        todas_actividades_huerfanas = set()

        for proj_id in proyectos_de_coccia:
            df_mo_un_proyecto = df_mo_coccia_puro[
                df_mo_coccia_puro[col_proy_mo].astype(str).str.strip() == proj_id
            ].copy()

            nombre_proj_desc = proj_id
            if col_desc_proy_mo and not df_mo_un_proyecto.empty:
                nombres_unicos = (
                    df_mo_un_proyecto[col_desc_proy_mo].dropna().astype(str).unique()
                )
                if len(nombres_unicos) > 0:
                    nombre_proj_desc = f"{proj_id} — {nombres_unicos[0]}"

            with st.expander(f"📁 Proyecto: {nombre_proj_desc}", expanded=False):
                st.markdown("##### 👷 Mano de Obra Ejecutada (Coccia)")
                col_act_mo = buscar_columna_segura(df_mo_un_proyecto, ["actividad", "código"])
                col_cant_mo = buscar_columna_segura(df_mo_un_proyecto, ["cantidad", "cant"])

                if col_act_mo and col_cant_mo:
                    df_mo_un_proyecto["Actividad_Clean"] = (
                        df_mo_un_proyecto[col_act_mo]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        .str.upper()
                    )
                    df_mo_un_proyecto["Cantidad_Num"] = (
                        df_mo_un_proyecto[col_cant_mo]
                        .apply(parsear_numero_seguro)
                        .fillna(0)
                    )
                    df_mo_resumen_proj = df_mo_un_proyecto.groupby(
                        "Actividad_Clean", as_index=False
                    )["Cantidad_Num"].sum()
                    df_mo_resumen_proj.rename(
                        columns={
                            "Actividad_Clean": "Actividad",
                            "Cantidad_Num": "Cantidad Ejecutada",
                        },
                        inplace=True,
                    )
                    mostrar_tabla_html_ejecutiva(df_mo_resumen_proj)
                else:
                    st.info("No se pudo estructurar el detalle de mano de obra.")

                st.markdown("##### 🛠️ Materiales SAP Correspondientes")
                df_mat_proj, costo_proj, huerfanas_p = calcular_materiales_de_df_mo(df_mo_un_proyecto)

                if huerfanas_p:
                    todas_actividades_huerfanas.update(huerfanas_p)
                    st.warning(f"🔍 **Actividades sin Maestro de Materiales en este proyecto:** {', '.join(huerfanas_p)}")

                if not df_mat_proj.empty:
                    df_mat_proj["Clean_Proy"] = proj_id
                    lista_df_materiales_todos.append(df_mat_proj)

                    df_mat_display = df_mat_proj.copy()
                    df_mat_display["Cantidad Requerida"] = df_mat_display[
                        "Cantidad_Total_Material"
                    ].apply(lambda x: f"{x:,.2f}")
                    df_mat_display["Precio Unitario SAP"] = df_mat_display[
                        "Precio_Oficial"
                    ].apply(lambda x: f"RD$ {x:,.2f}")
                    df_mat_display["Costo Total Material"] = df_mat_display[
                        "Costo_Material"
                    ].apply(lambda x: f"RD$ {x:,.2f}")

                    df_mat_display = df_mat_display.rename(
                        columns={
                            "Clean_SAP": "Código SAP",
                            "Descripcion_Oficial": "Descripción de Material",
                        }
                    )[
                        [
                            "Código SAP",
                            "Descripción de Material",
                            "Cantidad Requerida",
                            "Precio Unitario SAP",
                            "Costo Total Material",
                        ]
                    ]
                    mostrar_tabla_html_ejecutiva(df_mat_display)
                else:
                    st.info("Este proyecto no generó materiales teóricos asociados.")

        if todas_actividades_huerfanas:
            st.error(f"⚠️ **Resumen Global de Auditoría:** Se detectaron {len(todas_actividades_huerfanas)} actividades ejecutadas en campo que NO poseen materiales asignados en el archivo 'Actividades contratistas.xlsx': **{', '.join(sorted(list(todas_actividades_huerfanas)))}**")

        st.markdown("---")
        st.markdown("### 📊 AUDITORÍA DE ALMACÉN — MATRIZ CRUZADA (CONSOLIDADO COCCIA)")

        if len(lista_df_materiales_todos) > 0:
            df_todos_unidos = pd.concat(lista_df_materiales_todos, ignore_index=True)
            
            pivot_matriz = df_todos_unidos.pivot_table(
                index=['Clean_SAP', 'Descripcion_Oficial', 'Precio_Oficial'],
                columns='Clean_Proy',
                values='Cantidad_Total_Material',
                aggfunc='sum',
                fill_value=0.0
            ).reset_index()

            pivot_matriz.columns.name = None
            cols_proyectos = [c for c in pivot_matriz.columns if c not in ['Clean_SAP', 'Descripcion_Oficial', 'Precio_Oficial']]
            
            pivot_matriz['Cantidad Total Global'] = pivot_matriz[cols_proyectos].sum(axis=1)
            pivot_matriz['Costo Total Global'] = pivot_matriz['Cantidad Total Global'] * pivot_matriz['Precio_Oficial']

            cols_ordenadas = ['Clean_SAP', 'Descripcion_Oficial', 'Precio_Oficial'] + cols_proyectos + ['Cantidad Total Global', 'Costo Total Global']
            pivot_final = pivot_matriz[[c for c in cols_ordenadas if c in pivot_matriz.columns]]

            pivot_display = pd.DataFrame()
            pivot_display["Código SAP"] = pivot_final["Clean_SAP"]
            pivot_display["Descripción de Material"] = pivot_final["Descripcion_Oficial"]
            pivot_display["Precio Unitario SAP"] = pivot_final["Precio_Oficial"].apply(lambda x: f"RD$ {x:,.2f}")

            for cp in cols_proyectos:
                pivot_display[cp] = pivot_final[cp].apply(lambda x: f"{x:,.2f}" if x > 0 else "0.00")

            pivot_display["Cantidad Total Global"] = pivot_final["Cantidad Total Global"].apply(lambda x: f"{x:,.2f}")
            pivot_display["Costo Total Global"] = pivot_final["Costo Total Global"].apply(lambda x: f"RD$ {x:,.2f}")

            costo_global_pesos = pivot_final["Costo Total Global"].sum()

            st.metric(
                "💰 Costo Total de Almacén (Consolidado Coccia)",
                f"RD$ {costo_global_pesos:,.2f}",
            )

            mostrar_tabla_html_ejecutiva(pivot_display)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                pivot_final.to_excel(
                    writer, index=False, sheet_name="Matriz_Cruzada_Coccia"
                )

            st.download_button(
                label="📥 Descargar Matriz Cruzada de Almacén (.xlsx)",
                data=buffer.getvalue(),
                file_name="Matriz_Cruzada_Almacen_Coccia.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
            )
        else:
            st.warning("No hay materiales consolidados para mostrar.")
    else:
        st.error("Faltan archivos base para realizar la auditoría.")
