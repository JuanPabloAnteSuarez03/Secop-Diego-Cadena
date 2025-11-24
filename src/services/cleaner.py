import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

class DataCleaner:
    def __init__(self):
        self.encoders = {}

    def preparar_datos_entrenamiento(self, proyectos):
        """
        Recibe una lista de objetos Proyecto (SQLAlchemy) y devuelve un DataFrame
        listo para entrenar modelos de ML.
        """
        if not proyectos:
            return pd.DataFrame()

        # 1. Convertir a DataFrame plano
        data = []
        for p in proyectos:
            # Calcular si tuvo riesgo (adiciones en dinero o tiempo)
            total_adiciones_dinero = sum([a.valor_adicionado for a in p.adiciones])
            total_adiciones_dias = sum([a.tiempo_adicionado_dias for a in p.adiciones])
            
            tiene_riesgo = 1 if (total_adiciones_dinero > 0 or total_adiciones_dias > 0) else 0
            
            # Calcular duración estimada en días (si hay fechas)
            duracion_dias = 0
            if p.fecha_inicio and p.fecha_fin:
                try:
                    delta = p.fecha_fin - p.fecha_inicio
                    duracion_dias = delta.days
                except:
                    duracion_dias = 0

            row = {
                'presupuesto': p.presupuesto_inicial or 0,
                'duracion_estimada': duracion_dias,
                'tipo_contrato': p.tipo_contrato or "Desconocido",
                'departamento': p.departamento or "Desconocido",
                'entidad': p.nombre_entidad or "Desconocida",
                'target_riesgo': tiene_riesgo
            }
            data.append(row)

        df = pd.DataFrame(data)

        # 2. Limpieza y Codificación (Encoding)
        
        # A. Codificar DEPARTAMENTO (Label Encoding)
        le_depto = LabelEncoder()
        df['depto_encoded'] = le_depto.fit_transform(df['departamento'].astype(str))
        self.encoders['departamento'] = le_depto

        # B. Codificar TIPO CONTRATO (Label Encoding)
        le_tipo = LabelEncoder()
        df['tipo_encoded'] = le_tipo.fit_transform(df['tipo_contrato'].astype(str))
        self.encoders['tipo_contrato'] = le_tipo

        # C. Codificar ENTIDAD (Frequency Encoding - Mejor para muchas categorías)
        # Reemplazamos el nombre por qué tan frecuente es esa entidad (0 a 1)
        # Esto ayuda al modelo a saber si es una entidad que contrata mucho o poco.
        freq = df['entidad'].value_counts() / len(df)
        df['entidad_freq'] = df['entidad'].map(freq)

        # Seleccionar columnas finales para el modelo
        features = ['presupuesto', 'duracion_estimada', 'depto_encoded', 'tipo_encoded', 'entidad_freq']
        X = df[features].fillna(0)
        y = df['target_riesgo']

        return X, y, df # Retornamos también el DF completo para visualización si se requiere

    def preparar_datos_prediccion(self, datos_entrada):
        """
        Prepara un solo registro (o lista) para predecir, usando los encoders ya entrenados.
        datos_entrada: dict con keys ['presupuesto', 'duracion', 'tipo', 'departamento', 'entidad_freq']
        """
        # Nota: Para producción real, deberíamos guardar los encoders en disco (pickle).
        # Para este prototipo, asumiremos que se re-entrena o los encoders están en memoria.
        pass

