from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class ViabilityInputs:
    valor_venta: float
    costo_pct_sobre_venta: float  # e.g. 0.80
    capital_aportado: float  # $ (parte del costo que no se financia con crédito)
    credito: float  # $ (principal)
    tasa_anual: float  # e.g. 0.18
    plazo_meses: int
    tipo_credito: str  # "bullet" | "amortizado"


@dataclass(frozen=True)
class ViabilityResult:
    costo_estimado: float
    capital_aportado: float
    credito: float
    interes_total: float
    total_pagado_credito: float
    pago_mensual: float | None
    costo_total_proyecto: float
    utilidad: float
    margen: float | None  # utilidad / valor_venta
    roe: float | None  # utilidad / capital
    viable: bool


def _clamp01(x: float) -> float:
    if x < 0:
        return 0.0
    if x > 1:
        return 1.0
    return x


def _validate(inputs: ViabilityInputs) -> None:
    if inputs.valor_venta < 0:
        raise ValueError("El valor de venta no puede ser negativo.")
    if not (0 <= inputs.costo_pct_sobre_venta <= 1.5):
        raise ValueError("El % de costo sobre venta debe estar entre 0% y 150%.")
    if inputs.capital_aportado < 0:
        raise ValueError("El capital aportado no puede ser negativo.")
    if inputs.credito < 0:
        raise ValueError("El crédito no puede ser negativo.")
    if inputs.tasa_anual < 0:
        raise ValueError("La tasa anual no puede ser negativa.")
    if inputs.plazo_meses <= 0:
        raise ValueError("El plazo debe ser mayor a 0 meses.")
    if inputs.tipo_credito not in ("bullet", "amortizado"):
        raise ValueError("Tipo de crédito inválido.")


def calcular_viabilidad(inputs: ViabilityInputs) -> ViabilityResult:
    """
    Modelo simple:
    - costo_estimado = valor_venta * costo_pct
    - costo se cubre con capital + crédito (principal). Intereses se suman al costo total.
    - utilidad = valor_venta - costo_estimado - interes_total
    """
    _validate(inputs)

    costo_estimado = inputs.valor_venta * inputs.costo_pct_sobre_venta

    # Sanitizar capital/credito contra el costo (no obligamos, pero si excede lo tratamos igual)
    capital = max(0.0, float(inputs.capital_aportado))
    credito = max(0.0, float(inputs.credito))

    tasa_mensual = inputs.tasa_anual / 12.0
    n = int(inputs.plazo_meses)

    if credito == 0:
        interes_total = 0.0
        total_pagado_credito = 0.0
        pago_mensual = None
    elif inputs.tipo_credito == "bullet":
        # Pago único al final: FV = PV*(1+i)^n
        fv = credito * ((1.0 + tasa_mensual) ** n)
        interes_total = fv - credito
        total_pagado_credito = fv
        pago_mensual = None
    else:
        # Amortizado (cuotas fijas): PMT = PV * i*(1+i)^n / ((1+i)^n - 1)
        if tasa_mensual == 0:
            pago_mensual = credito / n
            total_pagado_credito = pago_mensual * n
            interes_total = total_pagado_credito - credito
        else:
            factor = (1.0 + tasa_mensual) ** n
            pago_mensual = credito * (tasa_mensual * factor) / (factor - 1.0)
            total_pagado_credito = pago_mensual * n
            interes_total = total_pagado_credito - credito

    # Costo total: costo base (materiales, predio, mano de obra, etc.) + intereses del crédito
    costo_total_proyecto = costo_estimado + interes_total
    utilidad = inputs.valor_venta - costo_total_proyecto

    margen = None
    if inputs.valor_venta > 0:
        margen = utilidad / inputs.valor_venta

    roe = None
    if capital > 0:
        roe = utilidad / capital

    # Viable: utilidad positiva (modelo simple)
    viable = (utilidad >= 0) and isfinite(utilidad)

    return ViabilityResult(
        costo_estimado=costo_estimado,
        capital_aportado=capital,
        credito=credito,
        interes_total=interes_total,
        total_pagado_credito=total_pagado_credito,
        pago_mensual=pago_mensual,
        costo_total_proyecto=costo_total_proyecto,
        utilidad=utilidad,
        margen=margen,
        roe=roe,
        viable=viable,
    )


def sugerir_credito_desde_capital(costo_estimado: float, capital_aportado: float) -> float:
    """Crédito requerido para completar el costo: max(costo - capital, 0)."""
    costo = max(0.0, float(costo_estimado))
    capital = max(0.0, float(capital_aportado))
    return max(costo - capital, 0.0)


