"""Textos estandarizados de advertencia y banners de seguridad crítica de CarBot."""

from __future__ import annotations

BANNER_FRENO = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO MORTAL - NO CONDUCIR EL VEHÍCULO**\n\n"
    "PROHIBICIÓN ESTRICTA: Detén el motor e inmovilice el vehículo de inmediato. "
    "Existe peligro inminente de pérdida total del sistema de frenos por falla hidráulica severa o daño en mangueras. "
    "Por su seguridad, inmovilice el vehículo de inmediato y solicite traslado exclusivo en grúa para inspección profesional. "
    "Bajo ninguna circunstancia intente conducir ni circular hasta el taller.\n\n"
)

BANNER_FRENO_ESTACIONAMIENTO_RODANDO = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO INMINENTE DE ATROPELLO O COLISIÓN**\n\n"
    "PROHIBICIÓN ESTRICTA: Inmovilice el vehículo DE INMEDIATO. "
    "Vehículo en pendiente sin freno de estacionamiento y en movimiento. Calce las ruedas con cuñas o tacos firmes, "
    "y gire las ruedas contra la vereda o bordillo. No intentes colocarte ni te interpongas en la trayectoria de rodadura. "
    "Solicite asistencia con grúa.\n\n"
)

BANNER_ACEITE = (
    "🛑 **BLOQUEO DE SEGURIDAD MECÁNICA — PELIGRO CRÍTICO: FALTA DE LUBRICACIÓN**\n\n"
    "PROHIBICIÓN ESTRICTA: Detén el motor de inmediato y no intentes arrancar ni circular. "
    "Inmovilice el vehículo y solicita servicio de grúa para trasladarlo al taller y apagar toda marcha. "
    "La presión de aceite en cero o el testigo de aceite encendido con ruidos mecánicos indica falta total de lubricación. "
    "Mantener el motor en marcha provocará fundición o destrucción irreversible de metales internos.\n\n"
)

BANNER_COMBUSTIBLE = (
    "� **BLOQUEO DE SEGURIDAD MECÁNICA — PELIGRO INMINENTE DE INCENDIO Y FUEGO**\n\n"
    "PROHIBICIÓN ESTRICTA: Detén el motor de inmediato y no intentes arrancar ni circular. "
    "Fuga activa de combustible detectada sobre escape caliente, múltiple o fuentes de ignición. "
    "Inmovilice el vehículo, solicita asistencia de grúa para trasladarlo al taller y procede a apagar todo el sistema eléctrico. "
    "Existe peligro extremo de incendio y fuego súbito. Mantén alejadas fuentes de chispa con extintor a mano.\n\n"
)

BANNER_TEMPERATURA = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: SOBRECALENTAMIENTO SEVERO**\n\n"
    "PELIGRO: Detén el vehículo de inmediato y apaga el motor en un lugar seguro. "
    "No abras el tapón del radiador mientras el motor esté caliente o hirviendo. "
    "No retires la tapa del depósito de refrigerante caliente o presurizado. "
    "El líquido presurizado puede causar quemaduras graves por vapor caliente.\n\n"
)

BANNER_HV = (
    "🛑 **BLOQUEO DE SEGURIDAD MECÁNICA — PELIGRO MORTAL DE ALTA TENSIÓN Y ELECTROCUCIÓN**\n\n"
    "PROHIBICIÓN ESTRICTA: Nunca toques, cortes ni manipules cables naranjas, inversor o batería de tracción de alta tensión. "
    "Riesgo inminente de descarga eléctrica letal y electrocución instantánea. "
    "Detén el trabajo de inmediato. Solo personal capacitado puede intervenir, con protección dieléctrica y herramientas "
    "adecuadas al sistema, aislamiento y comprobación de ausencia de tensión conforme al procedimiento OEM. "
    "Apagar el vehículo no acredita ausencia de tensión.\n\n"
)

BANNER_DIESEL_EMBALAMIENTO = (
    "🛑 **BLOQUEO DE SEGURIDAD MECÁNICA — PELIGRO MORTAL: EMBALAMIENTO DIÉSEL**\n\n"
    "PROHIBICIÓN ESTRICTA: Detén el motor inmediatamente si es seguro. No te acerques al motor. "
    "Nunca toques ni introduzcas manos, tablas o trapos en la admisión ante riesgo extremo de atrapamiento o rotura. "
    "No busques fugas ni intentes manipular el motor en marcha. "
    "Aléjate, despeja el área y solicita asistencia de emergencia ante un motor con embalamiento diésel fuera de control. "
    "La llave puede no apagar un motor autoalimentado por vapores de aceite.\n\n"
)

BANNER_DIESEL_ALTA_PRESION = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO DE INYECCIÓN DE COMBUSTIBLE A ALTA PRESIÓN**\n\n"
    "⚠️ **PROHIBICIÓN ESTRICTA: No aflojes racores ni tuberías. No busques fugas ni intentes comprobarlas "
    "con las manos, dedos, piel ni trapos u objetos.** "
    "Aléjate del sistema; no intentes localizar la fuga.\n\n"
    "Si el motor está funcionando, apágalo únicamente si puedes hacerlo desde un lugar seguro, sin acercarte al vano motor. Aléjate y solicita asistencia de personal capacitado para revisar el sistema según el procedimiento del fabricante.\n\n"
    "Si combustible pudo penetrar la piel, busca atención médica de emergencia de inmediato, aunque la lesión parezca pequeña.\n\n"
)

BANNER_BLOQUEO_REGENERACION_DILUCION = (
    "🛑 **BLOQUEO DE SEGURIDAD MECÁNICA: REGENERACIÓN DE DPF CONTRAINDICADA POR DILUCIÓN DE ACEITE**\n\n"
    "⚠️ **PROHIBICIÓN ESTRICTA: NO INICIE LA REGENERACIÓN FORZADA (ESTÁTICA O EN TALLER) EN ESTE MOMENTO.**\n\n"
    "Prohibido realizar la regeneración estática. Detén el motor y no intentes arrancar ni forzar el ciclo.\n\n"
    "1. **Riesgo Crítico de Embalamiento Térmico (Diesel Runaway) e Incendio:**\n"
    "Con el nivel de aceite por encima del máximo y diluido con combustible, la regeneración estática somete al motor a temperaturas extremas (550 °C a 650 °C en escape y cárter caliente) durante 20 a 35 minutos. El calor excesivo vaporiza el diésel acumulado en el cárter, y estos vapores inflamables son aspirados a través del sistema de ventilación positiva del cárter (PCV) hacia la admisión. Al ser un motor diésel sin mariposa de corte estricto, el motor comenzará a combustionar su propio aceite/diésel de forma incontrolada (**embalamiento diésel / runaway**), acelerándose por encima de las 5,000 RPM sin responder a la llave de contacto hasta su desbielamiento catastrófico o incendio en el taller.\n\n"
    "2. **Diferenciación Técnica: Sospecha vs Confirmación Física:**\n"
    "• Si se sospecha sobrellenado, confirme primero el nivel con el vehículo en superficie plana y motor frío (10 minutos de reposo).\n"
    "• Compruebe la consistencia y viscosidad: si el aceite está excesivamente fluido y desprende olor a diésel, sospeche dilución y solicite comprobación técnica.\n\n"
    "3. **Procedimiento Obligatorio Antes de Considerar la Regeneración:**\n"
    "El cambio de aceite por sí solo **NO constituye una autorización automática** para forzar la regeneración. Debe seguirse la secuencia técnica OEM:\n"
    "a) **Drenar y reemplazar totalmente el aceite y filtro contaminados** utilizando lubricante que cumpla estrictamente la norma del fabricante (aceite Low SAPS / bajo contenido de cenizas, ej. ACEA C2/C3).\n"
    "b) **Investigar y corregir la causa de la dilución previa:** postinyecciones reiteradas por regeneraciones automáticas abortadas en ciudad, inyectores con goteo o retorno excesivo, sensor de contrapresión de escape (DPF) descalibrado o termostato que no permite alcanzar temperatura de régimen.\n"
    "c) **Verificar los prerrequisitos OEM obligatorios antes de regenerar:**\n"
    "   • Temperatura de refrigerante de motor estabilizada conforme al manual aplicable.\n"
    "   • Sin códigos de falla activos en sensores EGT (temperatura de escape), MAF, EGR o bujías de incandescencia.\n"
    "   • Masa o acumulación de hollín dentro de los límites de regeneración de servicio.\n"
    "   • Nivel de combustible mínimo en el tanque conforme al manual aplicable.\n"
    "   • Vehículo en exterior ventilado, sobre suelo no inflamable y capó abierto.\n\n"
)

PRERREQUISITOS_REGENERACION_DPF_OEM = (
    "Prerrequisitos pendientes antes de considerar una regeneración DPF: "
    "No se autoriza iniciar el ciclo con esta respuesta. Comprueba nivel y estado del aceite, "
    "investiga y corrige cualquier dilución y su causa; no doy esas comprobaciones por realizadas. "
    "Consulta los límites de temperatura, carga de hollín y combustible del manual aplicable. "
    "Verifica DTC inhibitorios, sensores y seguridad del entorno con personal capacitado. "
    "Sin documentación y condiciones confirmadas, abstenerse de la regeneración forzada.\n"
)

BANNER_BATERIA_MOTOR_ENCENDIDO = (
    "⚠️ **ADVERTENCIA DE SEGURIDAD: NO DESCONECTE LA BATERÍA CON EL MOTOR ENCENDIDO**\n\n"
    "PROHIBICIÓN ESTRICTA: No intentes retirar ni desconectar los bornes de la batería mientras el motor esté funcionando. "
    "Esta maniobra puede generar sobretensiones y dañar módulos electrónicos, alternador u otros componentes eléctricos. "
    "Para comprobar el sistema de carga utilice mediciones apropiadas con multímetro o equipo de diagnóstico.\n\n"
)

BANNER_RADIADOR_CALIENTE = (
    "⚠️ **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO DE QUEMADURAS SEVERAS - NO ABRA EL SISTEMA EN CALIENTE**\n\n"
    "PELIGRO: NUNCA abras ni retires el tapón del radiador ni abras el depósito presurizado mientras el motor o el refrigerante estén calientes o hirviendo. "
    "La liberación súbita de presión expulsará vapor y refrigerante hirviendo a más de 100 °C, causando quemaduras corporales graves e instantáneas. "
    "Espere a que el motor se enfríe completamente y siga el procedimiento de despresurización del fabricante antes de cualquier comprobación o recarga.\n\n"
)

BANNER_AIRBAG_DETONADOR = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PROHIBIDO MEDIR DETONADORES PIROTÉCNICOS (AIRBAG / SRS)**\n\n"
    "PROHIBICIÓN ESTRICTA: Prohibido aplicar multímetro, óhmetro ni lámpara de prueba sobre los terminales del detonador pirotécnico de un airbag o pretensor de cinturón. "
    "La corriente de prueba del instrumento es suficiente para activar y detonar la carga explosiva de inmediato, causando lesiones corporales graves, fracturas o amputación. "
    "No intentes medir el detonador. La desactivación del SRS y el tiempo de descarga deben seguir el manual OEM aplicable; derive el diagnóstico a personal calificado.\n\n"
)

BANNER_APLASTAMIENTO_SOPORTE = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO MORTAL DE APLASTAMIENTO**\n\n"
    "PROHIBICIÓN ESTRICTA: NUNCA ingreses ni trabajes debajo de un vehículo soportado únicamente por una gata hidráulica (de botella o carrito). "
    "Las gatas son exclusivamente herramientas de elevación momentánea, no de retención: un fallo súbito del retén hidráulico o un deslizamiento causará aplastamiento mortal instantáneo. "
    "Por seguridad obligatoria, coloque caballetes / torres mecánicas certificadas sobre superficie plana y firme, y bloquee las ruedas restantes con tacos antes de meterse abajo.\n\n"
)

BANNER_SOLDADURA_COMBUSTIBLE = (
    "� **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO INMINENTE DE EXPLOSIÓN VIOLENTA**\n\n"
    "PROHIBICIÓN ESTRICTA: NUNCA apliques soldadura, soplete ni fuentes de calor sobre un tanque o conducto de combustible, aunque haya sido vaciado recientemente. "
    "Los vapores residuales de gasolina forman una mezcla altamente explosiva dentro del depósito que detonará violentamente al recibir calor. "
    "La reparación exige descontaminación química profesional, desgasificación certificada e inertización con vapor o CO2, o el reemplazo definitivo del tanque por personal calificado.\n\n"
)

BANNER_MONOXIDO_CARBONO = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: INTOXICACIÓN MORTAL POR MONÓXIDO DE CARBONO (CO)**\n\n"
    "PROHIBICIÓN ESTRICTA: Detén el motor de inmediato y sal al aire libre. Los gases de escape en un recinto cerrado acumulan monóxido de carbono, "
    "un veneno letal, invisible e inodoro que provoca mareo, pérdida del conocimiento y asfixia fatal en cuestión de minutos. "
    "Abra portones y ventanas para ventilar completamente el taller antes de reingresar. Nunca aceleres ni mantengas motores en marcha en interiores sin un extractor de humos al exterior.\n\n"
)

BANNER_BATERIA_EXPLOSION = (
    "🛑 **BLOQUEO DE SEGURIDAD MECÁNICA — PELIGRO INMINENTE DE EXPLOSIÓN DE BATERÍA**\n\n"
    "PROHIBICIÓN ESTRICTA: Detén el motor o cargador de inmediato. "
    "Nunca toques ni manipules una batería hinchada, sobrecalentada o que emane gas de azufre/hidrógeno explosivo. "
    "No intentes encender interruptores ni generar chispas en el área. "
    "Ventila inmediatamente el taller y mantente alejado ante riesgo inminente de explosión violenta de la batería y quemaduras por ácido sulfúrico.\n\n"
)

BANNER_DIRECCION_CRITICA = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO DE PÉRDIDA DE CONTROL DE DIRECCIÓN**\n\n"
    "PROHIBICIÓN ESTRICTA: Inmovilice el vehículo de inmediato. "
    "Bloqueo repentino o humo/fuego en la bomba de dirección asistida. Conducir en estas condiciones representa un riesgo inminente de colisión y choque. "
    "Solicite traslado en grúa para inspección profesional del sistema de dirección asistida.\n\n"
)

BANNER_TURBO_INCENDIO = (
    "🛑 **BLOQUEO DE SEGURIDAD MECÁNICA — SOBRECALENTAMIENTO CRÍTICO DE TURBOCOMPRESOR**\n\n"
    "PROHIBICIÓN ESTRICTA: NUNCA toques la caracola ni acerques manos ni materiales inflamables. "
    "Inmovilice el vehículo de inmediato. "
    "La caracola de turbo al rojo vivo con humo de aceite representa un peligro inminente de incendio y falla catastrófica. "
    "Detén el motor si puedes hacerlo sin acercarte al foco de peligro. No lo mantengas en ralentí ni lo reinicies. "
    "Aléjate del vehículo y evita que otros se acerquen; ante humo o fuego solicita servicios de emergencia. "
    "No abras el capó ni intentes localizar fugas junto al escape caliente. "
    "La inspección y el traslado en grúa deben quedar a cargo de personal capacitado cuando el área sea segura.\n\n"
)

BANNER_FRENO_PRECAUCION = (
    "⚠️ **ADVERTENCIA DE SEGURIDAD VIAL: SISTEMA DE FRENOS**\n\n"
    "Cualquier anomalía, chirrido o vibración en frenos compromete la distancia de detención y la estabilidad. "
    "Se recomienda precaución al circular y una inspección física prioritaria en taller especializado con elevador.\n\n"
)

BANNER_SUSPENSION_CRITICA = (
    "⚠️ **ADVERTENCIA DE SEGURIDAD VIAL: SUSPENSIÓN Y DIRECCIÓN**\n\n"
    "Ruidos secos o golpes metálicos al circular sobre baches indican holguras críticas en rótulas, bieletas o bujes "
    "que pueden comprometer el control direccional. Se recomienda inspección física inmediata en elevador por un taller especializado.\n\n"
)

BANNER_ACEITE_DETENCION_INMEDIATA = """🛑 **BLOQUEO DE SEGURIDAD MECÁNICA — PELIGRO CRÍTICO DE DESTRUCCIÓN DEL MOTOR — APAGADO INMEDIATO Y GRÚA OBLIGATORIA**

PROHIBICIÓN ESTRICTA: Detén el motor de inmediato y no intentes arrancar ni circular ni siquiera para llegar al taller. Inmovilice el vehículo. Seguir rodando provocará el fundido o agarrotamiento del cigüeñal y la rotura catastrófica del bloque del motor.

ACCIÓN OBLIGATORIA:
1. Detén el motor de inmediato y procede a apagar todo el vehículo en un lugar seguro.
2. Inmovilice el vehículo y solicita servicio de grúa plataforma para trasladar el auto al taller.
3. No intentes arrancar hasta desmontar cárter, verificar coladera obstruida o daño en la bomba de aceite."""

BANNER_INCOMPATIBILIDAD_BUJIAS_DIESEL = """� **INCOMPATIBILIDAD TÉCNICA Y SEGURIDAD: MOTORES DIÉSEL NO UTILIZAN BUJÍAS DE CHISPA**

⚠️ **FUNDAMENTO TERMODINÁMICO:** Los motores diésel funcionan por **autoencendido por compresión** (el aire se comprime a alta presión y temperatura en el cilindro antes de inyectar el combustible a más de 1600 bar). NO tienen ni pueden equipar bujías de chispa de encendido.

🔧 **DISPOSITIVOS REALES DEL MOTOR DIÉSEL:**
• Los únicos elementos roscados en la cámara son las **bujías de precalentamiento (calentadores / glow plugs)**, cuya función es exclusivamente entibiar la precámara o cámara durante el arranque en frío.
• Si el motor diésel no arranca, las comprobaciones válidas son: estado de los calentadores (resistencia en ohmios), presión en el riel Common Rail y compresión mecánica."""

BANNER_INCOMPATIBILIDAD_24V_12V = """🛑 **BLOQUEO DE SEGURIDAD MECÁNICA — INCOMPATIBILIDAD DE ALIMENTACIÓN ELÉCTRICA**

PROHIBICIÓN ESTRICTA: No conectes baterías en serie ni fuentes de tensión incompatibles al alternador o vehículo. Si la fuente es de 24 V y el alternador es de 12V como indicas, no realices esa conexión. Detén la prueba de inmediato: puede dañar reguladores y módulos, quemar cableado y provocar incendio o explosión de batería. Consulta la alimentación nominal y el procedimiento del fabricante antes de cualquier prueba; no improvises conexiones."""
