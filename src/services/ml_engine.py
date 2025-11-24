import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from src.services.cleaner import DataCleaner
from src.database.db_manager import GestorBaseDatos

class MotorIA:
    def __init__(self):
        self.cleaner = DataCleaner()
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.entrenado = False
        self.feature_names = []

    def entrenar(self):
        """
        Carga datos de la BD, los limpia y entrena el modelo.
        Retorna un diccionario con métricas de rendimiento.
        """
        print("🧠 Entrenando Modelo de IA...")
        gestor = GestorBaseDatos()
        proyectos = gestor.obtener_todos_proyectos()
        
        if not proyectos or len(proyectos) < 10:
            return {"error": "No hay suficientes datos para entrenar (Mínimo 10)."}

        # Limpieza y Preparación
        X, y, df_completo = self.cleaner.preparar_datos_entrenamiento(proyectos)
        self.feature_names = X.columns.tolist()

        # Split Train/Test (80% entrenamiento, 20% validación)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Entrenamiento
        self.model.fit(X_train, y_train)
        self.entrenado = True

        # Evaluación
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Feature Importance (¿Qué variables importan más?)
        importancias = dict(zip(self.feature_names, self.model.feature_importances_))
        # Ordenar por importancia
        importancias = dict(sorted(importancias.items(), key=lambda item: item[1], reverse=True))

        print(f"✅ Modelo Entrenado. Precisión: {accuracy:.2%}")
        
        return {
            "precision": accuracy,
            "total_datos": len(proyectos),
            "importancia_variables": importancias,
            "reporte": classification_report(y_test, y_pred, output_dict=True)
        }

    def predecir_riesgo(self, presupuesto, duracion_dias, departamento, tipo_contrato, entidad_freq=0.01):
        """
        Predice el riesgo de un NUEVO proyecto hipotético.
        """
        if not self.entrenado:
            return None

        # Codificar entradas usando los encoders del cleaner (si existen)
        try:
            # Manejo seguro de encoders (fallback a 0 si no existe la categoría)
            le_depto = self.cleaner.encoders.get('departamento')
            depto_code = 0
            if le_depto:
                try: depto_code = le_depto.transform([departamento])[0]
                except: depto_code = 0 # Default si el depto no se conoce

            le_tipo = self.cleaner.encoders.get('tipo_contrato')
            tipo_code = 0
            if le_tipo:
                try: tipo_code = le_tipo.transform([tipo_contrato])[0]
                except: tipo_code = 0

            input_data = pd.DataFrame([{
                'presupuesto': presupuesto,
                'duracion_estimada': duracion_dias,
                'depto_encoded': depto_code,
                'tipo_encoded': tipo_code,
                'entidad_freq': entidad_freq
            }])
            
            # Asegurar orden de columnas igual al entrenamiento
            input_data = input_data[self.feature_names]

            probabilidad = self.model.predict_proba(input_data)[0][1] # Probabilidad de clase 1 (Riesgo)
            clase = self.model.predict(input_data)[0]

            return {
                "riesgo_alto": bool(clase == 1),
                "probabilidad": float(probabilidad)
            }

        except Exception as e:
            print(f"Error en predicción: {e}")
            return None

