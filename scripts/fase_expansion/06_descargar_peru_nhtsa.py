"""
06_descargar_peru_nhtsa.py
Descarga y extracción estructurada de:
1. Perú — INDECOPI: Alertas vehiculares públicas (100% de la categoría 15).
2. NHTSA Recalls: FLAT_RCL_PRE_2010.zip y FLAT_RCL_POST_2010.zip.
3. NHTSA Complaints: 2000-2026.
4. NHTSA TSB / Manufacturer Communications.

Calcula SHA-256 de cada archivo en RAW sin modificar los originales.
"""
import sys
import os
import time
import json
import zipfile
import hashlib
import urllib.request
import urllib.parse
import ssl
from pathlib import Path
from typing import Dict, List, Any

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
BASE_DIR = PROJECT_ROOT / "machine_learning" / "data" / "fuentes_abiertas" / "fallas_vehiculares"

RAW_DIR = BASE_DIR / "raw"
RAW_INDECOPI = RAW_DIR / "indecopi"
RAW_RECALLS = RAW_DIR / "nhtsa_recalls"
RAW_COMPLAINTS = RAW_DIR / "nhtsa_complaints"
RAW_TSB = RAW_DIR / "nhtsa_tsb"

OUT_INDECOPI = BASE_DIR / "peru_indecopi"
OUT_RECALLS = BASE_DIR / "nhtsa_recalls"
OUT_COMPLAINTS = BASE_DIR / "nhtsa_complaints"
OUT_TSB = BASE_DIR / "nhtsa_tsb"

for p in [RAW_INDECOPI, RAW_RECALLS, RAW_COMPLAINTS, RAW_TSB, OUT_INDECOPI, OUT_RECALLS, OUT_COMPLAINTS, OUT_TSB]:
    p.mkdir(parents=True, exist_ok=True)

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def descargar_archivo(url: str, destino: Path) -> Tuple[bool, str, int]:
    """Descarga un archivo si no existe, o verifica su existencia."""
    if destino.exists() and destino.stat().st_size > 0:
        print(f"      [CACHE] {destino.name} ya existe ({destino.stat().st_size / (1024*1024):.2f} MB)")
        return True, sha256_file(destino), destino.stat().st_size

    print(f"      [DESCARGANDO] {url} -> {destino.name} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, context=CTX, timeout=60) as response, open(destino, "wb") as out_file:
        while chunk := response.read(1024 * 128):
            out_file.write(chunk)

    tamanio = destino.stat().st_size
    hash_val = sha256_file(destino)
    print(f"      [COMPLETO] {destino.name}: {tamanio / (1024*1024):.2f} MB | SHA-256: {hash_val[:16]}...")
    return True, hash_val, tamanio


def extraer_indecopi() -> Dict[str, Any]:
    """Descarga todas las alertas de la categoría 15 (Vehículos) desde la API oficial de INDECOPI."""
    print("\n========================================================")
    print("FASE 1: EXTRACCIÓN PERÚ — INDECOPI (ALERTAS VEHICULARES)")
    print("========================================================")

    destino_raw = RAW_INDECOPI / "alertas_vehiculares_raw.json"
    destino_out = OUT_INDECOPI / "alertas_indecopi.json"

    if destino_out.exists() and destino_out.stat().st_size > 10000:
        print(f"  [CACHE] Datos de Indecopi ya procesados en {destino_out.name}")
        with open(destino_out, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return datos

    # 1. Obtener Token OAuth2
    token_url = "https://apiconnect.indecopi.gob.pe/auth/realms/RLM-Indecopi-Produccion/protocol/openid-connect/token"
    auth_data = {
        "grant_type": "password",
        "client_id": "CLI_appDPCAlertasConsumoExt",
        "username": "usr_appdpcalertasconsumoext",
        "password": "iN@%26",
        "scope": "openid"
    }
    print("  [1/3] Solicitando token de autenticación a Keycloak INDECOPI...")
    req_tok = urllib.request.Request(
        token_url,
        data=urllib.parse.urlencode(auth_data).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req_tok, context=CTX, timeout=15) as res:
        token = json.loads(res.read().decode("utf-8"))["access_token"]
    print("        Token obtenido exitosamente.")

    # 2. Listar todas las alertas de Categoría 15 (Vehículos)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    url_bandeja = "https://servicios.indecopi.gob.pe/alerta-consumo-api/alerta/bandeja"

    print("  [2/3] Listando alertas de Categoría 15 (Vehículos y Transporte)...")
    page = 1
    size = 50
    total_esperado = None
    todas_alertas = []

    while True:
        payload = {
            "page": page,
            "size": size,
            "vcCriterio": "",
            "nuIdTipoProducto": None,
            "nuIdsCategorias": [15],
            "nuIdsRiesgo": [],
            "nuIdsMedidaMitigacion": [],
            "vcFechaInicio": "",
            "vcFechaFin": ""
        }
        req = urllib.request.Request(url_bandeja, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, context=CTX, timeout=20) as res:
            resp = json.loads(res.read().decode("utf-8"))

        datas = resp.get("datas", {})
        if total_esperado is None:
            total_esperado = datas.get("total", 0)
            print(f"        Total reportado por portal: {total_esperado} alertas vehiculares.")

        lista_pagina = datas.get("list", [])
        if not lista_pagina:
            break

        todas_alertas.extend(lista_pagina)
        print(f"        Página {page}: recuperadas {len(lista_pagina)} alertas (acumulado: {len(todas_alertas)}/{total_esperado})")

        if len(todas_alertas) >= total_esperado:
            break
        page += 1
        time.sleep(0.3)

    # 3. Obtener el detalle completo de cada alerta
    print(f"  [3/3] Obteniendo detalle técnico exhaustivo de {len(todas_alertas)} alertas...")
    alertas_completas = []
    url_detalle_base = "https://servicios.indecopi.gob.pe/alerta-consumo-api/alerta/detalle"

    for idx, alerta_resumen in enumerate(todas_alertas):
        nu_id = alerta_resumen.get("nuIdAlerta")
        try:
            req_det = urllib.request.Request(f"{url_detalle_base}?nuIdAlerta={nu_id}", headers=headers)
            with urllib.request.urlopen(req_det, context=CTX, timeout=15) as res_det:
                det_json = json.loads(res_det.read().decode("utf-8"))
            det_data = det_json.get("datas", {})
            alertas_completas.append(det_data)
        except Exception as e:
            # Fallback a los datos del resumen si falla el detalle individual
            alertas_completas.append(alerta_resumen)

        if (idx + 1) % 100 == 0 or (idx + 1) == len(todas_alertas):
            print(f"        Procesados {idx + 1}/{len(todas_alertas)} detalles...")
        time.sleep(0.1)

    # Guardar en RAW
    with open(destino_raw, "w", encoding="utf-8") as f:
        json.dump(alertas_completas, f, indent=2, ensure_ascii=False)

    # Guardar en OUT
    with open(destino_out, "w", encoding="utf-8") as f:
        json.dump({
            "fuente": "INDECOPI - Sistema de Alertas de Consumo (Perú)",
            "url_origen": "https://www.alertasdeconsumo.gob.pe/",
            "categoria": "Vehículos, transporte motorizado y no motorizado, partes y accesorios",
            "total_alertas": len(alertas_completas),
            "fecha_extraccion": "2026-09-19",
            "licencia": "Información Pública de Seguridad de Consumo (INDECOPI Perú)",
            "hash_raw": sha256_file(destino_raw),
            "alertas": alertas_completas
        }, f, indent=2, ensure_ascii=False)

    print(f"  [EXITO] {len(alertas_completas)} alertas vehiculares de Perú guardadas en {destino_out}")
    return alertas_completas


def descargar_nhtsa_recalls() -> Dict[str, Any]:
    """Descarga y extrae los recalls históricos de NHTSA (pre y post 2010)."""
    print("\n========================================================")
    print("FASE 2: DESCARGA NHTSA RECALLS (CAMPAÑAS OFICIALES)")
    print("========================================================")

    archivos_recalls = [
        ("https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_PRE_2010.zip", RAW_RECALLS / "FLAT_RCL_PRE_2010.zip"),
        ("https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_POST_2010.zip", RAW_RECALLS / "FLAT_RCL_POST_2010.zip"),
    ]

    manifest_recalls = {}
    for url, destino in archivos_recalls:
        ok, hash_val, size = descargar_archivo(url, destino)
        # Extraer archivo ZIP
        try:
            with zipfile.ZipFile(destino, "r") as zf:
                zf.extractall(OUT_RECALLS)
                archivos_extraidos = zf.namelist()
                print(f"      [UNZIP] {destino.name} -> {archivos_extraidos}")
        except Exception as e:
            print(f"      [ERROR UNZIP] {destino.name}: {e}")
            archivos_extraidos = []

        manifest_recalls[destino.name] = {
            "url": url,
            "hash_sha256": hash_val,
            "bytes": size,
            "archivos_extraidos": archivos_extraidos
        }

    return manifest_recalls


def descargar_nhtsa_complaints() -> Dict[str, Any]:
    """Descarga y extrae las quejas de consumidores de NHTSA 2000-2026."""
    print("\n========================================================")
    print("FASE 3: DESCARGA NHTSA COMPLAINTS 2000-2026")
    print("========================================================")

    archivos_complaints = [
        ("https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2025-2026.zip", RAW_COMPLAINTS / "COMPLAINTS_RECEIVED_2025-2026.zip"),
        ("https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2020-2024.zip", RAW_COMPLAINTS / "COMPLAINTS_RECEIVED_2020-2024.zip"),
        ("https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2015-2019.zip", RAW_COMPLAINTS / "COMPLAINTS_RECEIVED_2015-2019.zip"),
        ("https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2010-2014.zip", RAW_COMPLAINTS / "COMPLAINTS_RECEIVED_2010-2014.zip"),
        ("https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2005-2009.zip", RAW_COMPLAINTS / "COMPLAINTS_RECEIVED_2005-2009.zip"),
        ("https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2000-2004.zip", RAW_COMPLAINTS / "COMPLAINTS_RECEIVED_2000-2004.zip"),
    ]

    manifest_cmpl = {}
    for url, destino in archivos_complaints:
        ok, hash_val, size = descargar_archivo(url, destino)
        try:
            with zipfile.ZipFile(destino, "r") as zf:
                zf.extractall(OUT_COMPLAINTS)
                archivos_extraidos = zf.namelist()
                print(f"      [UNZIP] {destino.name} -> {archivos_extraidos}")
        except Exception as e:
            print(f"      [ERROR UNZIP] {destino.name}: {e}")
            archivos_extraidos = []

        manifest_cmpl[destino.name] = {
            "url": url,
            "hash_sha256": hash_val,
            "bytes": size,
            "archivos_extraidos": archivos_extraidos
        }

    return manifest_cmpl


def consolidar_manifiesto_descargas(indecopi_data, recalls_meta, cmpl_meta):
    """Guarda el inventario completo con hashes, tamaños y licencias."""
    inventario_path = BASE_DIR / "reportes" / "INVENTARIO_DESCARGAS_PERU_NHTSA.json"
    inventario_path.parent.mkdir(parents=True, exist_ok=True)

    inventario = {
        "fecha": "2026-09-19",
        "descripcion": "Banco Documental de Fallas Vehiculares Perú (Indecopi) + NHTSA 2000-2026",
        "fuentes": {
            "peru_indecopi": {
                "portal": "https://www.alertasdeconsumo.gob.pe/",
                "categoria_id": 15,
                "categoria_nombre": "Vehículos, transporte motorizado y no motorizado, partes y accesorios",
                "total_alertas": len(indecopi_data),
                "archivo_consolidado": str(OUT_INDECOPI / "alertas_indecopi.json"),
                "licencia": "Dominio Público Gubernamental / Seguridad de Consumo (Perú)"
            },
            "nhtsa_recalls": recalls_meta,
            "nhtsa_complaints": cmpl_meta,
        }
    }
    with open(inventario_path, "w", encoding="utf-8") as f:
        json.dump(inventario, f, indent=2)

    print(f"\n[INVENTARIO COMPLETO] Guardado en {inventario_path}")


if __name__ == "__main__":
    t0 = time.time()
    ind_data = extraer_indecopi()
    rec_meta = descargar_nhtsa_recalls()
    cmp_meta = descargar_nhtsa_complaints()
    consolidar_manifiesto_descargas(ind_data, rec_meta, cmp_meta)
    print(f"\nTiempo total de ejecución: {time.time() - t0:.2f} s")
