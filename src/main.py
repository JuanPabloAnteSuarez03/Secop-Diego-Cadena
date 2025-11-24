import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from src.ui.download_view import VistaDescarga
from src.ui.dashboard import Dashboard
from src.ui.ml_view import VistaML

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

        # Pestaña 2: Inteligencia Artificial (Nuevo)
        self.vista_ml = VistaML()
        self.tabs.addTab(self.vista_ml, "Predicción de Riesgo (IA)")

        # Pestaña 3: Descarga de Datos
        self.vista_descarga = VistaDescarga()
        self.tabs.addTab(self.vista_descarga, "Gestión de Datos SECOP")


def main():
    app = QApplication(sys.argv)
    
    # Aplicar un estilo visual básico (Fusion)
    app.setStyle("Fusion")
    
    window = VentanaPrincipal()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
