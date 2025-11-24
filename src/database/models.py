from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Proyecto(Base):
    __tablename__ = 'proyectos'

    id = Column(String, primary_key=True)  # Número del Contrato / Proceso
    nombre_entidad = Column(String)
    nombre_proyecto = Column(String)
    presupuesto_inicial = Column(Float)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date) # Fecha final prevista inicial
    departamento = Column(String)
    municipio = Column(String)
    tipo_contrato = Column(String) # Licitación, directa, etc.
    
    # Nuevos campos solicitados
    es_prorrogable = Column(Boolean, default=False)
    fecha_ultima_prorroga = Column(Date, nullable=True)
    
    # Relaciones
    adiciones = relationship("Adicion", back_populates="proyecto")
    datos_financieros = relationship("DatosFinancieros", uselist=False, back_populates="proyecto")

class Adicion(Base):
    __tablename__ = 'adiciones'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id = Column(String, ForeignKey('proyectos.id'))
    fecha = Column(Date)
    valor_adicionado = Column(Float, default=0.0) # Valor adicionado en dinero
    tiempo_adicionado_dias = Column(Integer, default=0) # Tiempo adicionado en días
    descripcion = Column(String)
    
    proyecto = relationship("Proyecto", back_populates="adiciones")

class DatosFinancieros(Base):
    __tablename__ = 'datos_financieros'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id = Column(String, ForeignKey('proyectos.id'))
    
    # Fuentes de Financiación (Origen de Recursos SECOP)
    pgn = Column(Float, default=0.0) # Presupuesto General Nación
    sgp = Column(Float, default=0.0) # Sist. Gral Participaciones
    regalias = Column(Float, default=0.0) # Sist. Gral Regalías
    recursos_propios = Column(Float, default=0.0) # Entidad / Alcaldías
    recursos_credito = Column(Float, default=0.0) # Crédito
    
    # Resultados simulados (se llenarán después del análisis)
    puntaje_riesgo = Column(Float) # 0 a 1
    margen_predicho = Column(Float)
    
    proyecto = relationship("Proyecto", back_populates="datos_financieros")
