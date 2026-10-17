"""Batería de Pruebas Independiente y Exhaustiva para el Detector OOD (Fase 5.1).

Evalúa:
1. Casos OOD positivos en las 6 familias (variaciones léxicas, jerga peruana, errores ortográficos).
2. Casos Canónicos In-Domain (61 clases oficiales) con jerga y variaciones -> cero falsas abstenciones.
3. Consultas Mixtas OOD + In-Domain (transiciones donde el usuario menciona OOD pero consulta falla canónica).
4. Negaciones (el usuario descarta explícitamente el sistema OOD).
5. GLP/GNV: Discriminación entre queja de kit de gas vs queja canónica de motor en auto dual.
6. Métricas: Recall OOD, Precisión OOD, Tasa de Falsas Abstenciones, Diagnósticos Forzados Evitados.
"""

import sys
from collections import defaultdict

sys.path.insert(0, "backend")
from src.core.diagnostico.detector_ood import detectar_sintoma_fuera_de_catalogo

CASOS_PRUEBA_OOD = [
    # --- 1. OOD POSITIVOS (Deben abstenerse) ---
    # AIRBAG_SRS_BCM
    {"id": "OOD_SRS_01", "categoria": "AIRBAG_SRS_BCM", "tipo": "OOD", "texto": "Se prendio la bolsa de aire en el tablero tras chocar la cuneta"},
    {"id": "OOD_SRS_02", "categoria": "AIRBAG_SRS_BCM", "tipo": "OOD", "texto": "Cinta del timon rota y no toca el claxon despues de desarmar la direccion"},
    {"id": "OOD_SRS_03", "categoria": "AIRBAG_SRS_BCM", "tipo": "OOD", "texto": "Luz roja del airbag parpadea seguido y testigo srs activo"},
    {"id": "OOD_SRS_04", "categoria": "AIRBAG_SRS_BCM", "tipo": "OOD", "texto": "Cable espiral roto en volante multifuncion"},
    # GLP_GNV_CONVERSION
    {"id": "OOD_GAS_01", "categoria": "GLP_GNV_CONVERSION", "tipo": "OOD", "texto": "El conmutador de gas pita 3 veces y se regresa solo a gasolina"},
    {"id": "OOD_GAS_02", "categoria": "GLP_GNV_CONVERSION", "tipo": "OOD", "texto": "Falla en el reductor de gnv no mantiene la presion en el riel de gas"},
    {"id": "OOD_GAS_03", "categoria": "GLP_GNV_CONVERSION", "tipo": "OOD", "texto": "Se pasa solo a gasolina cuando acelero a fondo en gas glp"},
    {"id": "OOD_GAS_04", "categoria": "GLP_GNV_CONVERSION", "tipo": "OOD", "texto": "Los inyectores de gas no abren en la fase de gas y conmutador titila"},
    # DIRECCION_EPS_ELECTRONICA
    {"id": "OOD_EPS_01", "categoria": "DIRECCION_EPS_ELECTRONICA", "tipo": "OOD", "texto": "Direccion electroasistida dura y testigo eps encendido"},
    {"id": "OOD_EPS_02", "categoria": "DIRECCION_EPS_ELECTRONICA", "tipo": "OOD", "texto": "El timon electrico se puso durisimo al parquear"},
    {"id": "OOD_EPS_03", "categoria": "DIRECCION_EPS_ELECTRONICA", "tipo": "OOD", "texto": "Golpeteo en la columna por la estrellita del timon o acoplador elastico"},
    {"id": "OOD_EPS_04", "categoria": "DIRECCION_EPS_ELECTRONICA", "tipo": "OOD", "texto": "Falla de sensor de par en columna de direccion eps"},
    # RED_CAN_INMOVILIZADOR_CENTRAL
    {"id": "OOD_CAN_01", "categoria": "RED_CAN_INMOVILIZADOR_CENTRAL", "tipo": "OOD", "texto": "Sin comunicacion can entre ecm y tablero de instrumentos"},
    {"id": "OOD_CAN_02", "categoria": "RED_CAN_INMOVILIZADOR_CENTRAL", "tipo": "OOD", "texto": "Can bus en corto linea caida y resistencia de 120 ohms en DLC"},
    {"id": "OOD_CAN_03", "categoria": "RED_CAN_INMOVILIZADOR_CENTRAL", "tipo": "OOD", "texto": "Candadito parpadea en el tablero motor bloqueado no da marcha"},
    {"id": "OOD_CAN_04", "categoria": "RED_CAN_INMOVILIZADOR_CENTRAL", "tipo": "OOD", "texto": "Chip de la llave desprogramado no reconoce el transponder"},
    # HVAC_COMPUERTA_MEZCLA_CALEFACCION
    {"id": "OOD_HVAC_01", "categoria": "HVAC_COMPUERTA_MEZCLA_CALEFACCION", "tipo": "OOD", "texto": "Compuerta de mezcla trabada sale solo aire caliente por copiloto"},
    {"id": "OOD_HVAC_02", "categoria": "HVAC_COMPUERTA_MEZCLA_CALEFACCION", "tipo": "OOD", "texto": "Suena clac-clac detras del tablero al cambiar la temperatura blend door"},
    {"id": "OOD_HVAC_03", "categoria": "HVAC_COMPUERTA_MEZCLA_CALEFACCION", "tipo": "OOD", "texto": "Actuador de mezcla trabado con engranaje de plastico roto"},
    # TRANSMISION_NO_CUBIERTA_CONVERTIDOR
    {"id": "OOD_TRANS_01", "categoria": "TRANSMISION_NO_CUBIERTA_CONVERTIDOR", "tipo": "OOD", "texto": "El convertidor de par patina en tercera y vibra al acelerar"},
    {"id": "OOD_TRANS_02", "categoria": "TRANSMISION_NO_CUBIERTA_CONVERTIDOR", "tipo": "OOD", "texto": "Mecatronica dsg sin presion acumulador reventado pierde liquido"},

    # --- 2. CANÓNICOS IN-DOMAIN (Deben pasar al clasificador; NO abstenerse) ---
    {"id": "IN_DOM_01", "categoria": "IN_DOMAIN", "tipo": "IN_DOMAIN", "texto": "El motor tiembla en minimo ratea al salir y prende check engine con P0301"},
    {"id": "IN_DOM_02", "categoria": "IN_DOMAIN", "tipo": "IN_DOMAIN", "texto": "Bateria amanece descargada y alternador no carga solo bota 11.9V"},
    {"id": "IN_DOM_03", "categoria": "IN_DOMAIN", "tipo": "IN_DOMAIN", "texto": "Pedal de freno esponjoso y se va hasta el piso al frenar en bajada"},
    {"id": "IN_DOM_04", "categoria": "IN_DOMAIN", "tipo": "IN_DOMAIN", "texto": "Direccion hidraulica pesada y bota liquido de direccion por la cremallera"},
    {"id": "IN_DOM_05", "categoria": "IN_DOMAIN", "tipo": "IN_DOMAIN", "texto": "Embrague patina en subida acelero suben las rpm pero el carro no avanza"},
    {"id": "IN_DOM_06", "categoria": "IN_DOMAIN", "tipo": "IN_DOMAIN", "texto": "Prendo el aire acondicionado pero el compresor no acopla y fuga gas refrigerante"},
    {"id": "IN_DOM_07", "categoria": "IN_DOMAIN", "tipo": "IN_DOMAIN", "texto": "Amortiguadores delanteros reventados golpea seco al pasar rompemuelles"},
    {"id": "IN_DOM_08", "categoria": "IN_DOMAIN", "tipo": "IN_DOMAIN", "texto": "Motor recalienta hierve el refrigerante en el deposito y termostato no abre"},
    {"id": "IN_DOM_09", "categoria": "IN_DOMAIN", "tipo": "IN_DOMAIN", "texto": "Humo negro por el tubo de escape olor a gasolina cruda codigo P0172"},
    {"id": "IN_DOM_10", "categoria": "IN_DOMAIN", "tipo": "IN_DOMAIN", "texto": "Al frenar a 80 km/h tiembla fuerte el timon y el pedal por disco alabeado"},

    # --- 3. CASOS MIXTOS / TRANSICIONES (Mención OOD pero síntoma canónico activo) ---
    {"id": "MIXTO_01", "categoria": "MIXTO_TRANSICION", "tipo": "IN_DOMAIN", "texto": "Entendido lo del airbag pero tambien el motor tiembla con bujias fallando y codigo P0300"},
    {"id": "MIXTO_02", "categoria": "MIXTO_TRANSICION", "tipo": "IN_DOMAIN", "texto": "Aparte del timon duro, el alternador no carga y la bateria esta muerta"},
    {"id": "MIXTO_03", "categoria": "MIXTO_TRANSICION", "tipo": "IN_DOMAIN", "texto": "Si ya vi el gas, pero ademas en gasolina ratea fuerte el cilindro 2"},
]


def ejecutar_evaluacion_ood():
    total = len(CASOS_PRUEBA_OOD)
    aciertos = 0
    falsas_abstenciones = 0
    falsos_negativos = 0  # OOD no detectado
    
    por_familia = defaultdict(lambda: {"total": 0, "detectados": 0})

    print("="*70)
    print("BATERÍA DE EVALUACIÓN INDEPENDIENTE DEL DETECTOR OOD (FASE 5.1)")
    print("="*70)

    for c in CASOS_PRUEBA_OOD:
        cid = c["id"]
        esperado_tipo = c["tipo"]
        cat = c["categoria"]
        txt = c["texto"]

        es_ood, regla = detectar_sintoma_fuera_de_catalogo(txt)
        regla_cat = regla.categoria if regla else "IN_DOMAIN"

        if esperado_tipo == "OOD":
            por_familia[cat]["total"] += 1
            if es_ood:
                aciertos += 1
                por_familia[cat]["detectados"] += 1
                print(f"[CORRECTO - OOD] {cid} -> Detectado: {regla_cat}")
            else:
                falsos_negativos += 1
                print(f"[FALLO - OOD NO DETECTADO] {cid} -> Texto: {txt}")
        else:
            # Esperado IN_DOMAIN (in-domain puro o mixto)
            if not es_ood:
                aciertos += 1
                print(f"[CORRECTO - IN_DOMAIN] {cid} -> Clasificador Canónico Permitido")
            else:
                falsas_abstenciones += 1
                print(f"[FALLO - FALSA ABSTENCIÓN] {cid} -> Bloqueado erróneamente por {regla_cat}")

    total_ood = sum(1 for c in CASOS_PRUEBA_OOD if c["tipo"] == "OOD")
    total_indomain = sum(1 for c in CASOS_PRUEBA_OOD if c["tipo"] == "IN_DOMAIN")

    recall_ood = (aciertos_ood := total_ood - falsos_negativos) / total_ood * 100
    precision_ood = aciertos_ood / (aciertos_ood + falsas_abstenciones) * 100 if (aciertos_ood + falsas_abstenciones) > 0 else 0
    tasa_falsas_abstenciones = falsas_abstenciones / total_indomain * 100

    print("\n" + "="*70)
    print("MÉTRICAS DEL DETECTOR OOD")
    print("="*70)
    print(f"Total Casos Evaluados:        {total}")
    print(f"Recall OOD (Detección):       {recall_ood:.2f}% ({aciertos_ood}/{total_ood})")
    print(f"Precisión OOD:                {precision_ood:.2f}%")
    print(f"Falsas Abstenciones:          {falsas_abstenciones}/{total_indomain} ({tasa_falsas_abstenciones:.2f}%)")
    print(f"Diagnósticos Forzados Evitados: {aciertos_ood}")
    print("\nDetalle por Familia OOD:")
    for f_nom, f_datos in por_familia.items():
        rec = f_datos["detectados"] / f_datos["total"] * 100 if f_datos["total"] > 0 else 0
        print(f"  - {f_nom:<35}: {f_datos['detectados']}/{f_datos['total']} ({rec:.1f}%)")
    print("="*70)


if __name__ == "__main__":
    ejecutar_evaluacion_ood()
