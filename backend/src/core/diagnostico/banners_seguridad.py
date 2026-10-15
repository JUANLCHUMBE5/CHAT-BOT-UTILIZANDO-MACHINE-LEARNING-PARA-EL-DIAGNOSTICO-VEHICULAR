"""Textos estandarizados de advertencia y banners de seguridad crítica de CarBot."""

from __future__ import annotations

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
