import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from src.database.db_manager import GestorBaseDatos

class MotorMonteCarlo:
    def __init__(self):
        self.stats_tiempos = None
        self.entrenado = False

    def calibrar_con_historia(self):
        """
        Analiza la distribución histórica de RETRASOS en TIEMPO.
        Usamos el tiempo como proxy del riesgo financiero.
        """
        print("\n--- CALIBRANDO MOTOR MONTE CARLO (vía Tiempo) ---")
        gestor = GestorBaseDatos()
        proyectos = gestor.obtener_todos_proyectos()
        
        if not proyectos:
            return False

        factores_tiempo = []
        
        for p in proyectos:
            # Calcular duración original estimada
            duracion_orig = 0
            if p.fecha_inicio and p.fecha_fin:
                try:
                    delta = (p.fecha_fin - p.fecha_inicio).days
                    if delta > 0:
                        duracion_orig = delta
                except:
                    pass
            
            # Solo analizamos contratos donde tengamos datos de tiempo válidos (> 30 días)
            if duracion_orig > 30: 
                # Si hubo adiciones de tiempo
                dias_extra = sum([a.tiempo_adicionado_dias for a in p.adiciones])
                
                # Factor = (Tiempo Real) / (Tiempo Planeado)
                # INCLUIMOS LOS QUE NO TIENEN ADICIONES (dias_extra = 0) -> Factor 1.0
                tiempo_total = duracion_orig + dias_extra
                factor = tiempo_total / duracion_orig
                
                # Filtros de sanidad (evitar errores extremos)
                if 0.5 <= factor <= 10.0:
                    factores_tiempo.append(factor)

        print(f"⏱️ Muestra de Tiempos Total (Sanos + Retrasados): {len(factores_tiempo)} contratos")
        
        if factores_tiempo:
            # Ajuste Log-Normal sobre los FACTORES DE TIEMPO
            log_data = np.log(factores_tiempo)
            mu_t = np.mean(log_data)
            sigma_t = np.std(log_data)
            
            print(f"   • Drift Tiempo (mu): {mu_t:.4f}")
            print(f"   • Volatilidad Tiempo (sigma): {sigma_t:.4f}")
            
            self.stats_tiempos = (mu_t, sigma_t)
        else:
            # Fallback conservador si no hay datos
            self.stats_tiempos = (0.05, 0.15) 

        self.entrenado = True
        return True

    def simular(self, presupuesto_inicial, duracion_dias=180, n_iteraciones=10000):
        if not self.entrenado:
            self.calibrar_con_historia()

        mu_base, sigma_base = self.stats_tiempos
        
        # --- REINTRODUCIENDO ESCALAMIENTO DE TIEMPO ---
        # La volatilidad histórica (sigma_base) corresponde al promedio de contratos.
        # Asumiremos que esa sigma base es para un contrato típico de ~6 meses (180 días).
        # Si el proyecto nuevo dura más, la incertidumbre crece (Difusión).
        
        TIEMPO_REF = 180.0
        if duracion_dias < 1: duracion_dias = 1
        
        # Escalamiento de Volatilidad (Ley de la Raíz Cuadrada del Tiempo)
        factor_escala = np.sqrt(duracion_dias / TIEMPO_REF)
        
        # Ajustamos la sigma para ESTE proyecto específico
        sigma_proyecto = sigma_base * factor_escala
        
        # Ajustamos la media (drift) linealmente con el tiempo
        # (Si dura el doble, es probable que se retrase el doble en proporción)
        mu_proyecto = mu_base * (duracion_dias / TIEMPO_REF)

        # 1. Simular Factores de Retraso (Tiempo) con parámetros ajustados
        factores_tiempo_simulados = np.random.lognormal(mu_proyecto, sigma_proyecto, n_iteraciones)
        
        # 2. Traducir Retraso a Sobrecosto Financiero
        # Modelo de Impacto Indirecto (Costos Variables en el Tiempo)
        COSTO_INDIRECTO_PCT = 0.20
        
        costos_finales = (presupuesto_inicial * (1 - COSTO_INDIRECTO_PCT)) + \
                         (presupuesto_inicial * COSTO_INDIRECTO_PCT * factores_tiempo_simulados)

        # Estadísticas
        resultados = {
            "costos_simulados": costos_finales,
            "media": np.mean(costos_finales),
            "p50": np.percentile(costos_finales, 50),
            "p90": np.percentile(costos_finales, 90),
            "p95": np.percentile(costos_finales, 95),
            "probabilidad_sobrecosto": np.mean(costos_finales > presupuesto_inicial * 1.01) # Margen 1%
        }
        
        return resultados

    def graficar_resultados(self, resultados, presupuesto_inicial):
        costos = resultados["costos_simulados"]
        fig, ax = plt.subplots(figsize=(6, 4))
        
        n, bins, patches = ax.hist(costos, bins=50, density=True, alpha=0.6, color='#9b59b6', label='Escenarios Simulados')
        
        ax.axvline(presupuesto_inicial, color='green', linestyle='--', linewidth=2, label='Presupuesto Inicial')
        ax.axvline(resultados['p90'], color='red', linestyle='--', linewidth=2, label='Riesgo P90')

        # AJUSTE VISUAL: Forzar límites del eje X para que la gráfica sea comprensible
        # Mostramos un rango de +/- 20% alrededor del presupuesto, o el rango real de datos si es mayor.
        min_view = min(presupuesto_inicial * 0.8, min(costos))
        max_view = max(presupuesto_inicial * 1.2, max(costos))
        ax.set_xlim(min_view, max_view)

        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:,.0f}M'))
        ax.set_title("Distribución de Costo Final (Impacto por Retrasos)")
        ax.set_xlabel("Costo Final Estimado")
        ax.legend()
        
        return fig
