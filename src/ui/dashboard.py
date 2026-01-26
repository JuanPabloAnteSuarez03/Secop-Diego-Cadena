import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt
from src.database.db_manager import GestorBaseDatos

# Estilo más legible para las gráficas
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({"font.size": 9})

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.gestor = GestorBaseDatos()
        self.init_ui()
        self.cargar_datos()

    def init_ui(self):
        # Para que se pueda ver TODO el dashboard sin recortar, lo ponemos dentro de un scroll.
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)
        
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
        # Usamos Grid 3x2 para agregar más visualizaciones relevantes sin saturar.
        graficos_layout = QGridLayout()
        graficos_layout.setContentsMargins(8, 8, 8, 8)
        graficos_layout.setHorizontalSpacing(34)
        graficos_layout.setVerticalSpacing(26)

        # Gráfica 1: Barras (Top Departamentos - volumen)
        self.fig1, self.ax1 = plt.subplots(figsize=(6.5, 4.2))
        self.canvas1 = FigureCanvas(self.fig1)
        self.canvas1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas1.setMinimumHeight(280)
        graficos_layout.addWidget(self.canvas1, 0, 0)

        # Gráfica 2: Torta (Tipos de Contrato - distribución)
        self.fig2, self.ax2 = plt.subplots(figsize=(6.5, 4.2))
        self.canvas2 = FigureCanvas(self.fig2)
        self.canvas2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas2.setMinimumHeight(280)
        graficos_layout.addWidget(self.canvas2, 0, 1)

        # Gráfica 3: Tasa de modificación por Tipo (Top 10)
        self.fig3, self.ax3 = plt.subplots(figsize=(6.5, 4.2))
        self.canvas3 = FigureCanvas(self.fig3)
        self.canvas3.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas3.setMinimumHeight(280)
        graficos_layout.addWidget(self.canvas3, 1, 0)

        # Gráfica 4: Probabilidad de modificación vs Presupuesto (por rangos)
        self.fig4, self.ax4 = plt.subplots(figsize=(6.5, 4.2))
        self.canvas4 = FigureCanvas(self.fig4)
        self.canvas4.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas4.setMinimumHeight(280)
        graficos_layout.addWidget(self.canvas4, 1, 1)

        # Gráfica 5: Top Entidades con mayor tasa de modificación
        self.fig5, self.ax5 = plt.subplots(figsize=(6.5, 4.2))
        self.canvas5 = FigureCanvas(self.fig5)
        self.canvas5.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas5.setMinimumHeight(280)
        graficos_layout.addWidget(self.canvas5, 2, 0)

        # Gráfica 6: Adiciones por mes (tendencia)
        self.fig6, self.ax6 = plt.subplots(figsize=(6.5, 4.2))
        self.canvas6 = FigureCanvas(self.fig6)
        self.canvas6.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas6.setMinimumHeight(280)
        graficos_layout.addWidget(self.canvas6, 2, 1)
        
        layout.addLayout(graficos_layout)

        # Tabla de "Últimos Proyectos Registrados" eliminada por solicitud.

        scroll.setWidget(content)
        root.addWidget(scroll)
        self.setLayout(root)

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

        # KPI "Riesgo": tasa global de contratos con modificación (proxy: adición de tiempo > 0)
        try:
            data_tipos = self.gestor.analytics_prorrogas_por_tipo()
            total_contratos = sum([d[1] for d in data_tipos]) if data_tipos else 0
            total_modificados = sum([d[2] for d in data_tipos]) if data_tipos else 0
            tasa_global = (total_modificados / total_contratos) * 100 if total_contratos else 0.0
            self.actualizar_tarjeta(self.card_riesgo, f"{tasa_global:.1f}%")
        except Exception:
            self.actualizar_tarjeta(self.card_riesgo, "—")

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
                self.ax1.set_title("Top 5 Departamentos (Histórico)", fontsize=11, fontweight="bold")
                self.ax1.tick_params(axis='x', rotation=25, labelsize=8)
                self.ax1.tick_params(axis='y', labelsize=8)
                self.fig1.tight_layout()
        except Exception as e:
            print(f"Error grafica deptos: {e}")
        self.canvas1.draw()

        # 4. Actualizar Gráfica 2 (Tipos Contrato - GLOBAL SQL)
        self.ax2.clear()
        try:
            tipos_sql = self.gestor.obtener_tipos_contrato()
            if tipos_sql:
                # Limitar a Top 6 y agrupar el resto en "Otros" para legibilidad
                top = tipos_sql[:6]
                otros = sum([x[1] for x in tipos_sql[6:]])
                labels = [x[0] for x in top]
                sizes = [x[1] for x in top]
                if otros > 0:
                    labels.append("Otros")
                    sizes.append(otros)
                
                # Mejor legibilidad: labels en leyenda, no encima de la torta.
                wedges, _, _ = self.ax2.pie(
                    sizes,
                    labels=None,
                    autopct="%1.1f%%",
                    startangle=90,
                    pctdistance=0.75,
                    textprops={"fontsize": 8},
                )
                self.ax2.legend(
                    wedges,
                    labels,
                    loc="center left",
                    bbox_to_anchor=(1.02, 0.5),
                    fontsize=8,
                    frameon=False,
                )
                self.ax2.set_ylabel('')
                self.ax2.set_title("Modalidad Contratación (Histórico)", fontsize=11, fontweight="bold")
                self.fig2.subplots_adjust(right=0.80)
        except Exception as e:
            print(f"Error grafica tipos: {e}")
        self.canvas2.draw()

        # 5. Gráfica 3: Tasa de modificación por Tipo (Top 10)
        self.ax3.clear()
        try:
            data = self.gestor.analytics_prorrogas_por_tipo()
            if data:
                procesada = []
                for tipo, total, con_mod in data:
                    if total:
                        procesada.append((str(tipo), (con_mod / total) * 100))

                procesada.sort(key=lambda x: x[1], reverse=True)
                procesada = procesada[:10]

                tipos = [p[0][:22] for p in procesada]
                tasas = [p[1] for p in procesada]
                bars = self.ax3.barh(tipos, tasas, color="#e67e22")
                self.ax3.invert_yaxis()
                self.ax3.set_title("Top 10 Modalidades con Mayor Tasa de Modificación (%)", fontsize=11, fontweight="bold")
                self.ax3.set_xlabel("% contratos con modificación", fontsize=9)
                self.ax3.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=8)
                self.fig3.subplots_adjust(left=0.28)
                self.fig3.tight_layout()
        except Exception as e:
            print(f"Error grafica tasa por tipo: {e}")
        self.canvas3.draw()

        # 6. Gráfica 4: Probabilidad de modificación vs Presupuesto (binned)
        self.ax4.clear()
        try:
            raw_data = self.gestor.analytics_presupuesto_vs_riesgo()
            if raw_data:
                df_bins = pd.DataFrame(raw_data, columns=["presupuesto", "tiene_modificacion"])
                # Rangos (ajústalos si tu universo es distinto)
                bins = [0, 50e6, 200e6, 1e9, 5e9, float("inf")]
                labels = ["<50M", "50-200M", "200M-1B", "1B-5B", ">5B"]
                df_bins["rango"] = pd.cut(df_bins["presupuesto"], bins=bins, labels=labels)
                grouped = df_bins.groupby("rango", observed=False)["tiene_modificacion"].mean() * 100

                self.ax4.plot(grouped.index.astype(str), grouped.values, marker="o", linestyle="-", color="#27ae60", linewidth=2)
                self.ax4.set_title("Probabilidad de Modificación vs Presupuesto", fontsize=11, fontweight="bold")
                self.ax4.set_ylabel("% probabilidad", fontsize=9)
                self.ax4.grid(True, linestyle=":", alpha=0.6)
                for i, val in enumerate(grouped.values):
                    if pd.notna(val):
                        self.ax4.annotate(f"{val:.1f}%", (i, val), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)
                self.fig4.tight_layout()
        except Exception as e:
            print(f"Error grafica presupuesto vs riesgo: {e}")
        self.canvas4.draw()

        # 7. Gráfica 5: Top Entidades con mayor tasa de modificación (%)
        self.ax5.clear()
        try:
            data = self.gestor.analytics_top_entidades(min_contratos=20, limite=10)
            if data:
                procesada = []
                for entidad, total, con_mod in data:
                    tasa = (con_mod / total) * 100 if total else 0.0
                    procesada.append((str(entidad), tasa, total))

                procesada.sort(key=lambda x: x[1], reverse=True)
                entidades = [p[0][:26] for p in procesada]
                tasas = [p[1] for p in procesada]

                bars = self.ax5.barh(entidades, tasas, color="#8e44ad")
                self.ax5.invert_yaxis()
                self.ax5.set_title("Top Entidades con Mayor Tasa de Modificación (%)", fontsize=11, fontweight="bold")
                self.ax5.set_xlabel("% contratos con modificación", fontsize=9)
                self.ax5.bar_label(bars, fmt="%.1f%%", padding=3, fontsize=8)
                self.fig5.subplots_adjust(left=0.38)
                self.fig5.tight_layout()
        except Exception as e:
            print(f"Error grafica top entidades: {e}")
        self.canvas5.draw()

        # 8. Gráfica 6: Adiciones por mes (tendencia)
        self.ax6.clear()
        try:
            serie = self.gestor.analytics_adiciones_por_mes(limite_meses=36)
            if serie:
                meses = [s[0] for s in serie]
                conteos = [s[1] for s in serie]

                self.ax6.plot(meses, conteos, marker="o", color="#2980b9", linewidth=2)
                self.ax6.set_title("Adiciones por Mes (últimos 36 meses)", fontsize=11, fontweight="bold")
                self.ax6.set_ylabel("# adiciones", fontsize=9)
                self.ax6.tick_params(axis="x", rotation=45, labelsize=8)
                self.ax6.tick_params(axis="y", labelsize=8)
                self.ax6.grid(True, linestyle=":", alpha=0.6)
                self.fig6.tight_layout()
            else:
                self.ax6.text(0.5, 0.5, "Sin adiciones\ncon fecha", ha="center", va="center")
                self.fig6.tight_layout()
        except Exception as e:
            print(f"Error grafica adiciones por mes: {e}")
        self.canvas6.draw()

