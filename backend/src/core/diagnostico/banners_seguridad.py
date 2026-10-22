"""Textos estandarizados de advertencia y banners de seguridad crítica de CarBot."""

from __future__ import annotations

BANNER_FRENO = (
    "🛑 **PELIGRO CRÍTICO: FALLA DE FRENOS; NO CONDUCIR EL VEHÍCULO**\n"
    "Los síntomas informados pueden indicar una pérdida de capacidad de frenado. "
    "Por su seguridad, inmovilice el vehículo de inmediato y solicite traslado en grúa para inspección profesional. "
    "Bajo ninguna circunstancia intente conducir hasta el taller.\n\n"
)

BANNER_FRENO_ESTACIONAMIENTO_RODANDO = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO INMINENTE DE ATROPELLO O COLISIÓN**\n\n"
    "PROHIBICIÓN ESTRICTA: Inmovilice el vehículo DE INMEDIATO. "
    "Vehículo en pendiente sin freno de estacionamiento y en movimiento. Calce las ruedas con cuñas o tacos firmes, "
    "y gire las ruedas contra la vereda o bordillo. No intentes colocarte ni te interpongas en la trayectoria de rodadura. "
    "Solicite asistencia con grúa.\n\n"
)

BANNER_ACEITE = (
    "🛑 **PELIGRO CRÍTICO: TESTIGO ROJO DE ACEITE CON RUIDO; DETENGA EL MOTOR Y NO CONDUZCA**\n"
    "Cuando sea seguro, detenga el vehículo y apague el motor. No lo vuelva a arrancar ni lo conduzca hasta que "
    "un técnico compruebe la presión real de lubricación y determine la causa. Solicite traslado en grúa; "
    "el testigo junto con un traqueteo puede indicar una avería grave y continuar la marcha puede destruir el motor.\n\n"
)

BANNER_COMBUSTIBLE = (
    "🔥 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO INMINENTE DE INCENDIO**\n"
    "La fuga de combustible, en especial cerca de superficies calientes, puede provocar fuego o un incendio. "
    "No arranque ni mueva el vehículo, no accione componentes eléctricos y no intente localizar o reparar la fuga. "
    "Aléjese, mantenga a otras personas y fuentes de ignición apartadas y solicite asistencia profesional.\n\n"
)

BANNER_TEMPERATURA = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: SOBRECALENTAMIENTO SEVERO**\n\n"
    "PELIGRO: Detén el vehículo de inmediato y apaga el motor en un lugar seguro. "
    "No abras el tapón del radiador mientras el motor esté caliente o hirviendo. "
    "No retires la tapa del depósito de refrigerante caliente o presurizado. "
    "El líquido presurizado puede causar quemaduras graves por vapor caliente.\n\n"
)

BANNER_HV = (
    "⚡ **ADVERTENCIA DE SEGURIDAD: SISTEMA DE ALTA TENSIÓN (EV/HÍBRIDO)**\n"
    "Los cables naranjas y la batería de tracción pueden causar electrocución. No corte, toque, desconecte "
    "ni manipule el sistema, el inversor o la batería. No manipule los cables naranjas ni la batería de tracción. "
    "Aléjese y derive la intervención a un técnico certificado "
    "que siga el procedimiento OEM específico.\n\n"
)

BANNER_DIESEL_EMBALAMIENTO = (
    "⚠️ **ADVERTENCIA CRÍTICA DE SEGURIDAD: RIESGO DE EMBALAMIENTO DIÉSEL (DIESEL RUNAWAY)**\n"
    "No te acerques al motor si hay indicios de aceleración descontrolada; no te aproximes al motor ni intente bloquear la admisión o intervenir "
    "componentes. Aléjese y aparte a otras personas; solicite ayuda de emergencia. Si el motor está apagado y hay "
    "sospecha de aceite diluido, no vuelva a arrancarlo ni fuerce la regeneración: solicite inspección profesional "
    "antes de operar el vehículo.\n\n"
)

BANNER_DIESEL_ALTA_PRESION = (
    "🛑 **ADVERTENCIA CRÍTICA DE SEGURIDAD: PELIGRO DE INYECCIÓN DE COMBUSTIBLE A ALTA PRESIÓN**\n\n"
    "⚠️ **PROHIBICIÓN ESTRICTA: NUNCA intente buscar, tocar, palpar ni comprobar fugas con las manos, dedos, piel ni trapos mientras el sistema de combustible esté o pueda estar presurizado.**\n\n"
    "No busques fugas ni te acerques a comprobarlas: no aflojes racores ni manipules el riel. Una línea Common Rail puede conservar presión peligrosa aunque el motor se haya detenido. No afloje tuberías, "
    "inyectores ni conexiones, y no intente comprobar la fuga. Mantenga distancia y derive la inspección a personal "
    "capacitado con el procedimiento OEM correspondiente. Si sospecha que combustible penetró la piel, acuda "
    "inmediatamente a urgencias para atención médica de emergencia e informe que se trata de una posible lesión por inyección subcutánea de "
    "combustible a alta presión."
)

BANNER_BLOQUEO_REGENERACION_DILUCION = (
    "🛑 **BLOQUEO DE SEGURIDAD MECÁNICA: REGENERACIÓN DE DPF CONTRAINDICADA POR DILUCIÓN DE ACEITE**\n\n"
    "⚠️ **PROHIBICIÓN ESTRICTA: NO INICIE LA REGENERACIÓN FORZADA, NO FUERCE EL CICLO Y NO ARRANQUE EL MOTOR.**\n\n"
    "No inicie ni fuerce la regeneración mientras persistan los indicios de contaminación. "
    "Un nivel de aceite por encima del máximo o con indicios de combustible puede señalar dilución y aumentar "
    "el riesgo de daños graves o embalamiento diésel / runaway (aceleración descontrolada). No realice comprobaciones ni reparaciones con el motor "
    "en marcha. Mantenga el vehículo apagado y solicite evaluación profesional para confirmar la condición y su causa.\n\n"
    "Diferenciación Técnica: Sospecha vs Confirmación Física. El aceite apropiado (por ejemplo, Low SAPS cuando lo exija el OEM) debe determinarse con la especificación del fabricante; esta mención NO constituye una autorización automática. El reemplazo de aceite por sí solo no autoriza una regeneración. Antes de considerar esa operación, un técnico "
    "debe comprobar la variante exacta del vehículo y seguir el procedimiento OEM aplicable. No hay umbrales "
    "universales de temperatura, hollín, presión o combustible que pueda recomendarse sin esa fuente."
)

PRERREQUISITOS_REGENERACION_DPF_OEM = (
    "📋 *Prerrequisitos y comprobaciones OEM antes de forzar la regeneración de DPF:*\n\n"
    "No existe una lista universal de valores para todos los vehículos. No inicie el ciclo basándose en cifras genéricas "
    "ni solo en el cambio de aceite. Confirme la marca, modelo, año, motor y mercado, identifique la causa de la "
    "dilución y consulte el procedimiento OEM correspondiente. Sin ese documento y sus criterios verificables, "
    "CarBot no puede indicar umbrales ni autorizar la regeneración; derive la comprobación a un técnico capacitado."
)

BANNER_BATERIA_MOTOR_ENCENDIDO = (
    "⚠️ **ADVERTENCIA DE SEGURIDAD: NO DESCONECTE LA BATERÍA CON EL MOTOR ENCENDIDO**\n\n"
    "PROHIBICIÓN ESTRICTA: No intentes retirar ni desconectar los bornes de la batería mientras el motor esté funcionando. "
    "Esta maniobra puede generar sobretensiones y dañar módulos electrónicos, alternador u otros componentes eléctricos. "
    "Para comprobar el sistema de carga utilice mediciones apropiadas con multímetro o equipo de diagnóstico.\n\n"
)

BANNER_RADIADOR_CALIENTE = (
    "⚠️ **PELIGRO: NO ABRA EL SISTEMA DE REFRIGERACIÓN EN CALIENTE**\n"
    "NUNCA abras el tapón del radiador ni el depósito presurizado mientras el motor o el refrigerante estén calientes. "
    "El sistema puede expulsar vapor y refrigerante a presión y causar quemaduras graves. "
    "Espere a que el motor se enfríe y solicite asistencia si no puede verificarlo con seguridad.\n\n"
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
    "🛑 **PELIGRO DE INTOXICACIÓN: SALGA DEL TALLER AHORA**\n"
    "El motor en marcha en un espacio cerrado puede acumular gases tóxicos, incluido monóxido de carbono. "
    "Salga al aire libre y avise a las demás personas para que también salgan. No arranque ni siga usando el motor. "
    "No vuelva a entrar para ventilar o apagarlo si eso exige exponerse; solicite ayuda de emergencia, "
    "especialmente si alguien siente mareo, "
    "náuseas, confusión o dolor de cabeza.\n\n"
)

BANNER_BATERIA_EXPLOSION = (
    "🛑 **BLOQUEO DE SEGURIDAD MECÁNICA — PELIGRO INMINENTE DE EXPLOSIÓN DE BATERÍA**\n\n"
    "PROHIBICIÓN ESTRICTA: Detén el motor o cargador de inmediato. "
    "Nunca toques ni manipules una batería hinchada, sobrecalentada o que emane gas de azufre/hidrógeno explosivo. "
    "No intentes encender interruptores ni generar chispas en el área. "
    "Ventila inmediatamente el taller y mantente alejado ante riesgo inminente de explosión violenta de la batería y quemaduras por ácido sulfúrico.\n\n"
)

BANNER_DIRECCION_CRITICA = (
    "🛑 **PELIGRO CRÍTICO EN LA DIRECCIÓN: NO CONDUZCA EL VEHÍCULO; NO CONTINÚE CONDUCIENDO**\n"
    "Una pérdida repentina de asistencia o humo en la dirección puede comprometer el control del vehículo. "
    "Deténgase en un lugar seguro únicamente si puede hacerlo sin maniobras bruscas; no continúe la marcha "
    "ni realice una prueba de ruta. Solicite asistencia y evaluación profesional antes de volver a circular.\n\n"
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


BANNER_BATERIA_DANADA = (
    "⚠️ **PELIGRO DE INCENDIO O EXPLOSIÓN: BATERÍA CALIENTE, HINCHADA O CON EMISIÓN DE GAS**\n"
    "Aléjese y mantenga a otras personas apartadas. No toque, cargue, puentee, mida ni desconecte la batería; "
    "evite chispas y fuentes de ignición. Si continúa calentándose, humea o emite gas, evacúe el área y contacte "
    "a los servicios de emergencia. No intente retirarla.\n\n"
)


BANNER_GATO_SIN_CABALLETES = (
    "🛑 **PELIGRO DE APLASTAMIENTO: NO TRABAJE DEBAJO SIN SOPORTE SEGURO**\n"
    "Una gata hidráulica por sí sola no es un soporte seguro para trabajar debajo. Salga de la zona de caída "
    "sin ubicarse bajo el vehículo y no intente manipular la gata desde esa posición. Solicite apoyo de personal "
    "capacitado. No vuelva debajo hasta confirmar un soporte seguro, como caballetes adecuados, instalado por "
    "personal competente conforme al fabricante. La seguridad de la inspección depende de un soporte estable.\n\n"
)


BANNER_AIRBAG_SRS = (
    "🛑 **PELIGRO: NO MIDA EL DETONADOR DEL AIRBAG**\n"
    "No conecte un multímetro, óhmetro ni fuente eléctrica al detonador o circuito SRS. La medición podría "
    "activar o detonar el airbag y causar lesiones. No manipule el circuito; derive la comprobación a personal "
    "capacitado que siga el procedimiento OEM específico.\n\n"
)


BANNER_VEHICULO_RODANDO = (
    "🛑 **PELIGRO INMEDIATO: VEHÍCULO SIN SUJECIÓN EN PENDIENTE**\n"
    "No se coloque delante, detrás ni en la trayectoria del vehículo, y no intente detenerlo con el cuerpo. "
    "Aléjese a una posición protegida, advierta a otras personas desde un lugar seguro y solicite asistencia "
    "para inmovilizarlo. No lo conduzca ni haga pruebas.\n\n"
)


BANNER_ESCAPE_CALIENTE = (
    "⚠️ **PELIGRO DE QUEMADURA O INCENDIO: ESCAPE O TURBO INCANDESCENTE**\n"
    "No toque, cubra ni enfríe el turbo o el escape y mantenga materiales inflamables y personas alejados. "
    "Si hay humo persistente o llamas, evacúe el área y contacte a emergencias; no se acerque para inspeccionar. "
    "Detén el motor solo si puedes hacerlo sin acercarte al peligro. No lo mantengas en ralentí ni lo reinicies. Solicite evaluación profesional antes de volver a operar el vehículo.\n\n"
)


BANNER_SOLDADURA_TANQUE = (
    "🛑 **PELIGRO DE EXPLOSIÓN: NO SUELDE NI CALIENTE EL TANQUE**\n"
    "Vaciar un tanque no garantiza que haya eliminado los vapores inflamables. No manipule el tanque ni use soplete, soldadura, "
    "corte ni otra fuente de calor. La reparación requiere un procedimiento profesional de trabajo en caliente "
    "y verificación segura del tanque; solicite un taller especializado.\n\n"
)


BANNER_ALTERNADOR_SOBREVOLTAJE = (
    "⚠️ **NO APLIQUE 24 V A UN ALTERNADOR DE 12V**\n"
    "No conectes baterías en serie ni energice el alternador para hacer esa prueba. La tensión puede quemar o dañar el "
    "regulador, los diodos y otros componentes, y producir chispas. Confirme la tensión nominal del sistema y "
    "siga el procedimiento del fabricante con equipo de prueba adecuado; si no puede confirmarlo, no lo energice.\n\n"
)


BANNER_DIESEL_EMBALAMIENTO_ACTIVO = (
    "🛑 **EMERGENCIA: MOTOR DIÉSEL ACELERADO SIN CONTROL (EMBALAMIENTO DIÉSEL)**\n"
    "No se acerque al vano motor, no intente bloquear la admisión ni manipular componentes. Aleje a las personas "
    "de la trayectoria y del vehículo, evacúe el área si hay humo o riesgo de incendio y contacte de inmediato "
    "a los servicios de emergencia. No vuelva a operar el vehículo hasta una evaluación profesional.\n\n"
)

BANNER_TEMPERATURA += "NUNCA intente abrir el tapón del radiador mientras el motor o el refrigerante permanezcan calientes.\n\n"
