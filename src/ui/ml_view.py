import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QComboBox, QDoubleSpinBox, QMessageBox,
                             QTextEdit, QProgressBar, QDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

from src.services.ml_engine import MotorIA
from src.services.monte_carlo import MotorMonteCarlo

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

class WorkerMonteCarlo(QThread):
    """Hilo para simulación Monte Carlo (evita freeze de UI)."""
    finalizado = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, motor_mc, presupuesto, duracion):
        super().__init__()
        self.motor_mc = motor_mc
        self.presupuesto = presupuesto
        self.duracion = duracion

    def run(self):
        try:
            res = self.motor_mc.simular(self.presupuesto, self.duracion)
            self.finalizado.emit(res)
        except Exception as e:
            self.error.emit(str(e))

class DialogoMonteCarlo(QDialog):
    """Ventana emergente para resultados de Simulación."""
    def __init__(self, presupuesto, duracion):
        super().__init__()
        self.setWindowTitle("Simulación de Flujo de Caja (Monte Carlo)")
        self.setGeometry(200, 200, 800, 600)
        self.presupuesto = presupuesto
        self.duracion = duracion
        self.motor_mc = MotorMonteCarlo()
        
        self.init_ui()
        self.iniciar_simulacion()

    def init_ui(self):
        layout = QVBoxLayout()
        
        self.lbl_info = QLabel("Inicializando motor estocástico...")
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_info.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        layout.addWidget(self.lbl_info)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0) # Indeterminado (loading)
        layout.addWidget(self.progress)

        # Placeholder para la gráfica
        self.grafica_container = QVBoxLayout()
        layout.addLayout(self.grafica_container)
        
        self.txt_stats = QTextEdit()
        self.txt_stats.setReadOnly(True)
        self.txt_stats.setMaximumHeight(100)
        layout.addWidget(self.txt_stats)
        
        self.setLayout(layout)

    def iniciar_simulacion(self):
        self.lbl_info.setText("Analizando 10.000 escenarios basados en historia real...")
        
        # Usar Worker para no congelar
        self.worker = WorkerMonteCarlo(self.motor_mc, self.presupuesto, self.duracion)
        self.worker.finalizado.connect(self.mostrar_resultados)
        self.worker.error.connect(self.mostrar_error)
        self.worker.start()

    def mostrar_resultados(self, res):
        self.progress.setVisible(False)
        self.lbl_info.setText("✅ Simulación Completada.")
        self.lbl_info.setStyleSheet("font-size: 14px; font-weight: bold; color: green;")

        # Texto
        texto = (f"📊 RESULTADOS ESTOCÁSTICOS:\n"
                 f"• Presupuesto Inicial: ${self.presupuesto:,.0f}\n"
                 f"• Costo Promedio Esperado: ${res['media']:,.0f}\n"
                 f"• Escenario Pesimista (P90): ${res['p90']:,.0f}\n"
                 f"• Probabilidad de Sobrecosto: {res['probabilidad_sobrecosto']:.1%}")
        self.txt_stats.setText(texto)

        # Gráfica
        try:
            # Limpiar gráfica anterior si hubiera
            while self.grafica_container.count():
                item = self.grafica_container.takeAt(0)
                widget = item.widget()
                if widget: widget.deleteLater()

            fig = self.motor_mc.graficar_resultados(res, self.presupuesto)
            canvas = FigureCanvas(fig)
            self.grafica_container.addWidget(canvas)
        except Exception as e:
            self.mostrar_error(f"Error graficando: {e}")

    def mostrar_error(self, error):
        self.progress.setVisible(False)
        self.lbl_info.setText("❌ Error en simulación")
        self.lbl_info.setStyleSheet("color: red;")
        self.txt_stats.setText(f"Detalle del error:\n{error}")

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
        if self.motor.entrenado:
            self.btn_entrenar.setText("Re-entrenar Modelo (Actualizar)")
            self.btn_entrenar.setStyleSheet("padding: 10px; background-color: #f39c12; color: white; font-weight: bold;")
        else:
            self.btn_entrenar.setStyleSheet("padding: 10px; background-color: #2ecc71; color: white; font-weight: bold;")
            
        self.btn_entrenar.clicked.connect(self.iniciar_entrenamiento)
        col_izq.addWidget(self.btn_entrenar)

        # Botón Eliminar Modelo
        self.btn_eliminar = QPushButton("Eliminar Modelo Actual")
        self.btn_eliminar.setStyleSheet("padding: 8px; background-color: #c0392b; color: white; font-weight: bold; margin-top: 5px;")
        self.btn_eliminar.setVisible(self.motor.entrenado) # Solo visible si existe
        self.btn_eliminar.clicked.connect(self.eliminar_modelo)
        col_izq.addWidget(self.btn_eliminar)

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
        
        # Botón Predecir (Clásico)
        self.btn_predecir = QPushButton("Calcular Riesgo (IA)")
        self.btn_predecir.setStyleSheet("padding: 10px; background-color: #3498db; color: white; font-weight: bold;")
        self.btn_predecir.setEnabled(self.motor.entrenado) # Habilitar si ya hay modelo cargado
        self.btn_predecir.clicked.connect(self.predecir)
        col_der.addWidget(self.btn_predecir)

        # Botón Monte Carlo (Nuevo)
        self.btn_montecarlo = QPushButton("🎲 Simular Flujo de Caja (Monte Carlo)")
        self.btn_montecarlo.setStyleSheet("padding: 10px; background-color: #9b59b6; color: white; font-weight: bold; margin-top: 10px;")
        self.btn_montecarlo.clicked.connect(self.lanzar_montecarlo)
        col_der.addWidget(self.btn_montecarlo)

        # Resultado IA
        texto_inicial = "Modelo listo (Cargado)." if self.motor.entrenado else "Esperando modelo..."
        self.lbl_resultado = QLabel(texto_inicial)
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
        self.btn_entrenar.setText("Re-entrenar Modelo (Actualizar)")
        self.btn_entrenar.setStyleSheet("padding: 10px; background-color: #f39c12; color: white; font-weight: bold;")
        
        self.btn_eliminar.setVisible(True)
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

    def eliminar_modelo(self):
        import os
        ruta = getattr(self.motor, "ruta_modelo", "data/modelo_entrenado.pkl")
        if os.path.exists(ruta):
            try:
                os.remove(ruta)
                self.motor.entrenado = False
                self.motor.model = None # Reset
                
                # Reset UI
                self.btn_predecir.setEnabled(False)
                self.btn_eliminar.setVisible(False)
                self.lbl_resultado.setText("Esperando modelo...")
                self.txt_reporte.clear()
                self.ax.clear()
                self.canvas.draw()
                
                self.btn_entrenar.setText("Entrenar Modelo (Random Forest)")
                self.btn_entrenar.setStyleSheet("padding: 10px; background-color: #2ecc71; color: white; font-weight: bold;")
                
                QMessageBox.information(self, "Éxito", "Modelo eliminado. El sistema ha olvidado lo aprendido.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar: {e}")

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

    def lanzar_montecarlo(self):
        presupuesto = self.spin_presupuesto.value()
        duracion = self.spin_duracion.value()
        
        if presupuesto <= 0:
            QMessageBox.warning(self, "Aviso", "Ingrese un presupuesto válido para simular.")
            return
            
        dlg = DialogoMonteCarlo(presupuesto, duracion)
        dlg.exec()
