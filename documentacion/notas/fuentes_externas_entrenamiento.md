# Fuentes externas para ampliar CarBot

## Fuente evaluada

- **Nombre:** Automotive Faults Dataset for Diagnostic and Maintenance Systems.
- **Autor:** Peter Obike; curaduría de Okure Obot.
- **Repositorio:** Zenodo.
- **DOI:** https://doi.org/10.5281/zenodo.15626055
- **Versión:** v1, publicada el 9 de junio de 2025.
- **Licencia:** Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Integridad del JSON:** MD5 `cb44431ef6b32f6ea9cf00dbe35f020c`.

## Regla de incorporación

La fuente no se incorpora automáticamente a `dataset_sintomas_limpio.csv`. Sus
registros están en inglés, contienen pocos síntomas por componente y no
representan por sí solos casos reales de talleres peruanos.

El proceso obligatorio es:

1. Verificar licencia, versión y checksum.
2. Proponer equivalencia con la taxonomía estable de CarBot.
3. Traducir el síntoma al español técnico/peruano sin cambiar su significado.
4. Validar cada ejemplo con un mecánico y registrar la evidencia.
5. Mantener los casos de evaluación externa completamente separados.
6. Reentrenar y aprobar métricas por clase, no solamente exactitud global.

## Datos OBD-II en cuarentena

Las 16,231 filas OBD-II existentes no son clases sin mapear. Incluyen etiquetas
genéricas y entradas defectuosas como `P0100: P0101`; no deben convertirse en
una falla mecánica específica. Los DTC deben resolverse mediante un catálogo o
motor de consulta separado y usarse como evidencia adicional, no como síntomas
masivos para el clasificador ML.

## Revisión regional LATAM

Se contrastó vocabulario usado en Perú, México, Colombia, Ecuador, Chile,
Argentina, Venezuela, Centroamérica y Caribe. El normalizador admite variantes
como `balata/pastilla`, `cloche/embrague`, `marcha/arrancador`,
`rulemán/rodamiento`, `mofle/silenciador` y `faja/correa`.

Fuentes de contraste:

- Diccionario de repuestos LATAM: https://usaautopartsexport.com/diccionario-de-repuestos/
- Lenguaje coloquial de autopartes: https://www.suplifai.com/blog/lenguaje-coloquial-autopartes/

Estas páginas se usan únicamente para contrastar equivalencias terminológicas;
no se copian sus textos como muestras de entrenamiento. Las equivalencias que
pueden cambiar de significado según el contexto quedan sin reemplazo automático.
Por ejemplo, `cardán`, `palier` y `semi-eje` no son intercambiables en todos los
vehículos.

## Fuente LATAM no compatible con el clasificador de texto

EngineFaultDB fue desarrollado con participación de la Universidad Politécnica
Salesiana de Ecuador y está publicado bajo GPL-3.0:
https://github.com/leoxthomas/EngineFaultDB. Contiene 55,999 mediciones de 14
variables de un motor C14NE, no descripciones textuales de mecánicos. Por ello se
documenta como posible fuente para un futuro modelo de sensores, pero no se
mezcla con el clasificador actual de síntomas de WhatsApp.

## Cobertura funcional buscada

La bandeja externa contempla frenos, climatización, refrigeración, transmisión,
arranque/carga, emisiones, motor, combustible, dirección, suspensión, ruedas y
carrocería. Las 196 frases están traducidas a español técnico peruano en
`data/candidatos_revision/zenodo_15626055_es_peru.csv`; siguen fuera del
entrenamiento hasta tener validación mecánica. Doce correspondencias de la
fuente fueron marcadas explícitamente como ambiguas.
