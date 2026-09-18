"""
Generador de registros para Lote 10 de Fase 10 - Clase 54 (CLIMATIZACION).
Cubre exactamente 40 registros:
- Clase 54: Falla en compresor de aire acondicionado o fuga de gas R134a (10 L1, 15 L2, 15 L3)
IDs: F10-L10-0001 a F10-L10-0040.
Macro: CLIMATIZACION.
"""

from typing import List, Dict

CLASE_54 = "Falla en compresor de aire acondicionado o fuga de gas R134a"

# Clases contrastivas canónicas
CLASE_06 = "Falla en sensor de oxigeno o mezcla rica"
CLASE_08 = "Falla en termostato o motoventilador de radiador"
CLASE_47 = "Alternador defectuoso o placa de diodos quemada"
CLASE_51 = "Foco o falla en sistema de refrigeracion de bateria/inversor (EV)"

MACRO_CLIMATIZACION = "CLIMATIZACION"
FUENTE = "SINTETICO_IA"


def obtener_casos_54(offset: int = 1) -> List[Dict[str, str]]:
    casos = []
    idx = offset

    def agregar(id_grupo, nivel, texto, lenguaje, condicion, presentes, negados, dtc, req_preg, es_cont, clase_cont, obs):
        nonlocal idx
        reg_id = f"F10-L10-{idx:04d}"
        casos.append({
            "id": reg_id,
            "id_grupo": id_grupo,
            "clase_objetivo": CLASE_54,
            "macro_sistema": MACRO_CLIMATIZACION,
            "nivel_informacion": nivel,
            "texto_usuario": texto,
            "tipo_lenguaje": lenguaje,
            "condicion_operacion": condicion,
            "sintomas_presentes": presentes,
            "sintomas_negados": negados,
            "dtc": dtc,
            "requiere_pregunta": req_preg,
            "es_contrastivo": es_cont,
            "clase_contrastiva": clase_cont,
            "fuente": FUENTE,
            "observaciones": obs
        })
        idx += 1

    # =========================================================================
    # L1 (10 casos): Información escasa, lenguaje natural, 1-2 síntomas, sin DTC
    # =========================================================================
    agregar("G-10-54-01", "L1", "Prendo el aire del auto pero solo bota aire tibio por las rejillas.", "COLOQUIAL", "USO_CABINA", "aire_tibio, no_enfria_cabina", "NO_REPORTA", "", "SI", "NO", "", "L1 aire tibio cabina")
    agregar("G-10-54-02", "L1", "El aire acondicionado no esta enfriando casi nada estos dias de calor.", "COLOQUIAL", "USO_CABINA", "poco_enfriamiento", "NO_REPORTA", "", "SI", "NO", "", "L1 climatizacion insuficiente")
    agregar("G-10-54-03", "L1", "Siento un silbido como de gas escapando por el tablero al encender el AC.", "COLOQUIAL", "ENCENDIDO_AC", "silbido_tablero_ac", "NO_REPORTA", "", "SI", "NO", "", "L1 siseo gas en tablero")
    agregar("G-10-54-04", "L1", "Al presionar el boton de aire acondicionado no se siente que acople nada.", "COLOQUIAL", "PULSACION_BOTON", "sin_acople_ac", "NO_REPORTA", "", "SI", "NO", "", "L1 no acopla compresor")
    agregar("G-10-54-05", "L1", "El aire enfriaba bien la semana pasada y de repente dejo de helar por completo.", "COLOQUIAL", "USO_CABINA", "perdida_enfriamiento_repentina", "NO_REPORTA", "", "SI", "NO", "", "L1 perdida de frio repentina")
    agregar("G-10-54-06", "L1", "Sale aire por las ventilas pero no enfria el habitaculo.", "COLOQUIAL", "VENTILACION", "flujo_aire_sin_frio", "NO_REPORTA", "", "SI", "NO", "", "L1 flujo sin frio")
    agregar("G-10-54-07", "L1", "Se escucha un chillido constante adelante cuando activo el interruptor del AC.", "COLOQUIAL", "ACTIVACION_AC", "chillido_al_activar_ac", "NO_REPORTA", "", "SI", "NO", "", "L1 chillido polea compresor")
    agregar("G-10-54-08", "L1", "El enfriamiento del coche se corta a los pocos minutos de prenderlo.", "COLOQUIAL", "MARCHA_URBANA", "enfriamiento_intermitente", "NO_REPORTA", "", "SI", "NO", "", "L1 corte intermitente de frio")
    agregar("G-10-54-09", "L1", "Noto manchas verdes fosforescentes en unas mangueras del sistema de aire.", "COLOQUIAL", "INSPECCION_VISUAL", "mancha_verde_manguera", "NO_REPORTA", "", "SI", "NO", "", "L1 traza tinte uv manguera")
    agregar("G-10-54-10", "L1", "El auto no enfria adentro cuando estoy en el trafico.", "COLOQUIAL", "DETENIDO_TRAFICO", "no_enfria_en_trafico", "NO_REPORTA", "", "SI", "NO", "", "L1 bajo rendimiento en ralenti")

    # =========================================================================
    # L2 (15 casos): Evidencia operacional, habitáculo vs motor, contraste
    # =========================================================================
    agregar("G-10-54-11", "L2", "Al encender el boton A/C el ventilador del habitaculo sopla con fuerza pero el aire sale a 28°C; el motor termico no presenta sobrecalentamiento ni variacion de temperatura en tablero.", "TECNICO", "RALENTI_CABINA", "aire_sale_caliente_28c, ventilador_cabina_ok", "sobrecalentamiento_motor", "", "NO", "SI", CLASE_08, "L2 aire acondicionado inoperante con motor a temp normal")
    agregar("G-10-54-12", "L2", "El sistema de aire acondicionado enfria algo cuando voy a 90 km/h en autopista, pero al detenerme en un semaforo sale aire totalmente calido por las toberas centrales.", "COLOQUIAL", "CARRETERA_VS_DETENIDO", "enfria_en_carretera_tibio_en_parado", "falla_temperatura_motor", "", "NO", "SI", CLASE_08, "L2 rendimiento depende de flujo frontal vs ventilador radiador")
    agregar("G-10-54-13", "L2", "Se observa fuga de refrigerante con aceite en la union del condensador frontal; la aguja de temperatura del refrigerante de motor esta clavada en 90°C sin anomalias en motor.", "TECNICO", "INSPECCION_CONDENSADOR", "fuga_aceite_condensador_ac, perdida_gas", "sobrecalentamiento_motor", "", "NO", "SI", CLASE_08, "L2 fuga condensador AC vs sistema enfriamiento motor")
    agregar("G-10-54-14", "L2", "Al oprimir el boton A/C la luz testigo verde enciende pero el embrague electromagnetico del compresor no pega; al apagar el A/C el motor gira sereno sin ruidos.", "TECNICO", "CONTACTO_AC_ON", "embrague_compresor_no_acopla, luz_ac_activa", "falla_inyeccion_motor", "", "NO", "NO", "", "L2 embrague compresor no acopla")
    agregar("G-10-54-15", "L2", "El compresor de climatizacion acopla y desacopla ciclicamente cada 4 segundos; el aire dentro del habitaculo no llega a enfriar debido a baja presion por perdida de gas.", "TECNICO", "RALENTI_AC_ON", "ciclado_rapido_4s_compresor, sin_enfriamiento", "falla_alternador", "", "NO", "SI", CLASE_47, "L2 ciclado rapido por presostato de baja vs alternador")
    agregar("G-10-54-16", "L2", "Escaneo del modulo de climatizacion HVAC detecta codigo B1422 relativo a circuito del embrague o sensor de velocidad del compresor de A/C, sin codigos DTC en la ECU de motor.", "TECNICO", "SCANNER_HVAC", "dtc_b1422_compresor_ac, hvac_falla", "falla_motor_ecu", "B1422", "NO", "NO", "", "L2 DTC B1422 en climatizacion")
    agregar("G-10-54-17", "L2", "Se escucha un siseo prolongado de gas evaporandose tras la guantera durante 20 segundos cada vez que apago el vehiculo, perdiendo la capacidad de enfriar en 3 dias.", "COLOQUIAL", "POST_APAGADO", "siseo_detras_guantera, perdida_carga_3dias", "fuga_liquido_frenos", "", "NO", "NO", "", "L2 fuga en evaporador detras de guantera")
    agregar("G-10-54-18", "L2", "Al activar el aire acondicionado el motor vibra fuertemente y emite un chillido agudo de faja; la polea del compresor de A/C se encuentra parcialmente engranada o trabada.", "TECNICO", "ACTIVACION_AC", "compresor_ac_trabado_chillido, freno_faja", "alternador_amarrado", "", "NO", "SI", CLASE_47, "L2 compresor AC amarrado vs alternador")
    agregar("G-10-54-19", "L2", "Vehiculo hibrido reporta inoperatividad de enfriamiento en cabina; la bateria de alto voltaje y su sistema de enfriamiento funcionan optimos pero el compresor electrico de cabina no arranca.", "TECNICO", "VEHICULO_HIBRIDO", "compresor_electrico_cabina_inoperante", "falla_refrigeracion_bateria_hv", "", "NO", "SI", CLASE_51, "L2 climatizacion cabina vs refrigeracion bateria EV")
    agregar("G-10-54-20", "L2", "El termometro colocado en la rejilla central marca 22°C con el A/C al maximo y soplador en velocidad 2; no hay codigos de error de motor ni tirones de combustion.", "TECNICO", "PRUEBA_TERMICA", "temp_rejilla_22c_alta, climatizacion_deficiente", "falla_mezcla_motor", "", "NO", "SI", CLASE_06, "L2 temp rejilla 22C vs falla de mezcla")
    agregar("G-10-54-21", "L2", "DTC B1423 presente en climatizador por circuito abierto en presostato de presion de refrigerante dual; el gas R134a se fugo por el sello del eje del compresor.", "TECNICO", "TALLER_DIAGNOSTICO", "dtc_b1423_presostato, fuga_sello_eje", "falla_sensor_motor", "B1423", "NO", "NO", "", "L2 DTC B1423 presostato de climatizacion")
    agregar("G-10-54-22", "L2", "Al cargar gas refrigerante el sistema enfrio a 7°C durante dos semanas, pero luego volvio a botar aire tibio; la manguera de alta presion presenta humedad aceitosa en el crimpado.", "TECNICO", "REVISION_CIRCUITO", "perdida_gas_dos_semanas, fuga_crimpado_manguera", "consumo_aceite_motor", "", "NO", "NO", "", "L2 fuga por manguera de alta presion")
    agregar("G-10-54-23", "L2", "El embrague del compresor recibe 12.8V en su conector al activar la tecla A/C pero no imanta la placa frontal por bobina de solenoide abierta, sin caida de voltaje en alternador.", "TECNICO", "PRUEBA_ELECTRICA", "bobina_embrague_abierta_12_8v_ok, placa_no_acopla", "falla_alternador", "", "NO", "SI", CLASE_47, "L2 bobina compresor abierta vs alternador")
    agregar("G-10-54-24", "L2", "El electroventilador del radiador activa su primera velocidad correctamente al encender A/C, pero las tuberias de aluminio del vano motor se mantienen a temperatura ambiente tibia.", "TECNICO", "INSPECCION_MOTOR", "electroventilador_enciende_ok, tuberias_ac_tibias", "falla_motoventilador", "", "NO", "SI", CLASE_08, "L2 ventilador ok pero circuito AC sin compresion")
    agregar("G-10-54-25", "L2", "En dia de 32°C exterior el interior del vehiculo no baja de 29°C; la valvula de expansion termostatica TXV emite silbido continuo sin lograr salto termico de evaporacion.", "TECNICO", "CALOR_EXTERIOR", "valvula_txv_silbido_sin_frio, cabina_caliente_29c", "recalentamiento_radiador", "", "NO", "SI", CLASE_08, "L2 valvula TXV sin salto termico vs radiador")

    # =========================================================================
    # L3 (15 casos): Manómetros manifold (baja/alta psi), detector UV, metrología
    # =========================================================================
    agregar("G-10-54-26", "L3", "Conexion de manometros manifold en tomas de servicio R134a a 1500 rpm: linea de baja marca 12 psi (nominal 28-35 psi) y linea de alta marca 95 psi (nominal 180-220 psi). Temperatura en difusor central de 19.5°C con ambiente a 26°C. Lampara de luz ultravioleta revela traza fluorescente de contraste UV en el sello mecanico del eje del compresor confirmando microfuga.", "TECNICO", "MANOMETRO_R134A", "baja_12psi_alta_95psi, temp_difusor_19_5c, fuga_uv_sello_eje", "falla_refrigeracion_motor", "", "NO", "SI", CLASE_08, "L3 presiones bajas 12-95 psi y fuga UV sello eje")
    agregar("G-10-54-27", "L3", "Diagnostico de climatizacion automotriz: prueba de presion estatica con motor apagado arroja 15 psi a 24°C ambiente (circuito practicamente vacio frente a 85 psi estaticos normales). Detector de fugas electronico por ionizacion pita al maximo en la esquina inferior derecha del condensador frontal por impacto de gravilla, descartando problemas de ventilador de radiador.", "TECNICO", "DETECTOR_ELECTRONICO_FUGA", "presion_estatica_15psi_vacio, detector_fugas_condensador", "falla_ventilador_radiador", "", "NO", "SI", CLASE_08, "L3 presion estatica 15 psi y fuga en condensador")
    agregar("G-10-54-28", "L3", "Evaluacion con manometros en sistema de A/C: linea de baja en vacio (-5 inHg) y linea de alta en 110 psi con compresor accionado continuamente. La valvula de expansion en bloque (TXV) se encuentra trabada en posicion cerrada; medicion de temperatura con termocupla en tubo de entrada marca 3°C y en salida 24°C sin retorno de vapor frio hacia compresor.", "TECNICO", "MANOMETRO_VACIO", "baja_en_vacio_negativo_5inhg, alta_110psi, txv_trabada_cerrada", "falla_motor_combustion", "", "NO", "NO", "", "L3 baja en vacio y TXV trabada cerrada")
    agregar("G-10-54-29", "L3", "Comprobacion electrica de embrague electromagnetico de compresor: con interruptor A/C activado y motor en ralenti se miden 13.9V en terminal de alimentacion; medicion de resistencia de la bobina con multimetro arroja circuito abierto (infinito vs valor nominal de 3.2 a 4.0 Ohmios). Galga de espesores mide entrehierro de 1.4 mm por desgaste severo de cara de friccion.", "TECNICO", "MULTIMETRO_BOBINA_AC", "resistencia_bobina_infinita_abierta, tension_13_9v_ok, entrehierro_1_4mm", "falla_alternador", "", "NO", "SI", CLASE_47, "L3 bobina compresor abierta y entrehierro 1.4mm")
    agregar("G-10-54-30", "L3", "Inspeccion de compresor de cilindrada variable sin embrague (valvula de control PWM): escaneo arroja DTC B1070; osciloscopio registra ciclo de trabajo de 82% a 400 Hz enviado por modulo HVAC hacia electrovalvula reguladora, pero presiones manometricas permanecen igualadas en 75 psi baja y 80 psi alta por rotura de plato oscilante (swash plate).", "TECNICO", "OSCILOSCOPIO_VALVULA_PWM", "dtc_b1070, pwm_valvula_82porciento, presiones_igualadas_75_80psi, swash_plate_roto", "falla_inyectores", "B1070", "NO", "NO", "", "L3 swash plate roto con presiones igualadas")
    agregar("G-10-54-31", "L3", "Prueba de hermeticidad con gas nitrogeno seco (N2) a 200 psi durante 45 minutos: la presion desciende de 200 a 140 psi. Rociado de solucion jabonosa espumogena revela burbujas abundantes en las conexiones de los tubos del evaporador bajo el salpicadero; el compresor y el radiador no presentan fuga.", "TECNICO", "PRUEBA_NITROGENO_200PSI", "nitrogeno_cae_200_a_140psi, burbujas_tubo_evaporador", "fuga_anticongelante_calefaccion", "", "NO", "SI", CLASE_08, "L3 prueba nitrogeno 200 psi fuga evaporador")
    agregar("G-10-54-32", "L3", "Escaneo de modulo HVAC en vehiculo moderno: DTC B1423 activo (Open in Pressure Sensor Circuit). Voltaje de salida de sensor de tres pines mide 0.35V (umbral de corte por baja presion menor a 0.6V). Al recuperar carga con estacion automatica solo se extraen 65 gramos de refrigerante R134a de una carga nominal de 550 gramos.", "TECNICO", "ESTACION_RECUPERADORA", "dtc_b1423, sensor_0_35v_baja_presion, recuperados_65g_de_550g", "falla_sensor_map", "B1423", "NO", "NO", "", "L3 recuperados solo 65g de 550g DTC B1423")
    agregar("G-10-54-33", "L3", "Analisis manometrico y termometrico: baja a 28 psi y alta a 240 psi a 1800 rpm. Temperatura ambiente 30°C. Al colocar termometro digital de contacto en linea de succion se miden 18°C (sobrecalentamiento excesivo de 16°C) y la temperatura en rejilla interior no baja de 16.5°C por degradacion de plato de valvulas del compresor que no comprime caudal volumetrico.", "TECNICO", "TERMOMETRO_DIGITAL_SUCCION", "baja_28psi_alta_240psi, sobrecalentamiento_16c, temp_rejilla_16_5c", "falla_termostato_motor", "", "NO", "SI", CLASE_08, "L3 sobrecalentamiento excesivo plato valvulas gastado")
    agregar("G-10-54-34", "L3", "Compresor de A/C ruidoso: se detectan 88 dBA de ruido metalico chirriante al acoplar; aceite PAG recuperado presenta color gris oscuro con limaduras de aluminio en suspension por desgaste destructivo de pistones recubiertos de teflon. Valvula de expansion y condensador taponados por viruta metalica.", "TECNICO", "ANALISIS_ACEITE_PAG", "aceite_pag_gris_viruta_aluminio, ruido_88dba, pistones_destruidos", "viruta_aceite_motor", "", "NO", "NO", "", "L3 destruccion interna pistones y aceite gris con viruta")
    agregar("G-10-54-35", "L3", "Verificacion en vehiculo hibrido/electrico con compresor scroll de alto voltaje trifasico (280V DC): DTC P0A1F registrado en modulo de climatizacion; medicion de resistencia de aislamiento con megohmetro a 500V entre bornes del compresor electrico y chasis mide 120 Megaohmios (aislamiento optimo), pero devanado trifasico U-V mide resistencia infinita por bobina abierta.", "TECNICO", "MEGOHMETRO_COMPRESOR_EV", "dtc_p0a1f, compresor_scroll_hv_bobina_abierta, aislamiento_120mohm_ok", "falla_motor_traccion_ev", "P0A1F", "NO", "SI", CLASE_51, "L3 compresor scroll electrico bobina abierta vs traccion")
    agregar("G-10-54-36", "L3", "Diagnostico de rendimiento termico: a 2000 rpm de motor con recirculacion activa, la presion de baja se clava en 48 psi y la de alta en 130 psi (baja alta y alta baja, sintoma clasico de fuga interna entre camaras de compresor por empaquetadura de culata de compresor soplada). Salto termico en rejilla apenas 4°C de diferencia con exterior.", "TECNICO", "MANOMETRO_CRUZADO", "baja_alta_48psi_alta_baja_130psi, empaquetadura_culata_compresor_fuga", "falla_empaquetadura_culata_motor", "", "NO", "NO", "", "L3 presiones cruzadas 48-130 psi fuga interna compresor")
    agregar("G-10-54-37", "L3", "Carga completa de 480g de R1234yf realizada en estacion certificada: termometro en difusor marca 4.8°C durante 48 horas. Al quinto dia sube a 17°C y manometros marcan 20 psi estaticos; inspeccion con liquido detector ultravioleta localiza mancha brillante en el racor de la valvula de servicio Schrader de baja presion que no sellaba el obus.", "TECNICO", "REVISION_VALVULA_SCHRADER", "carga_480g_r1234yf, perdida_a_20psi_estaticos, fuga_obus_schrader", "falla_sensor_temperatura", "", "NO", "NO", "", "L3 fuga por obus Schrader de toma de servicio")
    agregar("G-10-54-38", "L3", "Prueba de banco de polea desacopladora de compresor: con motor encendido y A/C OFF el rodamiento de doble hilera de bolas de la polea libre emite zumbido aspero de 82 dBA; holgura radial medida con reloj comparador centesimal arroja 0.22 mm (maximo 0.05 mm), amenazando con trabar la correa unica de accesorios sin afectar alternador.", "TECNICO", "RELOJ_COMPARADOR_POLEA", "rodamiento_polea_ac_zumbido_82dba, holgura_radial_0_22mm", "falla_rodamiento_alternador", "", "NO", "SI", CLASE_47, "L3 rodamiento polea compresor con holgura 0.22mm")
    agregar("G-10-54-39", "L3", "Evaluacion de sistema A/C: escaneo OBD registra DTC B1422 en climatizador; con osciloscopio en el conector del sensor de revoluciones del compresor (sensor Hall de efecto Pick-up) se constata ausencia de pulsos cuadrados al girar el embrague, provocando que la ECU desconecte el rele del compresor a los 3 segundos de encendido.", "TECNICO", "OSCILOSCOPIO_SENSOR_PICKUP", "dtc_b1422, sin_pulsos_sensor_pickup_compresor, rele_desconecta_3s", "falla_sensor_ckp_motor", "B1422", "NO", "SI", CLASE_08, "L3 sensor pickup de compresor sin pulsos DTC B1422")
    agregar("G-10-54-40", "L3", "Protocolo de deteccion de fugas por vacio profundo: bomba de vacio de dos etapas alcanza 250 micrones de mercurio (Hg). Al cerrar valvulas y apagar bomba, el vacuometro digital sube de 250 a 1800 micrones en 2 minutos, demostrando perdida de estanqueidad; presurizacion con mezcla formigal 95/5 y detector de hidrogeno ubica perforacion en nucleo de evaporador.", "TECNICO", "VACUOMETRO_MICRONES", "vacio_sube_250_a_1800_micrones, detector_hidrogeno_evaporador", "fuga_radiador_calefaccion", "", "NO", "SI", CLASE_08, "L3 perdida de vacio 250 a 1800 micrones fuga evaporador")

    return casos
