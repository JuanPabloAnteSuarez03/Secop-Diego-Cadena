import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QFrame, QGridLayout)
from PyQt6.QtCore import Qt
from src.database.db_manager import GestorBaseDatos

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.gestor = GestorBaseDatos()
        self.init_ui()
        self.cargar_datos()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # --- Encabezado ---
        header = QHBoxLayout()
        lbl_titulo = QLabel("Dashboard de Inteligencia de Contratos")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        
        btn_actualizar = QPushButton("Actualizar Análisis")
        btn_actualizar.clicked.connect(self.cargar_datos)
        
        header.addWidget(lbl_titulo)
        header.addStretch()
        header.addWidget(btn_actualizar)
        layout.addLayout(header)

        # --- KPIs (Tarjetas Superiores) ---
        self.kpi_layout = QHBoxLayout()
        self.card_total = self.crear_tarjeta("Total Proyectos", "0")
        self.card_dinero = self.crear_tarjeta("Presupuesto Analizado", "$0")
        self.card_riesgo = self.crear_tarjeta("Riesgo Promedio", "0%")
        
        self.kpi_layout.addWidget(self.card_total)
        self.kpi_layout.addWidget(self.card_dinero)
        self.kpi_layout.addWidget(self.card_riesgo)
        layout.addLayout(self.kpi_layout)

        # --- Gráficas (Centro) ---
        graficos_layout = QHBoxLayout()
        
        # Gráfica 1: Barras (Top Departamentos)
        self.fig1, self.ax1 = plt.subplots(figsize=(5, 4))
        self.canvas1 = FigureCanvas(self.fig1)
        graficos_layout.addWidget(self.canvas1)

        # Gráfica 2: Torta (Tipos de Contrato)
        self.fig2, self.ax2 = plt.subplots(figsize=(5, 4))
        self.canvas2 = FigureCanvas(self.fig2)
        graficos_layout.addWidget(self.canvas2)
        
        layout.addLayout(graficos_layout)

        # Tabla de "Últimos Proyectos Registrados" eliminada por solicitud.

        self.setLayout(layout)

    def crear_tarjeta(self, titulo, valor):
        card = QFrame()
        card.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #ddd; padding: 10px;")
        l = QVBoxLayout()
        t = QLabel(titulo)
        t.setStyleSheet("color: #777; font-size: 12px;")
        v = QLabel(valor)
        v.setStyleSheet("color: #333; font-size: 20px; font-weight: bold;")
        v.setObjectName("valor") # Para buscarlo luego
        l.addWidget(t)
        l.addWidget(v)
        card.setLayout(l)
        return card

    def actualizar_tarjeta(self, card, nuevo_valor):
        # Buscar el label del valor y actualizarlo
        for i in range(card.layout().count()):
            widget = card.layout().itemAt(i).widget()
            if widget and widget.objectName() == "valor":
                widget.setText(str(nuevo_valor))
                break

    def cargar_datos(self):
        # 1. Obtener datos de la BD (SOLO ÚLTIMOS 1000 PARA VELOCIDAD)
        proyectos = self.gestor.obtener_ultimos_proyectos(limite=1000)
        
        # 2. Calcular KPIs globales reales usando SQL (Optimizado)
        total_real, suma_presupuesto_real = self.gestor.obtener_kpis_globales()
        
        self.actualizar_tarjeta(self.card_total, f"{total_real:,.0f}")
        self.actualizar_tarjeta(self.card_dinero, f"${suma_presupuesto_real:,.0f}")
        self.actualizar_tarjeta(self.card_riesgo, "Bajo") # Dummy por ahora

        if not proyectos:
            return

        # Convertir a DataFrame para facilitar cálculos
        data = []
        for p in proyectos:
            data.append({
                "id": p.id,
                "entidad": p.nombre_entidad,
                "objeto": p.nombre_proyecto,
                "presupuesto": p.presupuesto_inicial,
                "depto": p.departamento,
                "tipo": p.tipo_contrato
            })
        df = pd.DataFrame(data)

        # 3. Actualizar Gráfica 1 (Top 5 Deptos - GLOBAL SQL)
        self.ax1.clear()
        try:
            top_deptos_sql = self.gestor.obtener_top_departamentos()
            if top_deptos_sql:
                # Desempaquetar [(Depto, Count), ...]
                nombres = [x[0] for x in top_deptos_sql]
                valores = [x[1] for x in top_deptos_sql]
                
                self.ax1.bar(nombres, valores, color='#4a90e2')
                self.ax1.set_title("Top 5 Departamentos (Histórico)")
                self.ax1.tick_params(axis='x', rotation=45)
                self.fig1.tight_layout()
        except Exception as e:
            print(f"Error grafica deptos: {e}")
        self.canvas1.draw()

        # 4. Actualizar Gráfica 2 (Tipos Contrato - GLOBAL SQL)
        self.ax2.clear()
        try:
            tipos_sql = self.gestor.obtener_tipos_contrato()
            if tipos_sql:
                labels = [x[0] for x in tipos_sql]
                sizes = [x[1] for x in tipos_sql]
                
                self.ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                self.ax2.set_ylabel('')
                self.ax2.set_title("Modalidad Contratación (Histórico)")
        except Exception as e:
            print(f"Error grafica tipos: {e}")
        self.canvas2.draw()

        # (Tabla eliminada)

