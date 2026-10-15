import re
from pathlib import Path

import pandas as pd

BASE_DIR = Path(r"c:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING\machine_learning\data")
LIMPIO_CSV = BASE_DIR / "dataset_sintomas_limpio.csv"
DATASET_CSV = BASE_DIR / "dataset_sintomas.csv"

# Casos altamente focalizados en la falla termica de sensores CKP/CMP, bobinas y bomba en caliente
casos_falla_termica = [
    # 1. Falla en bujias o bobinas de encendido (misfire) - Sensores CKP y encendido que calientan
    {
        "falla_patron": "bujias o bobinas",
        "sintomas": [
            "El carro arranca al primer llavazo en las mañanas pero apenas calienta en tráfico pesado se apaga de golpe, el motor gira con fuerza pero no enciende hasta que enfría 20 o 30 minutos",
            "Ruedo tranquilo media hora y de la nada se apaga en marcha como si le cortaran la corriente, intento dar arranque y el motor gira con fuerza pero no prende, prende al enfriar",
            "El auto se apaga de golpe en caliente tras media hora de uso, el motor de arranque gira vigoroso pero no hay chispa por sensor de cigüeñal CKP que dilata térmicamente",
            "Se apaga súbitamente en plena marcha en tráfico, el arrancador da vueltas con toda la fuerza pero no arranca, tengo que esperar media hora a que enfríe el motor",
            "Falla térmica de sensor CKP: arranca perfecto en frío, al calentar a 90 grados corta el encendido de golpe, da arranque rápido pero no prende hasta que baja la temperatura",
            "El vehículo se queda botado en caliente en el tráfico, el motor gira con ganas pero no hay pulso de inyección ni chispa, al cabo de 20 minutos frío enciende como si nada",
            "Corte repentino de corriente en marcha con motor caliente, el arrancador mueve el motor con fuerza pero no enciende, código DTC P0335 sensor de posición de cigüeñal",
            "Se apaga de la nada en caliente, espero 30 minutos que enfríe y arranca al toque, pero mientras esté caliente el motor gira con fuerza sin encender",
            "Bobina o captador de cigüeñal pierde la señal al dilatar por calor en tráfico pesado, motor da marcha con fuerza pero no hay combustión",
            "El motor se apaga rodando como si desconectaran la llave, el arrancador gira rápido y con fuerza pero no arranca hasta que reposa 25 minutos y enfría",
            "En frío prende al instante pero al calentar en marcha se apaga seco, da arranque con fuerza y no prende, sensor de posición de cigüeñal con bobina cortada en caliente",
            "Se apaga el motor en semáforo después de calentar, el motor gira con fuerza al darle arranque pero no arranca nada, a la media hora frío prende normal"
        ]
    },
    # 2. Bomba de gasolina quemada o con baja presion
    {
        "falla_patron": "Bomba de gasolina quemada",
        "sintomas": [
            "La bomba de gasolina se calienta y se traba en tráfico pesado, el motor se apaga en marcha, gira con fuerza el arranque pero no enciende hasta esperar 30 minutos",
            "Al calentar el motor se corta la gasolina y se apaga el auto, el motor de arranque gira con fuerza pero no hay presión en el riel hasta que enfría la bomba",
            "Pila de gasolina recalienta tras rodar 40 minutos y se apaga de golpe, da arranque con fuerza pero no prende hasta que reposa media hora",
            "El carro se apaga en caliente en plena avenida, el motor gira con vigor pero la bomba no zumba hasta que el tanque y el motor enfrían",
            "Bomba de combustible pierde presión por temperatura alta en tráfico, el motor da marcha con fuerza pero no enciende hasta que baja la temperatura"
        ]
    },
    # 3. Falla en modulo de bomba de gasolina FSCM / PEM (Ford / Chevrolet)
    {
        "falla_patron": "modulo de bomba de gasolina FSCM",
        "sintomas": [
            "El módulo FSCM de la bomba de gasolina recalienta en tráfico y corta el combustible, el motor gira con fuerza pero no prende hasta que enfría 20 minutos",
            "Módulo PEM bajo el chasis calienta en carretera y apaga el carro de golpe, da arranque con fuerza pero no inyecta hasta que se enfría",
            "Se apaga en marcha como si le cortaran la corriente, el motor gira vigoroso con el arrancador pero la bomba no recibe pulso hasta enfriar el módulo de combustible"
        ]
    }
]

def main():
    df_limpio = pd.read_csv(LIMPIO_CSV)
    clases_existentes = list(df_limpio["falla"].unique())
    print(f"Dataset limpio actual: {len(df_limpio)} filas.")

    textos_existentes = set(df_limpio["sintoma"].dropna().str.strip().str.lower())
    nuevas_filas = []

    for bloque in casos_falla_termica:
        patron = bloque["falla_patron"]
        clase_target = None
        for c in clases_existentes:
            if re.search(patron, c, re.IGNORECASE):
                clase_target = c
                break
        
        if not clase_target:
            print(f"[ALERTA] No se encontro clase para: {patron}")
            continue

        for s in bloque["sintomas"]:
            s_clean = s.strip()
            if s_clean.lower() not in textos_existentes:
                nuevas_filas.append({
                    "sintoma": s_clean,
                    "falla": clase_target,
                    "codigo_falla": "P0335",
                    "sistema": "Encendido / Inyeccion",
                    "severidad": "critica"
                })
                textos_existentes.add(s_clean.lower())

    print(f"Nuevas filas especializadas a agregar: {len(nuevas_filas)}")
    if nuevas_filas:
        df_nuevas = pd.DataFrame(nuevas_filas)
        df_act = pd.concat([df_limpio, df_nuevas], ignore_index=True)
        df_act.to_csv(LIMPIO_CSV, index=False)
        print(f"[EXITO] Guardado {LIMPIO_CSV}. Total filas: {len(df_act)}")

        if DATASET_CSV.exists():
            df_raw = pd.read_csv(DATASET_CSV)
            raw_textos = set(df_raw["sintoma"].dropna().str.strip().str.lower())
            filas_raw = [
                {"sintoma": nf["sintoma"], "falla": nf["falla"]}
                for nf in nuevas_filas if nf["sintoma"].lower() not in raw_textos
            ]
            if filas_raw:
                df_raw_act = pd.concat([df_raw, pd.DataFrame(filas_raw)], ignore_index=True)
                df_raw_act.to_csv(DATASET_CSV, index=False)
                print(f"[EXITO] Guardado {DATASET_CSV}. Total filas: {len(df_raw_act)}")

if __name__ == "__main__":
    main()
