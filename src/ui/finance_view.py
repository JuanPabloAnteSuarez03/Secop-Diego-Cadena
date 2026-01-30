from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QDoubleSpinBox,
    QComboBox,
    QFrame,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
)
from PyQt6.QtCore import Qt

from pathlib import Path

from src.services.finance import (
    ViabilityInputs,
    calcular_viabilidad,
    sugerir_credito_desde_capital,
)


def _fmt_money(x: float) -> str:
    return f"${x:,.0f}"


def _fmt_pct(x: float) -> str:
    return f"{x * 100:.2f}%"


class VistaFinanciera(QWidget):
    """
    Calculadora rápida de viabilidad:
    - costo_estimado = valor_venta * %costo
    - financiamiento = capital + crédito (principal)
    - intereses según tasa/plazo/tipo de crédito
    """

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.recalcular()

    def init_ui(self):
        # Para que no se “corte” en pantallas pequeñas o con DPI alto, usamos scroll.
        root = QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # --- Estilo local (mejora legibilidad en Windows/Fusion) ---
        assets_dir = Path(__file__).resolve().parent / "assets"
        up_arrow = (assets_dir / "arrow_up.svg").as_posix()
        down_arrow = (assets_dir / "arrow_down.svg").as_posix()

        # Nota: usamos rutas absolutas para que Qt encuentre los SVG en Windows.
        self.setStyleSheet(
            f"""
            QLineEdit, QComboBox, QAbstractSpinBox {{
                background: white;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 6px 10px;
                min-height: 34px;
            }}

            QLineEdit:hover, QComboBox:hover, QAbstractSpinBox:hover {{
                border: 1px solid #3498db;
            }}

            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 26px;
                border-left: 1px solid #bdc3c7;
                background: #ecf0f1;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }}
            QComboBox::drop-down:hover {{
                background: #dfe6e9;
            }}
            QComboBox::down-arrow {{
                image: url("{down_arrow}");
                width: 10px;
                height: 10px;
            }}

            /* Popup del ComboBox: hover/selección visibles */
            QComboBox QAbstractItemView {{
                background: white;
                color: #2c3e50;
                selection-background-color: #3498db;
                selection-color: white;
                outline: 0;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background: #eaf2fb;
                color: #2c3e50;
            }}

            /* Botones arriba/abajo del SpinBox: visibles (no blancos) */
            QAbstractSpinBox {{
                padding-right: 32px; /* espacio para botones */
            }}
            QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {{
                subcontrol-origin: border;
                background: #ecf0f1;
                width: 18px;
                border-left: 1px solid #bdc3c7;
            }}
            QAbstractSpinBox::up-button {{
                subcontrol-position: top right;
                border-top-right-radius: 6px;
            }}
            QAbstractSpinBox::down-button {{
                subcontrol-position: bottom right;
                border-bottom-right-radius: 6px;
            }}
            QAbstractSpinBox::up-button:hover, QAbstractSpinBox::down-button:hover {{
                background: #dfe6e9;
            }}
            QAbstractSpinBox::up-arrow {{
                image: url("{up_arrow}");
                width: 10px;
                height: 10px;
            }}
            QAbstractSpinBox::down-arrow {{
                image: url("{down_arrow}");
                width: 10px;
                height: 10px;
            }}

            /* Botones: altura consistente para evitar recortes con escalado */
            QPushButton {{
                min-height: 34px;
            }}
            """
        )

        # --- Encabezado ---
        header = QHBoxLayout()
        titulo = QLabel("Calculadora de Viabilidad Financiera")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")

        self.btn_calcular = QPushButton("Calcular")
        self.btn_calcular.setStyleSheet(
            """
            QPushButton {
                padding: 8px 14px;
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1e8449;
            }
            QPushButton:pressed {
                background-color: #186a3b;
            }
            """
        )
        self.btn_calcular.clicked.connect(self.recalcular)

        header.addWidget(titulo)
        header.addStretch()
        header.addWidget(self.btn_calcular)
        layout.addLayout(header)

        # --- Formulario ---
        form = QFrame()
        form.setStyleSheet(
            "background-color: white; border: 1px solid #bdc3c7; border-radius: 8px; padding: 12px;"
        )
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        # Cols: etiqueta / input / etiqueta / input (+ botón en col 4 cuando aplique)
        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 4)
        grid.setColumnStretch(2, 3)
        grid.setColumnStretch(3, 4)
        grid.setColumnStretch(4, 2)

        def mk_label(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setWordWrap(True)  # evita cortes: se parte en 2 líneas si es necesario
            lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            return lbl

        # Valor de venta
        grid.addWidget(mk_label("Valor de venta (ingreso) ($):"), 0, 0)
        self.spin_venta = QDoubleSpinBox()
        self.spin_venta.setRange(0, 1e13)
        self.spin_venta.setDecimals(0)
        self.spin_venta.setValue(100_000_000)
        self.spin_venta.valueChanged.connect(self.recalcular)
        self.spin_venta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        grid.addWidget(self.spin_venta, 0, 1)

        # % costo sobre venta
        grid.addWidget(mk_label("% costo sobre venta:"), 1, 0)
        self.spin_costo_pct = QDoubleSpinBox()
        self.spin_costo_pct.setRange(0, 150)
        self.spin_costo_pct.setDecimals(2)
        self.spin_costo_pct.setSuffix(" %")
        self.spin_costo_pct.setValue(80.0)
        self.spin_costo_pct.valueChanged.connect(self.recalcular)
        self.spin_costo_pct.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        grid.addWidget(self.spin_costo_pct, 1, 1)

        # Modo capital
        grid.addWidget(mk_label("Capital (modo):"), 2, 0)
        self.combo_capital_modo = QComboBox()
        self.combo_capital_modo.addItems(["Porcentaje del costo", "Monto ($)"])
        self.combo_capital_modo.currentIndexChanged.connect(self._on_capital_mode_changed)
        self.combo_capital_modo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        grid.addWidget(self.combo_capital_modo, 2, 1)

        # Capital % del costo
        grid.addWidget(mk_label("Capital (% del costo):"), 3, 0)
        self.spin_capital_pct = QDoubleSpinBox()
        self.spin_capital_pct.setRange(0, 100)
        self.spin_capital_pct.setDecimals(2)
        self.spin_capital_pct.setSuffix(" %")
        self.spin_capital_pct.setValue(20.0)
        self.spin_capital_pct.valueChanged.connect(self.recalcular)
        self.spin_capital_pct.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        grid.addWidget(self.spin_capital_pct, 3, 1)

        # Capital monto
        grid.addWidget(mk_label("Capital (monto) ($):"), 4, 0)
        self.spin_capital_monto = QDoubleSpinBox()
        self.spin_capital_monto.setRange(0, 1e13)
        self.spin_capital_monto.setDecimals(0)
        self.spin_capital_monto.setValue(20_000_000)
        self.spin_capital_monto.valueChanged.connect(self.recalcular)
        self.spin_capital_monto.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        grid.addWidget(self.spin_capital_monto, 4, 1)

        # Crédito principal (auto, editable)
        grid.addWidget(mk_label("Crédito (principal) ($):"), 5, 0)
        self.spin_credito = QDoubleSpinBox()
        self.spin_credito.setRange(0, 1e13)
        self.spin_credito.setDecimals(0)
        self.spin_credito.setValue(60_000_000)
        self.spin_credito.valueChanged.connect(self.recalcular)
        self.spin_credito.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        grid.addWidget(self.spin_credito, 5, 1)

        # Botón sugerir crédito = costo - capital
        self.btn_sugerir = QPushButton("Sugerir crédito = costo - capital")
        self.btn_sugerir.setStyleSheet(
            """
            QPushButton {
                padding: 6px 10px;
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2e86c1;
            }
            QPushButton:pressed {
                background-color: #2471a3;
            }
            """
        )
        self.btn_sugerir.clicked.connect(self.sugerir_credito)
        grid.addWidget(self.btn_sugerir, 5, 2)

        # Feedback de sugerencia (para que no "parezca" que no hizo nada)
        self.lbl_sugerencia = QLabel("")
        self.lbl_sugerencia.setStyleSheet("color: #2c3e50; font-size: 12px;")
        grid.addWidget(self.lbl_sugerencia, 6, 1, 1, 3)

        # Tasa anual
        grid.addWidget(mk_label("Tasa de interés (%):"), 0, 2)
        self.spin_tasa = QDoubleSpinBox()
        self.spin_tasa.setRange(0, 200)
        self.spin_tasa.setDecimals(2)
        self.spin_tasa.setSuffix(" %")
        self.spin_tasa.setValue(18.0)
        self.spin_tasa.valueChanged.connect(self.recalcular)
        self.spin_tasa.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.combo_tasa_tipo = QComboBox()
        self.combo_tasa_tipo.addItems(["Anual", "Mensual"])
        self.combo_tasa_tipo.currentIndexChanged.connect(self.recalcular)
        self.combo_tasa_tipo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        tasa_container = QWidget()
        tasa_layout = QHBoxLayout(tasa_container)
        tasa_layout.setContentsMargins(0, 0, 0, 0)
        tasa_layout.setSpacing(8)
        tasa_layout.addWidget(self.spin_tasa)
        tasa_layout.addWidget(self.combo_tasa_tipo)
        grid.addWidget(tasa_container, 0, 3)

        # Plazo meses
        grid.addWidget(mk_label("Plazo (meses):"), 1, 2)
        self.spin_plazo = QDoubleSpinBox()
        self.spin_plazo.setRange(1, 600)
        self.spin_plazo.setDecimals(0)
        self.spin_plazo.setValue(12)
        self.spin_plazo.valueChanged.connect(self.recalcular)
        self.spin_plazo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        grid.addWidget(self.spin_plazo, 1, 3)

        # Tipo crédito
        grid.addWidget(mk_label("Tipo de crédito:"), 2, 2)
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Pago al final (bullet)", "Cuotas fijas (amortizado)"])
        self.combo_tipo.currentIndexChanged.connect(self.recalcular)
        self.combo_tipo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        grid.addWidget(self.combo_tipo, 2, 3)

        form.setLayout(grid)
        layout.addWidget(form)

        # --- Resultados ---
        self.card_resultados = QFrame()
        self.card_resultados.setStyleSheet(
            "background-color: #f8f9fa; border: 1px solid #dfe6e9; border-radius: 8px; padding: 12px;"
        )
        res_layout = QVBoxLayout()

        self.lbl_estado = QLabel("Listo.")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setStyleSheet("font-size: 16px; font-weight: bold; padding: 8px;")
        res_layout.addWidget(self.lbl_estado)

        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_resumen.setStyleSheet("font-size: 13px;")
        res_layout.addWidget(self.lbl_resumen)

        self.card_resultados.setLayout(res_layout)
        layout.addWidget(self.card_resultados)

        layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)
        self.setLayout(root)

        self._on_capital_mode_changed()

    def _on_capital_mode_changed(self):
        modo_pct = self.combo_capital_modo.currentIndex() == 0
        self.spin_capital_pct.setEnabled(modo_pct)
        self.spin_capital_monto.setEnabled(not modo_pct)
        self.recalcular()

    def _capital_aportado(self, costo_estimado: float) -> float:
        if self.combo_capital_modo.currentIndex() == 0:
            pct = self.spin_capital_pct.value() / 100.0
            return max(costo_estimado * pct, 0.0)
        return float(self.spin_capital_monto.value())

    def sugerir_credito(self):
        try:
            costo_estimado = self.spin_venta.value() * (self.spin_costo_pct.value() / 100.0)
            capital = self._capital_aportado(costo_estimado)
            sugerido = sugerir_credito_desde_capital(costo_estimado, capital)
            anterior = float(self.spin_credito.value())
            self.spin_credito.blockSignals(True)
            self.spin_credito.setValue(sugerido)
            self.spin_credito.blockSignals(False)
            self.recalcular()
            # Mensaje claro incluso si el valor no cambia (p.ej. ya era 0)
            if abs(sugerido - anterior) < 0.5:
                self.lbl_sugerencia.setText(f"Crédito sugerido: {_fmt_money(sugerido)} (sin cambios)")
            else:
                self.lbl_sugerencia.setText(f"Crédito sugerido: {_fmt_money(sugerido)}")
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"No se pudo sugerir el crédito:\n{e}")

    def recalcular(self):
        try:
            valor_venta = float(self.spin_venta.value())
            costo_pct = float(self.spin_costo_pct.value()) / 100.0
            costo_estimado = valor_venta * costo_pct

            # --- Sincronizar % <-> monto para consistencia visual ---
            # (sin disparar recalcular en bucle)
            if self.combo_capital_modo.currentIndex() == 0:
                # Modo %: el monto se deriva del costo estimado
                pct = self.spin_capital_pct.value() / 100.0
                monto_derivado = max(costo_estimado * pct, 0.0)
                if abs(float(self.spin_capital_monto.value()) - monto_derivado) >= 0.5:
                    self.spin_capital_monto.blockSignals(True)
                    self.spin_capital_monto.setValue(monto_derivado)
                    self.spin_capital_monto.blockSignals(False)
            else:
                # Modo monto: el % se deriva del costo estimado (si existe)
                monto = float(self.spin_capital_monto.value())
                pct_derivado = 0.0
                if costo_estimado > 0:
                    pct_derivado = (monto / costo_estimado) * 100.0
                # Limitar a rango visible del spin
                pct_derivado = max(0.0, min(100.0, pct_derivado))
                if abs(float(self.spin_capital_pct.value()) - pct_derivado) >= 0.01:
                    self.spin_capital_pct.blockSignals(True)
                    self.spin_capital_pct.setValue(pct_derivado)
                    self.spin_capital_pct.blockSignals(False)

            capital = self._capital_aportado(costo_estimado)
            credito = float(self.spin_credito.value())
            tasa_ingresada = float(self.spin_tasa.value()) / 100.0
            # finance.py usa tasa_anual y la convierte a mensual (tasa_anual/12).
            # Si el usuario ingresa tasa mensual, la convertimos a anual equivalente (x12).
            tasa_anual = tasa_ingresada if self.combo_tasa_tipo.currentIndex() == 0 else (tasa_ingresada * 12.0)
            plazo_meses = int(self.spin_plazo.value())
            tipo_credito = "bullet" if self.combo_tipo.currentIndex() == 0 else "amortizado"

            res = calcular_viabilidad(
                ViabilityInputs(
                    valor_venta=valor_venta,
                    costo_pct_sobre_venta=costo_pct,
                    capital_aportado=capital,
                    credito=credito,
                    tasa_anual=tasa_anual,
                    plazo_meses=plazo_meses,
                    tipo_credito=tipo_credito,
                )
            )

            if res.viable:
                self.lbl_estado.setText("✅ Viable (utilidad positiva)")
                self.lbl_estado.setStyleSheet(
                    "font-size: 16px; font-weight: bold; padding: 8px; color: #1e8449;"
                )
            else:
                self.lbl_estado.setText("❌ No viable (utilidad negativa)")
                self.lbl_estado.setStyleSheet(
                    "font-size: 16px; font-weight: bold; padding: 8px; color: #c0392b;"
                )

            pago_mensual_txt = "—"
            if res.pago_mensual is not None:
                pago_mensual_txt = _fmt_money(res.pago_mensual)

            margen_txt = "—"
            if res.margen is not None:
                margen_txt = _fmt_pct(res.margen)

            roe_txt = "—"
            if res.roe is not None:
                roe_txt = _fmt_pct(res.roe)

            tasa_txt = (
                f"{self.spin_tasa.value():.2f}% anual"
                if self.combo_tasa_tipo.currentIndex() == 0
                else f"{self.spin_tasa.value():.2f}% mensual"
            )

            self.lbl_resumen.setText(
                "<b>Resumen</b><br/>"
                f"- Valor de venta: <b>{_fmt_money(valor_venta)}</b><br/>"
                f"- Costo estimado ({self.spin_costo_pct.value():.2f}%): <b>{_fmt_money(res.costo_estimado)}</b><br/>"
                f"- Capital aportado: <b>{_fmt_money(res.capital_aportado)}</b><br/>"
                f"- Crédito (principal): <b>{_fmt_money(res.credito)}</b><br/>"
                f"- Tasa usada: <b>{tasa_txt}</b><br/>"
                f"- Intereses estimados: <b>{_fmt_money(res.interes_total)}</b><br/>"
                f"- Total pagado por el crédito: <b>{_fmt_money(res.total_pagado_credito)}</b><br/>"
                f"- Pago mensual (si aplica): <b>{pago_mensual_txt}</b><br/>"
                f"- Costo total proyecto (costo + intereses): <b>{_fmt_money(res.costo_total_proyecto)}</b><br/>"
                f"- Utilidad estimada: <b>{_fmt_money(res.utilidad)}</b><br/>"
                f"- Margen (utilidad/venta): <b>{margen_txt}</b><br/>"
                f"- ROI sobre capital (utilidad/capital): <b>{roe_txt}</b>"
            )

        except Exception as e:
            self.lbl_estado.setText("⚠️ Revise los valores ingresados")
            self.lbl_estado.setStyleSheet(
                "font-size: 16px; font-weight: bold; padding: 8px; color: #b9770e;"
            )
            self.lbl_resumen.setText(f"Detalle: {e}")


