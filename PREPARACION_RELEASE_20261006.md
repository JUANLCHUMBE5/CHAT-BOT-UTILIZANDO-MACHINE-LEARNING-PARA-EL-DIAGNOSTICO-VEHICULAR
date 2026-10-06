# Preparación de release separado — todavía no desplegado

La rama parte del main de carbot-backend; se incorporaron únicamente fuentes y
regresiones revisadas, sin backups, .env, conversaciones de Alex ni datos operativos.
El checkout original permanece intacto salvo la mejora de ruta ML_ROOT y la
corrección de renovación de sesión en frontend.

Validación local en este checkout: 119 tests enfocados PASS, Ruff PASS.
No equivale a suite integral ni prueba de Meta/WhatsApp ni producción aprobada.

El workflow usa PostgreSQL carbot_test efímero y providers OFF. Necesita:

1. Secret CARBOT_ML_READ_TOKEN con lectura exclusiva del repositorio privado
   JUANLCHUMBE5/carbot-machine-learning. No usar tokens de producción ni pegarlo en chat.
2. Variable CARBOT_ML_SHA con SHA completo del commit ML validado, incluyendo
   el artefacto de ruteo. No apuntar a main mutable ni a una versión anterior sin ese archivo.
3. Configurar checks obligatorios de los tres PR y esperar finalización de todos.

No se crearon esos valores porque no hay una credencial de lectura de ML
designada para Actions. El workflow falla explícitamente si falta configuración.

docker-compose.gemini-only.yml es un override preparado, no ejecutado. Desactiva
Groq para texto y evita Alembic en el arranque de API; preserva el resto del
Compose. El flag de audio es separado: no asumir que este override desactiva
la transcripción Groq. Antes de deploy verificar servicio, imagen, mounts y
configuración reales en AWS; no sustituir .env ni recrear PostgreSQL/Redis.

ML_ROOT ahora se respeta también al cargar el router, necesario para los repos
separados. El deployment debe fijar las tres revisiones, verificar hashes de
artefactos y conservar un rollback; un push a estos main no acredita deploy automático.
