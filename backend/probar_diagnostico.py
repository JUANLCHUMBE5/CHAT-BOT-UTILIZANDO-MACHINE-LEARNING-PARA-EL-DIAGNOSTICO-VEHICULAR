"""
probar_diagnostico.py — Script de Demostración Interactiva para Sustentación de Tesis UCV 2026
Permite probar el chatbot de diagnóstico vehicular directamente desde la consola.
"""
import sys
import os

# Asegurar codificación UTF-8 en Windows
os.environ["PYTHONUTF8"] = "1"
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from src.core.gestor_diagnostico import GestorDiagnostico

def main():
    print("=" * 70)
    print("  🚗 CarBot — Diagnóstico Vehicular con Machine Learning")
    print("  Tesis UCV 2026 | Taller Mecánico en Carabayllo")
    print("=" * 70)
    print()
    
    print("⏳ Cargando modelo de Inteligencia Artificial...")
    gestor = GestorDiagnostico()
    print("✅ Modelo ML, Motor RAG y LLM cargados exitosamente.")
    print()
    print("Escriba un síntoma vehicular para obtener el diagnóstico.")
    print("Ejemplos:")
    print("  • 'el motor cascabelea al acelerar'")
    print("  • 'mi carro se chupa en la subida'")
    print("  • 'siento un chillido feo al frenar'")
    print("  • 'P0300 scanner me bota ese codigo'")
    print()
    print("Escriba 'salir' para terminar.")
    print("-" * 70)
    
    while True:
        try:
            sintoma = input("\n🔧 Síntoma > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 ¡Hasta luego!")
            break
            
        if not sintoma:
            continue
        if sintoma.lower() in ("salir", "exit", "quit"):
            print("\n👋 ¡Hasta luego! Gracias por usar CarBot.")
            break
        
        resultado = gestor.procesar_consulta_texto(
            texto_usuario=sintoma,
            placa="DEMO-001",
            marca_modelo="Vehiculo Demo"
        )
        
        print()
        print("=" * 70)
        print(f"🎯 Diagnóstico ML: {resultado.diagnostico_ml}")
        print(f"📊 Confianza: {resultado.confianza_ml * 100:.1f}%")
        if resultado.requiere_revision_humana:
            print("⚠️  Requiere revisión humana en taller")
        print("-" * 70)
        print(resultado.respuesta_texto)
        print("=" * 70)

if __name__ == "__main__":
    main()
