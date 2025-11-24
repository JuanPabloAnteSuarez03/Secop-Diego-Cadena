import sys
import os
import time
import random
from datetime import datetime
from src.services.secop_api import ClienteSecop
from src.database.db_manager import GestorBaseDatos

# Lista completa de departamentos de Colombia (normalizada para SECOP)
DEPARTAMENTOS_COLOMBIA = [
    "Amazonas", "Antioquia", "Arauca", "Atlántico", "Bolívar", 
    "Boyacá", "Caldas", "Caquetá", "Casanare", "Cauca", 
    "Cesar", "Chocó", "Córdoba", "Cundinamarca", "Bogotá D.C.", 
    "Guainía", "Guaviare", "Huila", "La Guajira", "Magdalena", 
    "Meta", "Nariño", "Norte de Santander", "Putumayo", "Quindío", 
    "Risaralda", "San Andrés, Providencia y Santa Catalina", "Santander", 
    "Sucre", "Tolima", "Valle del Cauca", "Vaupés", "Vichada"
]

def borrar_base_datos():
    """Elimina el archivo de base de datos si existe."""
    ruta_db = os.path.join("data", "base_datos_app.db")
    if os.path.exists(ruta_db):
        try:
            os.remove(ruta_db)
            print("🗑️  Base de datos antigua eliminada con éxito.")
        except Exception as e:
            print(f"⚠️  No se pudo borrar la BD: {e}")
    else:
        print("ℹ️  No existía base de datos previa.")

def seed_database():
    print("🚀 Iniciando RE-INGESTA TOTAL de Datos SECOP...")
    
    # 1. Borrar BD antigua para empezar limpio
    borrar_base_datos()
    
    # 2. Inicializar gestor (esto crea las tablas vacías de nuevo)
    cliente = ClienteSecop()
    gestor = GestorBaseDatos()
    
    # Años a consultar (Ventana histórica relevante)
    anios = [2020, 2021, 2022, 2023]
    
    total_descargados = 0
    errores = 0
    
    start_time = time.time()

    print(f"🌎 Consultando {len(DEPARTAMENTOS_COLOMBIA)} departamentos por {len(anios)} años...")

    for depto in DEPARTAMENTOS_COLOMBIA:
        print(f"\n📍 DEPARTAMENTO: {depto.upper()}")
        
        for anio in anios:
            try:
                print(f"   📅 Año {anio}...", end=" ")
                
                # Descargar lote
                resultados = cliente.obtener_contratos(
                    departamento=depto,
                    limite=10000, # Lote grande
                    year=anio
                )
                
                if not resultados:
                    print("⚠️  (0 encontrados)")
                    continue
                
                df = cliente.convertir_a_dataframe(resultados)
                
                # Guardar
                nuevos = gestor.guardar_dataframe(df)
                total_descargados += nuevos
                
                print(f"✅ (+{nuevos} contratos)")
                
                # Pausa anti-bloqueo
                time.sleep(1.0) 
                
            except Exception as e:
                print(f"\n   ❌ Error: {e}")
                errores += 1
                time.sleep(2)

    duration = (time.time() - start_time) / 60
    print("\n" + "="*50)
    print(f"🏁 PROCESO FINALIZADO en {duration:.1f} minutos.")
    print(f"📊 Total Contratos en BD: {total_descargados}")
    print(f"💀 Errores de conexión: {errores}")
    print("="*50)

if __name__ == "__main__":
    seed_database()
