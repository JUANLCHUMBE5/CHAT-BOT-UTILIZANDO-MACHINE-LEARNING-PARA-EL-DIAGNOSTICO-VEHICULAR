# Publicación del candidato de confianza — 2026-10-21

Autorización: publicar los cambios en GitHub y después desplegar.

Este commit conserva el candidato local en una rama de revisión del monorepo. No sustituye los repositorios separados ni modifica sus ramas main. Se excluyen archivos operativos, credenciales, datos de tesis y los scripts de auditoría profunda ajenos a este cambio.

Validación previa: 2171 PASS, 41 FAIL, 6 ERROR, 75 omitidas; benchmark conocido 107/120. Los fallos incluyen continuidad entre casos y discrepancias del contrato documental. No se declara aptitud para producción.

Bloqueo de activación: el flujo `Build verified release image` exige CI exitoso del SHA exacto. No se elimina esa condición ni se activa una candidata con regresiones funcionales pendientes. La autorización de despliegue está registrada; no se requiere una nueva confirmación para pasos rutinarios, pero deben resolverse los bloqueos técnicos.

Ver INFORME_CORRECCION_GENERAL_CONFIANZA_20261021.md para resultados, comandos y limitaciones. Los hashes canónicos y las expectativas permanecen intactos.
