import os
import pandas as pd
import numpy as np
from datetime import date, datetime
from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker, joinedload
from src.database.models import Base, Proyecto, Adicion, DatosFinancieros

# Definir la ruta de la base de datos
RUTA_DB = os.path.join("data", "base_datos_app.db")
URL_DATABASE = f"sqlite:///{RUTA_DB}"

class GestorBaseDatos:
    def __init__(self):
        """Inicializa la conexión a la base de datos."""
        self.engine = create_engine(URL_DATABASE, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Crear tablas si no existen
        self._crear_tablas()

    def _crear_tablas(self):
        """Crea las tablas en la base de datos SQLite basado en los modelos."""
        Base.metadata.create_all(bind=self.engine)

    def obtener_sesion(self):
        """Devuelve una nueva sesión de base de datos."""
        return self.SessionLocal()

    def guardar_dataframe(self, df: pd.DataFrame):
        """
        Recibe un DataFrame de Pandas con datos del SECOP y los guarda en la BD.
        Mapea las columnas automáticamente.
        """
        if df.empty:
            return 0

        # --- NUEVO: Limpieza Previa ---
        # 1. Eliminar duplicados en el DataFrame basado en 'referencia_del_contrato'
        if 'referencia_del_contrato' in df.columns:
            df = df.drop_duplicates(subset=['referencia_del_contrato'], keep='first')

        # Reemplazar NaN/NaT con None
        df = df.replace({np.nan: None})

        session = self.obtener_sesion()
        try:
            contador_nuevos = 0
            ids_existentes = {res[0] for res in session.query(Proyecto.id).all()}

            for _, row in df.iterrows():
                contrato_id = str(row.get('referencia_del_contrato', ''))
                if not contrato_id or contrato_id == 'None' or contrato_id == 'nan':
                    continue 
                if contrato_id in ids_existentes:
                    continue 

                # Helpers de limpieza
                def clean_float(val):
                    if val is None: return 0.0
                    try: return float(val)
                    except: return 0.0
                
                def clean_int(val):
                    if val is None: return 0
                    try: return int(float(val))
                    except: return 0
                
                def clean_date(val):
                    if pd.isna(val): return None
                    if isinstance(val, (date, datetime)):
                        return val if isinstance(val, date) and not isinstance(val, datetime) else val.date()
                    try:
                        if hasattr(val, 'to_pydatetime'):
                            return val.to_pydatetime().date()
                        if isinstance(val, str):
                            return datetime.fromisoformat(val.replace('T', ' ').split('.')[0]).date()
                    except: pass
                    return None
                
                def clean_bool(val):
                    if val is None: return False
                    if isinstance(val, str):
                        return val.lower() in ['si', 'sí', 'true', 'yes']
                    return bool(val)

                # 3. Crear Proyecto
                nuevo_proyecto = Proyecto(
                    id=contrato_id,
                    nombre_entidad=row.get('nombre_entidad'),
                    nombre_proyecto=row.get('objeto_del_contrato') or "No definido",
                    presupuesto_inicial=clean_float(row.get('valor_del_contrato')),
                    fecha_inicio=clean_date(row.get('fecha_de_inicio_del_contrato')),
                    fecha_fin=clean_date(row.get('fecha_de_fin_del_contrato')),
                    departamento=row.get('departamento'),
                    municipio=row.get('ciudad'),
                    tipo_contrato=row.get('tipo_de_contrato'),
                    es_prorrogable=clean_bool(row.get('el_contrato_puede_ser_prorrogado')),
                    fecha_ultima_prorroga=clean_date(row.get('fecha_de_notificaci_n_de_prorrogaci_n'))
                )
                session.add(nuevo_proyecto)
                
                # 4. Crear Adicion (si aplica)
                val_adiciones = clean_float(row.get('valor_total_de_adiciones'))
                dias_adicionados = clean_int(row.get('dias_adicionados'))
                
                if val_adiciones > 0 or dias_adicionados > 0:
                    fecha_adicion = clean_date(row.get('fecha_de_firma'))
                    nueva_adicion = Adicion(
                        proyecto_id=contrato_id,
                        fecha=fecha_adicion,
                        valor_adicionado=val_adiciones,
                        tiempo_adicionado_dias=dias_adicionados,
                        descripcion="Modificaciones reportadas en SECOP"
                    )
                    session.add(nueva_adicion)

                # 5. NUEVO: Guardar Datos Financieros (Origen de Recursos)
                pgn = clean_float(row.get('presupuesto_general_de_la_nacion_pgn'))
                sgp = clean_float(row.get('sistema_general_de_participaciones'))
                regalias = clean_float(row.get('sistema_general_de_regal_as'))
                credito = clean_float(row.get('recursos_de_credito'))
                
                # Sumar recursos propios (puede venir en dos campos diferentes)
                rec_propios = clean_float(row.get('recursos_propios')) + \
                              clean_float(row.get('recursos_propios_alcald_as_gobernaciones_y_resguardos_ind_genas_'))
                
                # Solo creamos el registro si hay algún dato financiero relevante
                if pgn > 0 or sgp > 0 or regalias > 0 or credito > 0 or rec_propios > 0:
                    datos_fin = DatosFinancieros(
                        proyecto_id=contrato_id,
                        pgn=pgn,
                        sgp=sgp,
                        regalias=regalias,
                        recursos_credito=credito,
                        recursos_propios=rec_propios
                    )
                    session.add(datos_fin)
                
                contador_nuevos += 1
            
            session.commit()
            print(f"Guardados {contador_nuevos} proyectos nuevos en la base de datos.")
            return contador_nuevos

        except Exception as e:
            session.rollback()
            print(f"Error guardando batch de proyectos: {e}")
            raise e
        finally:
            session.close()

    def obtener_todos_proyectos(self):
        """Obtiene la lista de todos los proyectos (PARA ENTRENAMIENTO)."""
        session = self.obtener_sesion()
        # Usar joinedload para cargar las adiciones en la misma consulta
        proyectos = session.query(Proyecto).options(joinedload(Proyecto.adiciones)).all()
        session.close()
        return proyectos

    def obtener_ultimos_proyectos(self, limite=100):
        """Obtiene los últimos N proyectos (PARA DASHBOARD)."""
        session = self.obtener_sesion()
        # Ordenar por fecha de inicio descendente (o por ID si fecha no existe)
        proyectos = session.query(Proyecto).order_by(desc(Proyecto.fecha_inicio)).limit(limite).all()
        session.close()
        return proyectos
        
    def obtener_kpis_globales(self):
        """
        Calcula KPIs usando SQL directo para máxima velocidad.
        Retorna: (total_proyectos, suma_presupuesto)
        """
        session = self.obtener_sesion()
        try:
            total = session.query(func.count(Proyecto.id)).scalar()
            suma = session.query(func.sum(Proyecto.presupuesto_inicial)).scalar() or 0.0
            return total, suma
        except Exception:
            return 0, 0.0
        finally:
            session.close()

    def obtener_top_departamentos(self):
        """Top 5 departamentos por número de contratos (SQL Group By)."""
        session = self.obtener_sesion()
        try:
            res = session.query(Proyecto.departamento, func.count(Proyecto.id))\
                .group_by(Proyecto.departamento)\
                .order_by(desc(func.count(Proyecto.id)))\
                .limit(5).all()
            return res # Lista de tuplas (Depto, Cantidad)
        finally:
            session.close()

    def obtener_tipos_contrato(self):
        """Top 5 tipos de contrato (SQL Group By)."""
        session = self.obtener_sesion()
        try:
            res = session.query(Proyecto.tipo_contrato, func.count(Proyecto.id))\
                .group_by(Proyecto.tipo_contrato)\
                .order_by(desc(func.count(Proyecto.id)))\
                .limit(5).all()
            return res # Lista de tuplas (Tipo, Cantidad)
        finally:
            session.close()
