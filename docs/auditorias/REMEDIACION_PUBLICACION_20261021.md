# Remediación para publicación y despliegue

Rama: codex/diagnostico-general-confianza. Se conservan los modelos y los ocho hashes canónicos. corpus_validado=False; selección experimental desactivada.

Correcciones: reinicio explícito antes de autopreguntas; procesamiento del síntoma incluido junto al comando de caso; registro de seguimiento ambiguo sin convertirlo en confirmación; conservación de síntomas durante bloqueos críticos; adaptación de metadatos históricos al contrato de recuperación; paquete corrupto inutilizado sin reconstrucción ni fallback; página exacta de cifra separada del alcance documental; orientación diferencial cualitativa ante pérdida de fuerza bajo carga.

Seguridad: se mantienen las prohibiciones de Common Rail, refrigeración caliente y DPF contaminado. Se explicita atención de emergencia y riesgo de embalamiento sin añadir umbrales OEM.

Validación intermedia: 141 regresiones aprobadas; suite completa inicial 2108 PASS, 5 FAIL y 6 ERROR, con los errores localizados en el montaje incompleto del paquete experimental. Nombre/usuario de PostgreSQL de pruebas alineados con el contrato existente. Reejecución final con PostgreSQL/Redis aislados en curso al crear este commit.

Benchmark conocido: 107/120; fallos incluyen expectativas de cifras universales no autorizadas. Se mantienen escenarios y criterios sin modificación. No es holdout independiente ni exactitud oficial de tesis.

Frontend separado: candidato sobre carbot-frontend/main 0c07f993; build, lint y nueve harness aprobados, conservando paginación y cambios responsivos. No se alteran registros operativos ni datos de tesis.

La autorización de despliegue está registrada. La activación requiere CI del SHA exacto, evidencia de integridad y reversión. Resultados finales y activación se documentarán tras completarse.
