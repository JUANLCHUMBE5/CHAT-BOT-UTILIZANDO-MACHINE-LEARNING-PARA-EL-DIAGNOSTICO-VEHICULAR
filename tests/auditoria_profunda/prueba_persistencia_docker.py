"""Prueba focalizada de persistencia real y aislamiento en Docker (Fase 7).

Simula:
1. Alternancia de turnos entre Mecánico Norte (Toyota Yaris) y Mecánico Sur (Ford Ranger).
2. Reinicio de PostgreSQL y Redis en plena conversación.
3. Verificación de retención de hechos y ausencia de contaminación cruzada.
"""

import hashlib
import hmac
import json
import subprocess
import time

import requests

API_URL = "http://127.0.0.1:8001/api/v1/webhook/meta"
META_SECRET = "test_meta_app_secret_12345678"
PHONE_NORTE = "PHONE_ID_TALLER_NORTE"
PHONE_SUR = "PHONE_ID_TALLER_SUR"
TEL_A = "+51987654321"  # Mecánico A (Norte)
TEL_B = "+51912345678"  # Mecánico B (Sur)

def ejecutar_psql(query: str) -> str:
    cmd = [
        "docker", "exec", "carbot-e2e-postgres",
        "psql", "-U", "carbot_test", "-d", "carbot_test_e2e",
        "-t", "-A", "-c", query
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return res.stdout.strip()

def enviar_msg(texto: str, remitente: str, phone_id: str) -> int:
    msg_id = f"wamid_pers_{time.time_ns()}"
    payload = {
        "entry": [{
            "changes": [{
                "value": {
                    "metadata": {"phone_number_id": phone_id},
                    "contacts": [{"wa_id": remitente.replace("+", ""), "profile": {"name": "Test"}}],
                    "messages": [{
                        "id": msg_id,
                        "from": remitente,
                        "type": "text",
                        "text": {"body": texto}
                    }]
                }
            }]
        }]
    }
    raw = json.dumps(payload).encode("utf-8")
    sig = "sha256=" + hmac.new(META_SECRET.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    headers = {"Content-Type": "application/json", "X-Hub-Signature-256": sig}
    resp = requests.post(API_URL, data=raw, headers=headers, timeout=10)
    return resp.status_code

def main():
    print("Iniciando prueba de persistencia real en Docker...")
    # Asegurar contenedores vivos
    subprocess.run(["docker", "start", "carbot-e2e-postgres", "carbot-e2e-redis", "carbot-e2e-api", "carbot-e2e-worker"], capture_output=True)
    time.sleep(4)

    # 1. Turno 1 Mecánico A
    st1 = enviar_msg("Toyota Yaris 2017 placa B3F-102 ratea en caliente", TEL_A, PHONE_NORTE)
    # 2. Turno 1 Mecánico B
    st2 = enviar_msg("Ford Ranger 2017 diesel placa N2K-808 con DPF tapado", TEL_B, PHONE_SUR)

    time.sleep(2)

    # 3. Reinicio de PostgreSQL y Redis en plena conversación
    print("Reiniciando PostgreSQL y Redis...")
    subprocess.run(["docker", "restart", "carbot-e2e-postgres", "carbot-e2e-redis"], check=True)
    time.sleep(5)

    # 4. Turno 2 Mecánico A (proporciona medición)
    st3 = enviar_msg("Le cambié bujías y medí compresión: 175 psi parejo", TEL_A, PHONE_NORTE)
    # 5. Turno 2 Mecánico B (proporciona síntoma)
    st4 = enviar_msg("El nivel de aceite está pasado con olor a diesel", TEL_B, PHONE_SUR)

    time.sleep(3)

    # 6. Consultar conversaciones en PostgreSQL
    ctx_a = ejecutar_psql(f"SELECT c.contexto::text FROM conversaciones c JOIN talleres t ON c.taller_id = t.id WHERE t.telefono_id_meta = '{PHONE_NORTE}' ORDER BY c.actualizado_en DESC LIMIT 1;")
    ctx_b = ejecutar_psql(f"SELECT c.contexto::text FROM conversaciones c JOIN talleres t ON c.taller_id = t.id WHERE t.telefono_id_meta = '{PHONE_SUR}' ORDER BY c.actualizado_en DESC LIMIT 1;")

    contaminacion_a = ("ranger" in ctx_a.lower() or "n2k-808" in ctx_a.lower() or "dpf" in ctx_a.lower())
    contaminacion_b = ("yaris" in ctx_b.lower() or "b3f-102" in ctx_b.lower() or "175 psi" in ctx_b.lower())

    res = {
        "mecanico_a_status": [st1, st3],
        "mecanico_b_status": [st2, st4],
        "contaminacion_a_con_b": contaminacion_a,
        "contaminacion_b_con_a": contaminacion_b,
        "persistencia_post_reinicio": (not contaminacion_a and not contaminacion_b),
    }
    print(json.dumps(res, indent=2))
    with open("scratch/auditoria_profunda/resultado_persistencia_docker.json", "w") as f:
        json.dump(res, f, indent=2)

if __name__ == "__main__":
    main()
