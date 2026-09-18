"""
Generador modular de casos independientes de FRENOS, CHASIS y NEUMATICA para Fase 8.
Blindaje: Totalmente disjunto del benchmark TEST G1_01-G1_50.
"""

from typing import List, Dict

def obtener_casos_chasis_frenos_fase8() -> List[Dict[str, str]]:
    casos = []

    # 1. Cáliper trabado
    f_cal = "Caliper de freno trabado o mordaza pegada (piston agarrotado)"
    s_cal = [
        "Despues de rodar 15 minutos en plano siento olor a quemado fuerte en la rueda delantera derecha y el aro quema al tocarlo",
        "El carro jala fuertemente hacia la izquierda mientras conduzco en recta sin tocar el pedal de freno, mordaza pegada",
        "Piston del caliper no retrocede al soltar el freno debido a oxido en el cilindro interior y guardapolvo roto",
        "Pernos guia deslizantes del caliper estan totalmente secos y agarrotados impidiendo que la pinza flote libremente",
        "Pastilla interior de freno de la rueda delantera izquierda esta en el fierro mientras la exterior tiene mas de la mitad de vida",
        "Al levantar el vehiculo en la gata la rueda trasera derecha esta totalmente frenada y cuesta girarla con las dos manos",
        "Consumo elevado de combustible y llanta delantera caliente con abundante polvillo negro de freno acumulado en el aro",
        "Mordaza de freno trabada calienta el liquido de frenos hasta hervirlo y genera pedal esponjoso en bajadas",
        "El disco de freno de una sola rueda se pone azul por friccion continua sin haber accionado el pedal de freno",
        "Perno pasador del caliper doblado o sin lubricacion traba la mordaza contra el disco de freno",
        "Rueda delantera humea al detener el vehiculo despues de un recorrido corto en autopista por caliper trabado",
        "Manguera flexible de freno obstruida internamente actua como valvula check impidiendo el retorno del liquido de la mordaza",
    ]
    for s in s_cal:
        casos.append({"sintoma": s, "falla": f_cal, "sistema": "FRENOS"})

    # 2. Rodamiento de maza / rueda
    f_rod = "Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura)"
    s_rod = [
        "Zumbido ronco continuo como de avion a partir de 60 km/h que aumenta de intensidad a mayor velocidad",
        "Al tomar una curva hacia la derecha el zumbido de rodadura se hace mucho mas fuerte porque se carga el rodaje izquierdo",
        "El zumbido ronco de rueda disminuye notablemente cuando giro hacia la izquierda quitandole peso al lado afectado",
        "Al girar la rueda en el elevador con la mano apoyada en el espiral de suspension se siente una aspereza y vibracion clara en la maza",
        "Rodaje de rueda doble hilera de bolas con pista picada produce rumor sordo de rodamiento constante",
        "Juego axial y cabeceo perceptible al mover la rueda con las manos en posicion 12 y 6 horas en el elevador",
        "Zumbido metalico permanente en rueda delantera que no cambia al frenar ni al poner neutro en bajada",
        "Maza de rueda recalienta y genera zumbido de rodaje seco que vibra ligeramente en el piso del vehiculo",
        "Ruido de rozamiento wub wub wub en la rueda trasera que se acelera con la velocidad de desplazamiento",
        "Rodamiento sellado de cubo de rueda con sello roto perdio la grasa sintetica y las pistas estan con pitting",
        "Zumbido constante en la cabina que suena en el tren delantero al rodar por asfalto liso",
        "Prueba de fonendoscopio en la maza de rueda en el elevador confirma sonido de rodillos danados",
    ]
    for s in s_rod:
        casos.append({"sintoma": s, "falla": f_rod, "sistema": "SUSPENSION_CHASIS"})

    # 3. Maxi-Brake (Cámara de resorte de freno de aire)
    f_maxi = "Falla en actuador de resorte o camara Maxi-Brake trabada (frenos de aire)"
    s_maxi = [
        "Camion de carga pesada con sistema de frenos neumatico no libera el freno de parqueo en el eje motriz trasero",
        "Presion de aire en los tanques marca 8 bares pero la camara de resorte Maxi-Brake tiene el diafragma roto y pierde aire",
        "Al soltar la valvula de parqueo amarilla en el tablero la rueda trasera izquierda se queda bloqueada arrastrando llanta",
        "Fuga constante de aire comprimido por el orificio de alivio del actuador elastico Maxi-Brake al aplicar presion",
        "Camara de freno combinada servicio estacionamiento con resorte de potencia roto o atascado mecanicamente",
        "El camion no avanza porque las balatas traseras quedan pegadas al tambor por falta de presion de liberacion en la camara de resorte",
        "Resorte interno de seguridad del Maxi-Brake no comprime completamente por baja presion de liberacion en el circuito secundario",
        "Perdida rapida de aire en el circuito de parqueo impide desbloquear las ruedas del remolque o eje posterior",
        "Camara de resorte de aire recalentada con humo en tambor trasero por actuador neumatico defectuoso",
        "Diafragma de estacionamiento de camara tipo 30/30 perforado fuga aire continuo al desactivar el freno de mano neumatico",
    ]
    for s in s_maxi:
        casos.append({"sintoma": s, "falla": f_maxi, "sistema": "CARROCERIA_NEUMATICA"})

    return casos
