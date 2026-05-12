from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any


def _now_date() -> date:
    return datetime.now(timezone.utc).date()


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    candidate = str(value).strip()
    if not candidate:
        return None

    for parser in (
        lambda raw: datetime.fromisoformat(raw.replace("Z", "+00:00")).date(),
        lambda raw: datetime.strptime(raw[:10], "%Y-%m-%d").date(),
    ):
        try:
            return parser(candidate)
        except Exception:
            continue
    return None


def build_hive_health_summary(hive: Any, reference_date: date | None = None) -> dict:
    today = reference_date or _now_date()
    score = 100
    alerts: list[str] = []
    recommended_actions: list[str] = []
    flags: list[str] = []

    status = str(getattr(hive, "status", "") or "")
    normalized_status = _normalize_text(status)
    if normalized_status == "malo":
        score -= 25
        flags.append("poor_status")
        alerts.append("La colmena está en estado malo.")
        recommended_actions.append("Realizá una revisión completa y prioritaria de la colmena.")
    elif normalized_status == "medio":
        score -= 12
        flags.append("medium_status")
        alerts.append("La colmena está en estado medio y necesita seguimiento.")

    queen_status = _normalize_text(getattr(hive, "queenStatus", "unknown"))
    if queen_status == "absent":
        score -= 35
        flags.append("queen_absent")
        alerts.append("No hay reina registrada en la colmena.")
        recommended_actions.append("Confirmá huérfandad y planificá recambio o unión.")
    elif queen_status == "unknown":
        score -= 15
        flags.append("queen_unknown")
        alerts.append("No está claro el estado de la reina.")
        recommended_actions.append("Verificá postura fresca y presencia de reina en la próxima visita.")

    hive_strength = _normalize_text(getattr(hive, "hiveStrength", "medium"))
    if hive_strength == "weak":
        score -= 20
        flags.append("weak_hive")
        alerts.append("La fortaleza de la colmena es débil.")
        recommended_actions.append("Evaluá refuerzo, alimentación o reducción de espacio.")
    elif hive_strength == "medium":
        score -= 5

    disease = str(getattr(hive, "disease", "") or "").strip()
    if disease:
        score -= 25
        flags.append("disease_reported")
        alerts.append(f"Se registró problema sanitario: {disease}.")
        recommended_actions.append("Aislá la observación y seguí un protocolo sanitario específico.")

    if bool(getattr(hive, "swarming", False)):
        score -= 15
        flags.append("swarming_risk")
        alerts.append("La colmena tiene señal de enjambrazón.")
        recommended_actions.append("Revisá espacio disponible, celdas reales y equilibrio poblacional.")

    inspection_date = _parse_date(getattr(hive, "lastInspection", None))
    last_inspection_days = None
    if inspection_date:
        last_inspection_days = max((today - inspection_date).days, 0)
        if last_inspection_days > 45:
            score -= 18
            flags.append("inspection_stale_critical")
            alerts.append(f"Hace {last_inspection_days} días que no se registra revisión.")
            recommended_actions.append("Programá una visita prioritaria para actualizar el estado real.")
        elif last_inspection_days > 30:
            score -= 10
            flags.append("inspection_stale")
            alerts.append(f"La última revisión fue hace {last_inspection_days} días.")
    else:
        score -= 12
        flags.append("inspection_missing")
        alerts.append("No hay fecha de última revisión.")
        recommended_actions.append("Registrá una inspección sanitaria para tener trazabilidad.")

    population = int(getattr(hive, "population", 0) or 0)
    brood_frames = int(getattr(hive, "broodFrames", 0) or 0)
    honey_frames = int(getattr(hive, "honeyFrames", 0) or 0)
    pollen_frames = int(getattr(hive, "pollenFrames", 0) or 0)

    if population <= 3:
        score -= 12
        flags.append("low_population")
        alerts.append("La población registrada es baja.")
        recommended_actions.append("Controlá reservas y evaluá capacidad de recuperación.")

    if brood_frames == 0 and population > 0:
        score -= 10
        flags.append("no_brood")
        alerts.append("No se registraron cuadros de cría.")
        recommended_actions.append("Verificá si hay postura reciente o problemas de reina.")

    if honey_frames == 0 and pollen_frames == 0:
        score -= 8
        flags.append("low_frames_reserves")
        alerts.append("No hay cuadros de miel ni de polen registrados.")
        recommended_actions.append("Evaluá reservas y necesidad de alimentación de apoyo.")

    if pollen_frames == 0 and brood_frames > 0:
        score -= 5
        flags.append("low_pollen")
        alerts.append("Hay cría pero no se registran reservas de polen.")

    numeric_reserves = float(getattr(hive, "honey", 0) or 0) + float(getattr(hive, "sugar", 0) or 0)
    if numeric_reserves <= 1:
        score -= 10
        flags.append("low_reserves")
        alerts.append("Las reservas registradas son bajas.")
        recommended_actions.append("Revisá disponibilidad de alimento y flujo de néctar en la zona.")

    score = max(0, min(score, 100))
    health_status = "critica" if score < 50 else "atencion" if score < 75 or len(flags) > 0 else "estable"

    # Deduplicar manteniendo orden
    unique_actions = list(dict.fromkeys(recommended_actions))
    unique_alerts = list(dict.fromkeys(alerts))
    unique_flags = list(dict.fromkeys(flags))

    return {
        "score": score,
        "status": health_status,
        "alerts": unique_alerts,
        "recommendedActions": unique_actions,
        "flags": unique_flags,
        "lastInspectionDays": last_inspection_days,
    }
