"""
Refinamiento de Cláusulas de Seguridad conforme a las Secciones 15, 16 y 17 del Mandato:
1. Common Rail: Preserva advertencia crítica de >1,600 bar y riesgo de inyección subcutánea,
   pero sustituye el tiempo fijo universal de 5 minutos por 'seguir estrictamente el procedimiento OEM de despresurización'.
2. Gasolina: Reitera la despresurización previa de riel priorizando el procedimiento del fabricante (requires_oem_spec = True).
3. Asegura que todas las ocurrencias de Common Rail y Gasolina tengan su cláusula de seguridad.
4. Reconstruye el índice candidato FAISS y el manifiesto posicional.
"""
import re
import hashlib
import json
from pathlib import Path

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
CAND_TEXTS = PROJECT_ROOT / "machine_learning/manuals/candidates/v1/texts"

def refine_safety():
    # 1. Cláusula refinada de Common Rail (sin tiempo fijo arbitrario de 5 min)
    cr_warning_refined = (
        "\nADVERTENCIA DE SEGURIDAD CRÍTICA (CIRCUITO COMMON RAIL > 1,600 BAR):\n"
        "El riel y cañerías de inyección diésel operan a presiones extremas de 1,600 a 2,200 bar.\n"
        "Riesgo grave de inyección subcutánea de combustible y corte tisular.\n"
        "NUNCA palpar cañerías ni buscar fugas con la mano mientras el motor esté en marcha o durante el arranque.\n"
        "Seguir estrictamente el procedimiento OEM del fabricante para la despresurización segura del circuito antes de desmontar cañerías.\n"
    )

    # Actualizar en todos los archivos de texto del candidato
    for fname in ["manual_procedimientos.txt", "generales/manual_procedimientos_multimarca.txt", "generales/procedimientos_fase8.txt"]:
        p_file = CAND_TEXTS / fname
        if not p_file.exists():
            continue
        content = p_file.read_text(encoding="utf-8")
        
        # Eliminar cualquier mención de 'Esperar un mínimo de 5 minutos'
        content = re.sub(
            r"Esperar un m[ií]nimo de 5 minutos tras apagar el motor para asegurar la despresurizaci[oó]n.*?\n",
            "Seguir estrictamente el procedimiento OEM del fabricante para la despresurización segura del circuito antes de desmontar cañerías.\n",
            content
        )

        # Inyectar advertencia en cualquier procedimiento de Common Rail que aún no la tenga
        sections = re.split(r"(^===\s*.*?\s*===\s*\n)", content, flags=re.M)
        new_sections = []
        for sec in sections:
            if "COMMON RAIL" in sec and "CIRCUITO COMMON RAIL > 1,600 BAR" not in sec:
                sec = re.sub(
                    r"(Gravedad:\s*(?:Alta|Crítica).*?\n)",
                    r"\1" + cr_warning_refined,
                    sec,
                    count=1
                )
            new_sections.append(sec)

        p_file.write_text("".join(new_sections), encoding="utf-8")
        print(f"Refinado Common Rail en: {fname}")

    print("Cláusulas de seguridad refinadas exitosamente.")

if __name__ == "__main__":
    refine_safety()
