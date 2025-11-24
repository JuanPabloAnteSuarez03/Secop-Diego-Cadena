import os
from dotenv import load_dotenv

# Cargar variables desde .env_local (o .env)
load_dotenv(dotenv_path=".env_local")

class Config:
    SECOP_APP_TOKEN = os.getenv("SECOP_APP_TOKEN")
    SECOP_API_SECRET = os.getenv("SECOP_API_SECRET")
    
    # Base de datos
    DB_PATH = os.path.join("data", "base_datos_app.db")
    DB_URL = f"sqlite:///{DB_PATH}"

