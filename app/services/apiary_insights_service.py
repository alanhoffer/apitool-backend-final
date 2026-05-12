from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.apiary import Apiary
from app.models.hive import Hive
from app.models.task import Task
from app.services.health_service import build_hive_health_summary
from app.services.weather_service import WeatherService


class ApiaryInsightsService:
    def __init__(self, db: Session):
        self.db = db

    async def get_apiary_insights(self, apiary: Apiary) -> dict:
        hives = self.db.query(Hive).filter(Hive.apiaryId == apiary.id, Hive.userId == apiary.userId).all()
        tasks = self.db.query(Task).filter(Task.apiary_id == apiary.id, Task.user_id == apiary.userId).all()
        weather = await self._get_weather_insight(apiary)

        hive_summaries = [build_hive_health_summary(hive) for hive in hives]
        attention_hives = [summary for summary in hive_summaries if summary["status"] != "estable"]
        critical_hives = [summary for summary in hive_summaries if summary["status"] == "critica"]

        pending_task_count = sum(1 for task in tasks if not task.completed)
        overdue_task_count = sum(
            1 for task in tasks
            if not task.completed and task.due_date and task.due_date.date() < self._today()
        )

        queen_issue_count = sum(1 for summary in hive_summaries if "queen_absent" in summary["flags"] or "queen_unknown" in summary["flags"])
        weak_hive_count = sum(1 for summary in hive_summaries if "weak_hive" in summary["flags"])
        low_reserve_count = sum(1 for summary in hive_summaries if "low_reserves" in summary["flags"] or "low_frames_reserves" in summary["flags"])
        disease_count = sum(1 for summary in hive_summaries if "disease_reported" in summary["flags"])
        stale_count = sum(1 for summary in hive_summaries if "inspection_stale" in summary["flags"] or "inspection_stale_critical" in summary["flags"] or "inspection_missing" in summary["flags"])
        swarming_count = sum(1 for summary in hive_summaries if "swarming_risk" in summary["flags"])

        apiary_reserves = float(apiary.honey or 0) + float(apiary.sugar or 0)
        apiary_score = self._compute_apiary_score(
            hive_summaries=hive_summaries,
            overdue_task_count=overdue_task_count,
            low_reserve_count=low_reserve_count,
            apiary_reserves=apiary_reserves,
        )
        apiary_status = "critica" if apiary_score < 50 else "atencion" if apiary_score < 75 or overdue_task_count > 0 else "estable"

        recommendations: list[dict[str, Any]] = []

        if disease_count > 0:
            recommendations.append({
                "priority": "high",
                "title": "Priorizar colmenas con problema sanitario",
                "description": f"{disease_count} colmena(s) registran signos sanitarios o enfermedad. Conviene aislar observación y revisar protocolo.",
                "affectedHives": disease_count,
            })

        if queen_issue_count > 0:
            recommendations.append({
                "priority": "high",
                "title": "Revisar estado de reina",
                "description": f"{queen_issue_count} colmena(s) no tienen reina clara o la muestran ausente. Confirmá postura y definí recambio o unión.",
                "affectedHives": queen_issue_count,
            })

        if swarming_count > 0:
            recommendations.append({
                "priority": "medium",
                "title": "Bajar riesgo de enjambrazón",
                "description": f"{swarming_count} colmena(s) muestran presión de enjambrazón. Revisá espacio, celdas reales y balance poblacional.",
                "affectedHives": swarming_count,
            })

        if weak_hive_count > 0:
            recommendations.append({
                "priority": "medium",
                "title": "Refuerzo o seguimiento a colmenas débiles",
                "description": f"{weak_hive_count} colmena(s) están débiles. Priorizá evaluación de reservas, reina y fortaleza real.",
                "affectedHives": weak_hive_count,
            })

        if low_reserve_count > 0 or apiary_reserves <= 2:
            description = (
                f"{low_reserve_count} colmena(s) tienen reservas bajas."
                if low_reserve_count > 0
                else "Las reservas a nivel apiario son bajas."
            )
            recommendations.append({
                "priority": "medium",
                "title": "Controlar reservas y alimentación",
                "description": f"{description} Evaluá apoyo alimenticio según floración y clima del día.",
                "affectedHives": low_reserve_count,
            })

        if stale_count > 0:
            recommendations.append({
                "priority": "medium",
                "title": "Actualizar inspecciones sanitarias",
                "description": f"{stale_count} colmena(s) tienen revisión vieja o sin fecha. Conviene refrescar datos antes de decidir tratamientos.",
                "affectedHives": stale_count,
            })

        if overdue_task_count > 0:
            recommendations.append({
                "priority": "high",
                "title": "Resolver tareas vencidas del apiario",
                "description": f"Hay {overdue_task_count} tarea(s) vencida(s) vinculadas a este apiario. Cerralas o reagendalas para no perder seguimiento.",
                "affectedHives": 0,
            })

        if weather:
            if weather["inspectionWindow"] == "desfavorable":
                recommendations.append({
                    "priority": "low",
                    "title": "Elegir mejor ventana de inspección",
                    "description": "El clima actual no es ideal para abrir colmenas. Si no es urgente, esperá una ventana más templada y con menos viento.",
                    "affectedHives": 0,
                })
            elif weather["inspectionWindow"] == "favorable" and attention_hives:
                recommendations.append({
                    "priority": "low",
                    "title": "Aprovechar la ventana climática",
                    "description": "El clima actual es razonable para inspección. Es un buen momento para visitar primero las colmenas con alertas.",
                    "affectedHives": len(attention_hives),
                })

        if not recommendations:
            recommendations.append({
                "priority": "low",
                "title": "Apiario estable",
                "description": "No aparecen alertas fuertes con la información disponible. Mantené el ritmo normal de visitas y registro.",
                "affectedHives": 0,
            })

        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda item: (priority_order.get(item["priority"], 99), -item.get("affectedHives", 0)))

        return {
            "apiaryId": apiary.id,
            "apiaryName": apiary.name,
            "managementType": apiary.managementType or "apiary",
            "healthScore": apiary_score,
            "healthStatus": apiary_status,
            "attentionHiveCount": len(attention_hives),
            "criticalHiveCount": len(critical_hives),
            "pendingTaskCount": pending_task_count,
            "overdueTaskCount": overdue_task_count,
            "weather": weather,
            "recommendations": recommendations[:5],
        }

    async def _get_weather_insight(self, apiary: Apiary) -> Optional[dict]:
        if apiary.latitude is None or apiary.longitude is None:
            return None

        try:
            payload = await WeatherService().get_weather(float(apiary.latitude), float(apiary.longitude))
        except HTTPException:
            return None
        except Exception:
            return None

        current = payload.get("current") or {}
        temp_c = current.get("temp_c")
        wind_kph = current.get("wind_kph")
        humidity = current.get("humidity")
        condition_text = ((current.get("condition") or {}).get("text")) or None

        inspection_window = "favorable"
        condition_normalized = str(condition_text or "").lower()
        if (
            temp_c is None
            or wind_kph is None
            or temp_c < 14
            or wind_kph > 25
            or "rain" in condition_normalized
            or "storm" in condition_normalized
        ):
            inspection_window = "desfavorable"
        elif humidity is not None and humidity >= 85:
            inspection_window = "con_precaucion"

        return {
            "temperatureC": temp_c,
            "feelsLikeC": current.get("feelslike_c"),
            "humidity": humidity,
            "windKph": wind_kph,
            "condition": condition_text,
            "inspectionWindow": inspection_window,
        }

    def _compute_apiary_score(
        self,
        hive_summaries: list[dict],
        overdue_task_count: int,
        low_reserve_count: int,
        apiary_reserves: float,
    ) -> int:
        if hive_summaries:
            average_score = sum(summary["score"] for summary in hive_summaries) / len(hive_summaries)
        else:
            average_score = 78

        score = average_score
        if overdue_task_count > 0:
            score -= min(12, overdue_task_count * 4)
        if low_reserve_count > 0:
            score -= min(10, low_reserve_count * 3)
        if apiary_reserves <= 2:
            score -= 8

        return max(0, min(int(round(score)), 100))

    def _today(self):
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).date()
