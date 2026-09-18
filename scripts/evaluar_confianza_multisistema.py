"""Evaluación exhaustiva de confianza e inferencia multidominio (ML + RAG + DTC)."""

import sys
import time
from pathlib import Path

# Configurar salida UTF-8 para caracteres y emojis
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

raiz = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(raiz / "backend"))

from src.core.gestor_diagnostico import GestorDiagnostico
from src.infrastructure.container import ServiceContainer

gestor = GestorDiagnostico()
dtc_service = ServiceContainer.get_dtc_service()

# 18 Casos de prueba que cubren todos los sistemas automotrices principales y quejas reales
CASOS_EVALUACION = [
    # 1. Sistema de Encendido / Misfire
    {
        "sistema": "Encendido",
        "sintoma": "Tengo código P0301 en el escáner, el motor tiembla al acelerar y pierde fuerza en subidas",
        "marca": "Toyota Yaris",
    },
    {
        "sistema": "Encendido",
        "sintoma": "El motor tiembla fuerte en ralentí y parpadea la luz de check engine con falla de cilindro",
        "marca": "Hyundai Accent",
    },
    {
        "sistema": "Encendido",
        "sintoma": "Falla intermitente en caliente, cambié bujías pero sigue tironeando en aceleración",
        "marca": "Kia Rio",
    },

    # 2. Sistema Eléctrico / Carga / Batería
    {
        "sistema": "Eléctrico",
        "sintoma": "Al girar la llave solo hace un click seco y no gira el motor, las luces del tablero se bajan",
        "marca": "Nissan Sentra",
    },
    {
        "sistema": "Eléctrico",
        "sintoma": "Parpadean los faros en marcha y la radio se apaga sola mientras manejo, código P0562 voltaje bajo",
        "marca": "Chevrolet Sail",
    },
    {
        "sistema": "Eléctrico",
        "sintoma": "Se descarga la batería de un día para otro y el alternador zumba caliente",
        "marca": "Toyota Corolla",
    },

    # 3. Sistema de Frenos
    {
        "sistema": "Frenos",
        "sintoma": "Al frenar a 90 km/h en autopista el pedal y el volante vibran fuertemente sin ruidos metálicos",
        "marca": "Honda Civic",
    },
    {
        "sistema": "Frenos",
        "sintoma": "El pedal de freno se hunde despacio hasta el fondo si lo mantengo pisado en el semáforo",
        "marca": "Toyota Hilux",
    },
    {
        "sistema": "Frenos",
        "sintoma": "Chillido agudo de metal contra metal cada vez que piso el freno suavemente",
        "marca": "Nissan Versa",
    },

    # 4. Mecánica de Motor / Culata / Aceite
    {
        "sistema": "Mecánica Motor",
        "sintoma": "Sale humo blanco constante con olor dulce por el escape y baja el refrigerante del depósito",
        "marca": "Suzuki Swift",
    },
    {
        "sistema": "Mecánica Motor",
        "sintoma": "Tic-tic metálico en la culata que aumenta con las revoluciones, taqués hidráulicos sonando en caliente",
        "marca": "Chevrolet Cruze",
    },
    {
        "sistema": "Mecánica Motor",
        "sintoma": "Consume un litro de aceite por semana y bota humo azul al acelerar fuerte en carretera",
        "marca": "Volkswagen Gol",
    },

    # 5. Embrague y Transmisión
    {
        "sistema": "Transmisión",
        "sintoma": "El motor se acelera en tercera y cuarta pero el carro no avanza con fuerza, patina el embrague y huele a quemado",
        "marca": "Toyota Yaris",
    },
    {
        "sistema": "Transmisión",
        "sintoma": "El pedal de embrague se fue directo al piso como trapo y quedó sin presión de líquido",
        "marca": "Kia Cerato",
    },

    # 6. Suspensión / Dirección / Ruedas
    {
        "sistema": "Suspensión",
        "sintoma": "Al pasar rompemuelles o baches suena un golpe seco cloc-cloc en la parte delantera de la suspensión",
        "marca": "Hyundai Tucson",
    },
    {
        "sistema": "Suspensión",
        "sintoma": "Chasquido clac-clac repetitivo en la rueda delantera al girar el timón a tope en curvas cerradas",
        "marca": "Toyota Probox",
    },
    {
        "sistema": "Ruedas",
        "sintoma": "El timón vibra solo entre 90 y 110 km/h en pista lisa y luego se quita al acelerar más",
        "marca": "Nissan Tiida",
    },

    # 7. Combustible / Admisión / Inyección
    {
        "sistema": "Combustible",
        "sintoma": "Se ahoga al pisar a fondo en subidas y la bomba de combustible zumba muy fuerte en el tanque",
        "marca": "Hyundai Accent",
    },
]


def ejecutar_evaluacion():
    print("=========================================================================================")
    print("       EVALUACIÓN MULTIDOMINIO DE CONFIANZA Y RENDIMIENTO (18 CASOS DE TALLER)")
    print("=========================================================================================\n")

    confianzas = []
    tiempos_ml = []
    tiempos_rag = []
    resultados_tabla = []

    for i, caso in enumerate(CASOS_EVALUACION, start=1):
        sintoma = caso["sintoma"]
        marca = caso["marca"]
        sistema = caso["sistema"]

        # 1. Medición directa de Machine Learning
        inicio_ml = time.perf_counter()
        top_fallas = gestor.modelo_ml.predecir_top_fallas(sintoma, limite=3)
        tiempo_ml = max(1, int((time.perf_counter() - inicio_ml) * 1000))
        tiempos_ml.append(tiempo_ml)

        top1 = top_fallas[0]
        diag_nombre = top1["falla"]
        conf = top1["probabilidad"] * 100
        confianzas.append(conf)

        # 2. Medición directa de RAG FAISS
        inicio_rag = time.perf_counter()
        ctx, titulo, similitud = gestor.motor_rag.recuperar_contexto_con_similitud(sintoma)
        tiempo_rag = max(1, int((time.perf_counter() - inicio_rag) * 1000))
        tiempos_rag.append(tiempo_rag)

        # 3. Consulta DTC SQLite
        codigos = dtc_service.extraer_codigos_en_texto(sintoma) if dtc_service.disponible else []
        codigo_str = codigos[0] if codigos else "---"

        diag_resumido = diag_nombre[:38] + ("..." if len(diag_nombre) > 38 else "")
        manual_resumido = titulo[:35] + ("..." if len(titulo) > 35 else "")

        resultados_tabla.append({
            "num": i,
            "sistema": sistema,
            "dtc": codigo_str,
            "confianza": conf,
            "diagnostico": diag_resumido,
            "manual": manual_resumido or "(Procedimiento general)",
            "tiempo_ml": tiempo_ml,
            "tiempo_rag": tiempo_rag,
        })

    # Imprimir tabla de resultados
    print(f"{'#':<3} | {'SISTEMA':<13} | {'DTC':<6} | {'CONFIANZA':<10} | {'DIAGNÓSTICO ML':<41} | {'PROCEDIMIENTO RAG':<38}")
    print("-" * 125)
    for r in resultados_tabla:
        print(
            f"{r['num']:<3} | {r['sistema']:<13} | {r['dtc']:<6} | {r['confianza']:>8.1f}% | {r['diagnostico']:<41} | {r['manual']:<38}"
        )
    print("-" * 125)

    # Estadísticas Consolidadas
    promedio_conf = sum(confianzas) / len(confianzas)
    max_conf = max(confianzas)
    min_conf = min(confianzas)
    alta_conf = sum(1 for c in confianzas if c >= 80.0)
    media_alta_conf = sum(1 for c in confianzas if 60.0 <= c < 80.0)
    baja_conf = sum(1 for c in confianzas if c < 60.0)

    print("\n📊 ESTADÍSTICAS GLOBALES DEL MODELO:")
    print(f"• Casos evaluados: {len(CASOS_EVALUACION)} consultas mecánicas")
    print(f"• Confianza Promedio: {promedio_conf:.1f}%")
    print(f"• Confianza Máxima Alcanzada: {max_conf:.1f}%")
    print(f"• Rango de Confianza: {min_conf:.1f}% – {max_conf:.1f}%")
    print(f"• Distribución de Certeza:")
    print(f"   - Alta Confianza (>= 80%): {alta_conf} casos ({alta_conf / len(confianzas) * 100:.1f}%)")
    print(f"   - Confianza Media-Alta (60% - 79%): {media_alta_conf} casos ({media_alta_conf / len(confianzas) * 100:.1f}%)")
    print(f"   - Confianza Moderada (< 60%): {baja_conf} casos ({baja_conf / len(confianzas) * 100:.1f}%)")
    print(f"• Latencia Promedio ML (Linear SVM): {sum(tiempos_ml)/len(tiempos_ml):.1f} ms")
    print(f"• Latencia Promedio RAG (FAISS): {sum(tiempos_rag)/len(tiempos_rag):.1f} ms")


if __name__ == "__main__":
    ejecutar_evaluacion()
