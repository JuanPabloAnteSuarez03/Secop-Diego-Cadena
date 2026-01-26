import os
from dotenv import load_dotenv

from src.utils.paths import ensure_user_file

# Cargar variables desde .env_local (o .env)
load_dotenv(dotenv_path=".env_local")

class Config:
    SECOP_APP_TOKEN = os.getenv("SECOP_APP_TOKEN")
    SECOP_API_SECRET = os.getenv("SECOP_API_SECRET")
    
    # Base de datos
    # Copiamos una DB inicial a una carpeta escribible del usuario (mejor para .exe / instalador)
    # Ojo: para SQLAlchemy/SQLite en Windows es más robusto usar forward slashes (C:/...)
    DB_PATH = ensure_user_file("data/base_datos_app.db", "base_datos_app.db").as_posix()
    # Alias para compatibilidad
    URL_DATABASE = f"sqlite:///{DB_PATH}"
