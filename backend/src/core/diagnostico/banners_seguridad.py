"""Textos estandarizados de advertencia y banners de seguridad crítica de CarBot."""

from __future__ import annotations

BANNER_FRENO = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO MORTAL - NO CONDUCIR EL VEHÍCULO**\n"
    "Existe peligro inminente de pérdida total del sistema de frenos por falla hidráulica severa o daño en mangueras. "
    "Por su seguridad, inmovilice el vehículo de inmediato y solicite traslado exclusivo en grúa para inspección profesional. "
    "Bajo ninguna circunstancia intente conducir ni circular hasta el taller.\n\n"
)

BANNER_FRENO_ESTACIONAMIENTO_RODANDO = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO INMINENTE DE ATROPELLO O COLISIÓN**\n"
    "Vehículo en pendiente sin freno de estacionamiento y en movimiento. Inmovilice el vehículo DE INMEDIATO: calce las ruedas con cuñas o tacos firmes, "
    "y gire las ruedas contra la vereda o bordillo. No se interponga en la trayectoria de rodadura y solicite asistencia con grúa.\n\n"
)

BANNER_ACEITE = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: APAGUE EL MOTOR INMEDIATAMENTE**\n"
    "La presión de aceite en cero o el testigo de aceite encendido con ruidos mecánicos indica falta total de lubricación. "
    "Mantener el motor en marcha provocará fundición o destrucción irreversible de metales internos. "
    "No vuelva a dar arranque hasta verificar el nivel y la presión mecánica.\n\n"
)

BANNER_COMBUSTIBLE = (
    "🔥 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO INMINENTE DE INCENDIO Y FUEGO**\n"
    "Fuga activa de combustible detectada sobre componentes calientes o fuentes de ignición. Apague el motor de inmediato y no accione componentes eléctricos. "
    "Existe peligro extremo de fuego súbito. Mantenga alejadas fuentes de ignición y solicite asistencia técnica urgente en un área ventilada con extintor a mano.\n\n"
)

BANNER_TEMPERATURA = (
    "⚠️ **ADVERTENCIA CRÍTICA DE SEGURIDAD: SOBRECALENTAMIENTO SEVERO**\n"
    "Detenga el vehículo en un lugar seguro y apague el motor. "
    "NUNCA intente abrir el tapón del radiador ni del depósito de refrigerante mientras el motor esté caliente: "
    "el líquido presurizado causará quemaduras graves inmediatas.\n\n"
)

BANNER_HV = "PELIGRO: No toques, cortes ni manipules cables naranjas, inversor o batería de tracción. Mantente alejado del sistema de alta tensión. Apagar el vehículo no acredita ausencia de tensión. Cualquier intervención requiere personal capacitado y el procedimiento, verificación de ausencia de tensión y protección establecidos por el fabricante para esa variante."

BANNER_DIESEL_EMBALAMIENTO = "PELIGRO: Embalamiento diésel. No te acerques al motor ni introduzcas manos, tablas o trapos en la admisión. Aléjate, despeja el área y solicita asistencia de emergencia. La llave puede no detener un motor autoalimentado. Solo personal capacitado debe aplicar el procedimiento de emergencia previsto por el fabricante, sin exponerse."

BANNER_DIESEL_ALTA_PRESION = "PELIGRO: No aflojes racores ni cañerías Common Rail con el motor funcionando o el sistema presurizado. No busques fugas con manos, trapos, cartón ni papel. Detén el motor si puedes hacerlo sin exponerte, mantente alejado y solicita personal capacitado. El apagado no acredita despresurización: cualquier intervención requiere el procedimiento y equipo del fabricante para esa variante. Si sospechas una lesión por inyección de combustible, solicita atención urgente e informa del combustible a alta presión."

BANNER_BLOQUEO_REGENERACION_DILUCION = "PELIGRO: No inicies regeneración forzada del DPF con sospecha de dilución o sobrellenado de aceite. Detén la maniobra. El cambio de aceite por sí solo no autoriza regenerar. Un taller capacitado debe verificar nivel, posible contaminación y su causa mediante el procedimiento del fabricante. Sin documentación aplicable no publico umbrales ni autorizo sustituciones o regeneración."

PRERREQUISITOS_REGENERACION_DPF_OEM = "No inicies regeneración forzada sin documentación OEM aplicable al vehículo, motor y mercado. Los umbrales de temperatura, hollín, presión diferencial y combustible deben verificarse en esa documentación y con el equipo indicado. Corregir el aceite no autoriza automáticamente el ciclo. Mantén pendiente la intervención hasta acreditar las condiciones y la seguridad del entorno."

BANNER_BATERIA_MOTOR_ENCENDIDO = (
    "⚠️ **ADVERTENCIA DE SEGURIDAD: NO DESCONECTE LA BATERÍA CON EL MOTOR ENCENDIDO**\n"
    "No retire ni desconecte los bornes de la batería mientras el motor esté funcionando. "
    "Esta maniobra puede generar sobretensiones y dañar módulos electrónicos, alternador u otros componentes eléctricos. "
    "Para comprobar el sistema de carga utilice mediciones apropiadas con multímetro o equipo de diagnóstico.\n\n"
)

BANNER_RADIADOR_CALIENTE = (
    "⚠️ **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO DE QUEMADURAS SEVERAS - NO ABRA EL SISTEMA EN CALIENTE**\n"
    "PELIGRO: NUNCA retire el tapón del radiador ni abra el depósito presurizado mientras el motor o el refrigerante estén calientes o hirviendo. "
    "La liberación súbita de presión expulsará vapor y refrigerante hirviendo a más de 100 °C, causando quemaduras corporales graves e instantáneas. "
    "Espere a que el motor se enfríe completamente y siga el procedimiento de despresurización del fabricante antes de cualquier comprobación o recarga.\n\n"
)

BANNER_AIRBAG_DETONADOR = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PROHIBIDO MEDIR DETONADORES PIROTÉCNICOS (AIRBAG / SRS)**\n"
    "PELIGRO: NUNCA aplique multímetro, óhmetro ni lámpara de prueba sobre los terminales del detonador pirotécnico de un airbag o pretensor de cinturón. "
    "La corriente de prueba del instrumento es suficiente para activar y detonar la carga explosiva de inmediato, causando lesiones corporales graves, fracturas o amputación. "
    "No mida el detonador. La desactivación del SRS y el tiempo de descarga deben seguir el manual OEM aplicable; derive el diagnóstico a personal calificado.\n\n"
)

BANNER_APLASTAMIENTO_SOPORTE = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO MORTAL DE APLASTAMIENTO**\n"
    "PELIGRO: NUNCA ingrese ni trabaje debajo de un vehículo soportado únicamente por una gata hidráulica (de botella o carrito). "
    "Las gatas son exclusivamente herramientas de elevación momentánea, no de retención: un fallo súbito del retén hidráulico o un deslizamiento causará aplastamiento mortal instantáneo. "
    "Por seguridad obligatoria, coloque caballetes / torres mecánicas certificadas sobre superficie plana y firme, y bloquee las ruedas restantes con tacos antes de meterse abajo.\n\n"
)

BANNER_SOLDADURA_COMBUSTIBLE = (
    "🔥 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO INMINENTE DE EXPLOSIÓN VIOLENTA**\n"
    "PELIGRO: NUNCA aplique soldadura, soplete ni fuentes de calor sobre un tanque o conducto de combustible, aunque haya sido vaciado recientemente. "
    "Los vapores residuales de gasolina forman una mezcla altamente explosiva dentro del depósito que detonará violentamente al recibir calor. "
    "La reparación exige descontaminación química profesional, desgasificación certificada e inertización con vapor o CO2, o el reemplazo definitivo del tanque por personal calificado.\n\n"
)

BANNER_MONOXIDO_CARBONO = (
    "⚠️ **ADVERTENCIA CRÍTICA DE SEGURIDAD: INTOXICACIÓN MORTAL POR MONÓXIDO DE CARBONO (CO)**\n"
    "PELIGRO: APAGUE EL MOTOR INMEDIATAMENTE Y SALGA AL AIRE LIBRE. Los gases de escape en un recinto cerrado acumulan monóxido de carbono, "
    "un veneno letal, invisible e inodoro que provoca mareo, pérdida del conocimiento y asfixia fatal en cuestión de minutos. "
    "Abra portones y ventanas para ventilar completamente el taller antes de reingresar. Nunca acelere ni mantenga motores en marcha en interiores sin un extractor de humos al exterior.\n\n"
)

BANNER_BATERIA_EXPLOSION = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO INMINENTE DE EXPLOSIÓN DE BATERÍA**\n"
    "PELIGRO: Una batería hinchada, sobrecalentada y con desprendimiento de gas de azufre (olor a huevo podrido) está sufriendo una fuga térmica con emisión masiva de hidrógeno explosivo y ácido sulfúrico. "
    "Desconecte de inmediato la alimentación del cargador o apague el motor sin generar chispas. Ventile intensamente el área, deje enfriar sin tocarla y no acerque ninguna fuente de ignición. "
    "El reemplazo de la batería debe realizarse con gafas de seguridad y guantes de protección química.\n\n"
)

BANNER_DIRECCION_CRITICA = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO DE PÉRDIDA DE CONTROL DE DIRECCIÓN**\n"
    "PELIGRO: Bloqueo repentino o humo/fuego en la bomba de dirección asistida. Conducir en estas condiciones representa un riesgo inminente de colisión y choque. "
    "Inmovilice el vehículo de inmediato y solicite traslado en grúa para inspección profesional del sistema de dirección asistida.\n\n"
)

BANNER_TURBO_INCENDIO = (
    "⚠️ **ADVERTENCIA DE SEGURIDAD: SOBRECALENTAMIENTO CRÍTICO DE TURBOCOMPRESOR**\n"
    "La caracola de turbo al rojo vivo con humo de aceite representa un peligro inminente de incendio y falla catastrófica. "
    "Mantenga el motor en ralentí durante 3 a 5 minutos para que la circulación de aceite disipe el calor extremo sin apagar de golpe "
    "(apagarlo de inmediato carboniza el aceite y destruye los cojinetes). Aleje de inmediato cualquier material inflamable del vano motor "
    "y verifique fugas de aceite hacia el escape.\n\n"
)

BANNER_FRENO_PRECAUCION = (
    "⚠️ **ADVERTENCIA DE SEGURIDAD VIAL: SISTEMA DE FRENOS**\n"
    "Cualquier anomalía, chirrido o vibración en frenos compromete la distancia de detención y la estabilidad. "
    "Se recomienda precaución al circular y una inspección física prioritaria en taller especializado con elevador.\n\n"
)

BANNER_SUSPENSION_CRITICA = (
    "⚠️ **ADVERTENCIA DE SEGURIDAD VIAL: SUSPENSIÓN Y DIRECCIÓN**\n"
    "Ruidos secos o golpes metálicos al circular sobre baches indican holguras críticas en rótulas, bieletas o bujes "
    "que pueden comprometer el control direccional. Se recomienda inspección física inmediata en elevador por un taller especializado.\n\n"
)

BANNER_ACEITE_DETENCION_INMEDIATA = """🛑 *PELIGRO CRÍTICO DE DESTRUCCIÓN DEL MOTOR — APAGADO INMEDIATO Y GRÚA OBLIGATORIA*

⚠️ **RIESGO INMINENTE:** La luz roja de aceite combinada con ruido o cascabeleo metálico indica **pérdida total o crítica de presión de lubricación** y contacto metal-metal en metales de biela, bancada o árbol de levas.

🚫 **PROHIBICIÓN ESTRICTA:** **BAJO NINGUNA CIRCUNSTANCIA continúes circulando ni mantengas el motor encendido** ni siquiera para llegar al taller. Seguir rodando provocará el fundido o agarrotamiento del cigüeñal y la perforación catastrófica del bloque del motor.

🚜 **ACCIÓN OBLIGATORIA:**
1. **Apaga el motor de inmediato** en un lugar seguro.
2. **Solicita servicio de GRÚA plataforma** para trasladar el vehículo al taller.
3. No des arranque hasta desmontar cárter, verificar coladera obstruida o daño en la bomba de aceite."""

BANNER_INCOMPATIBILIDAD_BUJIAS_DIESEL = """🚫 *INCOMPATIBILIDAD TÉCNICA Y SEGURIDAD: MOTORES DIÉSEL NO UTILIZAN BUJÍAS DE CHISPA*

⚠️ **FUNDAMENTO TERMODINÁMICO:** Los motores diésel funcionan por **autoencendido por compresión** (el aire se comprime a alta presión y temperatura en el cilindro antes de inyectar el combustible a más de 1600 bar). NO tienen ni pueden equipar bujías de chispa de encendido.

🔧 **DISPOSITIVOS REALES DEL MOTOR DIÉSEL:**
• Los únicos elementos roscados en la cámara son las **bujías de precalentamiento (calentadores / glow plugs)**, cuya función es exclusivamente entibiar la precámara o cámara durante el arranque en frío.
• Si el motor diésel no arranca, las comprobaciones válidas son: estado de los calentadores (resistencia en ohmios), presión en el riel Common Rail y compresión mecánica."""

BANNER_INCOMPATIBILIDAD_24V_12V = """⚡ *PELIGRO EXTREMO DE INCENDIO Y DESTRUCCIÓN ELECTRÓNICA — INCOMPATIBILIDAD 24 V EN 12 V*

⚠️ **RIESGO CRÍTICO:** Conectar 24 voltios a un sistema eléctrico y electrónico automotriz diseñado para 12 voltios provocará una sobretensión destructiva instantánea.

💥 **CONSECUENCIAS CATASTRÓFICAS:**
• **Explosión térmica de la batería de 12 V** y proyección violenta de ácido sulfúrico.
• **Destrucción irreversible de la ECU (computadora de motor)**, módulos BCM, airbag y tablero de instrumentos por sobretensión en varistores y pistas internas.
• **Riesgo severo de incendio vehicular** en el ramal principal de cables.

🚫 **PROHIBICIÓN ABSOLUTA:** Jamás uses cargadores, arrancadores auxiliares o camiones de 24 V para alimentar o auxiliar un vehículo de 12 V."""
