"""
Script para aplicar las actualizaciones de contenido textual aprobado (A3).
Aplica CHG-013 (EV/HEV), CHG-014 (Common Rail), CHG-015 (Despresurización Gasolina),
y CHG-016 (Cadena cualitativa flujo condensador A/C).
Únicamente modifica archivos dentro de machine_learning/manuals/candidates/v1/texts/.
"""
import re
from pathlib import Path

CAND_TEXTS = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING/machine_learning/manuals/candidates/v1/texts")

def apply_a3_text_updates():
    # 1. Actualizar RAG_PROC_064 en manual_procedimientos.txt (A/C Condensador y Flujo de Aire - CHG-016)
    p_man = CAND_TEXTS / "manual_procedimientos.txt"
    text_man = p_man.read_text(encoding="utf-8")

    old_proc_064_match = re.search(
        r"(===\s*PROCEDIMIENTO: DIAGNÓSTICO DE CONDENSADOR Y FUGAS EN EL RADIADOR DE CALEFACCIÓN / EVAPORADOR.*?\n)(.*?)(?====|\Z)",
        text_man,
        flags=re.DOTALL
    )
    if old_proc_064_match:
        header = old_proc_064_match.group(1)
        new_body = (
            "Código de Falla Asociado: DTC B1010 / Falla en compresor de aire acondicionado o fuga de gas R134a\n"
            "Modelos Compatibles Frecuentes en Perú: Toyota Yaris, Hyundai Accent, Kia Rio, Nissan Versa, Chevrolet Sail, DFSK Glory\n"
            "Gravedad: Media-Alta | Tiempo Estimado de Taller: 120 minutos\n"
            "Síntomas Principales:\n"
            "- Sale aire por las rejillas de ventilación pero casi no enfría o sale a temperatura ambiente.\n"
            "- En movimiento o carretera enfría un poco más, pero al detenerse en tráfico o semáforo vuelve a calentar.\n"
            "- Blower / ventilador interior sopla con normalidad pero sin aire frío.\n"
            "- Pérdida progresiva de refrigerante o condensador sucio por insectos y lodo.\n\n"
            "Diagnóstico Diferencial Técnico de Taller:\n"
            "1. Diferenciar falta de flujo de aire en condensador vs falta de gas refrigerante vs fallo de acople del compresor.\n"
            "2. Si el aire enfría en movimiento pero calienta al detenerse, el flujo de aire exterior forzado está compensando la falta de disipación térmica del motoventilador frontal o un panal tapado de suciedad.\n"
            "3. No aplicar presiones genéricas universales; las presiones de alta y baja dependen de la temperatura ambiente y de la ficha técnica OEM del fabricante (requires_oem_spec = true).\n\n"
            "Secuencia de Pruebas Cualitativas Paso a Paso:\n"
            "Paso 1: Con motor en marcha y A/C encendido al máximo, comprobar visualmente si el motoventilador del condensador enciende inmediatamente. Si no gira, revisar fusible de A/C fan, relé de alta/baja velocidad y señal del presostato.\n"
            "Paso 2: Inspección física de panal: Revisar el espacio entre el radiador del motor y el condensador. Retirar hojas, tierra o doblamiento de aletas que impidan el intercambio de calor.\n"
            "Paso 3: Verificar acople físico del clutch electromagnético del compresor o desplazamiento de carrera de la válvula reguladora PWM.\n"
            "Paso 4: Inspección de fugas de gas: Conectar equipo con lámpara UV para rastrear tinte fluorescente en uniones del condensador, tuberías y sello frontal del eje del compresor.\n"
            "Paso 5: Evacuación y recarga: Efectuar vacío de mínimo 30 minutos a 29 inHg y recargar la masa exacta de R134a/R1234yf especificada en la placa del fabricante bajo el capó.\n\n"
        )
        # Reemplazar la primera ocurrencia limpia
        text_man = text_man[:old_proc_064_match.start(2)] + new_body + text_man[old_proc_064_match.end(2):]
        p_man.write_text(text_man, encoding="utf-8")
        print("Actualizado RAG_PROC_064 con cadena cualitativa de A/C (CHG-016).")

    # 2. Actualizar Common Rail con Advertencia de Alta Presión (>1600 bar) en manual_procedimientos.txt y multimarca (CHG-014)
    common_rail_warning = (
        "\nADVERTENCIA DE SEGURIDAD CRÍTICA (CIRCUITO COMMON RAIL > 1,600 BAR):\n"
        "El riel y cañerías de inyección diésel operan a presiones extremas de hasta 1,600 a 2,200 bar.\n"
        "Riesgo grave de inyección subcutánea de combustible y corte tisular.\n"
        "NUNCA palpar cañerías ni buscar fugas con la mano mientras el motor esté en marcha o durante el arranque.\n"
        "Esperar un mínimo de 5 minutos tras apagar el motor para asegurar la despresurización antes de desmontar tuberías.\n"
    )

    for fname in ["manual_procedimientos.txt", "generales/manual_procedimientos_multimarca.txt", "generales/procedimientos_fase8.txt"]:
        p_file = CAND_TEXTS / fname
        if p_file.exists():
            content = p_file.read_text(encoding="utf-8")
            if "COMMON RAIL" in content and "CIRCUITO COMMON RAIL > 1,600 BAR" not in content:
                # Agregar advertencia tras el encabezado de gravedad
                content_new = re.sub(
                    r"(Gravedad:\s*(?:Alta|Crítica).*?\n)",
                    r"\1" + common_rail_warning,
                    content,
                    count=2
                )
                p_file.write_text(content_new, encoding="utf-8")
                print(f"Agregada advertencia Common Rail (CHG-014) en {fname}")

    # 3. Actualizar Despresurización de Gasolina (CHG-015) en multimarca y manual_procedimientos
    fuel_depressurize_step = (
        "\nPASO PREVIO OBLIGATORIO DE SEGURIDAD (DESPRESURIZACIÓN DE RIEL DE GASOLINA):\n"
        "Antes de desacoplar mangueras, racores o el riel de inyectores, retirar el fusible o relé de la bomba de combustible.\n"
        "Dar marcha al motor durante 5 a 10 segundos hasta que se apague por falta de presión residual de gasolina.\n"
        "Desconectar el borne negativo de la batería de 12V y usar trapos limpios alrededor de la conexión para contener vapores.\n"
    )

    p_multi = CAND_TEXTS / "generales/manual_procedimientos_multimarca.txt"
    if p_multi.exists():
        c_multi = p_multi.read_text(encoding="utf-8")
        if "DESPRESURIZACIÓN DE RIEL DE GASOLINA" not in c_multi:
            c_multi_new = re.sub(
                r"(=== PROCEDIMIENTO: DIAGNÓSTICO Y LIMPIEZA DE INYECTORES DE GASOLINA.*?\n.*?\n)",
                r"\1" + fuel_depressurize_step,
                c_multi,
                count=1
            )
            p_multi.write_text(c_multi_new, encoding="utf-8")
            print("Agregado paso de despresurización de gasolina (CHG-015) en multimarca.")

    # 4. Actualizar Advertencia EV/HEV (CHG-013) en toyota_prius_hev
    ev_warning = (
        "\nADVERTENCIA NORMATIVA DE SEGURIDAD (ALTA TENSIÓN > 300V CC):\n"
        "El sistema híbrido opera a tensión letal continua. Queda terminantemente prohibida la manipulación de cableado naranja,\n"
        "módulo inversor o celdas de tracción sin equipo de protección individual dieléctrico Clase 0 (1,000V) certificado,\n"
        "desconexión previa del Service Plug (puente de seguridad) y verificación de tensión residual nula (<12V) con voltímetro CAT III/IV.\n"
        "Todo procedimiento invasivo debe ser derivado a personal técnico certificado conforme al manual de taller OEM.\n"
    )

    p_prius = CAND_TEXTS / "toyota/prius_hev/2018/manual_toyota_prius_hev.txt"
    if p_prius.exists():
        c_prius = p_prius.read_text(encoding="utf-8")
        if "ALTA TENSIÓN > 300V CC" not in c_prius:
            c_prius_new = re.sub(
                r"(=== PROCEDIMIENTO: DIAGNÓSTICO DE BATERÍA DE ALTO VOLTAJE.*?\n.*?\n)",
                r"\1" + ev_warning,
                c_prius,
                count=1
            )
            p_prius.write_text(c_prius_new, encoding="utf-8")
            print("Agregada advertencia normativa EV/HEV (CHG-013) en Prius.")

    print("ACTUALIZACIONES DE CONTENIDO APROBADO (A3) COMPLETADAS.")

if __name__ == "__main__":
    apply_a3_text_updates()
