import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from io import BytesIO
import sqlite3
import os
from datetime import datetime

# Inicializar session state 
if 'facturas_rows' not in st.session_state:
    st.session_state.facturas_rows = 1

# Configuración de la base de datos y directorios
DB_NAME = "certificados.db"
EXCEL_TEMPLATES_DIR = "data"
CERTIFICADOS_DIR = "certificados_generados"

# Crear directorios necesarios
os.makedirs(EXCEL_TEMPLATES_DIR, exist_ok=True)
os.makedirs(CERTIFICADOS_DIR, exist_ok=True)

# Inicializar la base de datos
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Crear tabla para obras
    c.execute('''CREATE TABLE IF NOT EXISTS obras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        codigo INTEGER NOT NULL,
        aprobacion TEXT NOT NULL
    )''')
    
    # Crear tabla para certificados (con UNIQUE constraint correcta)
    c.execute('''CREATE TABLE IF NOT EXISTS certificados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_certificado INTEGER NOT NULL,
        obra_id INTEGER,
        fecha DATE NOT NULL,
        contrato TEXT,
        contratista TEXT,
        valor_contrato REAL,
        valor_pagado REAL,
        total_facturas REAL,
        archivo_path TEXT,
        fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (obra_id) REFERENCES obras (id),
        UNIQUE(obra_id, numero_certificado)
    )''')
    
    # Crear tabla para facturas
    c.execute('''CREATE TABLE IF NOT EXISTS facturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        certificado_id INTEGER,
        proveedor TEXT NOT NULL,
        numero_factura TEXT NOT NULL,
        importe REAL NOT NULL,
        codigo TEXT,
        FOREIGN KEY (certificado_id) REFERENCES certificados (id)
    )''')
    
    # Insertar obras iniciales si no existen
    obras_iniciales = [
        ('Mejoras Cayo Saetía', 759, 'A 37-018-15'),
        ('Marina Cayo Saetía', 677, 'A 37-024-19'),
        ('Viviendas Mayarí', 699, 'A 37-037-20'),
        ('Delfinario Cayo Saetía', 605, 'A 37-025-19'),
        ('Canal Dumois', 872, 'A 37-038-21')
    ]
    
    for nombre, codigo, aprobacion in obras_iniciales:
        try:
            c.execute("INSERT INTO obras (nombre, codigo, aprobacion) VALUES (?, ?, ?)",
                     (nombre, codigo, aprobacion))
        except sqlite3.IntegrityError:
            pass  # La obra ya existe
    
    conn.commit()
    conn.close()

# Función para obtener el siguiente número de certificado PARA UNA OBRA ESPECÍFICA
def get_next_certificado_number_por_obra(obra_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Obtiene el máximo número de certificado para la obra dada
    c.execute("SELECT MAX(numero_certificado) FROM certificados WHERE obra_id = ?", (obra_id,))
    result = c.fetchone()[0]
    conn.close()
    # Si no hay certificados para esta obra, el siguiente es 1
    return (result or 0) + 1

# Función para obtener todas las obras
def get_all_obras():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, nombre, codigo, aprobacion FROM obras ORDER BY nombre")
    obras = c.fetchall()
    conn.close()
    return obras

# Función para obtener un certificado por ID
def get_certificado_by_id(certificado_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT c.*, o.nombre as obra_nombre, o.codigo as obra_codigo, o.aprobacion 
                 FROM certificados c 
                 JOIN obras o ON c.obra_id = o.id 
                 WHERE c.id = ?""", (certificado_id,))
    certificado = c.fetchone()
    conn.close()
    return certificado

# Función para obtener facturas de un certificado
def get_facturas_by_certificado_id(certificado_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT proveedor, numero_factura, importe, codigo FROM facturas WHERE certificado_id = ? ORDER BY id", 
              (certificado_id,))
    facturas = c.fetchall()
    conn.close()
    return facturas

# Función para actualizar un certificado
def update_certificado(certificado_id, fecha, contrato, contratista, valor_contrato, valor_pagado, total_facturas):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""UPDATE certificados 
                 SET fecha = ?, contrato = ?, contratista = ?, valor_contrato = ?, valor_pagado = ?, total_facturas = ?
                 WHERE id = ?""",
              (fecha, contrato, contratista, valor_contrato, valor_pagado, total_facturas, certificado_id))
    conn.commit()
    conn.close()

# Función para actualizar facturas de un certificado
def update_facturas(certificado_id, facturas_data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Eliminar facturas existentes
    c.execute("DELETE FROM facturas WHERE certificado_id = ?", (certificado_id,))
    
    # Insertar nuevas facturas
    for factura in facturas_data:
        c.execute("""INSERT INTO facturas (certificado_id, proveedor, numero_factura, importe, codigo) 
                     VALUES (?, ?, ?, ?, ?)""",
                  (certificado_id, factura['proveedor'], factura['factura'], factura['importe'], factura['codigo']))
    
    conn.commit()
    conn.close()

# Función para obtener certificados por obra
def get_certificados_by_obra(obra_id=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    if obra_id:
        c.execute("""SELECT c.*, o.nombre as obra_nombre, o.codigo as obra_codigo
                     FROM certificados c 
                     JOIN obras o ON c.obra_id = o.id 
                     WHERE c.obra_id = ? 
                     ORDER BY c.numero_certificado DESC""", (obra_id,))
    else:
        c.execute("""SELECT c.*, o.nombre as obra_nombre, o.codigo as obra_codigo
                     FROM certificados c 
                     JOIN obras o ON c.obra_id = o.id 
                     ORDER BY o.nombre, c.numero_certificado DESC""")
    
    certificados = c.fetchall()
    conn.close()
    return certificados

# Función para agregar una nueva fila
def agregar_fila():
    st.session_state.facturas_rows += 1

# Función para eliminar la última fila
def eliminar_fila():
    if st.session_state.facturas_rows > 1:
        st.session_state.facturas_rows -= 1

# Función para validar campos obligatorios
def validar_campos_obligatorios(fecha, obra_seleccionada, facturas_data):
    errores = []
    
    # Validar fecha
    if not fecha:
        errores.append("❌ Debe seleccionar una fecha")
    
    # Validar que se haya seleccionado una obra
    if not obra_seleccionada:
        errores.append("❌ Debe seleccionar una obra")
    
    # Validar facturas
    if len(facturas_data) == 0:
        errores.append("❌ Debe agregar al menos una factura")
    else:
        for i, factura in enumerate(facturas_data):
            factura_num = i + 1
            if not factura['proveedor'].strip():
                errores.append(f"❌ Factura No {factura_num}: Debe ingresar el proveedor")
            if not factura['factura'].strip():
                errores.append(f"❌ Factura No {factura_num}: Debe ingresar el número de factura")
            if factura['importe'] <= 0:
                errores.append(f"❌ Factura No {factura_num}: El importe debe ser mayor que 0")
    
    return errores

# Función para crear el informe en Excel 
def generar_informe_excel(datos, numero_certificado):
    try:
        # Cargar la plantilla 
        wb = load_workbook('data/ejemplo.xlsx')
        ws = wb.active
        
        # Llenar los datos en las celdas correspondientes
        # Nota: Las celdas deben coincidir con la estructura de tu plantilla
        # Ajusta estas referencias según tu archivo real
        
        # Colocar el número de certificado consecutivo 
        ws['E11'] = numero_certificado
        
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
            ws['C32'] = datos['aprobacion']
            
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

# Función para guardar certificado en la base de datos
def guardar_certificado_db(numero_certificado, obra_id, fecha, contrato, contratista, 
                          valor_contrato, valor_pagado, total_facturas, facturas_data, archivo_path):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    try:
        # Insertar certificado con el número específico por obra
        c.execute("""INSERT INTO certificados 
                     (numero_certificado, obra_id, fecha, contrato, contratista, valor_contrato, 
                      valor_pagado, total_facturas, archivo_path) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (numero_certificado, obra_id, fecha, contrato, contratista, 
                   valor_contrato, valor_pagado, total_facturas, archivo_path))
        
        certificado_id = c.lastrowid
        
        # Insertar facturas
        for factura in facturas_data:
            c.execute("""INSERT INTO facturas (certificado_id, proveedor, numero_factura, importe, codigo) 
                         VALUES (?, ?, ?, ?, ?)""",
                      (certificado_id, factura['proveedor'], factura['factura'], 
                       factura['importe'], factura['codigo']))
        
        conn.commit()
        conn.close()
        return certificado_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        conn.close()
        # Relanzar la excepción para que se maneje en el lugar de llamada
        raise e

# Inicializar la base de datos
init_db()

# ==================== INTERFAZ DE USUARIO ====================

# Sidebar para navegación
st.sidebar.title("_CERTIFICADOS")
menu_opcion = st.sidebar.radio(
    "Seleccione una opción:",
    ["🏠 Crear Nuevo Certificado", "📋 Ver Certificados", "✏️ Editar Certificado"]
)

if menu_opcion == "🏠 Crear Nuevo Certificado":
    st.title("Crear Nuevo Certificado")
    
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

    # Obtener obras de la base de datos
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
    obra_id = None

    # Cuando se selecciona una obra
    if obras:
        # Filtrar el DataFrame por la obra seleccionada
        obra_seleccionada = data_obras[data_obras["Obras"] == obras]
        
        # Verificar que se encontró la obra
        if not obra_seleccionada.empty:
            # Obtener el código de obra seleccionada
            codigo_obra = obra_seleccionada["Código de Obra"].iloc[0]
            nombre_obra = obra_seleccionada["Obras"].iloc[0]
            
            # Obtener ID de la obra de la base de datos
            obras_db = get_all_obras()
            for obra_db in obras_db:
                if obra_db[1] == nombre_obra and obra_db[2] == codigo_obra:
                    obra_id = obra_db[0]
                    break
            
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
        # Validar campos obligatorios
        errores = validar_campos_obligatorios(fecha, obras, facturas_data)
        
        if errores:
            # Mostrar errores
            st.error("🚨 Por favor corrija los siguientes errores antes de generar el informe:")
            for error in errores:
                st.write(error)
        else:
            # Verificar que se haya seleccionado una obra para obtener su ID
            if not obra_id:
                 st.error("❌ Error: No se pudo identificar la obra seleccionada.")
            else:
                # Obtener número de certificado consecutivo PARA LA OBRA SELECCIONADA
                numero_certificado = get_next_certificado_number_por_obra(obra_id)
                
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
                excel_data = generar_informe_excel(datos_informe, numero_certificado)
                
                if excel_data:
                    # Crear directorio para la obra si no existe
                    obra_dir = os.path.join(CERTIFICADOS_DIR, nombre_obra.replace("/", "_").replace("\\", "_"))
                    os.makedirs(obra_dir, exist_ok=True)
                    
                    # Guardar archivo físico con el nombre que incluye el número de certificado
                    filename = f"certificado_{numero_certificado:04d}.xlsx"
                    file_path = os.path.join(obra_dir, filename)
                    
                    with open(file_path, "wb") as f:
                        f.write(excel_data.getvalue())
                    
                    # Guardar en base de datos
                    certificado_id = guardar_certificado_db(
                        numero_certificado, obra_id, fecha, contrato, contratista,
                        valor_contrato, valor_pagado, total_facturas, facturas_data, file_path
                    )
                    
                    # Ofrecer el archivo para descargar
                    st.download_button(
                        label="📥 Descargar Informe",
                        data=excel_data,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.success(f"✅ Certificado #{numero_certificado} para la obra '{nombre_obra}' generado correctamente!")
                else:
                    st.error("❌ Error al generar el informe. Por favor intente nuevamente.")

elif menu_opcion == "📋 Ver Certificados":
    st.title("Ver Certificados Generados")
    
    # Filtro por obra
    obras_db = get_all_obras()
    obras_dict = {obra[1]: obra[0] for obra in obras_db}  # nombre: id
    obras_nombres = ["Todas las obras"] + list(obras_dict.keys())
    
    obra_seleccionada = st.selectbox("Filtrar por obra:", obras_nombres)
    
    # Obtener certificados
    if obra_seleccionada == "Todas las obras":
        certificados = get_certificados_by_obra()
    else:
        obra_id = obras_dict[obra_seleccionada]
        certificados = get_certificados_by_obra(obra_id)
    
    if certificados:
        st.write(f"### Certificados encontrados: {len(certificados)}")
        
        # Mostrar tabla de certificados
        # Actualizado para incluir el código de la obra
        df_certificados = pd.DataFrame(certificados, 
                                     columns=['ID', 'N° Certificado', 'Obra ID', 'Fecha', 'Contrato', 
                                             'Contratista', 'Valor Contrato', 'Valor Pagado', 
                                             'Total Facturas', 'Archivo', 'Fecha Generación', 'Obra Nombre', 'Obra Codigo'])
        
        # Seleccionar columnas relevantes para mostrar
        df_mostrar = df_certificados[['N° Certificado', 'Obra Nombre', 'Obra Codigo', 'Fecha', 'Contratista', 
                                    'Valor Contrato', 'Valor Pagado', 'Total Facturas', 'Fecha Generación']]
        
        # Formatear valores monetarios
        df_mostrar['Valor Contrato'] = df_mostrar['Valor Contrato'].apply(lambda x: f"{x:,.2f}" if x else "0.00")
        df_mostrar['Valor Pagado'] = df_mostrar['Valor Pagado'].apply(lambda x: f"{x:,.2f}" if x else "0.00")
        df_mostrar['Total Facturas'] = df_mostrar['Total Facturas'].apply(lambda x: f"{x:,.2f}" if x else "0.00")
        
        st.dataframe(df_mostrar, use_container_width=True)
        
        # Opción para descargar certificados individuales
        st.markdown("---")
        st.subheader("Descargar Certificado")
        certificado_id_seleccion = st.selectbox(
            "Seleccione un certificado para descargar:",
            options=certificados,
            format_func=lambda x: f"#{x[1]} - {x[11]} ({x[12]}) - {x[3]}"  # N° - Obra - Codigo - Fecha
        )
        
        if certificado_id_seleccion:
            certificado_id = certificado_id_seleccion[0]
            archivo_path = certificado_id_seleccion[9]
            
            if os.path.exists(archivo_path):
                with open(archivo_path, "rb") as file:
                    st.download_button(
                        label="📥 Descargar Certificado Seleccionado",
                        data=file,
                        file_name=os.path.basename(archivo_path),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.warning("Archivo no encontrado. Puede que haya sido movido o eliminado.")
    else:
        st.info("No se encontraron certificados.")

elif menu_opcion == "✏️ Editar Certificado":
    st.title("Editar Certificado")
    
    # Obtener todos los certificados
    certificados = get_certificados_by_obra()
    
    if certificados:
        # Selector de certificado
        certificado_seleccionado = st.selectbox(
            "Seleccione un certificado para editar:",
            options=certificados,
            format_func=lambda x: f"#{x[1]} - {x[11]} ({x[12]}) - {x[3]}"  # N° - Obra - Codigo - Fecha
        )
        
        if certificado_seleccionado:
            certificado_id = certificado_seleccionado[0]
            numero_certificado = certificado_seleccionado[1]
            obra_nombre = certificado_seleccionado[11]
            obra_codigo = certificado_seleccionado[12]
            
            # Obtener datos del certificado
            certificado_data = get_certificado_by_id(certificado_id)
            facturas_data = get_facturas_by_certificado_id(certificado_id)
            
            # CORREGIDO: Añadido el ':' faltante
            if certificado_data and facturas_data:
                st.markdown(f"### Editando Certificado #{numero_certificado} - Obra: {obra_nombre} ({obra_codigo})")
                
                # Formulario de edición
                col1, col2 = st.columns(2)
                with col1:
                    fecha_edit = st.date_input("Fecha:", value=datetime.strptime(certificado_data[3], "%Y-%m-%d").date() if certificado_data[3] else datetime.now().date())
                    contrato_edit = st.text_input("Contrato:", value=certificado_data[4] or "")
                    valor_contrato_edit = st.number_input("Valor Contrato:", value=float(certificado_data[6] or 0.0), format="%.2f")
                
                with col2:
                    contratista_edit = st.text_input("Contratista:", value=certificado_data[5] or "")
                    valor_pagado_edit = st.number_input("Valor Pagado:", value=float(certificado_data[7] or 0.0), format="%.2f")
                    total_facturas_edit = st.number_input("Total Facturas:", value=float(certificado_data[8] or 0.0), format="%.2f")
                
                st.markdown("---")
                st.subheader("Facturas")
                
                # Editor de facturas
                facturas_edit_data = []
                for i, factura in enumerate(facturas_data):
                    st.markdown(f"**Factura {i+1}**")
                    col_prov, col_fact, col_imp, col_cod = st.columns(4)
                    
                    with col_prov:
                        proveedor = st.text_input(f"Proveedor {i+1}", value=factura[0], key=f"edit_prov_{i}")
                    with col_fact:
                        numero_fact = st.text_input(f"Factura {i+1}", value=factura[1], key=f"edit_fact_{i}")
                    with col_imp:
                        importe = st.number_input(f"Importe {i+1}", value=float(factura[2]), format="%.2f", key=f"edit_imp_{i}")
                    with col_cod:
                        codigo = st.text_input(f"Código {i+1}", value=factura[3] or "", key=f"edit_cod_{i}")
                    
                    facturas_edit_data.append({
                        'proveedor': proveedor,
                        'factura': numero_fact,
                        'importe': importe,
                        'codigo': codigo
                    })
                
                # Botón para guardar cambios
                if st.button("💾 Guardar Cambios"):
                    # Validar datos
                    if total_facturas_edit <= 0:
                        st.error("El total de facturas debe ser mayor que 0")
                    else:
                        # Actualizar certificado
                        update_certificado(certificado_id, fecha_edit, contrato_edit, contratista_edit,
                                         valor_contrato_edit, valor_pagado_edit, total_facturas_edit)
                        
                        # Actualizar facturas
                        update_facturas(certificado_id, facturas_edit_data)
                        
                        st.success("✅ Certificado actualizado correctamente!")
                        
                        # Opcional: regenerar el archivo Excel con los nuevos datos
                        st.info("Para regenerar el archivo Excel con los cambios, descárguelo nuevamente desde la sección 'Ver Certificados'")
            else:
                st.error("Error al cargar los datos del certificado")
    else:
        st.info("No hay certificados disponibles para editar.")