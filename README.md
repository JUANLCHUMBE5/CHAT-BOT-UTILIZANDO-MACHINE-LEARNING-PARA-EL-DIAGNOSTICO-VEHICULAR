# 🚗 CarBot: chatbot con Machine Learning para el diagnóstico vehicular

[![Tesis](https://img.shields.io/badge/Proyecto-Tesis_2026-blue.svg)](docs/guia_defensa_tesis.md)
[![Machine Learning](https://img.shields.io/badge/IA-Machine_Learning-F7931E.svg)](machine_learning/models/metricas_modelo.json)
[![WhatsApp](https://img.shields.io/badge/Canal-WhatsApp-25D366.svg?logo=whatsapp&logoColor=white)](https://developers.facebook.com)

Proyecto de investigación orientado a mejorar el proceso inicial de diagnóstico
vehicular en talleres mecánicos de Carabayllo, Lima, mediante un chatbot que
combina Machine Learning, recuperación de información técnica y asistencia
conversacional.

## 🎯 ¿Qué busca CarBot?

CarBot busca apoyar al mecánico durante la recepción y evaluación preliminar de
un vehículo. El sistema organiza los síntomas comunicados por WhatsApp, solicita
los datos técnicos que falten y genera una hipótesis que debe ser comprobada por
el personal del taller.

Sus objetivos principales son:

- Mejorar la precisión de la identificación preliminar de fallas.
- Reducir el tiempo empleado en recopilar y organizar los síntomas.
- Evitar diagnósticos incompletos por falta de marca, modelo, año, motor u otros datos.
- Estandarizar el registro de consultas y diagnósticos del taller.
- Facilitar el seguimiento y la validación posterior por parte del administrador.
- Brindar orientación técnica basada en información recuperable y trazable.

## 🔧 Problema que aborda

En los talleres mecánicos, los síntomas suelen comunicarse mediante frases
coloquiales como “pierde fuerza”, “cascabelea” o “se prendió el chancho”. Estas
descripciones pueden ser ambiguas y provocar que se omitan datos importantes del
vehículo o que se realicen pruebas sin un orden definido.

CarBot transforma esas expresiones en información técnica estructurada y ayuda a
identificar qué datos todavía deben preguntarse antes de producir una orientación.

## 🤖 ¿Qué hace el chatbot?

1. Recibe la consulta mediante WhatsApp.
2. Distingue entre un cliente y un mecánico autorizado.
3. Interpreta síntomas y expresiones de jerga automotriz peruana.
4. Solicita marca, modelo, año, motor, combustible y otros datos cuando sean necesarios.
5. Clasifica la posible falla utilizando un modelo de Machine Learning.
6. Busca procedimientos relacionados en el corpus técnico del sistema.
7. Presenta hipótesis, nivel de confianza y comprobaciones seguras.
8. Registra el resultado para que el administrador lo revise desde el panel web.

## 👥 Usuarios del sistema

### Cliente

Puede consultar servicios, horarios, ubicación y solicitar acceso como mecánico.
No recibe funciones técnicas restringidas.

### Mecánico autorizado

Trabaja directamente desde WhatsApp. Puede realizar consultas técnicas y aportar
los datos del vehículo, pero no necesita ingresar al panel administrativo.

### Administrador del taller

Es el único usuario que administra el panel web. Revisa solicitudes, autoriza
mecánicos, consulta diagnósticos, valida resultados y supervisa el funcionamiento
del sistema.

## 🧠 Enfoque de inteligencia artificial

CarBot utiliza un enfoque híbrido:

- **Machine Learning:** clasifica la categoría de falla y calcula una confianza estimada.
- **RAG:** recupera información relacionada desde el corpus técnico disponible.
- **Asistencia conversacional:** organiza la respuesta en un lenguaje comprensible.
- **Validación humana:** el mecánico confirma o descarta la hipótesis mediante pruebas físicas.

La respuesta del sistema es una orientación preliminar. No reemplaza la inspección,
el escáner automotriz, las mediciones ni el criterio profesional del mecánico.

## 📊 Aporte esperado

El proyecto evalúa la influencia del chatbot en tres dimensiones:

| Dimensión | Aporte buscado |
| --- | --- |
| Precisión | Mejorar la identificación preliminar de posibles fallas. |
| Completitud | Registrar síntomas y datos vehiculares de forma estructurada. |
| Eficiencia | Reducir el tiempo inicial de atención y clasificación. |

Las métricas del modelo y los resultados experimentales deben interpretarse dentro
del alcance de los datasets, pruebas controladas y validaciones documentadas del
proyecto; no representan certeza universal para todos los vehículos.

## 🛡️ Seguridad y responsabilidad

- Los diagnósticos requieren validación física antes de reparar o sustituir componentes.
- Las recomendaciones de seguridad tienen prioridad ante síntomas críticos.
- Los accesos técnicos se habilitan únicamente a números autorizados por el administrador.
- Los registros experimentales utilizan mecanismos de pseudonimización y trazabilidad.
- El sistema comunica cuando la información disponible es insuficiente.

## 🎓 Contexto académico

**Título:** Chatbot utilizando Machine Learning para el diagnóstico vehicular en
los talleres mecánicos de Carabayllo, 2026.

**Línea de investigación:** Inteligencia Artificial Aplicada, Procesamiento de
Lenguaje Natural y Sistemas de Información.

**Tesistas:**

- Juan Joel Leon Chumbe
- Luisa Leonor Poma Cataño

**Lugar y año:** Carabayllo, Lima, Perú — 2026.

La documentación académica, metodológica y técnica se encuentra organizada en el
[índice de documentación](docs/INDICE_DOCUMENTACION.md).
