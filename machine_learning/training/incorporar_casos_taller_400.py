"""Incorporación de los 400 casos de taller al dataset limpio de Machine Learning y reentrenamiento del modelo Linear SVM."""

from __future__ import annotations

import csv
import io
import os
from pathlib import Path
import pandas as pd
import joblib

# Mapeo exhaustivo de diagnósticos de taller hacia la taxonomía canónica de 48 clases
MAPA_DIAGNOSTICO_A_CANONICO = {
    # Inyección / Combustible
    "Inyectores con fuga": "Inyectores sucios o filtro de combustible obstruido",
    "Inyectores con fuga interna": "Inyectores sucios o filtro de combustible obstruido",
    "Inyectores goteando": "Inyectores sucios o filtro de combustible obstruido",
    "Inyectores goteando o sensor MAF": "Inyectores sucios o filtro de combustible obstruido",
    "Inyectores con fuga o MAF defectuoso": "Inyectores sucios o filtro de combustible obstruido",
    "Inyectores con fuga o sensor MAF": "Inyectores sucios o filtro de combustible obstruido",
    "Filtro de combustible tapado": "Inyectores sucios o filtro de combustible obstruido",
    "Filtro de combustible restringido": "Inyectores sucios o filtro de combustible obstruido",
    "Filtro de combustible muy tapado": "Inyectores sucios o filtro de combustible obstruido",
    "Filtro de combustible muy obstruido": "Inyectores sucios o filtro de combustible obstruido",
    "Filtro de combustible tapado o bomba débil": "Inyectores sucios o filtro de combustible obstruido",
    "Filtro de combustible o bomba débil": "Inyectores sucios o filtro de combustible obstruido",
    "Bomba de combustible débil": "Bomba de gasolina quemada o con baja presion",
    "Bomba de combustible fallando": "Bomba de gasolina quemada o con baja presion",
    "Bomba de combustible desgastada": "Bomba de gasolina quemada o con baja presion",
    "Bomba de combustible ruidosa (desgastada)": "Bomba de gasolina quemada o con baja presion",
    "Bomba de combustible o filtro tapado": "Bomba de gasolina quemada o con baja presion",
    "Bomba de combustible intermitente": "Bomba de gasolina quemada o con baja presion",
    "Regulador de presión de combustible": "Falla en sensor de oxigeno o mezcla rica",
    "Regulador de presión de combustible defectuoso": "Falla en sensor de oxigeno o mezcla rica",
    "Fuga en línea de combustible o regulador": "Falla en sensor de oxigeno o mezcla rica",
    "Fuga en líneas de combustible o regulador": "Falla en sensor de oxigeno o mezcla rica",
    "Cánister de vapores saturado o válvula de purga": "Falla en sensor de oxigeno o mezcla rica",
    "Cánister de carbón saturado o válvula PCV": "Falla en sensor de oxigeno o mezcla rica",
    "Cánister saturado o válvula de purga": "Falla en sensor de oxigeno o mezcla rica",

    # Encendido / Bobinas / Misfire
    "Bobinas de encendido": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobinas de encendido degradadas por calor": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobinas de encendido con fuga de corriente": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina de encendido (cilindro específico)": "Falla en bujias o bobinas de encendido (misfire)",
    "Bujías gastadas o incorrectas": "Falla en bujias o bobinas de encendido (misfire)",
    "Cables de bujía en mal estado": "Falla en bujias o bobinas de encendido (misfire)",
    "Cables de bujía deteriorados": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobinas de encendido en mal estado": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobinas o cables de bujía con fuga de corriente": "Falla en bujias o bobinas de encendido (misfire)",
    "Bujía o bobina de un cilindro": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina de encendido intermitente": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina o bujía del cilindro indicado": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobinas de encendido con grietas": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobinas o bujías en mal estado": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina de encendido que falla en caliente": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina o bujía del cilindro afectado": "Falla en bujias o bobinas de encendido (misfire)",
    "Varias bobinas de encendido fallando": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobinas o cables con fuga de alta tensión": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina que falla solo en caliente": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina + bujía del cilindro afectado": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobinas de encendido que fallan en caliente": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobinas con fuga de corriente": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina que falla en caliente": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina + bujía del cilindro": "Falla en bujias o bobinas de encendido (misfire)",
    "Bujías o bobinas en mal estado": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina intermitente": "Falla en bujias o bobinas de encendido (misfire)",
    "Módulo de encendido o bobina única": "Falla en bujias o bobinas de encendido (misfire)",
    "Bujías de grado térmico incorrecto": "Falla en bujias o bobinas de encendido (misfire)",
    "Bujías con grado térmico incorrecto": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobinas de encendido que fallan por temperatura": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina de encendido sensible a la temperatura": "Falla en bujias o bobinas de encendido (misfire)",
    "Sensor de posición del cigüeñal (CKP)": "Falla en bujias o bobinas de encendido (misfire)",
    "Sensor CKP o CMP defectuoso": "Falla en bujias o bobinas de encendido (misfire)",
    "Sensor de cigüeñal (CKP) o árbol de levas": "Falla en bujias o bobinas de encendido (misfire)",
    "Sensor CKP o CMP": "Falla en bujias o bobinas de encendido (misfire)",
    "Sensor de árbol de levas (CMP)": "Falla en bujias o bobinas de encendido (misfire)",

    # Soportes / Motor Ralentí
    "Soportes de motor rotos": "Amortiguadores reventados o bujes de suspension gastados",

    # Embrague y Transmisión
    "Rodamiento de embrague (thrust bearing)": "Falla en bombin o bomba hidraulica de embrague",
    "Rodamiento de empuje del embrague": "Falla en bombin o bomba hidraulica de embrague",
    "Rodamiento de embrague o problema en caja": "Falla en bombin o bomba hidraulica de embrague",
    "Rodamiento de embrague o caja": "Falla en bombin o bomba hidraulica de embrague",
    "Disco de embrague gastado": "Disco de embrague desgastado o patinando",
    "Disco de embrague al final de su vida": "Disco de embrague desgastado o patinando",
    "Disco de embrague al final de vida": "Disco de embrague desgastado o patinando",
    "Disco de embrague al final de su vida útil": "Disco de embrague desgastado o patinando",
    "Disco de embrague deformado o volante motor": "Disco de embrague desgastado o patinando",
    "Disco de embrague o volante motor": "Disco de embrague desgastado o patinando",
    "Sincronizadores gastados": "Falta o degradacion de aceite de caja de cambios",
    "Fluido de transmisión bajo o embrague desajustado": "Falta o degradacion de aceite de caja de cambios",
    "Fluido de transmisión degradado o bajo": "Falta o degradacion de aceite de caja de cambios",
    "Fluido de transmisión inadecuado o degradado": "Falta o degradacion de aceite de caja de cambios",
    "Fluido de transmisión degradado": "Falta o degradacion de aceite de caja de cambios",
    "Fluido de transmisión degradado o incorrecto": "Falta o degradacion de aceite de caja de cambios",

    # Sensores / Ralentí / IAC / TPS / MAF / O2
    "Sensor MAF sucio o fallando": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor MAF dando señal incorrecta": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor MAF sucio": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor MAF contaminado": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor MAP o MAF defectuoso": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor de oxígeno fallando": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor de oxígeno (O2) aguas arriba": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor O2 o MAF defectuoso": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor de oxígeno o MAF defectuoso": "Falla en sensor de oxigeno o mezcla rica",
    "Catalizador tapado": "Falla en sensor de oxigeno o mezcla rica",
    "Catalizador dañado": "Falla en sensor de oxigeno o mezcla rica",
    "Catalizador obstruido o dañado": "Falla en sensor de oxigeno o mezcla rica",
    "Catalizador deteriorado": "Falla en sensor de oxigeno o mezcla rica",
    "Catalizador o sensores de oxígeno": "Falla en sensor de oxigeno o mezcla rica",
    "Válvula IAC sucia o fallando": "Cuerpo de aceleracion o valvula IAC sucia",
    "Válvula IAC o cuerpo de aceleración sucio": "Cuerpo de aceleracion o valvula IAC sucia",
    "Cuerpo de aceleración sucio": "Cuerpo de aceleracion o valvula IAC sucia",
    "Cuerpo de aceleración sucio + sensor TPS": "Cuerpo de aceleracion o valvula IAC sucia",
    "Cuerpo de aceleración sucio + IAC": "Cuerpo de aceleracion o valvula IAC sucia",
    "Cuerpo de aceleración sucio + válvula IAC": "Cuerpo de aceleracion o valvula IAC sucia",
    "Sensor TPS descalibrado o fallando": "Cuerpo de aceleracion o valvula IAC sucia",
    "Sensor de posición del acelerador (TPS)": "Cuerpo de aceleracion o valvula IAC sucia",
    "Sensor TPS defectuoso": "Cuerpo de aceleracion o valvula IAC sucia",
    "Sensor TPS defectuoso o descalibrado": "Cuerpo de aceleracion o valvula IAC sucia",
    "Sensor TPS o cuerpo de aceleración": "Cuerpo de aceleracion o valvula IAC sucia",
    "Sensor TPS o cuerpo de aceleración sucio": "Cuerpo de aceleracion o valvula IAC sucia",

    # Dirección y Suspensión
    "Bomba de dirección hidráulica": "Cremallera de direccion asistida con holgura o fuga",
    "Bomba de dirección o bajo nivel de líquido": "Cremallera de direccion asistida con holgura o fuga",
    "Bomba de dirección hidráulica débil": "Cremallera de direccion asistida con holgura o fuga",
    "Terminales de dirección o bujes de suspensión": "Amortiguadores reventados o bujes de suspension gastados",
    "Bujes de horquilla o terminales de dirección": "Amortiguadores reventados o bujes de suspension gastados",
    "Terminales de dirección gastados": "Amortiguadores reventados o bujes de suspension gastados",
    "Terminales de dirección o brazos de dirección gastados": "Amortiguadores reventados o bujes de suspension gastados",
    "Terminales o brazos de dirección gastados": "Amortiguadores reventados o bujes de suspension gastados",
    "Bujes de suspensión o terminales": "Amortiguadores reventados o bujes de suspension gastados",
    "Junta homocinética (CV joint) dañada": "Juntas homocineticas o palieres danados",
    "Junta homocinética dañada": "Juntas homocineticas o palieres danados",
    "Junta homocinética (CV joint) externa": "Juntas homocineticas o palieres danados",
    "Junta homocinética externa": "Juntas homocineticas o palieres danados",
    "Junta homocinética (CV joint)": "Juntas homocineticas o palieres danados",

    # Distribución y Mecánica Motor
    "Tensor o cadena de distribución estirada": "Faja o cadena de distribucion destensada o con salto de punto",
    "Tensor de cadena de distribución": "Faja o cadena de distribucion destensada o con salto de punto",
    "Tensor hidráulico de cadena de distribución": "Faja o cadena de distribucion destensada o con salto de punto",
    "Tensor hidráulico de cadena débil": "Faja o cadena de distribucion destensada o con salto de punto",
    "Tensor hidráulico de cadena": "Faja o cadena de distribucion destensada o con salto de punto",
    "Tensor de cadena de distribución débil": "Faja o cadena de distribucion destensada o con salto de punto",
    "Tensor de cadena de distribución hidráulico": "Faja o cadena de distribucion destensada o con salto de punto",
    "Tensor de cadena o cadena estirada": "Faja o cadena de distribucion destensada o con salto de punto",
    "Tensor de cadena o cadena elongada": "Faja o cadena de distribucion destensada o con salto de punto",
    "Correa de accesorios floja o gastada": "Faja o cadena de distribucion destensada o con salto de punto",
    "Tensor de correa de distribución o accesorios": "Faja o cadena de distribucion destensada o con salto de punto",
    "Correa de accesorios o tensor": "Faja o cadena de distribucion destensada o con salto de punto",
    "Correa de accesorios o tensor gastado": "Faja o cadena de distribucion destensada o con salto de punto",

    # Batería y Alternador
    "Batería descargada o en mal estado": "Bateria descargada o bornes sulfatados",
    "Batería con poca carga o celdas malas": "Bateria descargada o bornes sulfatados",
    "Batería totalmente descargada o fusible principal": "Bateria descargada o bornes sulfatados",
    "Batería agotada o terminales sueltos/sucios": "Bateria descargada o bornes sulfatados",
    "Batería descargada o terminales sueltos": "Bateria descargada o bornes sulfatados",
    "Batería agotada o terminales": "Bateria descargada o bornes sulfatados",
    "Alternador defectuoso": "Alternador defectuoso o placa de diodos quemada",
    "Alternador no carga correctamente": "Alternador defectuoso o placa de diodos quemada",
    "Alternador no genera suficiente": "Alternador defectuoso o placa de diodos quemada",
    "Alternador o regulador de voltaje": "Alternador defectuoso o placa de diodos quemada",
    "Mala masa o conexión a tierra": "Bateria descargada o bornes sulfatados",
    "Mala conexión en alternador o regulador de voltaje": "Alternador defectuoso o placa de diodos quemada",
    "Mala masa o conexión suelta en el alternador": "Alternador defectuoso o placa de diodos quemada",
    "Mala conexión de masa o alternador irregular": "Alternador defectuoso o placa de diodos quemada",
    "Mala masa o alternador irregular": "Alternador defectuoso o placa de diodos quemada",
    "Mala conexión de masa o alternador": "Alternador defectuoso o placa de diodos quemada",
    "Cortocircuito en el cableado": "Falla electrica del cierre centralizado o actuador de puerta",
    "Cableado rozando o con aislamiento dañado": "Falla electrica del cierre centralizado o actuador de puerta",
    "Cableado con aislamiento dañado o rozando": "Falla electrica del cierre centralizado o actuador de puerta",

    # Motor de Arranque
    "Motor de arranque defectuoso": "Bateria descargada o bornes sulfatados",
    "Solenoide de arranque defectuoso": "Bateria descargada o bornes sulfatados",
    "Motor de arranque desgastado (carbones)": "Bateria descargada o bornes sulfatados",
    "Motor de arranque con carbones gastados": "Bateria descargada o bornes sulfatados",
    "Solenoide o motor de arranque": "Bateria descargada o bornes sulfatados",
    "Motor de arranque o solenoide": "Bateria descargada o bornes sulfatados",
    "Motor de arranque desgastado": "Bateria descargada o bornes sulfatados",
    "Solenoide de arranque intermitente": "Bateria descargada o bornes sulfatados",

    # Frenos
    "Discos de freno alabeados": "Discos de freno alabeados o desgastados",
    "Discos de freno alabeados (delanteros)": "Discos de freno alabeados o desgastados",
    "Discos traseros alabeados": "Discos de freno alabeados o desgastados",
    "Discos delanteros alabeados": "Discos de freno alabeados o desgastados",
    "Discos de freno delanteros alabeados": "Discos de freno alabeados o desgastados",
    "Pastillas de freno gastadas": "Desgaste de pastillas y zapatas de freno",
    "Pastillas de freno gastadas (indicador de desgaste)": "Desgaste de pastillas y zapatas de freno",
    "Pastillas de freno gastadas (sensor de desgaste)": "Desgaste de pastillas y zapatas de freno",
    "Pastillas de freno al límite": "Desgaste de pastillas y zapatas de freno",
    "Pastillas de freno al límite de desgaste": "Desgaste de pastillas y zapatas de freno",
    "Pastillas completamente gastadas": "Desgaste de pastillas y zapatas de freno",
    "Pastillas muy gastadas (líquido baja)": "Desgaste de pastillas y zapatas de freno",
    "Pastillas muy gastadas (el líquido baja al compensar)": "Desgaste de pastillas y zapatas de freno",
    "Pastillas o discos de freno desgastados de forma irregular": "Desgaste de pastillas y zapatas de freno",
    "Pinza de freno pegada o pastillas irregulares": "Fuga hidraulica o aire en el sistema de frenos",
    "Pinza pegada o desgaste irregular": "Fuga hidraulica o aire en el sistema de frenos",
    "Aire en el sistema de frenos o fuga": "Fuga hidraulica o aire en el sistema de frenos",
    "Aire en las líneas de freno": "Fuga hidraulica o aire en el sistema de frenos",
    "Cilindro maestro con fuga interna": "Fuga hidraulica o aire en el sistema de frenos",
    "Fuga interna en cilindro maestro": "Fuga hidraulica o aire en el sistema de frenos",
    "Servofreno (booster) defectuoso": "Falla en servofreno (booster) o linea de vacio",
    "Sensor de ABS o anillo tono": "Falla en sensor de velocidad de rueda ABS",
    "Sensor de ABS o anillo de tono": "Falla en sensor de velocidad de rueda ABS",
    "Cable de freno de mano flojo o pastillas traseras": "Desgaste de pastillas y zapatas de freno",
    "Cable de freno de mano estirado o pastillas traseras": "Desgaste de pastillas y zapatas de freno",

    # Enfriamiento y Culata
    "Empaque de cabeza (junta de culata)": "Empaque de culata soplado o danado",
    "Empaque de cabeza quemado": "Empaque de culata soplado o danado",
    "Junta de culata quemada": "Empaque de culata soplado o danado",
    "Junta de culata (empaque de cabeza)": "Empaque de culata soplado o danado",
    "Junta de culata": "Empaque de culata soplado o danado",
    "Termostato pegado abierto": "Falla en termostato o motoventilador de radiador",
    "Termostato atorado en posición abierta": "Falla en termostato o motoventilador de radiador",
    "Termostato abierto permanentemente": "Falla en termostato o motoventilador de radiador",
    "Termostato atorado abierto": "Falla en termostato o motoventilador de radiador",
    "Termostato abierto": "Falla en termostato o motoventilador de radiador",
    "Termostato cerrado o bomba de agua fallando": "Falla en termostato o motoventilador de radiador",
    "Termostato cerrado o bomba de agua": "Falla en termostato o motoventilador de radiador",
    "Ventilador de radiador defectuoso": "Falla en termostato o motoventilador de radiador",
    "Ventilador de radiador no funciona": "Falla en termostato o motoventilador de radiador",
    "Clutch de ventilador o ventilador eléctrico defectuoso": "Falla en termostato o motoventilador de radiador",
    "Ventilador de radiador no funciona correctamente": "Falla en termostato o motoventilador de radiador",
    "Ventilador de radiador no activa": "Falla en termostato o motoventilador de radiador",
    "Sensor ECT (temperatura de refrigerante)": "Falla en termostato o motoventilador de radiador",
    "Sensor de temperatura del refrigerante (ECT)": "Falla en termostato o motoventilador de radiador",
    "Sensor ECT defectuoso": "Falla en termostato o motoventilador de radiador",
    "Sensor ECT o relé del ventilador": "Falla en termostato o motoventilador de radiador",
    "Bomba de agua con fuga": "Fuga en mangueras de refrigerante o radiador picado",
    "Radiador con fuga o mangueras": "Fuga en mangueras de refrigerante o radiador picado",
    "Radiador con fuga o tapa de radiador": "Fuga en mangueras de refrigerante o radiador picado",
    "Radiador o tapa de radiador defectuosa": "Fuga en mangueras de refrigerante o radiador picado",
    "Radiador, tapa o mangueras": "Fuga en mangueras de refrigerante o radiador picado",
    "Tapa de radiador, radiador o empaque": "Fuga en mangueras de refrigerante o radiador picado",
    "Tapa de radiador defectuosa": "Fuga en mangueras de refrigerante o radiador picado",
    "Bomba de agua (rodamiento)": "Fuga en mangueras de refrigerante o radiador picado",
    "Bomba de agua (rodamiento dañado)": "Fuga en mangueras de refrigerante o radiador picado",

    # Ruedas / Neumáticos / Rodajes
    "Llantas desbalanceadas": "Llantas desbalanceadas o desalineadas",
    "Llantas desbalanceadas o rin doblado": "Llantas desbalanceadas o desalineadas",
    "Llantas desbalanceadas o pesos perdidos": "Llantas desbalanceadas o desalineadas",
    "Balanceo de llantas necesario": "Llantas desbalanceadas o desalineadas",
    "Balanceo de llantas": "Llantas desbalanceadas o desalineadas",
    "Balanceo de llantas traseras": "Llantas desbalanceadas o desalineadas",
    "Balanceo dinámico de llantas traseras": "Llantas desbalanceadas o desalineadas",
    "Llantas con bulbo o rin doblado": "Llantas desbalanceadas o desalineadas",
    "Alineación desajustada": "Llantas desbalanceadas o desalineadas",
    "Alineación incorrecta": "Llantas desbalanceadas o desalineadas",
    "Alineación o presión de llantas irregular": "Llantas desbalanceadas o desalineadas",
    "Alineación desajustada o presión irregular de llantas": "Llantas desbalanceadas o desalineadas",
    "Llantas desbalanceadas o rin dañado": "Llantas desbalanceadas o desalineadas",
    "Rodamiento de rueda": "Rodajes de caja mecanica o diferencial gastados",
    "Rodamiento de rueda dañado": "Rodajes de caja mecanica o diferencial gastados",
    "Rodamiento de rueda o llanta defectuosa": "Rodajes de caja mecanica o diferencial gastados",
    "Rodamiento de rueda o llanta con daño interno": "Rodajes de caja mecanica o diferencial gastados",
    "Rodamiento de rueda en mal estado": "Rodajes de caja mecanica o diferencial gastados",

    # Aire Acondicionado
    "Falta de gas refrigerante": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Bajo nivel de gas refrigerante": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Condensador tapado o ventilador de A/C": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Bajo nivel de refrigerante o presostato": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Bajo nivel de gas o presostato": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Evaporador sucio o con hongos": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Evaporador con hongos o bacteria": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Evaporador contaminado": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Evaporador con hongos": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Evaporador contaminado con hongos": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Compresor del A/C no prende nunca": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Compresor del A/C no llega a embragar": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Falta de gas, presostato o clutch": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Falta de gas, clutch o presostato": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Bajo nivel de gas o condensador tapado": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Bajo nivel de gas o condensador obstruido": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Presostato, bajo nivel de gas o condensador": "Falla en compresor de aire acondicionado o fuga de gas R134a",

    # Aceite / Motor Interno / Taqués / Fugas
    "Anillos de pistón o guías de válvulas": "Consumo de aceite por desgaste de anillos o retenes",
    "Anillos de pistón desgastados": "Consumo de aceite por desgaste de anillos o retenes",
    "Sellos de válvulas o guías gastadas": "Consumo de aceite por desgaste de anillos o retenes",
    "Sellos de vástago de válvulas": "Consumo de aceite por desgaste de anillos o retenes",
    "Sellos de válvulas": "Consumo de aceite por desgaste de anillos o retenes",
    "Válvulas o anillos": "Consumo de aceite por desgaste de anillos o retenes",
    "Válvulas o anillos de pistón": "Consumo de aceite por desgaste de anillos o retenes",
    "Válvula PCV tapada o manguera": "Consumo de aceite por desgaste de anillos o retenes",
    "Válvula PCV tapada": "Consumo de aceite por desgaste de anillos o retenes",
    "Taqués (lifters) hidráulicos": "Baja presion de aceite o bomba de aceite defectuosa",
    "Taqués hidráulicos colapsados": "Baja presion de aceite o bomba de aceite defectuosa",
    "Taqués hidráulicos sucios o con poco aceite": "Baja presion de aceite o bomba de aceite defectuosa",
    "Taqués hidráulicos con suciedad o poco aceite": "Baja presion de aceite o bomba de aceite defectuosa",
    "Cojinetes de biela o cigüeñal (grave)": "Baja presion de aceite o bomba de aceite defectuosa",
    "Cojinetes de biela (muy grave)": "Baja presion de aceite o bomba de aceite defectuosa",
    "Cojinetes de bancada o biela": "Baja presion de aceite o bomba de aceite defectuosa",
    "Cojinetes de biela o bancada": "Baja presion de aceite o bomba de aceite defectuosa",
    "Cojinetes de biela": "Baja presion de aceite o bomba de aceite defectuosa",
    "Retén de cigüeñal o empaque de cárter": "Baja presion de aceite o bomba de aceite defectuosa",
    "Empaque de tapa de punterías": "Baja presion de aceite o bomba de aceite defectuosa",
    "Pistones o anillos (cascabeleo de motor)": "Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)",
    "Carbonilla en cámaras de combustión (cascabeleo)": "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)",
    "Carbonilla excesiva en cámaras + gasolina de bajo octanaje": "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)",
    "Carbonilla en cámaras de combustión": "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)",
    "Carbonilla excesiva en pistones": "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)",
    "Fuga de vacío en manguera o junta": "Cuerpo de aceleracion o valvula IAC sucia",
    "Fuga de vacío o admisión": "Cuerpo de aceleracion o valvula IAC sucia",
    "Fuga de vacío en mangueras o junta de admisión": "Cuerpo de aceleracion o valvula IAC sucia",
    "Fuga de vacío": "Cuerpo de aceleracion o valvula IAC sucia",
    "Fuga de vacío en admisión": "Cuerpo de aceleracion o valvula IAC sucia",
    "Fuga en escape o catalizador roto": "Falla en sensor de oxigeno o mezcla rica",
    "Fuga en el sistema de escape": "Falla en sensor de oxigeno o mezcla rica",

    # Variantes adicionales detectadas en los 400 casos
    "Cuerpo de aceleración sucio o sensor TPS": "Cuerpo de aceleracion o valvula IAC sucia",
    "Bomba de dirección hidráulica débil o bajo nivel de líquido": "Cremallera de direccion asistida con holgura o fuga",
    "Discos de freno traseros alabeados": "Discos de freno alabeados o desgastados",
    "Guías de válvulas o sellos de vástago": "Consumo de aceite por desgaste de anillos o retenes",
    "Sensor MAF sucio o descalibrado": "Falla en sensor de oxigeno o mezcla rica",
    "Batería descargada o conexión de terminales": "Bateria descargada o bornes sulfatados",
    "Sensor TPS (posición del acelerador)": "Cuerpo de aceleracion o valvula IAC sucia",
    "Conexión de masa floja o alternador irregular": "Alternador defectuoso o placa de diodos quemada",
    "Sensor MAF sucio o contaminado": "Falla en sensor de oxigeno o mezcla rica",
    "Pinza de freno pegada o desgaste irregular": "Desgaste de pastillas y zapatas de freno",
    "Sensor ECT (temperatura refrigerante)": "Falla en termostato o motoventilador de radiador",
    "Tensor o cadena estirada": "Faja o cadena de distribucion destensada o con salto de punto",
    "Bomba de dirección débil": "Cremallera de direccion asistida con holgura o fuga",
    "Fuga de vacío o sensor MAF": "Cuerpo de aceleracion o valvula IAC sucia",
    "Alternador o mala conexión de batería": "Alternador defectuoso o placa de diodos quemada",
}


def procesar_e_incorporar_casos(texto_csv: str, ruta_dataset_limpio: Path):
    """Parsea el CSV de casos, mapea a las 48 clases canónicas e incorpora al dataset."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
    from src.core.taxonomy.catalogo_fallas import CATALOGO_TAXONOMIA

    # Mapear falla_principal a metadatos de taxonomía
    meta_taxonomia = {}
    for f in CATALOGO_TAXONOMIA.values():
        meta_taxonomia[f.falla_principal] = {
            "codigo_falla": f.codigo,
            "sistema": f.sistema,
            "severidad": f.severidad,
        }

    reader = csv.DictReader(io.StringIO(texto_csv.strip()))
    filas_nuevas = []
    sin_mapeo = set()

    for row in reader:
        sintoma_raw = (row.get("sintomas") or "").strip()
        diag_raw = (row.get("diagnostico_principal") or "").strip()
        tags_raw = (row.get("etiquetas") or "").strip()

        if not sintoma_raw or not diag_raw:
            continue

        falla_canonica = MAPA_DIAGNOSTICO_A_CANONICO.get(diag_raw)
        if not falla_canonica:
            sin_mapeo.add(diag_raw)
            continue

        meta = meta_taxonomia.get(falla_canonica, {
            "codigo_falla": "GEN_001",
            "sistema": "General",
            "severidad": "media",
        })

        # Variante 1: Síntoma natural directo
        filas_nuevas.append({
            "sintoma": sintoma_raw,
            "falla": falla_canonica,
            "codigo_falla": meta["codigo_falla"],
            "sistema": meta["sistema"],
            "severidad": meta["severidad"],
        })

        # Variante 2: Síntoma enriquecido con etiquetas técnicas si aportan contexto
        if tags_raw:
            tags_limpios = " ".join(tags_raw.replace("_", " ").split(","))
            sintoma_enriquecido = f"{sintoma_raw} {tags_limpios}".strip()
            filas_nuevas.append({
                "sintoma": sintoma_enriquecido,
                "falla": falla_canonica,
                "codigo_falla": meta["codigo_falla"],
                "sistema": meta["sistema"],
                "severidad": meta["severidad"],
            })

        # Decisión técnica validada por el usuario (Opción 1 y 2):
        # Para "Soportes de motor rotos", incorporar también la variante de inestabilidad de ralentí
        if diag_raw == "Soportes de motor rotos":
            falla_alt = "Cuerpo de aceleracion o valvula IAC sucia"
            meta_alt = meta_taxonomia.get(falla_alt, meta)
            filas_nuevas.append({
                "sintoma": sintoma_raw,
                "falla": falla_alt,
                "codigo_falla": meta_alt["codigo_falla"],
                "sistema": meta_alt["sistema"],
                "severidad": meta_alt["severidad"],
            })
            if tags_raw:
                filas_nuevas.append({
                    "sintoma": sintoma_enriquecido,
                    "falla": falla_alt,
                    "codigo_falla": meta_alt["codigo_falla"],
                    "sistema": meta_alt["sistema"],
                    "severidad": meta_alt["severidad"],
                })

    if sin_mapeo:
        print(f"ADVERTENCIA: Diagnósticos sin mapear ({len(sin_mapeo)}): {sin_mapeo}")

    print(f"Casos procesados listos para agregar: {len(filas_nuevas)}")

    # Cargar dataset existente
    df_existente = pd.read_csv(ruta_dataset_limpio, encoding="utf-8")
    print(f"Dataset actual: {len(df_existente)} filas.")

    df_nuevos = pd.DataFrame(filas_nuevas)
    df_combinado = pd.concat([df_existente, df_nuevos], ignore_index=True)

    # Limpieza: normalizar espacios, eliminar duplicados exactos de 'sintoma'
    df_combinado["sintoma"] = df_combinado["sintoma"].str.strip()
    df_combinado = df_combinado.drop_duplicates(subset=["sintoma"], keep="first")
    df_combinado = df_combinado.dropna(subset=["sintoma", "falla"])

    print(f"Dataset resultante tras deduplicación: {len(df_combinado)} filas.")
    print(f"Clases únicas: {df_combinado['falla'].nunique()} (deben ser 48).")

    df_combinado.to_csv(ruta_dataset_limpio, index=False, encoding="utf-8")
    print(f"¡Dataset guardado exitosamente en: {ruta_dataset_limpio}!")


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parents[2]
    ruta_raw = raiz / "machine_learning" / "data" / "casos_taller_400_raw.csv"
    ruta_limpio = raiz / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"

    with open(ruta_raw, "r", encoding="utf-8") as f:
        texto_csv = f.read()

    procesar_e_incorporar_casos(texto_csv, ruta_limpio)
