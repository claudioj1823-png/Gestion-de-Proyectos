import streamlit as st
import pandas as pd

st.set_page_config(page_title="Panel Ejecutivo - EDEESTE", layout="wide")

st.title("⚡ Panel de Control y Gestión de Proyectos - EDEESTE")
st.markdown("---")

st.sidebar.header("Navegación")
menu = st.sidebar.selectbox("Seleccione una vista:", ["Resumen Ejecutivo", "Presupuestos y Metas", "Seguimiento de Contratistas"])

if menu == "Resumen Ejecutivo":
    st.subheader("📊 Resumen Global de Proyectos")
    st.info("Bienvenido al panel ejecutivo. Sube tus archivos o conecta los datos para visualizar el avance global, presupuestos y ejecución de EDEESTE.")
    
    # Widget para cargar archivos directamente si GitHub web falla
    uploaded_file = st.file_uploader("Cargar archivo de códigos o proyectos (.xlsx)", type=["xlsx"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.write("Vista previa de los datos cargados:")
        st.dataframe(df)

elif menu == "Presupuestos y Metas":
    st.subheader("🎯 Control de Metas y Presupuestos Sap")
    st.write("Aquí se visualizarán los análisis de costos y cumplimiento de metas.")

else:
    st.subheader("👷 Seguimiento de Actividades y Contratistas")
    st.write("Control detallado de cuadrillas, mano de obra y avances en campo.")
