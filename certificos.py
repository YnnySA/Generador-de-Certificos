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

# Función para crear el informe en Excel
def generar_informe_excel(datos):
    try:
        # Cargar la plantilla 
        wb = load_workbook('data/ejemplo.xlsx')
        ws = wb.active
        
        # Llenar los datos en las celdas correspondientes
        # Nota: Las celdas deben coincidir con la estructura de tu plantilla
        # Ajusta estas referencias según tu archivo real
        
        # Fecha 
        if datos['fecha']:
            ws['E6'] = datos['fecha']
            
        # Contrato 
        if datos['contrato']:
            ws['B13'] = datos['contrato']
            
        # Contratista 
        if datos['contratista']:
            ws['B16'] = datos['contratista']
            
        # Obra 
        if datos['obra']:
            ws['B16'] = datos['obra']
        
        if datos['codigo_obra'] is not None: # Verificar que el código de obra exista
            ws['E18'] = f"{datos['codigo_obra']}"
            
        # Aprobación (celda A19 en la imagen)
        if datos['aprobacion']:
            ws['B18'] = datos['aprobacion']
            
        # Valor total contrato (celda A23 en la imagen)
        if datos['valor_contrato']:
            ws['C20'] = f"{datos['valor_contrato']:,.2f}"
            
        # Valor pagado (celda A25 en la imagen)
        if datos['valor_pagado']:
            ws['C22'] = f"{datos['valor_pagado']:,.2f}"
            
        # Insertar las facturas comenzando desde la fila 28 (ajusta según tu plantilla)
        fila_inicio_facturas = 26
        for i, factura in enumerate(datos['facturas']):
            fila = fila_inicio_facturas + i
            if fila <= ws.max_row:
                ws[f'A{fila}'] = factura['proveedor']
                ws[f'C{fila}'] = factura['factura']
                ws[f'E{fila}'] = factura['importe']
                ws[f'F{fila}'] = factura['codigo']
            else:
                # Si hay más filas, agregarlas
                ws.append([factura['proveedor'], factura['factura'], factura['importe'], factura['codigo']])
        
        # Total de facturas (celda E35 en la imagen, aproximadamente)
        ws['E32'] = f"{datos['total_facturas']:,.2f} CUP"
        
        # Guardar el archivo en memoria
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return output
    except Exception as e:
        st.error(f"Error al generar el informe: {str(e)}")
        return None

encabezado_superior = st.columns([0.20, 0.70, 0.20], vertical_alignment="bottom")

with encabezado_superior[0]:
    st.image('logo.png', width=150)
with encabezado_superior[1]:
    st.header('Inmobiliaria ALMEST \n UBI Obras Varias')
with encabezado_superior[2]:
    fecha = st.date_input(' ', format='DD/MM/YYYY')

st.write('Certificamos que los valores de las facturas que se relacionan corresponden a los  documentos legales debidamente autorizados y que se ajustan a la obra de referencia.')
contrato = st.text_input('No. Contrato')
contratista = st.text_input('Contratista')

data_obras = pd.DataFrame(
    {
    "Obras": ['Mejoras Cayo Saetía', 'Marina Cayo Saetía', 'Viviendas Mayarí', 'Delfinario Cayo Saetía', 'Canal Dumois'], 
    "Código de Obra": [759, 677, 699, 605, 872],
    "Aprobación": ['A 37-018-15', 'A 37-024-19', 'A 37-037-20', 'A 37-025-19', 'A 37-038-21'],   
})

obras = st.selectbox('Obra',data_obras["Obras"], index=None, placeholder="Despliegue y seleccione una Obra")

# Variables para almacenar datos de la obra seleccionada
codigo_obra = None
nombre_obra = None
aprobacion = None

# Cuando se selecciona una obra
if obras:
    # Filtrar el DataFrame por la obra seleccionada
    obra_seleccionada = data_obras[data_obras["Obras"] == obras]
    
    # Verificar que se encontró la obra
    if not obra_seleccionada.empty:
        # Obtener el código de obra seleccionada
        codigo_obra = obra_seleccionada["Código de Obra"].iloc[0]
        nombre_obra = obra_seleccionada["Obras"].iloc[0]
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            # Mostrar el código concatenado con el nombre de la Obra.
            st.write(f"Obra {codigo_obra}  {nombre_obra}")

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
    'Valor Total del Contrato (CUP):',
    min_value=0.0,
    max_value=1000000000.0,
    value=0.0,
    step=1000.0,
    format="%.2f",
    help="Introduzca el monto total del contrato en CUP"
)

valor_pagado = st.number_input(
    'Valor Total Certificado (CUP):',
    min_value=0.0,
    max_value=1000000000.0,
    value=0.0,
    step=1000.0,
    format="%.2f",
    help="Introduzca el monto total del contrato en CUP"
)

# Botones para agregar/eliminar filas
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
with col_btn1:
    st.button("➕ Agregar Factura", on_click=agregar_fila)
with col_btn2:
    st.button("➖ Eliminar Factura", on_click=eliminar_fila)

st.divider()

# Listas para almacenar datos de facturas
facturas_data = []

# Crear las filas de facturas
for i in range(st.session_state.facturas_rows):
    st.markdown(f"**Factura No {i+1}**")
    proovedores, facturas, importe, codigo = st.columns([2, 2, 1.5, 1])
    
    with proovedores:
        proveedor_val = st.text_input(f"Proveedor", key=f"proveedor_{i}")
        
    with facturas:
        factura_val = st.text_input(f"Factura", key=f"factura_{i}")
        
    with importe:
        importe_factura = st.number_input(f"Importe", 
                                        format="%.2f", 
                                        step=1000.0,
                                        key=f"importe_{i}")
        # Mostrar importe formateado
        if importe_factura > 0:
            st.write(f"{importe_factura:,.2f} CUP")
    
    with codigo:
        codigo_val = st.text_input(f"Código", key=f"codigo_{i}")
    
    # Almacenar datos de la factura
    facturas_data.append({
        'proveedor': proveedor_val,
        'factura': factura_val,
        'importe': importe_factura,
        'codigo': codigo_val
    })
    
    st.divider()

# Calcular y mostrar el total de todas las facturas
total_facturas = sum(f['importe'] for f in facturas_data)

# Mostrar el total formateado
st.markdown("---")
col_total1, col_total2, col_total3 = st.columns([1.1, 2, 2])
with col_total2:
    st.markdown("**TOTAL DE FACTURAS:**")
with col_total3:
    st.markdown(f"**{total_facturas:,.2f} CUP**")
    st.divider()

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

# Botón para generar el informe
st.markdown("---")
if st.button("📄 Generar Informe en Excel"):
    # Recopilar todos los datos
    datos_informe = {
        'fecha': fecha,
        'contrato': contrato,
        'contratista': contratista,
        'obra': f"{codigo_obra} {nombre_obra}" if codigo_obra and nombre_obra else "",
        'codigo_obra': f"{codigo_obra}02" if codigo_obra else "",
        'nombre_obra': nombre_obra,
        'aprobacion': aprobacion,
        'valor_contrato': valor_contrato,
        'valor_pagado': valor_pagado,
        'facturas': facturas_data,
        'total_facturas': total_facturas
    }
    
    # Generar el informe
    excel_data = generar_informe_excel(datos_informe)
    
    if excel_data:
        # Ofrecer el archivo para descargar
        st.download_button(
            label="📥 Descargar Informe",
            data=excel_data,
            file_name="Certificado_Facturas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )