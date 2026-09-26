"""Ejecuta una simulacion tecnica POST aislada usando el pipeline real de CarBot.

No escribe en PostgreSQL, no altera modelos ni datos PRE/POST oficiales. Los
artefactos resultantes se identifican como SIMULACION_POST y son solo para
verificar la captura de las fichas antes del trabajo de campo oficial.
"""

from __future__ import annotations

import csv
import json
import sys
import time
import unicodedata
from datetime import date, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from src.core.gestor_diagnostico import GestorDiagnostico


ESTADO = "SIMULACION_POST"
CONFIG_COMPLETITUD = "CAMPOS_COMPLETITUD_PENDIENTES_DE_VALIDACION"
SALIDA = ROOT / "docs" / "simulaciones_tecnicas" / "simulacion_post_202609"

# Referencias de prueba definidas antes de ejecutar. No son fallas confirmadas
# físicamente y nunca se usan como datos oficiales de tesis.
CASOS = [
    ("El motor se apaga al detenerme en el semáforo y vuelve a encender después.", "Cuerpo de aceleración o válvula IAC sucia"),
    ("En frío demora bastante en arrancar, el motor gira pero recién prende al segundo intento.", "Batería descargada o bornes sulfatados"),
    ("En subida no responde al acelerador y pierde fuerza con el aire acondicionado encendido.", "Inyectores sucios o filtro de combustible obstruido"),
    ("El motor tironea, tiembla en ralentí y se encendió check engine después de lluvia.", "Falla en bujías o bobinas de encendido (misfire)"),
    ("Al acelerar siento jaloneos y por el escape sale olor fuerte a gasolina.", "Inyectores sucios o filtro de combustible obstruido"),
    ("Las revoluciones suben y bajan solas cuando el auto está detenido.", "Cuerpo de aceleración o válvula IAC sucia"),
    ("La aguja de temperatura sube rápido y el depósito de refrigerante baja cada semana.", "Fuga de refrigerante o bomba de agua defectuosa"),
    ("El ventilador no entra y el motor se recalienta en tráfico lento.", "Falla en termostato o motoventilador de radiador"),
    ("Se escucha un chillido por la parte delantera del motor al encender el aire acondicionado.", "Correa de accesorios floja o desgastada"),
    ("Al frenar el volante vibra y el pedal late como si rebotara.", "Discos de freno alabeados o desgastados"),
    ("El pedal se va hasta abajo y debo bombear para que el vehículo frene.", "Fuga hidráulica o aire en sistema de frenos"),
    ("Al girar a la derecha se oye un zumbido que aumenta con la velocidad.", "Rodamiento de rueda desgastado"),
    ("En los baches suena clac clac adelante y el auto se siente inestable.", "Bieletas de la barra estabilizadora desgastadas"),
    ("Una rueda quedó inclinada y el neumático se desgasta solo por el borde interior.", "Amortiguador o componente de suspensión desgastado"),
    ("El auto rebota varias veces después de pasar un rompemuelles.", "Amortiguadores desgastados"),
    ("El motor enciende check engine, gasta más gasolina y falla al acelerar.", "Sensor de oxígeno defectuoso"),
    ("Marca error de mezcla pobre y se siente poca fuerza al salir desde parado.", "Sensor MAF sucio o defectuoso"),
    ("El velocímetro deja de marcar intermitentemente y aparece check engine.", "Sensor de velocidad defectuoso"),
    ("En primera el motor revoluciona pero el carro casi no avanza y huele a quemado.", "Disco de embrague desgastado o patinando"),
    ("Cuesta entrar los cambios y el pedal de embrague se queda pegado abajo.", "Falla en bombín o bomba hidráulica de embrague"),
    ("Al dar arranque solo se escucha un clic, las luces del tablero bajan de intensidad.", "Batería descargada o bornes sulfatados"),
    ("La batería se descarga aunque es nueva y la luz de batería prende mientras manejo.", "Alternador defectuoso o placa de diodos quemada"),
    ("Las luces parpadean y el tablero se apaga por segundos al acelerar.", "Mala masa eléctrica o terminales de batería sulfatados"),
    ("El motor no enciende después de cargar combustible; se siente olor a gasolina.", "Bomba de gasolina con baja presión"),
    ("Al acelerar a fondo pierde potencia y da tirones, como si no llegara combustible.", "Bomba de gasolina con baja presión"),
    ("Enciende, pero luego de unos minutos empieza a fallar un cilindro y vibra todo el motor.", "Falla en bujías o bobinas de encendido (misfire)"),
    ("Cuando suelto el acelerador se apaga; el ralentí es muy bajo e inestable.", "Cuerpo de aceleración o válvula IAC sucia"),
    ("Sube la temperatura en carretera y se escucha un ruido metálico cerca de la bomba de agua.", "Fuga de refrigerante o bomba de agua defectuosa"),
    ("Al frenar fuerte el vehículo se desvía hacia un lado y una rueda queda caliente.", "Caliper de freno trabado"),
    ("Se oye un golpeteo al pasar pistas maltratadas y la dirección tiene juego.", "Holgura en rótulas o terminales de dirección"),
]

# Oráculo experimental fijado antes de ejecutar; una falla por caso, sin cambios posteriores.
REFERENCIAS_ESPECIFICAS = [
    "Cuerpo de aceleración sucio", "Batería descargada", "Inyectores sucios", "Bobina de encendido defectuosa", "Inyector con fuga", "Válvula IAC sucia", "Bomba de agua defectuosa", "Motoventilador de radiador defectuoso", "Correa de accesorios desgastada", "Discos de freno alabeados", "Aire en sistema hidráulico de frenos", "Rodamiento de rueda desgastado", "Bieleta de barra estabilizadora desgastada", "Brazo de suspensión doblado", "Amortiguadores desgastados", "Sensor de oxígeno defectuoso", "Sensor MAF sucio", "Sensor de velocidad defectuoso", "Disco de embrague patinando", "Cilindro maestro de embrague defectuoso", "Batería descargada", "Alternador defectuoso", "Terminal negativo de batería sulfatado", "Bomba de gasolina con baja presión", "Bomba de gasolina con baja presión", "Bobina de encendido defectuosa", "Válvula IAC sucia", "Bomba de agua defectuosa", "Cáliper de freno trabado", "Rótula de dirección con holgura",
]


def normalizar(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", valor or "")
    return "".join(c for c in texto.lower() if not unicodedata.combining(c)).strip()


def serializar_predicciones(resultado: Any) -> list[dict[str, Any]]:
    return [item.model_dump() for item in (resultado.predicciones_ml or [])]


def escribir_csv(nombre: str, filas: list[dict[str, Any]], campos: list[str]) -> None:
    with (SALIDA / nombre).open("w", newline="", encoding="utf-8-sig") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(filas)


def resumen_por_grupo(filas: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    prediccion, completitud, eficiencia = [], [], []
    for grupo in range(1, 11):
        bloque = [f for f in filas if f["grupo"] == grupo]
        ejecutados = [f for f in bloque if f["estado_ejecucion"] == "EJECUTADO"]
        correctos = sum(f["coincide_principal_con_referencia"] is True for f in ejecutados)
        total = len(ejecutados)
        suma_ms = sum(float(f["tiempo_real_ms"]) for f in ejecutados)
        prediccion.append({
            "grupo": grupo, "total_predicciones_realizadas": total,
            "predicciones_correctas": correctos,
            "ppcf_porcentaje": round(correctos / total * 100, 2) if total else None,
        })
        completitud.append({
            "grupo": grupo, "total_registros_evaluados": total,
            "registros_completos": "PENDIENTE_DE_VALIDACION",
            "prdc_porcentaje": "NO_CALCULABLE_SIN_DEFINICION_VALIDADA_DE_8_CAMPOS",
            "configuracion": CONFIG_COMPLETITUD,
        })
        eficiencia.append({
            "grupo": grupo, "diagnosticos_evaluados": total,
            "suma_tiempo_real_ms": round(suma_ms, 2),
            "tiempo_promedio_real_ms": round(suma_ms / total, 2) if total else None,
        })
    return prediccion, completitud, eficiencia


def escribir_reporte(filas: list[dict[str, Any]], prediccion: list[dict[str, Any]], eficiencia: list[dict[str, Any]]) -> None:
    ejecutados = [f for f in filas if f["estado_ejecucion"] == "EJECUTADO"]
    correctos = sum(f["coincide_principal_con_referencia"] is True for f in ejecutados)
    suma_ms = sum(float(f["tiempo_real_ms"]) for f in ejecutados)
    promedio = suma_ms / len(ejecutados) if ejecutados else 0
    lineas = [
        "# Simulación técnica POST de CarBot", "",
        f"- Estado: `{ESTADO}`; no es POST_OFICIAL ni muestra de tesis.",
        "- Ejecución: pipeline real local (ML + RAG + generación configurada).",
        "- Persistencia oficial: ninguna. Si se publica en historial local, usa DEVELOPMENT y conserva la marca SIMULACION_POST.",
        "- Fechas simuladas: 2026-09-24 a 2026-10-03, posteriores al PRE finalizado el 2026-09-23.",
        f"- Casos ejecutados: {len(ejecutados)}/30; fallidos: {30 - len(ejecutados)}.",
        f"- PPCF técnico de referencias simuladas: {correctos}/{len(ejecutados)} = {round(correctos / len(ejecutados) * 100, 2) if ejecutados else 'N/A'}%.",
        f"- Tiempo promedio real del pipeline: {promedio:.2f} ms.", "",
        "## Ficha 2: condición metodológica", "",
        f"La configuración `{CONFIG_COMPLETITUD}` está deliberadamente pendiente. No se calculó PRDC ni se declaró un registro completo, porque la definición final de los 8 campos debe validarse antes del POST oficial.",
        "Campos observados por esta ejecución: identificador, fecha, síntoma, predicción principal, alternativas ML, contexto/procedimiento RAG, respuesta del pipeline, confianza ML, tiempos ML/RAG/LLM/total y estado de ejecución.",
        "", "## Resumen por grupo", "",
        "| Grupo | Ejecutados | Correctos | PPCF | Promedio real (ms) |",
        "|---:|---:|---:|---:|---:|",
    ]
    for p, e in zip(prediccion, eficiencia):
        lineas.append(f"| {p['grupo']} | {p['total_predicciones_realizadas']} | {p['predicciones_correctas']} | {p['ppcf_porcentaje']}% | {e['tiempo_promedio_real_ms']} |")
    (SALIDA / "REPORTE_SIMULACION_POST.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    configuracion = {
        "nombre": CONFIG_COMPLETITUD,
        "estado": "PENDIENTE_DE_VALIDACION_METODOLOGICA",
        "regla": "No calcula PRDC hasta validar formalmente los 8 campos.",
        "campos_observados_pipeline": ["id_caso", "fecha", "sintoma", "diagnostico_principal", "alternativas_ml", "contexto_rag", "respuesta", "tiempos"],
    }
    (SALIDA / "CONFIGURACION_COMPLETITUD_PENDIENTE.json").write_text(
        json.dumps(configuracion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    gestor = GestorDiagnostico()
    # Evita modificaciones del tracker de desarrollo: los resultados se guardan abajo, aislados.
    gestor._registrar_en_tracker = lambda **_: None
    filas: list[dict[str, Any]] = []
    inicio_fecha = date(2026, 9, 24)
    for indice, (sintoma, _) in enumerate(CASOS, start=1):
        referencia = REFERENCIAS_ESPECIFICAS[indice - 1]
        grupo = (indice - 1) // 3 + 1
        fecha = inicio_fecha + timedelta(days=grupo - 1)
        fila: dict[str, Any] = {
            "id_caso": f"SIMULACION_POST_{indice:03d}", "placa_simulada": f"SIMPOST-{indice:03d}", "grupo": grupo,
            "fecha": fecha.isoformat(), "estado": ESTADO, "sintoma_ingresado": sintoma,
            "diagnostico_referencia_esperado_simulado": referencia,
            "criterio_coincidencia": "igualdad_normalizada_prediccion_principal_vs_referencia",
        }
        try:
            inicio = time.perf_counter()
            resultado = gestor.procesar_consulta_texto(
                sintoma, placa=f"SIM-{indice:03d}", marca_modelo="Vehículo de simulación",
                session_id=f"simulacion-post-{indice:03d}", proveedor="simulacion_local",
            )
            tiempo_real_ms = round((time.perf_counter() - inicio) * 1000, 2)
            alternativas = serializar_predicciones(resultado)
            principal = resultado.diagnostico_ml
            fila.update({
                "estado_ejecucion": "EJECUTADO", "diagnostico_principal_carbot": principal,
                "alternativas_diagnosticas_carbot": json.dumps(alternativas, ensure_ascii=False),
                "coincide_principal_con_referencia": normalizar(principal) == normalizar(referencia),
                "informacion_generada_carbot": resultado.respuesta_texto,
                "contexto_rag": resultado.contexto_manual, "titulo_manual": resultado.titulo_manual,
                "confianza_ml": resultado.confianza_ml, "tiempo_real_ms": tiempo_real_ms,
                "tiempo_ml_ms": resultado.tiempo_ml_ms, "tiempo_rag_ms": resultado.tiempo_rag_ms,
                "tiempo_llm_ms": resultado.tiempo_llm_ms, "tiempo_total_reportado_ms": resultado.tiempo_total_ms,
                "modo_diagnostico": resultado.modo_diagnostico, "error": "",
            })
        except Exception as exc:  # Conserva evidencia de fallos sin inventar resultados.
            fila.update({"estado_ejecucion": "FALLIDO", "error": f"{type(exc).__name__}: {exc}"})
        filas.append(fila)
        print(f"[{indice:02d}/30] {fila['id_caso']}: {fila['estado_ejecucion']}")

    campos = [
        "id_caso", "placa_simulada", "grupo", "fecha", "estado", "estado_ejecucion", "sintoma_ingresado",
        "diagnostico_principal_carbot", "alternativas_diagnosticas_carbot",
        "diagnostico_referencia_esperado_simulado", "criterio_coincidencia",
        "coincide_principal_con_referencia", "informacion_generada_carbot", "contexto_rag",
        "titulo_manual", "confianza_ml", "tiempo_real_ms", "tiempo_ml_ms", "tiempo_rag_ms",
        "tiempo_llm_ms", "tiempo_total_reportado_ms", "modo_diagnostico", "error",
    ]
    prediccion, completitud, eficiencia = resumen_por_grupo(filas)
    escribir_csv("SIMULACION_POST_30_CASOS_DETALLE.csv", filas, campos)
    escribir_csv("FICHA_1_PREDICCION_PPCF.csv", prediccion, list(prediccion[0]))
    escribir_csv("FICHA_2_CONTROL_INFORMACION_PRDC_PENDIENTE.csv", completitud, list(completitud[0]))
    escribir_csv("FICHA_3_EFICIENCIA_TPRD.csv", eficiencia, list(eficiencia[0]))
    escribir_reporte(filas, prediccion, eficiencia)
    print(f"Resultados aislados: {SALIDA}")


if __name__ == "__main__":
    main()
