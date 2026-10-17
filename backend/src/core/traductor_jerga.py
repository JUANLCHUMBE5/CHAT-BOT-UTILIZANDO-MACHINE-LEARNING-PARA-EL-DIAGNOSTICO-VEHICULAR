import re

DICCIONARIO_VARIANTES_ENTRADA: tuple[tuple[str, str], ...] = (
    # Correcciones de dictado/tipeo frecuente en siglas de combustible.
    (r"\bg\s*[.\-/]?\s*n\s*[.\-/]?\s*[vb]\b", "gnv"),
    (r"\bg\s*[.\-/]?\s*l\s*[.\-/]?\s*[pb]\b", "glp"),
    (r"\b(?:gas\s+natural\s+vehicular|gas\s+natural)\b", "gnv"),
    (r"\b(?:gas\s+licuado(?:\s+de\s+petroleo|\s+de\s+petróleo)?|autogas|auto\s+gas)\b", "glp"),
    (r"\b(?:nafta|bencina)\b", "gasolina"),
    (r"\b(?:gasoil|acpm)\b", "diesel"),
    # Expresiones coloquiales de pérdida de potencia o respuesta lenta.
    (
        r"\b(?:se\s+chanchea|se\s+achancha|se\s+pone\s+chancho|"
        r"se\s+vuelve\s+chancho|esta\s+chancho|está\s+chancho|"
        r"se\s+queda\s+sin\s+fuerza|no\s+tiene\s+fuerza\s+en\s+subida)\b",
        "pierde potencia y presenta tirones al acelerar",
    ),
    # Errores de escritura y modismos peruanos frecuentes en consultas reales de taller/WhatsApp.
    (r"\bno\s+aranca\b", "no arranca"),
    (r"\b(?:frena\s+)?malaso\b", "frena muy mal anomalia en frenos"),
    (r"\b(?:suena|ruido)\s+cuado\s+giro\b", "suena cuando giro chasquido palier junta homocinetica"),
    (r"\b(?:se\s+)?calienta\s+muxo\b", "se calienta mucho sobrecalentamiento del motor"),
    (r"\b(?:se\s+amarra|esta\s+amarrado|está\s+amarrado)\b", "caliper trabado o freno pegado se amarra"),
    (r"\b(?:esta\s+temblando\s+feo|está\s+temblando\s+feo)\b", "vibracion excesiva e inestabilidad en el motor"),
    (r"\b(?:suena\s+como\s+lata|traqueteo\s+de\s+lata)\b", "ruido metalico o golpeteo suelto"),
    (r"\b(?:rompemuelle|rompemuelles)\b", "baches o desniveles"),
    (r"\b(?:menjar|manejarlo|manejando)\b", "manejar"),
    (r"\b(?:vibraciones|vibracion|vibración)\s+al\s+manejar\b", "vibracion al manejar"),
    (r"\b(?:llanta|llantas)\s+desbalancead[ao]s?\b", "llantas desbalanceadas"),
    # Términos técnicos que mejoran coincidencia con clases canónicas del modelo ML.
    (
        r"\b(?:humo\s+blanco|bota\s+humo\s+blanco|sale\s+humo\s+blanco)"
        r"(?=.*(?:refrigerante|agua|culata|temperatura|recalienta|calienta))\b",
        "humo blanco por escape vapor blanco consume refrigerante posible empaque de culata",
    ),
    # Emulsión agua-aceite ("café con leche" / "mayonesa" en tapa o varilla) -> Empaque de culata
    (
        r"\b(?:cafe\s+con\s+leche|café\s+con\s+leche|mayonesa|lechoso|chocolatada|emulsionad[oa])\b",
        "se mezcla el agua con el aceite chocolatada en el motor empaque de culata soplado",
    ),
    # Burbujeo en radiador o botella de expansión -> Empaque de culata
    (
        r"\b(?:burbujea\s+(?:el\s+)?(?:radiador|deposito|depósito|agua|refrigerante)|"
        r"burbujas\s+en\s+(?:el\s+)?(?:radiador|deposito|depósito|vaso|botella))\b",
        "radiador bota burbujas presion en sistema de refrigeracion empaque de culata",
    ),
    # Jerga eléctrica de taller: "roba corriente" -> Fuga parásita
    (
        r"\b(?:roba\s+corriente|consume\s+corriente\s+apagado|se\s+baja\s+la\s+bateria\s+sola|"
        r"se\s+descarga\s+de\s+noche|amanece\s+muerta\s+la\s+bateria)\b",
        "fuga parasita de corriente en reposo consumo nocturno de bateria amanece descargada",
    ),
    # Jerga de frenos: "rueda frenada" / "llanta amarrada" -> Cáliper trabado
    (
        r"\b(?:rueda\s+(?:frenada|amarrada|pegada|trabada)|llanta\s+(?:frenada|amarrada|pegada)|"
        r"mordaza\s+pegada|caliper\s+pegado)\b",
        "caliper de freno trabado o mordaza pegada piston agarrotado recalienta un solo aro",
    ),
    # Jerga de dirección: "cajas de dirección" / "cremallera"
    (
        r"\b(?:caja\s+de\s+direccion|caja\s+hidraulica|botella\s+de\s+direccion)\b",
        "cremallera de direccion asistida",
    ),
    # Jerga de transmisión/embrague: "collarín" / "crapodina" / "ruleman de empuje"
    (
        r"\b(?:ruleman\s+de\s+empuje|rodamiento\s+de\s+empuje|cojinete\s+de\s+embrague|"
        r"crapodina|collarin\s+de\s+embrague)\b",
        "collarin de empuje o crapodina de embrague",
    ),
    # Códigos OBD-II frecuentes hacia síntomas canónicos
    (r"\bp030[0-8]\b", r"codigo \g<0> de falla de encendido multiple en cilindros bujias o bobinas"),
    (r"\bp0420\b", "codigo p0420 eficiencia de catalizador por debajo del umbral convertidor catalitico"),
    (r"\bp0171\b", "codigo p0171 mezcla pobre en banco 1 vacio o inyeccion"),
    (r"\bp0172\b", "codigo p0172 mezcla rica en banco 1 sensor de oxigeno o inyectores"),
)


DICCIONARIO_JERGA_LATAM: tuple[tuple[str, str], ...] = (
    # Frenos y rodamientos: México, Colombia, Chile, Argentina y Venezuela.
    (r"\bbalatas?\b", "pastillas de freno"),
    (r"\b(?:bandas|cintas)\s+de\s+freno\b", "zapatas de freno"),
    (r"\b(?:bomba\s+central\s+de\s+freno|cilindro\s+maestro)\b", "bomba de freno"),
    (r"\b(?:mordaza\s+de\s+freno|c[aá]liper)\b", "caliper de freno"),
    (r"\b(?:rulem[aá]n|rolinera|balero|maza\s+de\s+rueda)\b", "rodamiento"),
    # Transmisión, embrague y tracción.
    (r"\b(?:clutch|cloche|croche)\b", "embrague"),
    (r"\b(?:flecha\s+homocin[eé]tica|semieje|eje\s+homocin[eé]tico)\b", "palier"),
    (r"\b(?:triceta|tripoide)\b", "junta homocinetica interior"),
    (r"\b(?:caja\s+de\s+velocidades|transmisi[oó]n\s+mec[aá]nica)\b", "caja de cambios"),
    # Arranque, carga y encendido.
    (r"\b(?:burro de arranque|motor de partida|starter)\b", "motor de arranque"),
    (r"\bla\s+marcha\s+(?:no\s+gira|no\s+da|pesada|pegada|arrastra|falla)\b", "el motor de arranque no gira"),
    (r"\brelevador\b", "rele"),
    (r"\bbug[ií]a\b", "bujia"),
    # Motor, refrigeración y escape.
    (r"\b(?:banda|correa)\s+(?:de\s+)?(?:tiempo|distribucion|distribución)\b", "faja de distribucion"),
    (r"\b(?:banda|correa)\s+(?:serpentina|de accesorios?)\b", "faja de accesorios"),
    (r"\b(?:cabezote|cabeza del motor)\b", "culata"),
    (r"\b(?:empacadura|empaquetadura|guarnicion|guarnición)\s+de\s+(?:culata|cabeza)\b", "empaque de culata"),
    (r"\b(?:mofle|mufla|exosto)\b", "silenciador de escape"),
    (r"\b(?:anticongelante|coolant)\b", "refrigerante"),
    # Suspensión, dirección, ruedas y carrocería.
    (r"\b(?:shock|shock absorber)\b", "amortiguador"),
    (r"\b(?:bota|acordeon|acordeón)\s+(?:de\s+)?homocinetica\b", "fuelle de junta homocinetica"),
    (r"\b(?:cubierta|caucho|goma)\s+(?:del\s+)?(?:auto|carro|vehiculo|vehículo|rueda)\b", "llanta"),
    (r"\bneumatico\b", "llanta"),
    (r"\b(?:latoneria|latonería|hojalateria|hojalatería|desabolladura)\s+y\s+pintura\b", "planchado y pintura"),
    (r"\b(?:cajuela|baul|baúl)\b", "maletera"),
    (r"\bcofre\b", "capot"),
    (r"\b(?:volante de direccion|volante de dirección)\b", "timon"),
    (r"\b(?:elevavidrios|elevalunas|alzavidrios|alzacristales)\b", "elevalunas alzacristales elevador de vidrio"),
    (r"\b(?:plumillas|escobillas)\s+(?:del\s+)?limpiaparabrisas\b", "plumas de limpiaparabrisas"),
)


DICCIONARIO_JERGA_PERUANA: tuple[tuple[str, str], ...] = (
    (r"\bcaña\b", "vehiculo"),
    (r"\bcascabelea\b", "preignicion o falla de bujias por cascabeleo"),
    (r"\bcascabeleando\b", "preignicion o falla de bujias"),
    (r"\bcabecea\b", "vibracion e inestabilidad en el motor"),
    (r"\bse chupa\b", "pierde potencia y se aguanta al acelerar"),
    (r"\bse aguanta\b", "perdida de fuerza al acelerar"),
    (
        r"\b(?:zapatea(?:\s+feo)?\s+al\s+arrancar(?:\s+en\s+primera)?|"
        r"zapateo\s+de\s+embrague|trepidaci[oó]n\s+al\s+salir|"
        r"al\s+arrancar\s+en\s+primera\s+zapatea)\b",
        "trepidacion de embrague al arrancar",
    ),
    (
        r"\b(?:zapatea\s+(?:al\s+frenar|frenando)|al\s+frenar\s+zapatea)\b",
        "vibracion por discos de freno alabeados",
    ),
    (r"\bzapatea\b", "vibracion"),
    (r"\bzapateo\b", "vibracion"),
    (r"\bbota vapor\b", "sobrecalentamiento y expulsion de refrigerante"),
    (r"\b(?:taca\s*taca|traque\s*traque|clac\s*clac|cla\s*cla)\b", "chasquido clac clac en junta homocinetica o palier"),
    (r"\b(?:doblar|doblo|giro|girar|doblando|girando)\s+(?:en\s+u|todo\s+el\s+tim[oó]n|el\s+tim[oó]n\s+a\s+tope)\b", "girar el timon a tope en curva cerrada palier"),
    (r"\b(?:grasa\s+negra|grasa\s+botada|grasa\s+esparcida)\b", "fuga de grasa por fuelle roto de palier o junta homocinetica"),
    (r"\b(?:fuelle|guardapolvo)\s+(?:roto|rajado|abierto|picado)\b", "fuelle roto de junta homocinetica con perdida de grasa"),
    (r"\bpedal esponjoso\b", "pedal de freno esponjoso por aire o fuga hidraulica"),
    (r"\bpedal largo\b", "recorrido excesivo del pedal de freno"),
    (r"\bchillido de faja\b", "chillido de faja de accesorios"),
    (r"\bhumo garzo\b", "humo azul por consumo de aceite"),
    (r"\bhumo azul\b", "humo azul por consumo de aceite"),
    (r"\bhumo negro\b", "humo negro por mezcla rica o combustion incompleta"),
    (r"\bhumo blanco\b", "humo blanco o vapor por ingreso de refrigerante"),
    (r"\bplumas\b", "plumas de limpiaparabrisas"),
    (r"\bchapa\b", "chapa cerradura de puerta"),
    (r"\bpestillo\b", "pestillo cerradura"),
    (r"\ben minimo\b", "motor en ralenti sin acelerar"),
    (r"\bjalonea\b", "presenta tirones al circular o acelerar"),
    (r"\bgolpe en baches\b", "golpe de suspension al pasar baches"),
    (r"\bgolpe en buches\b", "golpe de suspension al pasar baches"),
    (r"\btrancazo seco\b", "golpe seco en suspension"),
    (r"\brasca el cambio\b", "dificultad o raspado al engranar cambios"),
)


def normalizar_jerga_peruana(texto: str) -> str:
    """Convierte jerga peruana y regional LATAM a términos técnicos peruanos."""
    if not texto:
        return ""

    texto_procesado = texto.lower()
    diccionarios = (
        DICCIONARIO_VARIANTES_ENTRADA
        + DICCIONARIO_JERGA_LATAM
        + DICCIONARIO_JERGA_PERUANA
    )
    for patron, reemplazo in diccionarios:
        texto_procesado = re.sub(patron, reemplazo, texto_procesado, flags=re.IGNORECASE)

    return re.sub(r"\s+", " ", texto_procesado).strip()
