
import os
from pathlib import Path

from dotenv import load_dotenv


# 1. CARGAR VARIABLES DE ENTORNO
load_dotenv(Path(__file__).with_name(".env"))


# 2. CONFIGURACIÓN DE POSTGRESQL
class Config:
    PGHOST = os.getenv("PGHOST", "db")
    PGPORT = int(os.getenv("PGPORT", "5432"))
    PGDATABASE = os.getenv("PGDATABASE")
    PGUSER = os.getenv("PGUSER")
    PGPASSWORD = os.getenv("PGPASSWORD")


# 3. INSTANCIA DE CONFIGURACIÓN
config = Config()
