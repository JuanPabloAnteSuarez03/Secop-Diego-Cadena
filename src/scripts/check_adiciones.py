import pandas as pd
from sodapy import Socrata
from src.utils.config import Config

# ID del Dataset de SECOP II
DATASET_ID = "jbjy-vk9h" 
URL_DATOS_GOV = "www.datos.gov.co"

def verificar_adiciones():
    print("🔍 Verificando si existen contratos con ADICIONES DE DINERO en SECOP...")
    
    client = Socrata(URL_DATOS_GOV, Config.SECOP_APP_TOKEN)
    client.timeout = 60

    try:
        # Consulta SoQL específica: "Trae 5 contratos donde valor_total_de_adiciones sea mayor a 0"
        query = "valor_total_de_adiciones > 0"
        
        results = client.get(
            DATASET_ID,
            where=query,
            limit=5,
            order="valor_total_de_adiciones DESC" # Traer los más grandes
        )

        if not results:
            print("❌ RESULTADO: La API devolvió 0 registros. Parece que la columna no se usa o está vacía.")
        else:
            print(f"✅ ÉXITO: Se encontraron contratos con adiciones de dinero.")
            for i, r in enumerate(results):
                print(f"\n--- Contrato {i+1} ---")
                print(f"ID: {r.get('referencia_del_contrato')}")
                print(f"Objeto: {r.get('objeto_del_contrato')}")
                print(f"Presupuesto: ${float(r.get('valor_del_contrato', 0)):,.0f}")
                print(f"ADICIÓN: ${float(r.get('valor_total_de_adiciones', 0)):,.0f}")
                print(f"Link: {r.get('urlproceso', {}).get('url', 'N/A')}")

    except Exception as e:
        print(f"🔥 Error conectando a la API: {e}")

if __name__ == "__main__":
    verificar_adiciones()

