import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QComboBox, QDoubleSpinBox, QMessageBox,
                             QTextEdit, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

from src.services.ml_engine import MotorIA

class WorkerEntrenamiento(QThread):
    """Hilo para entrenar el modelo sin congelar la UI."""
    finalizado = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, motor):
        super().__init__()
        self.motor = motor

    def run(self):
        try:
            resultados = self.motor.entrenar()
            if "error" in resultados:
                self.error.emit(resultados["error"])
            else:
                self.finalizado.emit(resultados)
        except Exception as e:
            self.error.emit(str(e))

class VistaML(QWidget):
    def __init__(self):
        super().__init__()
        self.motor = MotorIA()
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()

        # --- COLUMNA IZQUIERDA: Entrenamiento y Métricas ---
        col_izq = QVBoxLayout()
        
        lbl_titulo = QLabel("Motor de Inteligencia Artificial")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold;")
        col_izq.addWidget(lbl_titulo)

        self.btn_entrenar = QPushButton("Entrenar Modelo (Random Forest)")
        self.btn_entrenar.setStyleSheet("padding: 10px; background-color: #2ecc71; color: white; font-weight: bold;")
        self.btn_entrenar.clicked.connect(self.iniciar_entrenamiento)
        col_izq.addWidget(self.btn_entrenar)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        col_izq.addWidget(self.progress)

        # Área de reporte
        self.txt_reporte = QTextEdit()
        self.txt_reporte.setReadOnly(True)
        self.txt_reporte.setPlaceholderText("Aquí aparecerán las métricas del modelo una vez entrenado...")
        col_izq.addWidget(self.txt_reporte)

        # Gráfica de Importancia
        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.canvas = FigureCanvas(self.fig)
        col_izq.addWidget(QLabel("Importancia de Variables:"))
        col_izq.addWidget(self.canvas)

        layout.addLayout(col_izq, stretch=1)

        # --- COLUMNA DERECHA: Simulador ---
        col_der = QVBoxLayout()
        
        lbl_sim = QLabel("🔮 Simulador de Riesgo")
        lbl_sim.setStyleSheet("font-size: 18px; font-weight: bold; color: #e67e22;")
        col_der.addWidget(lbl_sim)

        form_layout = QVBoxLayout()
        
        # Inputs
        form_layout.addWidget(QLabel("Presupuesto Estimado ($):"))
        self.spin_presupuesto = QDoubleSpinBox()
        self.spin_presupuesto.setRange(0, 1e12) # Hasta 1 billón
        self.spin_presupuesto.setValue(100000000)
        form_layout.addWidget(self.spin_presupuesto)

        form_layout.addWidget(QLabel("Duración Estimada (Días):"))
        self.spin_duracion = QDoubleSpinBox()
        self.spin_duracion.setRange(0, 5000)
        self.spin_duracion.setValue(180)
        form_layout.addWidget(self.spin_duracion)

        form_layout.addWidget(QLabel("Departamento:"))
        self.combo_depto = QComboBox()
        # Llenaremos esto dinámicamente o con lista estática por ahora
        self.combo_depto.addItems([
    "Amazonas", "Antioquia", "Arauca", "Atlántico", "Bolívar", 
    "Boyacá", "Caldas", "Caquetá", "Casanare", "Cauca", 
    "Cesar", "Chocó", "Córdoba", "Cundinamarca", "Bogotá D.C.", 
    "Guainía", "Guaviare", "Huila", "La Guajira", "Magdalena", 
    "Meta", "Nariño", "Norte de Santander", "Putumayo", "Quindío", 
    "Risaralda", "San Andrés, Providencia y Santa Catalina", "Santander", 
    "Sucre", "Tolima", "Valle del Cauca", "Vaupés", "Vichada"
])
        form_layout.addWidget(self.combo_depto)

        form_layout.addWidget(QLabel("Tipo Contrato:"))
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Obra", "Consultoría", "Suministros", "Prestación de servicios", "Compraventa"])
        form_layout.addWidget(self.combo_tipo)

        col_der.addLayout(form_layout)
        
        self.btn_predecir = QPushButton("Calcular Riesgo")
        self.btn_predecir.setStyleSheet("padding: 10px; background-color: #3498db; color: white; font-weight: bold;")
        self.btn_predecir.setEnabled(False) # Deshabilitado hasta entrenar
        self.btn_predecir.clicked.connect(self.predecir)
        col_der.addWidget(self.btn_predecir)

        # Resultado
        self.lbl_resultado = QLabel("Esperando modelo...")
        self.lbl_resultado.setStyleSheet("font-size: 16px; border: 1px solid #ddd; padding: 15px; border-radius: 5px;")
        self.lbl_resultado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col_der.addWidget(self.lbl_resultado)
        
        col_der.addStretch()

        layout.addLayout(col_der, stretch=1)
        self.setLayout(layout)

    def iniciar_entrenamiento(self):
        self.btn_entrenar.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0) # Indeterminado
        self.lbl_resultado.setText("Entrenando modelo...")
        
        self.worker = WorkerEntrenamiento(self.motor)
        self.worker.finalizado.connect(self.fin_entrenamiento)
        self.worker.error.connect(self.error_entrenamiento)
        self.worker.start()

    def fin_entrenamiento(self, resultados):
        self.btn_entrenar.setEnabled(True)
        self.progress.setVisible(False)
        self.btn_predecir.setEnabled(True)
        
        # Mostrar métricas
        precision = resultados['precision']
        self.txt_reporte.setText(f"✅ Entrenamiento Exitoso\n\n"
                                 f"Precisión Global: {precision:.2%}\n"
                                 f"Datos usados: {resultados['total_datos']}\n\n"
                                 f"Detalles por clase:\n"
                                 f"{resultados['reporte']}")

        # Graficar Importancia
        importancias = resultados['importancia_variables']
        nombres = list(importancias.keys())
        valores = list(importancias.values())

        self.ax.clear()
        self.ax.barh(nombres, valores, color='#8e44ad')
        self.ax.set_title("Variables más influyentes")
        self.ax.set_xlabel("Peso")
        self.fig.tight_layout()
        self.canvas.draw()
        
        self.lbl_resultado.setText("Modelo listo para predicciones.")

    def error_entrenamiento(self, error):
        self.btn_entrenar.setEnabled(True)
        self.progress.setVisible(False)
        QMessageBox.critical(self, "Error", f"Fallo en entrenamiento:\n{error}")

    def predecir(self):
        res = self.motor.predecir_riesgo(
            presupuesto=self.spin_presupuesto.value(),
            duracion_dias=self.spin_duracion.value(),
            departamento=self.combo_depto.currentText(),
            tipo_contrato=self.combo_tipo.currentText()
        )
        
        if res:
            prob = res['probabilidad']
            es_riesgo = res['riesgo_alto']
            
            color = "red" if prob > 0.5 else "green"
            texto = "ALTO RIESGO" if prob > 0.5 else "BAJO RIESGO"
            
            self.lbl_resultado.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color}; border: 2px solid {color}; padding: 20px;")
            self.lbl_resultado.setText(f"{texto}\n\nProbabilidad de Sobrecosto/Retraso:\n{prob:.1%}")
        else:
            self.lbl_resultado.setText("Error en predicción.")

