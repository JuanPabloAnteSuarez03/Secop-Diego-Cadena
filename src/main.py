import sys
from pathlib import Path

# Allow running this file directly (e.g., `python src/main.py`) by ensuring the
# project root (parent of `src/`) is on sys.path so `import src...` works.
if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))


from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QSplashScreen
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette

def _crear_splash() -> QSplashScreen:
    """
    Splash simple (sin archivos externos) para dar feedback mientras cargan imports pesados.
    Nota: no puede cubrir el tiempo antes de que Python arranque, pero sí el de imports/montaje UI.
    """
    w, h = 520, 220
    pixmap = QPixmap(w, h)
    pixmap.fill(QColor("#f8f9fa"))

    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QColor("#2c3e50"))

    title_font = QFont("Segoe UI", 16)
    title_font.setBold(True)
    p.setFont(title_font)
    p.drawText(20, 70, "SistemaContratos")

    sub_font = QFont("Segoe UI", 10)
    p.setFont(sub_font)
    p.setPen(QColor("#7f8c8d"))
    p.drawText(20, 100, "Iniciando aplicación...")
    p.end()

    splash = QSplashScreen(pixmap)
    splash.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
    return splash


def _forzar_tema_claro(app: QApplication) -> None:
    """
    Fuerza un tema claro independiente del modo oscuro del SO.
    Esto evita que Windows "Dark Mode" cambie la paleta de la app.
    """
    app.setStyle("Fusion")

    pal = QPalette()
    # Base UI
    pal.setColor(QPalette.ColorRole.Window, QColor("#f8f9fa"))
    pal.setColor(QPalette.ColorRole.WindowText, QColor("#2c3e50"))
    pal.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor("#f2f4f7"))
    pal.setColor(QPalette.ColorRole.Text, QColor("#2c3e50"))
    pal.setColor(QPalette.ColorRole.Button, QColor("#ecf0f1"))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor("#2c3e50"))

    # Accents / selection
    pal.setColor(QPalette.ColorRole.Highlight, QColor("#3498db"))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))

    # Links / tooltips
    pal.setColor(QPalette.ColorRole.Link, QColor("#2e86c1"))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor("#2c3e50"))

    # Disabled (en PyQt6: Disabled es un ColorGroup, no un ColorRole)
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor("#95a5a6"))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#95a5a6"))
    pal.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#95a5a6"))

    app.setPalette(pal)

    # Asegurar fondos claros también vía stylesheet (cubre widgets que ignoran paleta en algunos estilos)
    app.setStyleSheet(
        """
        QWidget { background-color: #f8f9fa; color: #2c3e50; }
        QFrame { background-color: transparent; }
        QToolTip { background-color: #ffffff; color: #2c3e50; border: 1px solid #bdc3c7; }
        """
    )


def main():
    app = QApplication(sys.argv)

    # Forzar tema claro (no depende del modo oscuro del sistema)
    _forzar_tema_claro(app)

    splash = _crear_splash()
    splash.show()
    splash.showMessage("Cargando módulos...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, QColor("#2c3e50"))
    app.processEvents()

    # Imports pesados DESPUÉS del splash, para que el usuario vea feedback
    from src.ui.dashboard import Dashboard
    splash.showMessage("Cargando Dashboard...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, QColor("#2c3e50"))
    app.processEvents()

    from src.ui.ml_view import VistaML
    splash.showMessage("Cargando módulo de IA...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, QColor("#2c3e50"))
    app.processEvents()

    from src.ui.finance_view import VistaFinanciera
    splash.showMessage("Cargando calculadora financiera...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, QColor("#2c3e50"))
    app.processEvents()

    class VentanaPrincipal(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Sistema de Inteligencia de Contratos - Obras Civiles")
            self.setGeometry(100, 100, 1200, 800)

            # Widget central con Pestañas
            self.tabs = QTabWidget()
            self.setCentralWidget(self.tabs)

            # Pestaña 1: Dashboard (Resumen)
            self.dashboard = Dashboard()
            self.tabs.addTab(self.dashboard, "Dashboard General")

            # Pestaña 2: Inteligencia Artificial
            self.vista_ml = VistaML()
            self.tabs.addTab(self.vista_ml, "Predicción de Riesgo (IA)")

            # Pestaña 4: Viabilidad Financiera
            self.vista_financiera = VistaFinanciera()
            self.tabs.addTab(self.vista_financiera, "Viabilidad Financiera")

    splash.showMessage("Abriendo ventana...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft, QColor("#2c3e50"))
    app.processEvents()

    window = VentanaPrincipal()
    window.show()
    splash.finish(window)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
