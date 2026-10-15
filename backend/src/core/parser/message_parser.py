"""Intérprete estructurado de mensajes de una sola pasada (Single-Pass Message Parser).

Extrae de forma desacoplada y determinista:
- Placa vehicular validada (sin falsos positivos con años, DTCs o palabras comunes).
- Entidades del vehículo (marca, modelo, año, motor, combustible, transmisión).
- Síntomas afirmados y negados mediante análisis de polaridad.
- Mediciones físicas y lecturas de herramientas.
- Códigos de diagnóstico OBD-II (DTCs).
- Intención primaria y marcadores de ciclo de vida (corrección vs. cambio de caso).
"""

from __future__ import annotations

import re
import uuid
from typing import List, Optional, Tuple

from src.core.conversacion.detector_polaridad import DetectorPolaridad
from src.core.conversacion.diccionario_automotriz import normalizar_jerga_automotriz
from src.core.vehicle_profile import COMBUSTIBLES, MARCAS
from src.domain.schemas.conversation_contracts import (
    HechoClinico,
    IntentType,
    MedicionTecnica,
    UserTurnInputDTO,
    VehiculoIdentificado,
)


class SinglePassMessageParser:
    """Analizador sintáctico-semántico determinista de mensajes de usuario en una sola pasada."""

    # 1. Expresiones regulares para DTCs OBD-II
    PATRON_DTC = re.compile(r"\b([PBUCpbuc][0-3][0-9A-Fa-f]{3})\b")

    # 2. Expresiones regulares para mediciones físicas
    PATRON_MEDICION = re.compile(
        r"\b(\d+(?:[.,]\d+)?)\s*(psi|bar|kpa|v(?:olts?|oltios?)?|mv|ohm(?:ios?)?|mm)\b",
        re.IGNORECASE,
    )

    # 3. Expresiones regulares de Placa vehicular (Perú y Latinoamérica)
    # Formato A: Prefijado explícito: "placa ABC-123", "placa: A1B-234", "patente XYZ1234"
    PATRON_PLACA_PREFIJADA = re.compile(
        r"\b(?:placa|patente|matr[ií]cula)\s*(?:es|era|fue|[:=-])?\s*([A-Za-z0-9]{2,4}[-\s]?[A-Za-z0-9]{3,4})\b",
        re.IGNORECASE,
    )
    # Formato B: Placa aislada estándar con guion o espacio: ABC-123, ABC-1234, A1B-234, AB-1234
    PATRON_PLACA_ESTANDAR = re.compile(
        r"\b([A-Za-z0-9]{2,3})[-]([A-Za-z0-9]{3,4})\b"
    )
    # Formato C: Placa continua (6-7 caracteres alfanuméricos mezclados)
    PATRON_PLACA_CONTINUA = re.compile(
        r"\b(?![0-9]{4,7}\b)(?![A-Za-z]{4,8}\b)([A-Za-z0-9]{6,7})\b"
    )

    # Palabras comunes de 6-7 letras y marcas que NUNCA deben interpretarse como placa
    PALABRAS_EXCLUIDAS_PLACA = {
        "TOYOTA", "NISSAN", "SUZUKI", "HYUNDAI", "CHEVY", "COROLLA", "SENTRA", "YARIS",
        "TIEMBLA", "FRENOS", "ARRANCA", "MOTOR", "ESCAPE", "BATERIA", "BOBINA", "BUJIAS",
        "CARBURA", "REVERSA", "CAMBIOS", "ACEITE", "CALOR", "HUMEDO", "PRESION", "VOLTAJE",
        "SUBIDA", "BAJADA", "RALENTI", "MINIMO", "RAPIDO", "LENTO", "GOLPE", "RUIDO",
        "CUANDO", "PORQUE", "SIEMPRE", "NUNCA", "TAMBIEN", "ADEMAS", "BUENOS", "TARDES",
        "NOCHES", "AMIGOS", "CARBOT", "TALLER", "MAESTRO", "CLIENTE", "VEHICULO", "CARROS",
    }

    # 4. Marcadores de no tener placa a la mano
    PATRONES_SIN_PLACA = re.compile(
        r"\b(no\s+(?:tiene|s[eé]|tengo|hay)\s+(?:la\s+)?placa|"
        r"sin\s+placa|placa\s+no\s+(?:la\s+)?tengo|"
        r"no\s+la\s+tengo\s+a\s+la\s+mano|despu[eé]s\s+te\s+doy\s+la\s+placa|"
        r"no\s+me\s+acuerdo\s+la\s+placa|no\s+recuerdo\s+la\s+placa)\b",
        re.IGNORECASE,
    )

    # 5. Marcadores de cambio de caso / nuevo auto vs corrección sobre el mismo
    PATRONES_CAMBIO_CASO = re.compile(
        r"\b(otro\s+(?:carro|auto|veh[ií]culo|caso|cliente|problema)|"
        r"nuevo\s+(?:caso|diagn[oó]stico|auto|carro|veh[ií]culo)|"
        r"caso\s+nuevo|vamos\s+con\s+otro|termin[eé]\s+(?:ese|con\s+ese)|"
        r"este\s+es\s+otro\s+(?:carro|auto|veh[ií]culo)|"
        r"tengo\s+otro\s+(?:carro|auto|veh[ií]culo)\s+en\s+el\s+taller)\b",
        re.IGNORECASE,
    )

    PATRONES_CORRECCION = re.compile(
        r"\b(me\s+equivoqu[eé]|me\s+confund[ií]|corrijo|corrigiendo|"
        r"en\s+realidad\s+es|quise\s+decir|la\s+placa\s+no\s+es\s+esa|"
        r"el\s+carro\s+no\s+es\s+ese|el\s+modelo\s+es|la\s+marca\s+es|"
        r"el\s+año\s+es|no\s+es\s+un|no\s+era\s+un)\b",
        re.IGNORECASE,
    )

    # 6. Marcadores de intención
    PATRON_SALUDO = re.compile(
        r"^\s*(?:hola+|buen(?:as|os)?(?:\s+(?:d[ií]as|tardes|noches))?|qu[eé]\s+tal|saludos?|alo|al[oó])\s*[!.,]*\s*$",
        re.IGNORECASE,
    )

    PATRON_SOLICITUD_DETALLE = re.compile(
        r"\b(m[aá]s\s+detalles?|dame\s+m[aá]s\s+detalles?|detallar|c[oó]mo\s+(?:se\s+)?prueba|"
        r"c[oó]mo\s+(?:lo\s+)?reviso|paso\s+a\s+paso|procedimiento\s+t[eé]cnico)\b",
        re.IGNORECASE,
    )

    PATRON_REINICIO = re.compile(
        r"^\s*(?:reiniciar|limpiar\s+sesi[oó]n|(?:comenzar|empezar)\s+de\s+(?:nuevo|cero))\s*[!.,]*\s*$",
        re.IGNORECASE,
    )

    @classmethod
    def normalizar_texto(cls, texto: str) -> str:
        """Limpia caracteres de escape y normaliza jerga automotriz básica."""
        if not texto:
            return ""
        limpio = normalizar_jerga_automotriz(texto.strip())
        return re.sub(r"\s+", " ", limpio).strip()

    @classmethod
    def extraer_placa(cls, texto: str, dtcs_detectados: List[str]) -> Tuple[Optional[str], bool]:
        """
        Extrae y valida una placa automotriz. Retorna (placa_normalizada, es_provisional).
        Garantiza que no coincida con DTCs, años ni palabras castellanas.
        """
        if cls.PATRONES_SIN_PLACA.search(texto):
            return None, True

        dtc_set = {d.upper() for d in dtcs_detectados}
        candidato = None

        # Intento 1: Búsqueda con prefijo explícito (ej: "placa: ABC-123", "la placa es XYZ-789")
        m_pref = cls.PATRON_PLACA_PREFIJADA.search(texto)
        if m_pref:
            cand_p = m_pref.group(1).upper().replace(" ", "").replace("-", "")
            if cand_p not in cls.PALABRAS_EXCLUIDAS_PLACA and cand_p not in dtc_set:
                candidato = cand_p

        # Intento 2: Búsqueda de placa estándar con guion (ej: "ABC-123", "A1B-234")
        if not candidato:
            for m in cls.PATRON_PLACA_ESTANDAR.finditer(texto):
                p1, p2 = m.group(1).upper(), m.group(2).upper()
                candidato_raw = f"{p1}{p2}"
                # Validar que no sea año ni DTC
                if candidato_raw not in dtc_set and not (len(candidato_raw) == 4 and candidato_raw.isdigit()):
                    candidato = candidato_raw
                    break

        # Intento 3: Búsqueda continua
        if not candidato:
            for m in cls.PATRON_PLACA_CONTINUA.finditer(texto):
                cand = m.group(1).upper()
                # Excluir palabras de diccionario automotriz y DTCs
                if cand not in cls.PALABRAS_EXCLUIDAS_PLACA and cand not in dtc_set:
                    # Debe contener al menos un dígito y una letra para evitar palabras comunes
                    tiene_letra = any(c.isalpha() for c in cand)
                    tiene_num = any(c.isdigit() for c in cand)
                    if tiene_letra and tiene_num:
                        candidato = cand
                        break

        if not candidato:
            return None, False

        # Limpiar alfanuméricos
        candidato_limpio = re.sub(r"[^A-Za-z0-9]", "", candidato).upper()
        if len(candidato_limpio) < 5 or len(candidato_limpio) > 8:
            return None, False

        # Formatear estándar: primeras 3 posiciones, guion, resto
        if len(candidato_limpio) == 6:
            placa_fmt = f"{candidato_limpio[:3]}-{candidato_limpio[3:]}"
        elif len(candidato_limpio) == 7:
            placa_fmt = f"{candidato_limpio[:3]}-{candidato_limpio[3:]}"
        else:
            placa_fmt = candidato_limpio

        return placa_fmt, False

    @classmethod
    def extraer_mediciones(cls, texto: str) -> List[MedicionTecnica]:
        """Extrae lecturas cuantitativas con unidades automotrices."""
        mediciones: List[MedicionTecnica] = []
        for m in cls.PATRON_MEDICION.finditer(texto):
            val_str = m.group(1).replace(",", ".")
            uni_raw = m.group(2).upper()
            try:
                val = float(val_str)
            except ValueError:
                continue

            # Mapeo canónico de unidad y tipo
            if uni_raw in ("V", "VOLT", "VOLTS", "VOLTIOS"):
                tipo = "voltaje"
                unidad = "V"
            elif uni_raw == "MV":
                tipo = "voltaje"
                unidad = "mV"
            elif uni_raw in ("PSI", "BAR", "KPA"):
                tipo = "presion"
                unidad = uni_raw
            elif uni_raw in ("OHM", "OHMIOS"):
                tipo = "resistencia"
                unidad = "ohm"
            elif uni_raw == "MM":
                tipo = "distancia_holgura"
                unidad = "mm"
            else:
                tipo = "medicion_general"
                unidad = uni_raw

            # Contexto operacional de la medición
            contexto = None
            texto_l = texto.lower()
            if "arranque" in texto_l or "dar marcha" in texto_l or "al dar arranque" in texto_l:
                contexto = "arranque"
            elif "reposo" in texto_l or "apagado" in texto_l or "contacto" in texto_l:
                contexto = "reposo"
            elif "ralenti" in texto_l or "minimo" in texto_l:
                contexto = "ralenti"

            mediciones.append(MedicionTecnica(tipo=tipo, valor=val, unidad=unidad, contexto=contexto))
        return mediciones

    @classmethod
    def extraer_vehiculo(cls, texto: str, placa: Optional[str] = None, es_provisional: bool = False) -> VehiculoIdentificado:
        """Extrae atributos del vehículo evitando colisiones con síntomas."""
        texto_l = texto.lower()
        # Filtrar marcas y modelos precedidos de negación (ej: "no es corolla", "no era toyota")
        descartados = set()
        for m_desc in re.finditer(r"\b(?:no\s+es|no\s+era|no\s+fue)\s+(?:un\s+|una\s+)?([a-z0-9_-]+)\b", texto_l):
            descartados.add(m_desc.group(1).lower())

        marca = None
        for m in MARCAS:
            if m in descartados:
                continue
            if re.search(rf"\b{re.escape(m)}\b", texto_l):
                marca = m.title()
                break

        # Modelos comunes frecuentes
        modelos_comunes = (
            "corolla", "yaris", "hilux", "rav4", "etios", "avanza",
            "sentra", "versa", "tiida", "frontier", "kicks", "march",
            "rio", "cerato", "sportage", "picanto", "seltos", "sorento",
            "elantra", "accent", "tucson", "santa fe", "i10", "grand i10",
            "sail", "aveo", "spark", "onix", "cruze", "tracker",
            "gol", "polo", "vento", "amarok", "golf", "fox",
            "civic", "city", "cr-v", "fit",
        )
        modelo = None
        for mod in modelos_comunes:
            if mod in descartados:
                continue
            if re.search(rf"\b{re.escape(mod)}\b", texto_l):
                modelo = mod.title()
                break

        anio = None
        m_anio = re.search(r"\b((?:19[89]\d|20[0-2]\d))\b", texto)
        if m_anio:
            val_anio = int(m_anio.group(1))
            # Verificar que no coincida con el valor numérico de la placa
            if not (placa and str(val_anio) in placa.replace("-", "")):
                anio = val_anio

        combustible = None
        for k, v in COMBUSTIBLES.items():
            if re.search(rf"\b{re.escape(k)}\b", texto_l):
                combustible = v
                break

        motor = None
        m_motor = re.search(r"\b([0-2]\.[0-9]|v6|v8)\b", texto_l)
        if m_motor:
            motor = m_motor.group(1)

        transmision = None
        if re.search(r"\b(automatica|autom[aá]tico|caja\s+automatica|cvt|dsg)\b", texto_l):
            transmision = "automatica"
        elif re.search(r"\b(mecanica|mec[aá]nico|manual|sincr[oó]nica)\b", texto_l):
            transmision = "manual"

        id_prov = f"PROV_{uuid.uuid4().hex[:8]}" if es_provisional else None

        return VehiculoIdentificado(
            placa=placa if not es_provisional else None,
            es_provisional=es_provisional,
            id_provisional=id_prov,
            marca=marca,
            modelo=modelo,
            anio=anio,
            motor=motor,
            combustible=combustible,
            transmision=transmision,
        )

    @classmethod
    def extraer_hechos_clinicos(cls, texto: str) -> Tuple[List[HechoClinico], List[HechoClinico]]:
        """Extrae hechos clínicos y los clasifica de forma estricta por polaridad (afirmado vs negado)."""
        afirmados: List[HechoClinico] = []
        negados: List[HechoClinico] = []
        texto_l = texto.lower()

        # 1. Utilizar DetectorPolaridad para negaciones y comprobaciones no revisadas
        for campo_nr, val_nr in DetectorPolaridad.extraer_componentes_no_revisados(texto):
            negados.append(HechoClinico(
                campo=campo_nr,
                valor=val_nr,
                polaridad=False,
                categoria="inspeccion_pendiente",
                texto_origen=val_nr,
            ))

        for campo_norm, val_norm in DetectorPolaridad.extraer_sistemas_normales(texto):
            negados.append(HechoClinico(
                campo=campo_norm,
                valor=val_norm,
                polaridad=False,
                categoria="sistema_normal",
                texto_origen=val_norm,
            ))

        # 2. Negaciones específicas de síntomas frecuentes
        negaciones_patrones = [
            (r"\b(?:al\s+frenar|frenando)\s+(?:no|tampoco)\s+(?:vibra|tiembla)\b|\bno\s+(?:vibra|tiembla)\s+al\s+frenar\b", "sintoma_vibracion_frenos", "no vibra al frenar"),
            (r"\bno\s+(?:recalienta|se\s+calienta|hierve|levanta\s+temperatura)\b", "sintoma_sobrecalentamiento", "no recalienta"),
            (r"\bno\s+(?:pierde|bota|gotea|consume)\s+(?:agua|refrigerante|liquido)\b", "sintoma_fuga_refrigerante", "no pierde refrigerante"),
            (r"\bno\s+(?:bota|sale|humo\s+por\s+el)\s+humo\b|\bsin\s+humo\b", "sintoma_humo_escape", "no bota humo"),
            (r"\bluces\s+(?:no\s+bajan|no\s+se\s+aten[uú]an|est[aá]n\s+fuertes)\b", "estado_bateria_luces", "luces no se atenúan"),
        ]
        for pat, campo, val in negaciones_patrones:
            if re.search(pat, texto_l):
                negados.append(HechoClinico(
                    campo=campo,
                    valor=val,
                    polaridad=False,
                    categoria="sintoma_negado",
                    texto_origen=val,
                ))

        # 3. Síntomas afirmados frecuentes
        afirmaciones_patrones = [
            (r"\b(no\s+(?:quiere\s+|quiso\s+)?(?:arranca|arrancar|prende|prender|enciende|encender)|no\s+da\s+marcha)\b", "sintoma_no_arranca", "no arranca"),
            (r"\b(demora\s+en\s+arrancar|tarda\s+en\s+prender|le\s+cuesta\s+arrancar|arranque\s+pesado)\b", "sintoma_demora_arranque", "demora en arrancar"),
            (r"\b(clic\s+seco|un\s+solo\s+clic|chasquido\s+al\s+dar\s+llave)\b", "sintoma_clic_seco", "clic seco al dar arranque"),
            (r"\b(cascabelea|cascabeleo|pistoneo|pistonea)\b", "sintoma_cascabeleo", "cascabeleo"),
            (r"\b(tiembla|vibra|vibraci[oó]n|zapatea)\b", "sintoma_vibracion", "vibración / temblor"),
            (r"\b(pierde\s+fuerza|falta\s+potencia|no\s+tiene\s+fuerza|se\s+chupa|chancho|se\s+ahoga)\b", "sintoma_perdida_potencia", "pérdida de potencia"),
            (r"\b(humo\s+blanco|vapor\s+en\s+el\s+escape)\b", "sintoma_humo_blanco", "humo blanco en escape"),
            (r"\b(humo\s+negro)\b", "sintoma_humo_negro", "humo negro en escape"),
            (r"\b(humo\s+azul)\b", "sintoma_humo_azul", "humo azul en escape"),
            (r"\b(fuga\s+de\s+refrigerante|pierde\s+agua|gotea\s+refrigerante)\b", "sintoma_fuga_refrigerante", "pérdida de refrigerante"),
            (r"\b(temperatura\s+(?:alta|sube|al\s+m[aá]ximo)|se\s+recalienta|hierve)\b", "sintoma_sobrecalentamiento", "sobrecalentamiento"),
            (r"\b(pedal\s+(?:al\s+piso|se\s+hunde|esponjoso|largo))\b", "sintoma_frenos_pedal", "pedal de freno esponjoso/al piso"),
            (r"\b(vibra\s+al\s+frenar|tiembla\s+al\s+frenar)\b", "sintoma_vibracion_frenado", "vibra al frenar"),
        ]
        for pat, campo, val in afirmaciones_patrones:
            # Solo agregar afirmado si no fue explícitamente negado en este mismo turno
            if re.search(pat, texto_l) and not any(n.campo == campo for n in negados):
                afirmados.append(HechoClinico(
                    campo=campo,
                    valor=val,
                    polaridad=True,
                    categoria="sintoma",
                    texto_origen=val,
                ))

        return afirmados, negados

    @classmethod
    def clasificar_intencion(
        cls,
        texto: str,
        tiene_sintomas: bool,
        tiene_dtcs: bool,
        tiene_mediciones: bool,
        es_cambio_caso: bool,
        es_correccion: bool,
    ) -> Tuple[IntentType, str]:
        """Clasifica la intención del usuario de forma jerárquica y determinista."""
        texto_l = texto.lower().strip()

        if cls.PATRON_REINICIO.match(texto):
            return IntentType.REINICIO, "Orden de reinicio explícito de sesión"

        if cls.PATRON_SALUDO.match(texto):
            return IntentType.SALUDO, "Saludo de cortesía sin datos diagnósticos"

        if es_cambio_caso:
            return IntentType.CAMBIO_CASO, "Marcador de cambio hacia otro vehículo o consulta nueva"

        if es_correccion:
            return IntentType.CORRECCION_DATOS, "Marcador de corrección de datos del vehículo activo"

        if cls.PATRON_SOLICITUD_DETALLE.search(texto) and not (tiene_sintomas or tiene_dtcs):
            return IntentType.SOLICITUD_DETALLE, "Solicitud de profundización o procedimiento técnico"

        if tiene_sintomas or tiene_dtcs or tiene_mediciones:
            return IntentType.DIAGNOSTICO_SINTOMA, "Presencia de queja clínica, síntomas o DTCs reportados"

        # Preguntas informativas automotrices puras
        if re.search(r"^(?:qu[eé]|c[oó]mo|cu[aá]ndo|d[oó]nde|cu[aá]nto|por\s+qu[eé])\b", texto_l):
            return IntentType.CONSULTA_TECNICA, "Pregunta informativa de taller sin reporte de falla activa"

        return IntentType.INDETERMINADO, "Mensaje sin marcadores claros"

    @classmethod
    def parse(cls, texto: str) -> UserTurnInputDTO:
        """
        Punto de entrada principal del parser de una sola pasada.
        Retorna el contrato atómico UserTurnInputDTO.
        """
        texto_crudo = texto or ""
        texto_norm = cls.normalizar_texto(texto_crudo)

        # 1. DTCs
        dtcs = [m.upper() for m in cls.PATRON_DTC.findall(texto_crudo)]

        # 2. Mediciones
        mediciones = cls.extraer_mediciones(texto_crudo)

        # 3. Placa
        placa, es_provisional = cls.extraer_placa(texto_crudo, dtcs)

        # 4. Vehículo
        vehiculo = cls.extraer_vehiculo(texto_crudo, placa=placa, es_provisional=es_provisional)

        # 5. Hechos clínicos y polaridad
        afirmados, negados = cls.extraer_hechos_clinicos(texto_crudo)

        # 6. Control de ciclo de vida
        es_cambio = bool(cls.PATRONES_CAMBIO_CASO.search(texto_crudo))
        es_corr = bool(cls.PATRONES_CORRECCION.search(texto_crudo)) and not es_cambio

        # 7. Respuestas cortas
        es_corta = len(texto_norm.split()) <= 3
        val_corta = texto_norm if es_corta else None

        # 8. Intención
        intencion, motivo_int = cls.clasificar_intencion(
            texto=texto_crudo,
            tiene_sintomas=len(afirmados) > 0,
            tiene_dtcs=len(dtcs) > 0,
            tiene_mediciones=len(mediciones) > 0,
            es_cambio_caso=es_cambio,
            es_correccion=es_corr,
        )

        # 9. Datos faltantes clave
        faltantes: List[str] = []
        if not placa and not es_provisional:
            faltantes.append("placa")
        if not afirmados and not dtcs:
            if intencion in (IntentType.DIAGNOSTICO_SINTOMA, IntentType.INDETERMINADO) or placa or vehiculo.marca:
                faltantes.append("sintoma")

        return UserTurnInputDTO(
            mensaje_original=texto_crudo,
            mensaje_normalizado=texto_norm,
            intencion=intencion,
            motivo_intencion=motivo_int,
            vehiculo=vehiculo,
            hechos_afirmados=afirmados,
            hechos_negados=negados,
            dtcs=dtcs,
            mediciones=mediciones,
            es_respuesta_corta=es_corta,
            valor_respuesta_corta=val_corta,
            es_correccion_vehiculo=es_corr,
            es_cambio_caso=es_cambio,
            datos_faltantes=faltantes,
        )
