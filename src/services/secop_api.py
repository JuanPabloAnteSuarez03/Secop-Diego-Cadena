import pandas as pd
from sodapy import Socrata
from typing import List, Dict, Optional
from src.utils.config import Config

# ID del Dataset de SECOP II en Datos Abiertos (Contratos Electrónicos)
DATASET_ID_SECOP_II = "jbjy-vk9h" 
URL_DATOS_GOV = "www.datos.gov.co"

class ClienteSecop:
    def __init__(self):
        """
        Inicializa el cliente de Socrata para SECOP II usando token de config.
        """
        self.client = Socrata(URL_DATOS_GOV, Config.SECOP_APP_TOKEN)
        # Aumentar el tiempo de espera para descargas grandes
        self.client.timeout = 60

    def obtener_contratos(self, 
                          limite: int = 1000, 
                          departamento: Optional[str] = None, 
                          municipio: Optional[str] = None,
                          year: Optional[int] = None) -> List[Dict]:
        """
        Descarga contratos del SECOP II aplicando filtros básicos.
        """
        try:
            # Construir filtros (cláusula WHERE de SoQL)
            filtros = {}
            # Nota: Nombres de columnas corregidos según el error 400 recibido
            # departamento_entidad -> departamento
            # ciudad_entidad -> ciudad
            
            # Construir la consulta SoQL
            where_clause = "valor_del_contrato > 0" # Filtro base para evitar basura
            
            if departamento:
                if "Bogotá" in departamento:
                    # Manejo especial para Bogotá que a veces es D.C. y a veces no
                    where_clause += f" AND (departamento LIKE '%Bogot%')"
                else:
                    where_clause += f" AND departamento = '{departamento}'"
            
            if municipio:
                where_clause += f" AND ciudad = '{municipio}'"
            if year:
                where_clause += f" AND date_extract_y(fecha_de_firma) = '{year}'"

            # Ejecutar consulta
            resultados = self.client.get(
                DATASET_ID_SECOP_II,
                limit=limite,
                where=where_clause,
                order="fecha_de_firma DESC" # Traer los más recientes primero
            )
            
            return resultados

        except Exception as e:
            print(f"Error conectando a SECOP: {e}")
            return []

    def convertir_a_dataframe(self, datos: List[Dict]) -> pd.DataFrame:
        """Convierte la lista de resultados JSON en un DataFrame de Pandas limpio."""
        if not datos:
            return pd.DataFrame()
            
        df = pd.DataFrame.from_records(datos)
        
        # Convertir columnas numéricas
        cols_numericas = ['valor_del_contrato', 'valor_total_de_adiciones']
        for col in cols_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        # Convertir fechas
        cols_fechas = ['fecha_de_firma', 'fecha_de_inicio_del_contrato', 'fecha_de_fin_del_contrato']
        for col in cols_fechas:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                
        return df

