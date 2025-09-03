import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from io import BytesIO


# Inicializar session state 
if 'facturas_rows' not in st.session_state:
    st.session_state.facturas_rows = 1

# Función para agregar una nueva fila
def agregar_fila():
    st.session_state.facturas_rows += 1

# Función para eliminar la última fila
def eliminar_fila():
    if st.session_state.facturas_rows > 1:
        st.session_state.facturas_rows -= 1

encabezado_superior = st.columns([0.20, 0.70, 0.20], vertical_alignment="bottom")

with encabezado_superior[0]:
    st.image('logo.png', width=150)
with encabezado_superior[1]:
    st.header('Inmobiliaria ALMEST \n UBI Obras Varias')
with encabezado_superior[2]:
    st.date_input(' ', format='DD/MM/YYYY')

st.write('Certificamos que los valores de las facturas que se relacionan corresponden a los  documentos legales debidamente autorizados y que se ajustan a la obra de referencia.')
st.text_input('No. Contrato')
st.text_input('Contratista')

data_obras = pd.DataFrame(
    {
    "Obras": ['Mejoras Cayo Saetía', 'Marina Cayo Saetía', 'Viviendas Mayarí', 'Delfinario Cayo Saetía', 'Canal Dumois'], 
    "Código de Obra": [759, 677, 699, 605, 872],
    "Aprobación": ['A 37-018-15', 'A 37-024-19', 'A 37-037-20', 'A 37-025-19', 'A 37-038-21'],   
})

obras = st.selectbox('Obra',data_obras["Obras"], index=None, placeholder="Despliegue y seleccione una Obra")

# Cuando se selecciona una obra
if obras:
    # Filtrar el DataFrame por la obra seleccionada
    obra_seleccionada = data_obras[data_obras["Obras"] == obras]
    
    # Verificar que se encontró la obra
    if not obra_seleccionada.empty:

        # Obtener el código de obra seleccionada
        codigo_obra = obra_seleccionada["Código de Obra"].iloc[0]

        col1, col2, col3 = st.columns([1, 1, 1])

        with col2:

            # Mostrar el código concatenado con el nombre de la Obra.
            st.write(f"Obra {codigo_obra}  {obra_seleccionada['Obras'].iloc[0]}")

        # Obtener la Aprobación de la obra en cuestión
        aprobacion = obra_seleccionada["Aprobación"].iloc[0]  
        
        col1, col2 = st.columns([2, 1])

        with col1:
            # Mostrar el resultado
            st.write(f"Aprobación: {aprobacion}")

        with col2:            
            # Mostrar el código del objeto de obra                    
            st.write(f"CODIGO DE OBRA  {codigo_obra}02")        
    else:
        st.warning("No se encontraron datos para esta obra")

valor_contrato = st.number_input(
    'Valor Total del Contrato (CUP):',  # Etiqueta
    min_value=0.0,                      # Valor mínimo
    max_value=1000000000.0,            # Valor máximo (opcional)
    value=0.0,                         # Valor por defecto
    step=1000.0,                       # Incremento
    format="%.2f",                     # Formato (2 decimales)
    help="Introduzca el monto total del contrato en CUP"
)

valor_pagado = st.number_input(
    'Valor Total Certificado (CUP):',  # Etiqueta
    min_value=0.0,                      # Valor mínimo
    max_value=1000000000.0,            # Valor máximo (opcional)
    value=0.0,                         # Valor por defecto
    step=1000.0,                       # Incremento
    format="%.2f",                     # Formato (2 decimales)
    help="Introduzca el monto total del contrato en CUP"
)


# Botones para agregar/eliminar filas
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
with col_btn1:
    st.button("➕ Agregar Factura", on_click=agregar_fila)
with col_btn2:
    st.button("➖ Eliminar Factura", on_click=eliminar_fila)

st.divider()

# Crear las filas de facturas
for i in range(st.session_state.facturas_rows):
    st.markdown(f"**Factura No {i+1}**")
    proovedores, facturas, importe, codigo = st.columns([2, 2, 1.5, 1])
    
    with proovedores:
        st.text_input(f"Proveedor", key=f"proveedor_{i}")
        
    with facturas:
        st.text_input(f"Factura", key=f"factura_{i}")
        
    with importe:
        importe_factura = st.number_input(f"Importe", 
                                        format="%.2f", 
                                        step=1000.0,
                                        key=f"importe_{i}")
        # Mostrar importe formateado
        if importe_factura > 0:
            st.write(f"{importe_factura:,.2f} CUP")
    
    with codigo:
        st.text_input(f"Código", key=f"codigo_{i}")
    
    st.divider()  # Línea divisoria entre filas

# Calcular y mostrar el total de todas las facturas
total_facturas = 0.0
for i in range(st.session_state.facturas_rows):
    # Obtener el valor del importe de cada factura
    importe_key = f"importe_{i}"
    if importe_key in st.session_state:
        total_facturas += st.session_state[importe_key]

# Mostrar el total formateado
st.markdown("---")
col_total1, col_total2, col_total3 = st.columns([1.1, 2, 2])
with col_total2:
    st.markdown("**TOTAL DE FACTURAS:**")
with col_total3:
    st.markdown(f"**{total_facturas:,.2f} CUP**")
    st.divider( )

st.write(" ")
st.write(" ")
st.write(" ")

pie1, pie2, pie3 = st.columns([1,1,1.5])

with pie1:
    st.write("Firma:")
    st.write("Especialista en Inversiones")
    st.write("Ing. Yenny Sánchez Aguilar")
    
    
with pie3:
    st.write("Firma:")
    st.write("Jefe de Grupo Técnico UBI Obras Varias.")
    st.write("Ing. Osvaldo Sánchez Breff")
    