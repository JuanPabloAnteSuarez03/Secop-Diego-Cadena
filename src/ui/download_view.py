from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QSpinBox, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from src.services.secop_api import ClienteSecop
from src.database.db_manager import GestorBaseDatos

class WorkerDescarga(QThread):
    """Hilo en segundo plano para no congelar la interfaz mientras descarga."""
    datos_descargados = pyqtSignal(object) # Señal para enviar el DataFrame
    error_ocurrido = pyqtSignal(str)

    def __init__(self, departamento, limite):
        super().__init__()
        self.departamento = departamento
        self.limite = limite

    def run(self):
        try:
            cliente = ClienteSecop()
            # Descargar datos
            datos = cliente.obtener_contratos(
                departamento=self.departamento, 
                limite=self.limite
            )
            # Convertir a DataFrame
            df = cliente.convertir_a_dataframe(datos)
            self.datos_descargados.emit(df)
        except Exception as e:
            self.error_ocurrido.emit(str(e))

class VistaDescarga(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- Panel de Control (Arriba) ---
        panel_control = QHBoxLayout()
        
        self.combo_depto = QComboBox()
        self.combo_depto.addItems(["Antioquia", "Bogotá D.C.", "Cundinamarca", "Valle del Cauca", "Santander"])
        self.combo_depto.setEditable(True) # Permitir escribir otros
        self.combo_depto.setPlaceholderText("Departamento")
        
        self.spin_limite = QSpinBox()
        self.spin_limite.setRange(10, 5000)
        self.spin_limite.setValue(50)
        self.spin_limite.setPrefix("Límite: ")

        self.btn_descargar = QPushButton("Descargar Datos SECOP")
        self.btn_descargar.clicked.connect(self.iniciar_descarga)

        panel_control.addWidget(QLabel("Departamento:"))
        panel_control.addWidget(self.combo_depto)
        panel_control.addWidget(self.spin_limite)
        panel_control.addWidget(self.btn_descargar)
        panel_control.addStretch()

        layout.addLayout(panel_control)

        # --- Tabla de Resultados (Centro) ---
        self.tabla = QTableWidget()
        layout.addWidget(self.tabla)
        
        # --- Estado (Abajo) ---
        self.lbl_estado = QLabel("Listo.")
        layout.addWidget(self.lbl_estado)

        self.setLayout(layout)

    def iniciar_descarga(self):
        depto = self.combo_depto.currentText()
        limite = self.spin_limite.value()

        self.lbl_estado.setText(f"Conectando a SECOP para descargar {limite} registros de {depto}...")
        self.btn_descargar.setEnabled(False)
        self.tabla.clear()
        self.tabla.setRowCount(0)
        self.tabla.setColumnCount(0)

        # Iniciar hilo
        self.worker = WorkerDescarga(depto, limite)
        self.worker.datos_descargados.connect(self.mostrar_datos)
        self.worker.error_ocurrido.connect(self.mostrar_error)
        self.worker.start()

    def mostrar_datos(self, df):
        self.btn_descargar.setEnabled(True)
        
        if df.empty:
            self.lbl_estado.setText("Descarga completada. 0 registros encontrados.")
            QMessageBox.warning(self, "Sin datos", "No se encontraron contratos con esos filtros.")
            return

        # Guardar en BD automáticamente
        try:
            gestor = GestorBaseDatos()
            nuevos = gestor.guardar_dataframe(df)
            self.lbl_estado.setText(f"Descarga completada. {len(df)} registros encontrados. ({nuevos} nuevos guardados en BD)")
        except Exception as e:
            self.lbl_estado.setText(f"Datos descargados, pero error guardando en BD: {e}")

        # Configurar tabla
        columnas = list(df.columns)
        # Seleccionar solo algunas columnas relevantes para mostrar
        cols_interes = ['referencia_del_contrato', 'objeto_del_contrato', 'valor_del_contrato', 'fecha_de_firma']
        # Filtrar solo las que existan en el DF
        cols_finales = [c for c in cols_interes if c in columnas]
        
        # Si no hay columnas de interés (API cambió), mostramos todas
        if not cols_finales:
            cols_finales = columnas[:10] # Primeras 10

        self.tabla.setColumnCount(len(cols_finales))
        self.tabla.setHorizontalHeaderLabels(cols_finales)
        self.tabla.setRowCount(len(df))

        for i, row in df.iterrows():
            for j, col in enumerate(cols_finales):
                valor = str(row[col])
                self.tabla.setItem(i, j, QTableWidgetItem(valor))
        
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def mostrar_error(self, error):
        self.btn_descargar.setEnabled(True)
        self.lbl_estado.setText("Error en la descarga.")
        QMessageBox.critical(self, "Error", f"Fallo al conectar con SECOP:\n{error}")

