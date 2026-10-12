"""Política centralizada de seguridad para respuestas diagnósticas críticas de CarBot."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Optional, Tuple


class SeveridadSeguridad(str, Enum):
    """Niveles de severidad de riesgo para la seguridad física y del vehículo."""
    CRITICAL_STOP = "CRITICAL_STOP"          # Peligro de vida / pérdida de frenos / incendio / fundición inminente
    URGENT_INSPECTION = "URGENT_INSPECTION"  # Inspección prioritaria antes de continuar marcha prolongada
    NORMAL_DIAGNOSTIC = "NORMAL_DIAGNOSTIC"  # Diagnóstico técnico estándar de taller


# Patrones deterministas de condiciones críticas
PATRON_FRENO_CRITICO = re.compile(
    r"\b(pedal\s+(?:se\s+fue|se\s+va|llego|llega)\s+al\s+fondo|pedal\s+al\s+piso|"
    r"se\s+queda\s+sin\s+frenos?|sin\s+presi[oó]n\s+de\s+frenos?|pedal\s+sin\s+resistencia|"
    r"fuga\s+(?:grave|severa|importante|abundante)?\s*de\s+l[ií]quido\s+de\s+frenos?|"
    r"charco\s+de\s+l[ií]quido\b.{0,30}\bfreno|"
    r"bomba\s+de\s+freno\s+reventada|freno\s+no\s+responde)\b",
    re.IGNORECASE,
)

PATRON_ACEITE_CRITICO = re.compile(
    r"\b((?:luz\s+(?:roja\s+)?(?:de\s+)?|testigo\s+(?:rojo\s+)?(?:de\s+)?)(?:presi[oó]n\s+de\s+)?aceite\b.{0,50}\b(?:encend|prend|son|suen|ruido|cascabeleo|met[aá]lic|golpete)|"
    r"presi[oó]n\s+de\s+aceite\s+(?:en\s+)?(?:cero|0|baja|nula)|"
    r"sin\s+presi[oó]n\s+de\s+aceite|bomba\s+de\s+aceite\s+rota)\b",
    re.IGNORECASE,
)

PATRON_COMBUSTIBLE_CRITICO = re.compile(
    r"\b(fuga\s+(?:de\s+)?(?:gasolina|nafta|combustible)|gotea\s+(?:gasolina|nafta|combustible)|"
    r"fuga\s+cerca\s+del\s+escape|olor\s+fuert(?:e|emente)\s+a\s+(?:gasolina|nafta|combustible)|"
    r"chorrea\s+gasolina|l[ií]nea\s+de\s+gasolina\s+rota)\b",
    re.IGNORECASE,
)

PATRON_TEMPERATURA_CRITICA = re.compile(
    r"\b(temperatura\s+(?:al\s+m[aá]ximo|en\s+zona\s+roja|al\s+tope|pegada\s+al\s+m[aá]ximo|sube\s+casi\s+a\s+la\s+zona\s+roja|muy\s+alta|cr[ií]tica|peligrosa)|"
    r"aguja\s+(?:de\s+temperatura\s+)?(?:sube|llega|casi|en)\s+(?:a\s+la\s+)?zona\s+roja|"
    r"(?:el\s+motor\s+|motor\s+)?recalienta(?:\s+cuando|\s+en|\s+al|\s+detenido|\s+parado)?|"
    r"recalentamiento\s+(?:extremo|severo|peligroso|del\s+motor|en\s+tr[aá]fico)?|"
    r"(?:sale|bota|botando|sale\s+con|expulsa|tirando)\s+(?:mucho\s+)?vapor|"
    r"(?:agua|refrigerante)\s+hirviendo|hirviendo\s+(?:con\s+vapor|el\s+agua|el\s+refrigerante)|"
    r"sale\s+vapor\s+(?:blanco\s+)?(?:del\s+motor|debajo\s+del\s+cap[oó]|por\s+el\s+cap[oó])|hierve\s+el\s+refrigerante|"
    r"burbujea\s+el\s+(?:dep[oó]sito|reservorio|tanque|radiador)|"
    r"radiador\s+(?:hirviendo|reventado|rajado|botando\s+agua)|"
    r"sobrecalentamiento\s+(?:extremo|severo|peligroso|motor)|humo\s+de\s+vapor\s+blanco\s+en\s+vano|"
    r"(?:temperatura\s+(?:del\s+motor\s+)?de\s+)?(?:10[6-9]|1[1-9]\d)\s*(?:°\s*c|c|grados))\b",
    re.IGNORECASE,
)

PATRON_ALTA_TENSION = re.compile(
    r"\b(alta\s+tensi[oó]n|alto\s+voltaje|aislamiento\s+(?:de\s+)?(?:alto\s+voltaje|alta\s+tensi[oó]n|hv)|"
    r"cable(?:ado)?\s+naranja|bater[ií]a\s+de\s+tracci[oó]n|bater[ií]a\s+hv|inversor\s+igbt|inversor\s+el[eé]ctrico|"
    r"falla\s+de\s+aislamiento\s+el[eé]ctrico|propulsi[oó]n\s+ev)\b",
    re.IGNORECASE,
)

PATRON_DIESEL_EMBALAMIENTO_CRITICO = re.compile(
    r"\b("
    r"(?:embalamiento|runaway|desbielamiento|aceleraci[oó]n\s+descontrolada)\b|"
    r"(?:c[aá]rter\s+lleno\s+de\s+(?:di[eé]sel|petr[oó]leo)|aceite\s+(?:diluido|mezclado)\s+con\s+(?:di[eé]sel|petr[oó]leo))|"
    r"(?:peligro\b.{0,35}\b(?:arranc(?:ar|o)|encend(?:er|ido))\b.{0,45}\b(?:c[aá]rter|aceite|di[eé]sel))|"
    r"(?:medidas?\s+de\s+seguridad\b.{0,45}\bregeneraci[oó]n)|"
    r"(?:(?:varilla|nivel\s+de\s+aceite)\b.{0,45}\b(?:\d+\s*cm|por\s+encima|sobre|alto)\b.{0,45}\b(?:full|m[aá]ximo)\b.{0,60}\b(?:dpf|regeneraci[oó]n|p2463|di[eé]sel|1gd|holl[ií]n))|"
    r"(?:(?:dpf|regeneraci[oó]n|p2463|holl[ií]n)\b.{0,60}\b(?:varilla|nivel\s+de\s+aceite)\b.{0,45}\b(?:\d+\s*cm|por\s+encima|sobre|alto)\b.{0,45}\b(?:full|m[aá]ximo))"
    r")\b",
    re.IGNORECASE,
)

PATRON_DIESEL_ALTA_PRESION_TACTIL = re.compile(
    r"\b("
    r"(?:(?:pas(?:ar|o|e|ando)|toc(?:ar|o|e|ando)|palp(?:ar|o|e|ando)|tante(?:ar|o|e|ando)|met(?:er|o|e|iendo)|acerc(?:ar|o|e|ando))\s+(?:la\s+mano|el\s+dedo|las\s+manos|los\s+dedos|la\s+piel|mano|(?:un\s+|una\s+)?(?:trapo|trapito|franela|tela|paño))\b.{0,60}\b(?:cañer[ií]a|caño|tuber[ií]a|tubo|riel|rail|inyector|alta\s+presi[oó]n|fuga|petr[oó]leo|di[eé]sel|combustible))|"
    r"(?:(?:cañer[ií]a|caño|tuber[ií]a|tubo|riel|rail|common\s*rail|inyector|alta\s+presi[oó]n|fuga|petr[oó]leo|di[eé]sel|chorro)\b.{0,60}\b(?:pas(?:ar|o|e|ando)|toc(?:ar|o|e|ando)|palp(?:ar|o|e|ando)|tante(?:ar|o|e|ando)|met(?:er|o|e|iendo)|acerc(?:ar|o|e|ando)|revis(?:ar|o|e))\b.{0,35}\b(?:la\s+mano|el\s+dedo|las\s+manos|los\s+dedos|la\s+piel|mano|con\s+(?:la\s+mano|el\s+dedo|un\s+trapo|trapito|una\s+franela|tela|paño)|(?:un\s+|una\s+)?(?:trapo|trapito|franela|tela|paño)))|"
    r"(?:(?:revis(?:ar|o|e)|busc(?:ar|o|e)|sentir|tante(?:ar|o|e)|comprob(?:ar|o|e)|detect(?:ar|o|e))\b.{0,45}\b(?:fuga|petr[oó]leo|di[eé]sel|inyecci[oó]n|chorro)\b.{0,45}\b(?:con\s+(?:la\s+mano|el\s+dedo|las\s+manos|los\s+dedos|un\s+trapo|trapito|trapos|el\s+cuerpo|la\s+piel|una\s+franela|tela|paño)|a\s+mano|al\s+tacto))|"
    r"(?:(?:con\s+(?:la\s+mano|el\s+dedo|las\s+manos|los\s+dedos|un\s+trapo|trapito|trapos|una\s+franela|tela|paño)|al\s+tacto)\b.{0,45}\b(?:revis(?:ar|o|e)|busc(?:ar|o|e)|sentir|tante(?:ar|o|e)|comprob(?:ar|o|e)|detect(?:ar|o|e))\b.{0,45}\b(?:fuga|petr[oó]leo|di[eé]sel|cañer[ií]a|caño|tuber[ií]a|tubo|riel|inyector|chorro))|"
    r"(?:(?:puedo|voy\s+a|se\s+puede|meter(?:le)?)\s+(?:tocar|pasar(?:le|lo)?\s+(?:la\s+mano|el\s+dedo|(?:un\s+|una\s+)?(?:trapo|trapito|franela|tela|paño))|usar\s+(?:un\s+|una\s+)?(?:trapo|trapito|franela|tela|paño)|palpar|tantear|meter\s+mano)\b.{0,50}\b(?:cañer[ií]a|caño|tuber[ií]a|tubo|inyector|fuga|petr[oó]leo|riel|chorro))|"
    r"(?:(?:qu[eé]\s+riesgo|peligro|es\s+peligroso|qu[eé]\s+pasa\s+si|qu[eé]\s+consecuencia(?:s)?|consecuencia\s+m[eé]dica)\b.{0,50}\b(?:fuga\s+de\s+alta\s+presi[oó]n|chorro\s+de\s+inyecci[oó]n|alta\s+presi[oó]n\s+(?:di[eé]sel|petr[oó]leo|common\s*rail)|fuga\s+en\s+(?:el\s+)?common\s*rail|chorro\s+de\s+(?:di[eé]sel|petr[oó]leo|inyecci[oó]n)))|"
    r"(?:(?:pinche|pinchazo|inyecci[oó]n)\b.{0,30}\b(?:chorro|alta\s+presi[oó]n|di[eé]sel|petr[oó]leo|common\s*rail)\b)"
    r")\b",
    re.IGNORECASE,
)

PATRON_SOLICITUD_REGENERACION_DPF = re.compile(
    r"\b("
    r"(?:(?:le\s+)?(?:tiro|meto|hago|fuerzo|iniciar|activo)|tirar(?:le)?|meter(?:le)?|hacer(?:le)?|forzar(?:le)?|iniciar|activar|ejecutar|realizar|puedo\s+(?:forzar|hacer|iniciar|activar|ejecutar|realizar|tirar|meter)|voy\s+a\s+(?:forzar|hacer|iniciar|activar|ejecutar|realizar|tirar|meter))\s+(?:(?:una|la|el)\s+)?(?:regeneraci[oó]n|regenerar|regenerada)\b|"
    r"regeneraci[oó]n\s+(?:forzada|est[aá]tica|estacionaria|con\s+(?:el\s+)?esc[aá]ner)|"
    r"regenerar\s+(?:el\s+)?(?:dpf|filtro|fap)\s+(?:con\s+(?:el\s+)?esc[aá]ner|en\s+(?:taller|est[aá]tico|parado)|a\s+la\s+fuerza)|"
    r"(?:puedo|se\s+puede)\s+regenerar\b|"
    r"destapar\s+(?:el\s+)?(?:filtro|dpf)\s+(?:con\s+(?:el\s+)?esc[aá]ner|forzando)"
    r")\b",
    re.IGNORECASE,
)

PATRON_INDICIOS_DILUCION_ACEITE = re.compile(
    r"\b("
    r"(?:varilla|nivel\s+de\s+aceite|aceite)\b.{0,50}(?:\d+\s*cm|por\s+encima|encima|sobre|alto|pasado)\b.{0,30}\b(?:full|m[aá]ximo|marca)|"
    r"aceite\b.{0,40}\b(?:diluido|mezclado|con\s+olor|huele|olor\s+a)\b.{0,30}\b(?:di[eé]sel|petr[oó]leo|combustible)|"
    r"(?:olor\s+a\s+(?:di[eé]sel|petr[oó]leo)|huele\s+a\s+(?:di[eé]sel|petr[oó]leo))\b.{0,40}\baceite|"
    r"c[aá]rter\b.{0,35}\b(?:lleno|sobrellenado|con\s+(?:di[eé]sel|petr[oó]leo)|contaminado)|"
    r"(?:nivel|aceite)\s+(?:de\s+aceite\s+)?subi[oó]\b|"
    r"subi[oó]\s+(?:el\s+)?nivel(?:\s+de\s+aceite)?|"
    r"aceite\s+est[aá]\s+pasado\s+del\s+m[aá]ximo"
    r")\b",
    re.IGNORECASE,
)

PATRON_CORRECCION_ACEITE_COMPROBADA = re.compile(
    r"\b("
    r"(?:dren[eé]|vaci[eé]|bot[eé]|cambi[eé]|puse|coloqu[eé]|reemplac[eé]|correg[ií])\b.{0,50}\b(?:aceite|filtro|problema\s+del\s+aceite)|"
    r"aceite\s+(?:ya\s+)?(?:est[aá]\s+)?(?:nuevo|cambiado|reemplazado|a\s+nivel|en\s+su\s+nivel)|"
    r"nivel\s+(?:normal|correcto|en\s+el\s+m[aá]ximo|entre\s+marcas)"
    r")\b",
    re.IGNORECASE,
)

PATRON_APERTURA_RADIADOR_CALIENTE = re.compile(
    r"\b("
    r"(?:(?:abr(?:ir|o|e|ando)|destap(?:ar|o|e|ando)|retir(?:ar|o|e|ando)|quit(?:ar|o|e|ando)|sacar)\b.{0,45}\b(?:tapa|tap[oó]n|radiador|dep[oó]sito|reservorio)\b.{0,60}\b(?:caliente|hirviendo|temperatura\s+alta|10[0-9]|1[1-9]\d))|"
    r"(?:(?:caliente|hirviendo|temperatura\s+alta|10[0-9]|1[1-9]\d)\b.{0,60}\b(?:abr(?:ir|o|e|ando)|destap(?:ar|o|e|ando)|retir(?:ar|o|e|ando)|quit(?:ar|o|e|ando)|sacar)\b.{0,45}\b(?:tapa|tap[oó]n|radiador|dep[oó]sito|reservorio))"
    r")\b",
    re.IGNORECASE,
)


BANNER_FRENO = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: NO CONDUCIR EL VEHÍCULO**\n"
    "Existe riesgo inminente de pérdida total del sistema de frenos por falla hidráulica severa. "
    "Por su seguridad, inmovilice el vehículo de inmediato y solicite traslado en grúa para inspección profesional. "
    "Bajo ninguna circunstancia intente conducir hasta el taller.\n\n"
)

BANNER_ACEITE = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: APAGUE EL MOTOR INMEDIATAMENTE**\n"
    "La presión de aceite en cero o el testigo de aceite encendido con ruidos mecánicos indica falta total de lubricación. "
    "Mantener el motor en marcha provocará fundición o destrucción irreversible de metales internos. "
    "No vuelva a dar arranque hasta verificar el nivel y la presión mecánica.\n\n"
)

BANNER_COMBUSTIBLE = (
    "🔥 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO INMINENTE DE INCENDIO**\n"
    "Fuga activa de combustible detectada. No intente arrancar el motor ni accionar componentes eléctricos. "
    "Mantenga alejadas fuentes de ignición o calor y solicite asistencia técnica profesional en un área ventilada.\n\n"
)

BANNER_TEMPERATURA = (
    "⚠️ **ADVERTENCIA CRÍTICA DE SEGURIDAD: SOBRECALENTAMIENTO SEVERO**\n"
    "Detenga el vehículo en un lugar seguro y apague el motor. "
    "NUNCA intente abrir el tapón del radiador ni del depósito de refrigerante mientras el motor esté caliente: "
    "el líquido presurizado causará quemaduras graves inmediatas.\n\n"
)

BANNER_HV = (
    "⚡ **ADVERTENCIA DE SEGURIDAD: SISTEMA DE ALTA TENSIÓN (EV/HÍBRIDO)**\n"
    "Los sistemas de propulsión eléctrica e híbrida operan con tensiones letales (> 300V DC). "
    "Está estrictamente prohibido que el usuario o personal no capacitado toque, desconecte o manipule cables naranjas, el inversor o la batería de tracción. "
    "La intervención exige derivación obligatoria a un técnico certificado en alta tensión y protocolos normados.\n\n"
)

BANNER_DIESEL_EMBALAMIENTO = (
    "⚠️ **ADVERTENCIA CRÍTICA DE SEGURIDAD: RIESGO DE EMBALAMIENTO DIÉSEL (DIESEL RUNAWAY)**\n"
    "El nivel de aceite por encima del máximo con combustible acumulado en el cárter (dilución por regeneraciones de DPF fallidas o postinyección) "
    "representa un peligro severo de embalamiento del motor diésel: el motor puede aspirar los vapores de aceite y combustible "
    "a través del sistema de ventilación del cárter (PCV) y acelerarse sin control hasta su destrucción catastrófica o incendio, "
    "sin responder al corte de llave de contacto.\n"
    "🛑 **MEDIDA OBLIGATORIA:** NO intente arrancar el motor ni forzar regeneraciones estáticas hasta drenar y reemplazar completamente "
    "el aceite y filtro contaminados, y verificar la causa de la postinyección anómala.\n\n"
)

BANNER_DIESEL_ALTA_PRESION = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO DE INYECCIÓN DE COMBUSTIBLE A ALTA PRESIÓN**\n\n"
    "⚠️ **PROHIBICIÓN ESTRICTA: NUNCA intente buscar, tocar, palpar ni comprobar fugas con las manos, dedos, piel ni trapos mientras el sistema de combustible esté o pueda estar presurizado.**\n\n"
    "1. **Riesgo Vital y Mecanismo de Lesión:**\n"
    "Los sistemas Common Rail operan a presiones extremas de 1,000 a más de 2,200 bar (15,000 a 32,000+ psi). Un orificio diminuto o chorro fino microscópico de combustible a esta presión **atraviesa la piel y los guantes de trabajo instantáneamente**, penetrando profundamente en los tejidos musculares y torrente sanguíneo. Aunque la herida de entrada inicial parezca un pinchazo minúsculo, indoloro o insignificante, el combustible provoca toxicidad química inmediata, trombosis vascular, gangrena y necrosis masiva de tejidos, con alto riesgo de **amputación del miembro o muerte por sepsis**.\n\n"
    "2. **Procedimiento Seguro de Inspección:**\n"
    "• **Detenga inmediatamente el motor** y corte el contacto.\n"
    "• **Espere el tiempo de despresurización** especificado por el fabricante OEM (típicamente 5 a 15 minutos) antes de aproximarse al vano motor.\n"
    "• Para localizar el origen de una fuga, utilice **únicamente una pantalla protectora de cartón grueso o papel**, manteniéndola a distancia segura con pinzas o mango largo para observar si se mancha con el rocío de combustible. Utilice siempre gafas de seguridad y protección facial completa.\n\n"
    "3. **Protocolo Médico de Emergencia Obligatorio:**\n"
    "Si sospecha que combustible a alta presión ha entrado en contacto con su piel o ha penetrado en cualquier parte de su cuerpo, **ACUDA DE INMEDIATO A UN SERVICIO HOSPITALARIO DE URGENCIAS**. Advierta de inmediato al personal médico tratante que se trata de un accidente por **inyección de hidrocarburo a alta presión**, el cual requiere evaluación quirúrgica urgente para desbridamiento y descompresión, independientemente de la aparente levedad del orificio externo."
)

BANNER_BLOQUEO_REGENERACION_DILUCION = (
    "🛑 **BLOQUEO DE SEGURIDAD MECÁNICA: REGENERACIÓN DE DPF CONTRAINDICADA POR DILUCIÓN DE ACEITE**\n\n"
    "⚠️ **PROHIBICIÓN ESTRICTA: NO INICIE LA REGENERACIÓN FORZADA (ESTÁTICA O EN TALLER) EN ESTE MOMENTO.**\n\n"
    "1. **Riesgo Crítico de Embalamiento Térmico (Diesel Runaway) e Incendio:**\n"
    "Con el nivel de aceite por encima del máximo y diluido con combustible, la regeneración estática somete al motor a temperaturas extremas (550 °C a 650 °C en escape y cárter caliente) durante 20 a 35 minutos. El calor excesivo vaporiza el diésel acumulado en el cárter, y estos vapores inflamables son aspirados a través del sistema de ventilación positiva del cárter (PCV) hacia la admisión. Al ser un motor diésel sin mariposa de corte estricto, el motor comenzará a combustionar su propio aceite/diésel de forma incontrolada (**embalamiento diésel / runaway**), acelerándose por encima de las 5,000 RPM sin responder a la llave de contacto hasta su desbielamiento catastrófico o incendio en el taller.\n\n"
    "2. **Diferenciación Técnica: Sospecha vs Confirmación Física:**\n"
    "• Si se sospecha sobrellenado, confirme primero el nivel con el vehículo en superficie plana y motor frío (10 minutos de reposo).\n"
    "• Compruebe la consistencia y viscosidad: si el aceite está excesivamente fluido y desprende olor a diésel, la dilución está confirmada físicamente.\n\n"
    "3. **Procedimiento Obligatorio Antes de Considerar la Regeneración:**\n"
    "El cambio de aceite por sí solo **NO constituye una autorización automática** para forzar la regeneración. Debe seguirse la secuencia técnica OEM:\n"
    "a) **Drenar y reemplazar totalmente el aceite y filtro contaminados** utilizando lubricante que cumpla estrictamente la norma del fabricante (aceite Low SAPS / bajo contenido de cenizas, ej. ACEA C2/C3).\n"
    "b) **Investigar y corregir la causa de la dilución previa:** postinyecciones reiteradas por regeneraciones automáticas abortadas en ciudad, inyectores con goteo o retorno excesivo, sensor de contrapresión de escape (DPF) descalibrado o termostato que no permite alcanzar temperatura de régimen.\n"
    "c) **Verificar los prerrequisitos OEM obligatorios antes de regenerar:**\n"
    "   • Temperatura de refrigerante de motor estabilizada (> 75 °C - 80 °C).\n"
    "   • Sin códigos de falla activos en sensores EGT (temperatura de escape), MAF, EGR o bujías de incandescencia.\n"
    "   • Masa o acumulación de hollín dentro de los límites de regeneración de servicio (típicamente < 100% o < 35-40 gramos; por encima de ese umbral, la regeneración estática está prohibida por riesgo de sobretemperatura y rotura del sustrato cerámico, requiriendo limpieza química desmontado o reemplazo).\n"
    "   • Nivel de combustible mínimo en el tanque (al menos 1/4 o 15 litros).\n"
    "   • Vehículo en exterior ventilado, sobre suelo no inflamable (lejos de pasto o cartones) y capó abierto."
)

PRERREQUISITOS_REGENERACION_DPF_OEM = (
    "📋 *Prerrequisitos y comprobaciones OEM antes de forzar la regeneración de DPF:*\n\n"
    "Habiendo verificado y corregido el aceite de motor (nivel correcto y sin dilución), confirme todos los requisitos del manual de servicio antes de iniciar el ciclo con el escáner:\n\n"
    "1. **Temperatura de motor:** Refrigerante estabilizado a temperatura de régimen de trabajo (> 75 °C - 80 °C).\n"
    "2. **Sin DTCs inhibitorios:** Compruebe que no existan códigos activos en sensores de temperatura de escape (EGT), sensor MAF, válvula EGR ni bujías de precalentamiento (esenciales para postinyección térmica).\n"
    "3. **Masa de hollín dentro de límites de servicio:** La acumulación no debe superar el umbral crítico de regeneración estática (típicamente < 100% o < 35-40 gramos; con cargas superiores está prohibida la regeneración por riesgo de incendio del panal cerámico, requiriendo desmontaje para lavado químico o reemplazo).\n"
    "4. **Sensor de presión diferencial:** Compruebe que las mangueras no estén cuarteadas y que la lectura en ralentí sea coherente (< 20-25 mbar con filtro saturado, < 5-8 mbar limpio).\n"
    "5. **Nivel de combustible:** Al menos 1/4 de tanque (mínimo 15 litros).\n"
    "6. **Seguridad del entorno:** Vehículo estacionado en área abierta ventilada, lejos de materiales inflamables (suelo de concreto, capó abierto)."
)


BANNER_BATERIA_MOTOR_ENCENDIDO = (
    "⚠️ **ADVERTENCIA DE SEGURIDAD: NO DESCONECTE LA BATERÍA CON EL MOTOR ENCENDIDO**\n"
    "No retire ni desconecte los bornes de la batería mientras el motor esté funcionando. "
    "Esta maniobra puede generar sobretensiones y dañar módulos electrónicos, alternador u otros componentes eléctricos. "
    "Para comprobar el sistema de carga utilice mediciones apropiadas con multímetro o equipo de diagnóstico.\n\n"
)

BANNER_RADIADOR_CALIENTE = (
    "⚠️ **ADVERTENCIA DE SEGURIDAD: NO ABRA EL SISTEMA DE REFRIGERACIÓN EN CALIENTE**\n"
    "No retire el tapón del radiador ni abra el depósito presurizado mientras el motor o el refrigerante estén calientes. "
    "El sistema puede expulsar vapor y refrigerante a presión y causar quemaduras graves. "
    "Espere a que el motor se enfríe antes de realizar una inspección segura.\n\n"
)


class PoliticaSeguridad:
    """Capa centralizada de auditoría y aplicación de directivas de seguridad en respuestas."""

    PRERREQUISITOS_REGENERACION_DPF_OEM = PRERREQUISITOS_REGENERACION_DPF_OEM

    @classmethod
    def _hay_dilucion_aceite_activa(
        cls,
        texto_usuario: str,
        estado: Optional[Any] = None,
    ) -> bool:
        """Determina si existe reporte activo de dilución de aceite o sobrellenado peligroso."""
        txt_l = texto_usuario.lower()
        if PATRON_CORRECCION_ACEITE_COMPROBADA.search(txt_l):
            return False

        if PATRON_INDICIOS_DILUCION_ACEITE.search(txt_l):
            return True

        if estado is not None:
            hechos = getattr(estado, "hechos", {})
            for k, h in hechos.items():
                campo = str(getattr(h, "campo", "")).lower()
                st = getattr(h, "estado", None)
                st_val = str(getattr(st, "value", st)).upper()
                if (
                    k in ("reemplazado_aceite", "aceite_reemplazado", "aceite_drenado_reemplazado")
                    or ("aceite" in campo and "reemplazado" in campo)
                ):
                    if st_val in ("CONFIRMADO", "ACTIVO", "SI"):
                        return False

            for k, h in hechos.items():
                campo = str(getattr(h, "campo", "")).lower()
                st = getattr(h, "estado", None)
                st_val = str(getattr(st, "value", st)).upper()
                if (
                    k in ("aceite_sobrellenado_diluido", "dilucion_aceite_combustible")
                    or "dilucion" in campo
                    or "sobrellenado" in campo
                    or ("aceite" in campo and "maximo" in campo)
                ):
                    if st_val not in ("DESCARTADO", "CORREGIDO", "AUSENTE_NEGADO"):
                        return True

            hist = getattr(estado, "historial_mensajes_usuario", [])
            if hist:
                dilucion_idx = -1
                correccion_idx = -1
                for idx, msg in enumerate(hist):
                    msg_l = msg.lower()
                    if PATRON_INDICIOS_DILUCION_ACEITE.search(msg_l):
                        dilucion_idx = idx
                    if PATRON_CORRECCION_ACEITE_COMPROBADA.search(msg_l):
                        correccion_idx = idx

                if dilucion_idx != -1 and correccion_idx <= dilucion_idx:
                    return True

        return False

    @classmethod
    def evaluar_severidad(
        cls,
        texto_usuario: str,
        diagnostico_ml: str = "",
        estado: Optional[Any] = None,
    ) -> Tuple[SeveridadSeguridad, Optional[str]]:
        """Evalúa si la condición descrita requiere un banner de seguridad crítico."""
        txt_comb = f"{texto_usuario} {diagnostico_ml}".lower()

        # 1. Comprobación de fuga de combustible Common Rail a alta presión (búsqueda táctil / contacto directo)
        if PATRON_DIESEL_ALTA_PRESION_TACTIL.search(texto_usuario):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_DIESEL_ALTA_PRESION

        # 2. Comprobación de bloqueo de regeneración DPF con dilución de aceite / cárter sobrellenado
        if PATRON_SOLICITUD_REGENERACION_DPF.search(texto_usuario):
            if cls._hay_dilucion_aceite_activa(texto_usuario, estado):
                return SeveridadSeguridad.CRITICAL_STOP, BANNER_BLOQUEO_REGENERACION_DILUCION

        # 3. Solicitud de abrir/destapar sistema de refrigeración en caliente
        if PATRON_APERTURA_RADIADOR_CALIENTE.search(texto_usuario):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_RADIADOR_CALIENTE

        if PATRON_DIESEL_EMBALAMIENTO_CRITICO.search(txt_comb):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_DIESEL_EMBALAMIENTO
        if PATRON_FRENO_CRITICO.search(txt_comb):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_FRENO
        if PATRON_ACEITE_CRITICO.search(txt_comb):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_ACEITE
        if PATRON_COMBUSTIBLE_CRITICO.search(txt_comb):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_COMBUSTIBLE
        if PATRON_TEMPERATURA_CRITICA.search(txt_comb):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_TEMPERATURA
        if PATRON_ALTA_TENSION.search(txt_comb):
            return SeveridadSeguridad.CRITICAL_STOP, BANNER_HV

        return SeveridadSeguridad.NORMAL_DIAGNOSTIC, None

    @classmethod
    def enriquecer_respuesta_seguridad(
        cls,
        respuesta_texto: str,
        texto_usuario: str,
        diagnostico_ml: str = "",
        estado: Optional[Any] = None,
    ) -> str:
        """
        Garantiza que toda respuesta frente a una condición crítica presente
        la advertencia obligatoria al inicio y no contenga instrucciones peligrosas.
        """
        sev, banner = cls.evaluar_severidad(texto_usuario, diagnostico_ml, estado=estado)
        if banner is None:
            return cls.interceptar_maniobras_peligrosas(respuesta_texto)

        # Si es banner de Common Rail, bloqueo de regeneración o radiador caliente, debe ser la respuesta íntegra prioritaria
        if banner in (BANNER_DIESEL_ALTA_PRESION, BANNER_BLOQUEO_REGENERACION_DILUCION, BANNER_RADIADOR_CALIENTE):
            return banner.strip()

        # Si la respuesta ya incluye el banner exacto, no duplicar ni pasar el banner oficial por el interceptor
        banner_clean = banner.strip()
        if banner_clean in respuesta_texto:
            return respuesta_texto

        # Para alta tensión, sanear posibles invitaciones peligrosas a reparar con guantes
        resp_modificada = respuesta_texto
        if sev == SeveridadSeguridad.CRITICAL_STOP and banner == BANNER_HV:
            resp_modificada = re.sub(
                r"\b(p[oó]ngase|use)\s+guantes\s+(?:diel[eé]ctricos\s+)?clase\s+0\s+y\s+(?:repare|desarme|revise|manipule|toque)\b",
                "la manipulación con guantes Clase 0 está reservada exclusivamente a técnicos certificados",
                resp_modificada,
                flags=re.IGNORECASE,
            )

        resp_modificada = cls.interceptar_maniobras_peligrosas(resp_modificada)

        return f"{banner}{resp_modificada}".strip()

    @classmethod
    def interceptar_maniobras_peligrosas(
        cls,
        respuesta_texto: str,
    ) -> str:
        """
        Intercepta instrucciones operativas peligrosas que pudieran aparecer
        en una respuesta generada, aunque el síntoma del usuario no haya
        activado previamente una condición crítica.
        """
        respuesta = respuesta_texto or ""
        # ----------------------------------------------------
        # Batería: nunca recomendar desconexión con motor activo
        # ----------------------------------------------------
        patron_bateria = re.compile(
            r"\b(?:desconect(?:a|e|ar)|retir(?:a|e|ar)|quit(?:a|e|ar))"
            r".{0,45}\b(?:borne|terminal|bater[ií]a)\b"
            r".{0,80}\b(?:motor\s+(?:encendido|en\s+marcha|funcionando)|"
            r"veh[ií]culo\s+encendido)\b",
            re.IGNORECASE,
        )

        patron_bateria_inverso = re.compile(
            r"\b(?:motor\s+(?:encendido|en\s+marcha|funcionando)|"
            r"veh[ií]culo\s+encendido)\b"
            r".{0,80}\b(?:desconect(?:a|e|ar)|retir(?:a|e|ar)|quit(?:a|e|ar))"
            r".{0,45}\b(?:borne|terminal|bater[ií]a)\b",
            re.IGNORECASE,
        )

        prefijos_negacion = ("no ", "nunca ", "evite ", "prohibido ", "sin ", "no intente ", "no abrir", "no retirar", "no quitar", "no se debe ")

        bateria_peligrosa = False
        for m in patron_bateria.finditer(respuesta):
            pre = respuesta[max(0, m.start() - 30):m.start()].lower()
            if not any(w in pre for w in prefijos_negacion):
                bateria_peligrosa = True
                break
        if not bateria_peligrosa:
            for m in patron_bateria_inverso.finditer(respuesta):
                sub_txt = m.group(0)
                m_v = re.search(r"\b(?:desconect(?:a|e|ar)|retir(?:a|e|ar)|quit(?:a|e|ar))\b", sub_txt, re.IGNORECASE)
                if m_v:
                    idx = m_v.start()
                    pre = sub_txt[max(0, idx - 30):idx].lower()
                    if not any(w in pre for w in prefijos_negacion):
                        bateria_peligrosa = True
                        break

        # ----------------------------------------------------
        # Refrigeración: nunca recomendar apertura en caliente
        # ----------------------------------------------------
        patron_radiador = re.compile(
            r"\b(?:abr(?:e|ir)|retir(?:a|e|ar)|quit(?:a|e|ar))"
            r".{0,50}\b(?:tap[oó]n|tapa)"
            r".{0,40}\b(?:radiador|dep[oó]sito|refrigerante)\b"
            r".{0,90}\b(?:caliente|motor\s+caliente|temperatura\s+alta)\b",
            re.IGNORECASE,
        )

        patron_radiador_inverso = re.compile(
            r"\b(?:motor\s+caliente|refrigerante\s+caliente|"
            r"temperatura\s+alta)\b"
            r".{0,90}\b(?:abr(?:e|ir)|retir(?:a|e|ar)|quit(?:a|e|ar))"
            r".{0,50}\b(?:tap[oó]n|tapa)"
            r".{0,40}\b(?:radiador|dep[oó]sito)\b",
            re.IGNORECASE,
        )

        radiador_peligroso = False
        for m in patron_radiador.finditer(respuesta):
            pre = respuesta[max(0, m.start() - 30):m.start()].lower()
            if not any(w in pre for w in prefijos_negacion):
                radiador_peligroso = True
                break
        if not radiador_peligroso:
            for m in patron_radiador_inverso.finditer(respuesta):
                sub_txt = m.group(0)
                m_v = re.search(r"\b(?:abr(?:e|ir)|retir(?:a|e|ar)|quit(?:a|e|ar))\b", sub_txt, re.IGNORECASE)
                if m_v:
                    idx = m_v.start()
                    pre = sub_txt[max(0, idx - 30):idx].lower()
                    if not any(w in pre for w in prefijos_negacion):
                        radiador_peligroso = True
                        break

        banners = []

        if bateria_peligrosa:
            banners.append(BANNER_BATERIA_MOTOR_ENCENDIDO.strip())

        if radiador_peligroso:
            banners.append(BANNER_RADIADOR_CALIENTE.strip())

        if not banners:
            return respuesta

        # Ante una instrucción insegura generada, no conservar
        # parcialmente la frase original: podría dejar fragmentos
        # gramaticales o instrucciones ambiguas.
        recomendaciones_seguras = []

        if bateria_peligrosa:
            recomendaciones_seguras.append(
                "Para comprobar el sistema de carga, mida el voltaje con un multímetro "
                "o equipo de diagnóstico sin desconectar la batería mientras el motor está en marcha."
            )

        if radiador_peligroso:
            recomendaciones_seguras.append(
                "Para revisar el sistema de refrigeración, apague el motor y espere a que "
                "se enfríe completamente antes de abrir o retirar cualquier tapón presurizado."
            )

        prefijo = "\n\n".join(banners)
        recomendacion = " ".join(recomendaciones_seguras)

        return f"{prefijo}\n\n{recomendacion}".strip()
