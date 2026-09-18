"""Incorporación de los 300 casos de taller al dataset limpio de Machine Learning y reentrenamiento del modelo Linear SVM."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import unicodedata
import pandas as pd
import joblib

# Mapeo exhaustivo de diagnósticos de taller hacia la taxonomía canónica de 48 clases
MAPA_DIAGNOSTICO_A_CANONICO_300 = {
    # Admision
    "Fuga de vacio o manguera rota": "Cuerpo de aceleracion o valvula IAC sucia",
    "Fuga de vacío o manguera rota": "Cuerpo de aceleracion o valvula IAC sucia",
    "Fuga en intercooler o mangueras de turbo": "Fuga en mangueras de intercooler o turbocompresor danado",
    "Turbo con fuga o actuador fallando": "Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI",

    # Clima
    "Clutch de compresor o falta de gas": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Clutch o falta de gas": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Bajo nivel de gas": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Bajo nivel de gas o condensador": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Condensador tapado o ventilador de A/C": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Evaporador con hongos": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    "Evaporador contaminado": "Falla en compresor de aire acondicionado o fuga de gas R134a",

    # Combustible
    "Bomba de combustible debil": "Bomba de gasolina quemada o con baja presion",
    "Bomba de combustible débil": "Bomba de gasolina quemada o con baja presion",
    "Bomba de combustible desgastada": "Bomba de gasolina quemada o con baja presion",
    "Bomba de combustible o filtro tapado": "Bomba de gasolina quemada o con baja presion",
    "Bomba de combustible ruidosa": "Bomba de gasolina quemada o con baja presion",
    "Bomba o filtro tapado": "Bomba de gasolina quemada o con baja presion",
    "Canister o valvula de purga": "Falla en sensor de oxigeno o mezcla rica",
    "Canister saturado o valvula de purga": "Falla en sensor de oxigeno o mezcla rica",
    "Cánister o válvula de purga": "Falla en sensor de oxigeno o mezcla rica",
    "Cánister saturado o válvula de purga": "Falla en sensor de oxigeno o mezcla rica",
    "Filtro de combustible muy obstruido": "Inyectores sucios o filtro de combustible obstruido",
    "Filtro de combustible restringido": "Inyectores sucios o filtro de combustible obstruido",
    "Filtro de combustible tapado": "Inyectores sucios o filtro de combustible obstruido",
    "Filtro muy obstruido": "Inyectores sucios o filtro de combustible obstruido",
    "Inyectores con fuga": "Inyectores sucios o filtro de combustible obstruido",
    "Inyectores con fuga o MAF": "Inyectores sucios o filtro de combustible obstruido",
    "Inyectores goteando o sensor de oxigeno": "Inyectores sucios o filtro de combustible obstruido",
    "Inyectores goteando o sensor de oxígeno": "Inyectores sucios o filtro de combustible obstruido",
    "Fuga en lineas o regulador": "Falla en sensor de oxigeno o mezcla rica",
    "Fuga en líneas o regulador": "Falla en sensor de oxigeno o mezcla rica",
    "Fuga en regulador o lineas": "Falla en sensor de oxigeno o mezcla rica",
    "Fuga en regulador o líneas": "Falla en sensor de oxigeno o mezcla rica",

    # Direccion
    "Alineacion desajustada": "Llantas desbalanceadas o desalineadas",
    "Alineación desajustada": "Llantas desbalanceadas o desalineadas",
    "Alineacion incorrecta": "Llantas desbalanceadas o desalineadas",
    "Alineación incorrecta": "Llantas desbalanceadas o desalineadas",
    "Alineacion o presion de llantas": "Llantas desbalanceadas o desalineadas",
    "Alineación o presión de llantas": "Llantas desbalanceadas o desalineadas",
    "Bomba de direccion": "Cremallera de direccion asistida con holgura o fuga",
    "Bomba de dirección": "Cremallera de direccion asistida con holgura o fuga",
    "Bomba de direccion debil": "Cremallera de direccion asistida con holgura o fuga",
    "Bomba de dirección débil": "Cremallera de direccion asistida con holgura o fuga",
    "Bomba de direccion hidraulica": "Cremallera de direccion asistida con holgura o fuga",
    "Bomba de dirección hidráulica": "Cremallera de direccion asistida con holgura o fuga",
    "Caja de direccion o terminales": "Cremallera de direccion asistida con holgura o fuga",
    "Caja de dirección o terminales": "Cremallera de direccion asistida con holgura o fuga",
    "Falla en sistema de direccion electrica": "Cremallera de direccion asistida con holgura o fuga",
    "Falla en sistema de dirección eléctrica": "Cremallera de direccion asistida con holgura o fuga",
    "Terminales de direccion gastados": "Amortiguadores reventados o bujes de suspension gastados",
    "Terminales de dirección gastados": "Amortiguadores reventados o bujes de suspension gastados",
    "Terminales o brazos de direccion": "Amortiguadores reventados o bujes de suspension gastados",
    "Terminales o brazos de dirección": "Amortiguadores reventados o bujes de suspension gastados",

    # Electrico
    "Alternador defectuoso": "Alternador defectuoso o placa de diodos quemada",
    "Alternador no carga": "Alternador defectuoso o placa de diodos quemada",
    "Alternador o conexion de bateria": "Alternador defectuoso o placa de diodos quemada",
    "Alternador o conexión de batería": "Alternador defectuoso o placa de diodos quemada",
    "Alternador o mala conexion de bateria": "Alternador defectuoso o placa de diodos quemada",
    "Alternador o mala conexión de batería": "Alternador defectuoso o placa de diodos quemada",
    "Alternador o mala masa": "Alternador defectuoso o placa de diodos quemada",
    "Alternador o regulador": "Alternador defectuoso o placa de diodos quemada",
    "Alternador o regulador de voltaje": "Alternador defectuoso o placa de diodos quemada",
    "Bateria agotada o terminales": "Bateria descargada o bornes sulfatados",
    "Batería agotada o terminales": "Bateria descargada o bornes sulfatados",
    "Bateria agotada o terminales sueltos": "Bateria descargada o bornes sulfatados",
    "Batería agotada o terminales sueltos": "Bateria descargada o bornes sulfatados",
    "Bateria descargada": "Bateria descargada o bornes sulfatados",
    "Batería descargada": "Bateria descargada o bornes sulfatados",
    "Bateria descargada o terminales": "Bateria descargada o bornes sulfatados",
    "Batería descargada o terminales": "Bateria descargada o bornes sulfatados",
    "Bateria totalmente descargada": "Bateria descargada o bornes sulfatados",
    "Batería totalmente descargada": "Bateria descargada o bornes sulfatados",
    "Cableado con aislamiento dañado": "Falla electrica del cierre centralizado o actuador de puerta",
    "Cableado con aislamiento da\xc3\xb1ado": "Falla electrica del cierre centralizado o actuador de puerta",
    "Cableado dañado": "Falla electrica del cierre centralizado o actuador de puerta",
    "Cableado da\xc3\xb1ado": "Falla electrica del cierre centralizado o actuador de puerta",
    "Cortocircuito": "Falla electrica del cierre centralizado o actuador de puerta",
    "Cortocircuito en el cableado": "Falla electrica del cierre centralizado o actuador de puerta",
    "Cortocircuito o relé defectuoso": "Falla electrica del cierre centralizado o actuador de puerta",
    "Cortocircuito o rele defectuoso": "Falla electrica del cierre centralizado o actuador de puerta",
    "Mala conexion a tierra": "Bateria descargada o bornes sulfatados",
    "Mala conexión a tierra": "Bateria descargada o bornes sulfatados",
    "Mala conexion de masa": "Bateria descargada o bornes sulfatados",
    "Mala conexión de masa": "Bateria descargada o bornes sulfatados",
    "Mala masa o alternador irregular": "Alternador defectuoso o placa de diodos quemada",
    "Motor de arranque desgastado": "Bateria descargada o bornes sulfatados",
    "Solenoide de arranque": "Bateria descargada o bornes sulfatados",
    "Solenoide de arranque defectuoso": "Bateria descargada o bornes sulfatados",
    "Solenoide de arranque intermitente": "Bateria descargada o bornes sulfatados",
    "Solenoide intermitente": "Bateria descargada o bornes sulfatados",

    # Emisiones
    "Catalizador dañado": "Falla en sensor de oxigeno o mezcla rica",
    "Catalizador da\xc3\xb1ado": "Falla en sensor de oxigeno o mezcla rica",
    "Catalizador deteriorado": "Falla en sensor de oxigeno o mezcla rica",
    "Catalizador o sensores O2": "Falla en sensor de oxigeno o mezcla rica",
    "Catalizador o sensores de oxigeno": "Falla en sensor de oxigeno o mezcla rica",
    "Catalizador o sensores de oxígeno": "Falla en sensor de oxigeno o mezcla rica",
    "Catalizador obstruido": "Falla en sensor de oxigeno o mezcla rica",
    "Fuga en el sistema de escape": "Falla en sensor de oxigeno o mezcla rica",
    "Fuga en escape o catalizador roto": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor de oxigeno fallando": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor de oxígeno fallando": "Falla en sensor de oxigeno o mezcla rica",
    "Valvula EGR tapada o fallando": "Cuerpo de aceleracion o valvula IAC sucia",
    "Válvula EGR tapada o fallando": "Cuerpo de aceleracion o valvula IAC sucia",

    # Encendido
    "Bobina del cilindro afectado": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina intermitente": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina o bujia del cilindro afectado": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina o bujía del cilindro afectado": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina sensible a la temperatura": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina sensible a temperatura": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina y bujia del cilindro": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobina y bujía del cilindro": "Falla en bujias o bobinas de encendido (misfire)",
    "Fallo de cilindro especifico": "Falla en bujias o bobinas de encendido (misfire)",
    "Fallo de cilindro específico": "Falla en bujias o bobinas de encendido (misfire)",
    "Fallo de encendido": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobinas con fuga de alta tension": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobinas con fuga de alta tensión": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobinas con fuga de corriente": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobinas que fallan en caliente": "Falla en bujias o bobinas de encendido (misfire)",
    "Bobinas sensibles al calor": "Falla en bujias o bobinas de encendido (misfire)",
    "Bujias con grado termico incorrecto": "Falla en bujias o bobinas de encendido (misfire)",
    "Bujías con grado térmico incorrecto": "Falla en bujias o bobinas de encendido (misfire)",
    "Bujias de grado termico incorrecto": "Falla en bujias o bobinas de encendido (misfire)",
    "Bujías de grado térmico incorrecto": "Falla en bujias o bobinas de encendido (misfire)",
    "Bujias gastadas": "Falla en bujias o bobinas de encendido (misfire)",
    "Bujías gastadas": "Falla en bujias o bobinas de encendido (misfire)",
    "Bujias incorrectas": "Falla en bujias o bobinas de encendido (misfire)",
    "Bujías incorrectas": "Falla en bujias o bobinas de encendido (misfire)",
    "Bujias o bobinas en mal estado": "Falla en bujias o bobinas de encendido (misfire)",
    "Bujías o bobinas en mal estado": "Falla en bujias o bobinas de encendido (misfire)",
    "Cables de bujia deteriorados": "Falla en bujias o bobinas de encendido (misfire)",
    "Cables de bujía deteriorados": "Falla en bujias o bobinas de encendido (misfire)",
    "Cables de bujia en mal estado": "Falla en bujias o bobinas de encendido (misfire)",
    "Cables de bujía en mal estado": "Falla en bujias o bobinas de encendido (misfire)",
    "Modulo de encendido": "Falla en bujias o bobinas de encendido (misfire)",
    "Módulo de encendido": "Falla en bujias o bobinas de encendido (misfire)",
    "Modulo de encendido o bobina unica": "Falla en bujias o bobinas de encendido (misfire)",
    "Módulo de encendido o bobina única": "Falla en bujias o bobinas de encendido (misfire)",

    # Frenos
    "Cable de freno de mano": "Desgaste de pastillas y zapatas de freno",
    "Cable de freno de mano estirado": "Desgaste de pastillas y zapatas de freno",
    "Cable de freno de mano flojo": "Desgaste de pastillas y zapatas de freno",
    "Aire en el sistema de frenos": "Fuga hidraulica o aire en el sistema de frenos",
    "Fuga interna en cilindro maestro": "Fuga hidraulica o aire en el sistema de frenos",
    "Discos de freno alabeados": "Discos de freno alabeados o desgastados",
    "Discos delanteros alabeados": "Discos de freno alabeados o desgastados",
    "Discos traseros alabeados": "Discos de freno alabeados o desgastados",
    "Pastillas al limite": "Desgaste de pastillas y zapatas de freno",
    "Pastillas al límite": "Desgaste de pastillas y zapatas de freno",
    "Pastillas al limite de desgaste": "Desgaste de pastillas y zapatas de freno",
    "Pastillas al límite de desgaste": "Desgaste de pastillas y zapatas de freno",
    "Pastillas completamente gastadas": "Desgaste de pastillas y zapatas de freno",
    "Pastillas desgastadas": "Desgaste de pastillas y zapatas de freno",
    "Pastillas muy gastadas": "Desgaste de pastillas y zapatas de freno",
    "Pinza de freno pegada": "Fuga hidraulica o aire en el sistema de frenos",
    "Sensor de ABS": "Falla en sensor de velocidad de rueda ABS",
    "Sensor de ABS o anillo de tono": "Falla en sensor de velocidad de rueda ABS",
    "Servofreno defectuoso": "Falla en servofreno (booster) o linea de vacio",

    # Motor
    "Anillos de piston desgastados": "Consumo de aceite por desgaste de anillos o retenes",
    "Anillos de pistón desgastados": "Consumo de aceite por desgaste de anillos o retenes",
    "Presion de aceite baja en caliente": "Baja presion de aceite o bomba de aceite defectuosa",
    "Presión de aceite baja en caliente": "Baja presion de aceite o bomba de aceite defectuosa",
    "Bomba de agua con rodamiento dañado": "Fuga en mangueras de refrigerante o radiador picado",
    "Bomba de agua con rodamiento da\xc3\xb1ado": "Fuga en mangueras de refrigerante o radiador picado",
    "Bomba de agua dañada": "Fuga en mangueras de refrigerante o radiador picado",
    "Bomba de agua da\xc3\xb1ada": "Fuga en mangueras de refrigerante o radiador picado",
    "Carbonilla en camaras": "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)",
    "Carbonilla en cámaras": "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)",
    "Carbonilla en camaras de combustion": "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)",
    "Carbonilla en cámaras de combustión": "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)",
    "Cojinetes de biela": "Baja presion de aceite o bomba de aceite defectuosa",
    "Cojinetes de biela (grave)": "Baja presion de aceite o bomba de aceite defectuosa",
    "Correa de accesorios floja": "Faja o cadena de distribucion destensada o con salto de punto",
    "Correa de accesorios floja o tensor": "Faja o cadena de distribucion destensada o con salto de punto",
    "Correa de accesorios o tensor": "Faja o cadena de distribucion destensada o con salto de punto",
    "Correa o tensor de accesorios": "Faja o cadena de distribucion destensada o con salto de punto",
    "Junta de culata quemada": "Empaque de culata soplado o danado",
    "Empaque de tapa de punterias": "Baja presion de aceite o bomba de aceite defectuosa",
    "Empaque de tapa de punterías": "Baja presion de aceite o bomba de aceite defectuosa",
    "Fuga de vacio": "Cuerpo de aceleracion o valvula IAC sucia",
    "Fuga de vacío": "Cuerpo de aceleracion o valvula IAC sucia",
    "Fuga de vacio en admision": "Cuerpo de aceleracion o valvula IAC sucia",
    "Fuga de vacío en admisión": "Cuerpo de aceleracion o valvula IAC sucia",
    "Reten de cigueñal": "Baja presion de aceite o bomba de aceite defectuosa",
    "Retén de cigüeñal": "Baja presion de aceite o bomba de aceite defectuosa",
    "Reten de cigue\xc3\xb1al": "Baja presion de aceite o bomba de aceite defectuosa",
    "Reten de cigueñal o empaque de carter": "Baja presion de aceite o bomba de aceite defectuosa",
    "Retén de cigüeñal o empaque de cárter": "Baja presion de aceite o bomba de aceite defectuosa",
    "Reten de cigue\xc3\xb1al o empaque de carter": "Baja presion de aceite o bomba de aceite defectuosa",
    "Sellos de vastago de valvulas": "Consumo de aceite por desgaste de anillos o retenes",
    "Sellos de vástago de válvulas": "Consumo de aceite por desgaste de anillos o retenes",
    "Sensor de detonacion o carbonilla": "Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)",
    "Sensor de detonación o carbonilla": "Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)",
    "Taques hidraulicos": "Baja presion de aceite o bomba de aceite defectuosa",
    "Taqués hidráulicos": "Baja presion de aceite o bomba de aceite defectuosa",
    "Taques hidraulicos colapsados": "Baja presion de aceite o bomba de aceite defectuosa",
    "Taqués hidráulicos colapsados": "Baja presion de aceite o bomba de aceite defectuosa",
    "Taques hidraulicos sucios": "Baja presion de aceite o bomba de aceite defectuosa",
    "Taqués hidráulicos sucios": "Baja presion de aceite o bomba de aceite defectuosa",
    "Tensor de cadena debil": "Faja o cadena de distribucion destensada o con salto de punto",
    "Tensor de cadena débil": "Faja o cadena de distribucion destensada o con salto de punto",
    "Tensor de cadena hidraulico": "Faja o cadena de distribucion destensada o con salto de punto",
    "Tensor de cadena hidráulico": "Faja o cadena de distribucion destensada o con salto de punto",
    "Tensor de cadena o cadena estirada": "Faja o cadena de distribucion destensada o con salto de punto",
    "Tensor o cadena estirada": "Faja o cadena de distribucion destensada o con salto de punto",
    "Valvula PCV tapada": "Consumo de aceite por desgaste de anillos o retenes",
    "Válvula PCV tapada": "Consumo de aceite por desgaste de anillos o retenes",
    "Valvulas o anillos": "Consumo de aceite por desgaste de anillos o retenes",
    "Válvulas o anillos": "Consumo de aceite por desgaste de anillos o retenes",
    "Valvulas o anillos de piston": "Consumo de aceite por desgaste de anillos o retenes",
    "Válvulas o anillos de pistón": "Consumo de aceite por desgaste de anillos o retenes",

    # Refrigeracion
    "Radiador con fuga": "Fuga en mangueras de refrigerante o radiador picado",
    "Radiador o tapa defectuosa": "Fuga en mangueras de refrigerante o radiador picado",
    "Sensor ECT o rele del ventilador": "Falla en termostato o motoventilador de radiador",
    "Sensor ECT o relé del ventilador": "Falla en termostato o motoventilador de radiador",
    "Sensor de temperatura o rele": "Falla en termostato o motoventilador de radiador",
    "Sensor de temperatura o relé": "Falla en termostato o motoventilador de radiador",
    "Tapa de radiador defectuosa": "Fuga en mangueras de refrigerante o radiador picado",
    "Termostato abierto": "Falla en termostato o motoventilador de radiador",
    "Termostato atorado abierto": "Falla en termostato o motoventilador de radiador",
    "Termostato cerrado": "Falla en termostato o motoventilador de radiador",
    "Termostato cerrado o bomba de agua": "Falla en termostato o motoventilador de radiador",
    "Termostato defectuoso": "Falla en termostato o motoventilador de radiador",
    "Ventilador de radiador defectuoso": "Falla en termostato o motoventilador de radiador",
    "Ventilador de radiador no funciona": "Falla en termostato o motoventilador de radiador",
    "Ventilador no funciona": "Falla en termostato o motoventilador de radiador",
    "Ventilador o sensor de temperatura": "Falla en termostato o motoventilador de radiador",

    # Ruedas
    "Balanceo de llantas": "Llantas desbalanceadas o desalineadas",
    "Balanceo de llantas traseras": "Llantas desbalanceadas o desalineadas",
    "Llantas con bulbo o rin doblado": "Llantas desbalanceadas o desalineadas",
    "Llantas desbalanceadas": "Llantas desbalanceadas o desalineadas",
    "Llantas desbalanceadas o problema de alineacion": "Llantas desbalanceadas o desalineadas",
    "Llantas desbalanceadas o problema de alineación": "Llantas desbalanceadas o desalineadas",
    "Llantas desbalanceadas o rin dañado": "Llantas desbalanceadas o desalineadas",
    "Llantas desbalanceadas o rin da\xc3\xb1ado": "Llantas desbalanceadas o desalineadas",
    "Llantas desbalanceadas o rin doblado": "Llantas desbalanceadas o desalineadas",
    "Rodamiento de rueda": "Rodajes de caja mecanica o diferencial gastados",
    "Rodamiento de rueda dañado": "Rodajes de caja mecanica o diferencial gastados",
    "Rodamiento de rueda da\xc3\xb1ado": "Rodajes de caja mecanica o diferencial gastados",

    # Sensores
    "Cuerpo de aceleracion sucio": "Cuerpo de aceleracion o valvula IAC sucia",
    "Cuerpo de aceleración sucio": "Cuerpo de aceleracion o valvula IAC sucia",
    "Cuerpo de aceleracion sucio o TPS": "Cuerpo de aceleracion o valvula IAC sucia",
    "Cuerpo de aceleración sucio o TPS": "Cuerpo de aceleracion o valvula IAC sucia",
    "Sensor de cigueñal defectuoso": "Falla en bujias o bobinas de encendido (misfire)",
    "Sensor de cigüeñal defectuoso": "Falla en bujias o bobinas de encendido (misfire)",
    "Sensor de cigue\xc3\xb1al defectuoso": "Falla en bujias o bobinas de encendido (misfire)",
    "Sensor de cigueñal o arbol de levas": "Falla en bujias o bobinas de encendido (misfire)",
    "Sensor de cigüeñal o árbol de levas": "Falla en bujias o bobinas de encendido (misfire)",
    "Sensor de cigue\xc3\xb1al o arbol de levas": "Falla en bujias o bobinas de encendido (misfire)",
    "Sensor de arbol de levas": "Falla en bujias o bobinas de encendido (misfire)",
    "Sensor de árbol de levas": "Falla en bujias o bobinas de encendido (misfire)",
    "Sensor de temperatura defectuoso": "Falla en termostato o motoventilador de radiador",
    "Fuga de vacio o MAF": "Falla en sensor de oxigeno o mezcla rica",
    "Fuga de vacío o MAF": "Falla en sensor de oxigeno o mezcla rica",
    "Fuga de vacio o sensor MAF": "Falla en sensor de oxigeno o mezcla rica",
    "Fuga de vacío o sensor MAF": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor MAF contaminado": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor MAF o fuga de vacio": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor MAF o fuga de vacío": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor MAF sucio": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor MAF sucio o fuga de vacio": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor MAF sucio o fuga de vacío": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor TPS defectuoso": "Cuerpo de aceleracion o valvula IAC sucia",
    "Sensor TPS descalibrado": "Cuerpo de aceleracion o valvula IAC sucia",
    "Sensor TPS o cuerpo sucio": "Cuerpo de aceleracion o valvula IAC sucia",
    "Sensor de detonacion defectuoso": "Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)",
    "Sensor de detonación defectuoso": "Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)",
    "Sensor de oxigeno o MAF": "Falla en sensor de oxigeno o mezcla rica",
    "Sensor de oxígeno o MAF": "Falla en sensor de oxigeno o mezcla rica",
    "Regulacion de ralenti con carga": "Cuerpo de aceleracion o valvula IAC sucia",
    "Regulación de ralentí con carga": "Cuerpo de aceleracion o valvula IAC sucia",
    "Valvula IAC o cuerpo sucio": "Cuerpo de aceleracion o valvula IAC sucia",
    "Válvula IAC o cuerpo sucio": "Cuerpo de aceleracion o valvula IAC sucia",
    "Valvula IAC o regulacion de ralenti": "Cuerpo de aceleracion o valvula IAC sucia",
    "Válvula IAC o regulación de ralentí": "Cuerpo de aceleracion o valvula IAC sucia",
    "Valvula IAC sucia o fallando": "Cuerpo de aceleracion o valvula IAC sucia",
    "Válvula IAC sucia o fallando": "Cuerpo de aceleracion o valvula IAC sucia",

    # Suspension
    "Amortiguadores o topes de suspension": "Amortiguadores reventados o bujes de suspension gastados",
    "Amortiguadores o topes de suspensión": "Amortiguadores reventados o bujes de suspension gastados",
    "Bujes de horquilla o terminales": "Amortiguadores reventados o bujes de suspension gastados",
    "Bujes de suspension gastados": "Amortiguadores reventados o bujes de suspension gastados",
    "Bujes de suspensión gastados": "Amortiguadores reventados o bujes de suspension gastados",
    "Bujes de suspension o terminales": "Amortiguadores reventados o bujes de suspension gastados",
    "Bujes de suspensión o terminales": "Amortiguadores reventados o bujes de suspension gastados",
    "Junta homocinetica dañada": "Juntas homocineticas o palieres danados",
    "Junta homocinética dañada": "Juntas homocineticas o palieres danados",
    "Junta homocinetica da\xc3\xb1ada": "Juntas homocineticas o palieres danados",
    "Junta homocinetica externa": "Juntas homocineticas o palieres danados",
    "Junta homocinética externa": "Juntas homocineticas o palieres danados",
    "Junta homocinetica interna o externa": "Juntas homocineticas o palieres danados",
    "Junta homocinética interna o externa": "Juntas homocineticas o palieres danados",

    # Transmision
    "Disco de embrague al final de vida": "Disco de embrague desgastado o patinando",
    "Disco de embrague gastado": "Disco de embrague desgastado o patinando",
    "Disco de embrague o volante": "Disco de embrague desgastado o patinando",
    "Disco de embrague o volante motor": "Disco de embrague desgastado o patinando",
    "Embrague patinando": "Disco de embrague desgastado o patinando",
    "Fluido de transmision degradado": "Falta o degradacion de aceite de caja de cambios",
    "Fluido de transmisión degradado": "Falta o degradacion de aceite de caja de cambios",
    "Fluido de transmision o solenoides": "Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
    "Fluido de transmisión o solenoides": "Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
    "Rodamiento de embrague": "Falla en bombin o bomba hidraulica de embrague",
    "Rodamiento de embrague dañado": "Falla en bombin o bomba hidraulica de embrague",
    "Rodamiento de embrague dañada": "Falla en bombin o bomba hidraulica de embrague",
    "Rodamiento de embrague da\xc3\xb1ada": "Falla en bombin o bomba hidraulica de embrague",
    "Rodamiento de embrague da\xc3\xb1ado": "Falla en bombin o bomba hidraulica de embrague",
    "Rodamiento de embrague o caja": "Falla en bombin o bomba hidraulica de embrague",
    "Rodamiento de empuje": "Falla en bombin o bomba hidraulica de embrague",
}


def procesar_e_incorporar_casos_300(ruta_raw: Path, ruta_dataset_limpio: Path):
    """Parsea el CSV de los 300 casos, mapea a las 48 clases canónicas e incorpora al dataset."""
    import sys
    raiz = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(raiz / "backend"))
    from src.core.taxonomy.catalogo_fallas import CATALOGO_TAXONOMIA

    # Metadatos canónicos
    meta_taxonomia = {}
    for f in CATALOGO_TAXONOMIA.values():
        meta_taxonomia[f.falla_principal] = {
            "codigo_falla": f.codigo,
            "sistema": f.sistema,
            "severidad": f.severidad,
        }

    df_raw = pd.read_csv(ruta_raw, encoding="utf-8")
    print(f"Total casos leídos de {ruta_raw.name}: {len(df_raw)}")

    filas_nuevas = []
    sin_mapeo = set()

    for _, row in df_raw.iterrows():
        sintoma_raw = str(row.get("texto_sintomas") or "").strip()
        falla_raw = str(row.get("falla") or "").strip()
        componente = str(row.get("componente") or "").strip()
        categoria = str(row.get("categoria_falla") or "").strip()

        if not sintoma_raw or not falla_raw:
            continue

        falla_canonica = MAPA_DIAGNOSTICO_A_CANONICO_300.get(falla_raw)
        if not falla_canonica:
            sin_mapeo.add(falla_raw)
            continue

        meta = meta_taxonomia.get(falla_canonica, {
            "codigo_falla": "GEN_001",
            "sistema": categoria or "General",
            "severidad": "media",
        })

        # 1. Frase directa original del síntoma
        filas_nuevas.append({
            "sintoma": sintoma_raw,
            "falla": falla_canonica,
            "codigo_falla": meta["codigo_falla"],
            "sistema": meta["sistema"],
            "severidad": meta["severidad"],
        })

        # 2. Variante contextual enriquecida con componente y categoria para fijar n-gramas
        tokens_tecnicos = f"{componente} {categoria}".strip()
        if tokens_tecnicos:
            sintoma_enriquecido = f"{sintoma_raw} (componente: {componente})"
            filas_nuevas.append({
                "sintoma": sintoma_enriquecido,
                "falla": falla_canonica,
                "codigo_falla": meta["codigo_falla"],
                "sistema": meta["sistema"],
                "severidad": meta["severidad"],
            })

    if sin_mapeo:
        print(f"ADVERTENCIA: Diagnósticos sin mapear ({len(sin_mapeo)}): {sin_mapeo}")
        raise ValueError(f"Fallas sin mapeo detectadas: {sin_mapeo}")
    else:
        print("Mapeo 100% exitoso: 0 fallas sin clasificar.")

    print(f"Nuevas muestras generadas: {len(filas_nuevas)}")

    # Cargar dataset existente
    df_existente = pd.read_csv(ruta_dataset_limpio, encoding="utf-8")
    print(f"Dataset previo: {len(df_existente)} filas.")

    df_nuevos = pd.DataFrame(filas_nuevas)
    df_combinado = pd.concat([df_existente, df_nuevos], ignore_index=True)

    # Normalizar espacios y deduplicar
    df_combinado["sintoma"] = df_combinado["sintoma"].str.strip()
    df_combinado = df_combinado.drop_duplicates(subset=["sintoma"], keep="first")
    df_combinado = df_combinado.dropna(subset=["sintoma", "falla"])

    print(f"Dataset resultante tras deduplicación: {len(df_combinado)} filas.")
    print(f"Clases únicas: {df_combinado['falla'].nunique()} (deben ser 48).")

    assert df_combinado["falla"].nunique() == 48, f"Se esperaban 48 clases, se obtuvieron {df_combinado['falla'].nunique()}"

    df_combinado.to_csv(ruta_dataset_limpio, index=False, encoding="utf-8")
    print(f"Dataset actualizado y guardado exitosamente en: {ruta_dataset_limpio}")


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parents[2]
    ruta_raw = raiz / "machine_learning" / "data" / "casos_taller_300_raw.csv"
    ruta_limpio = raiz / "machine_learning" / "data" / "dataset_sintomas_limpio.csv"

    procesar_e_incorporar_casos_300(ruta_raw, ruta_limpio)
