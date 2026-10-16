"""Patrones regex y heurísticas para detección de riesgos de seguridad automotriz."""

from __future__ import annotations

import re

# Patrones deterministas de condiciones críticas
PATRON_FRENO_CRITICO = re.compile(
    r"\b(pedal\s+(?:se\s+fue|se\s+va|llego|llega)\s+al\s+fondo|pedal\s+al\s+piso|"
    r"se\s+queda\s+sin\s+frenos?|sin\s+presi[oó]n\s+de\s+frenos?|pedal\s+sin\s+resistencia|"
    r"fuga\s+(?:grave|severa|importante|abundante)?\s*de\s+l[ií]quido\s+de\s+frenos?|"
    r"charco\s+de\s+l[ií]quido\b.{0,30}\bfreno|"
    r"bomba\s+de\s+freno\s+reventada|freno\s+no\s+responde)\b",
    re.IGNORECASE,
)

PATRON_SUSPENSION_CRITICA = re.compile(
    r"\b(golpes?\s+met[aá]licos?\s+en\s+(?:la\s+)?suspensi[oó]n|golpes?\s+en\s+baches\b.{0,30}\bsuspensi[oó]n|"
    r"suspensi[oó]n\b.{0,30}\bgolpes?\s+met[aá]licos?|r[oó]tula\s+(?:rota|suelta|con\s+juego|con\s+holgura))\b",
    re.IGNORECASE,
)

PATRON_FRENO_PRECAUCION = re.compile(
    r"\b(chirrido\b.{0,30}\b(?:freno|frenar|ruedas)|vibraci[oó]n\b.{0,30}\b(?:al\s+frenar|en\s+el\s+pedal)|freno\b.{0,30}\bvibraci[oó]n)\b",
    re.IGNORECASE,
)

PATRON_ACEITE_CRITICO = re.compile(
    r"\b((?:luz\s+(?:roja\s+)?(?:de\s+)?|testigo\s+(?:rojo\s+)?(?:de\s+)?)(?:presi[oó]n\s+de\s+)?aceite\b.{0,50}\b(?:encend|prend|son|suen|ruido|cascabeleo|met[aá]lic|golpete)|"
    r"presi[oó]n\s+de\s+aceite\s+(?:en\s+)?(?:cero|0|baja|nula)|"
    r"sin\s+presi[oó]n\s+de\s+aceite|bomba\s+de\s+aceite\s+rota)\b",
    re.IGNORECASE,
)

PATRON_COMBUSTIBLE_CRITICO = re.compile(
    r"\b(fuga\s+(?:de\s+)?(?:gasolina|nafta|combustible)|gotea\s+(?:gasolina|nafta|combustible)|"
    r"pierde\s+(?:gasolina|nafta|combustible)|bota\s+(?:gasolina|nafta|combustible)|"
    r"charco\s+de\s+(?:gasolina|nafta|combustible)|manguera\s+de\s+(?:gasolina|combustible)\s+rota|"
    r"fuga\s+cerca\s+del\s+escape|olor\s+fuert(?:e|emente)\s+a\s+(?:gasolina|nafta|combustible)|"
    r"huele\s+(?:mucho|fuerte)\s+a\s+(?:gasolina|nafta|combustible)|"
    r"chorrea\s+(?:gasolina|nafta|combustible)|l[ií]nea\s+de\s+(?:gasolina|combustible)\s+rota)\b",
    re.IGNORECASE,
)

PATRON_TEMPERATURA_CRITICA = re.compile(
    r"\b(temperatura\s+(?:al\s+m[aá]ximo|en\s+zona\s+roja|al\s+tope|pegada\s+al\s+m[aá]ximo|sube\s+casi\s+a\s+la\s+zona\s+roja|muy\s+alta|cr[ií]tica|peligrosa)|"
    r"aguja\s+(?:de\s+temperatura\s+)?(?:sube|llega|casi|en)\s+(?:a\s+la\s+)?zona\s+roja|"
    r"(?:el\s+motor\s+|motor\s+)?recalienta(?:\s+cuando|\s+en|\s+al|\s+detenido|\s+parado)?|"
    r"recalentamiento\s+(?:extremo|severo|peligroso|del\s+motor|en\s+tr[aá]fico)?|"
    r"(?:sale|bota|botando|sale\s+con|expulsa|tirando)\s+(?:mucho\s+)?vapor|"
    r"(?:agua|refrigerante)\s+hirviendo|hirviendo\s+(?:con\s+vapor|el\s+agua|el\s+refrigerante)|"
    r"sale\s+vapor\s+(?:blanco\s+)?(?:del\s+motor|debajo\s+del\s+cap[oó]|por\s+el\s+cap[oó])|hierve\s+el\s+refrigerante|"
    r"burbujea\s+el\s+(?:dep[oó]sito|reservorio|tanque|radiador)|"
    r"radiador\s+(?:hirviendo|reventado|rajado|botando\s+agua)|"
    r"sobrecalentamiento\s+(?:extremo|severo|peligroso|motor)|humo\s+de\s+vapor\s+blanco\s+en\s+vano|"
    r"(?:temperatura\s+(?:del\s+motor\s+)?de\s+)?(?:10[6-9]|1[1-9]\d)\s*(?:°\s*c|c|grados))\b",
    re.IGNORECASE,
)

PATRON_ALTA_TENSION = re.compile(
    r"\b(alta\s+tensi[oó]n|alto\s+voltaje|aislamiento\s+(?:de\s+)?(?:alto\s+voltaje|alta\s+tensi[oó]n|hv)|"
    r"cable(?:ado)?\s+naranja|bater[ií]a\s+de\s+tracci[oó]n|bater[ií]a\s+hv|inversor\s+igbt|inversor\s+el[eé]ctrico|"
    r"falla\s+de\s+aislamiento\s+el[eé]ctrico|propulsi[oó]n\s+ev)\b",
    re.IGNORECASE,
)

PATRON_DIESEL_EMBALAMIENTO_CRITICO = re.compile(
    r"\b("
    r"(?:embalamiento|runaway|desbielamiento|aceleraci[oó]n\s+descontrolada)\b|"
    r"(?:c[aá]rter\s+lleno\s+de\s+(?:di[eé]sel|petr[oó]leo)|aceite\s+(?:diluido|mezclado)\s+con\s+(?:di[eé]sel|petr[oó]leo))|"
    r"(?:peligro\b.{0,35}\b(?:arranc(?:ar|o)|encend(?:er|ido))\b.{0,45}\b(?:c[aá]rter|aceite|di[eé]sel))|"
    r"(?:medidas?\s+de\s+seguridad\b.{0,45}\bregeneraci[oó]n)|"
    r"(?:(?:varilla|nivel\s+de\s+aceite)\b.{0,45}\b(?:\d+\s*cm|por\s+encima|sobre|alto)\b.{0,45}\b(?:full|m[aá]ximo)\b.{0,60}\b(?:dpf|regeneraci[oó]n|p2463|di[eé]sel|1gd|holl[ií]n))|"
    r"(?:(?:dpf|regeneraci[oó]n|p2463|holl[ií]n)\b.{0,60}\b(?:varilla|nivel\s+de\s+aceite)\b.{0,45}\b(?:\d+\s*cm|por\s+encima|sobre|alto)\b.{0,45}\b(?:full|m[aá]ximo))"
    r")\b",
    re.IGNORECASE,
)

PATRON_DIESEL_ALTA_PRESION_TACTIL = re.compile(
    r"\b("
    r"(?:(?:afloj(?:ar|o|[eé]|es|a|an|ando)?(?:le|lo|la)?|desconect(?:ar|o|[eé]|ando)|solt(?:ar|o|[eé]|ando))\b.{0,40}\b(?:cañer[ií]a|caño|tuber[ií]a|tubo|riel|rail|inyector)\b.{0,60}\b(?:con\s+(?:la\s+mano|el\s+dedo|un\s+trapo)|a\s+mano|la\s+mano|el\s+dedo|al\s+tacto))|"
    r"(?:(?:pas(?:ar|o|[eé]|ó|aron|es|a|an|ando|emos)?(?:le|lo|la|los|las)?|toc(?:ar|o|[eé]|ó|aron|es|a|an|ando|emos)?(?:le|lo|la)?|palp(?:ar|o|[eé]|ó|aron|es|a|an|ando|emos)?(?:le|lo|la)?|tante(?:ar|o|[eé]|ó|aron|es|a|an|ando|emos)?(?:le|lo|la)?|met(?:er|o|[ií]|ió|ieron|es|a|an|iendo|amos)?(?:le|lo|la)?|acerc(?:ar|o|[eé]|ó|aron|es|a|an|ando|emos)?(?:le|lo)?|revis(?:ar|o|[eé]|ó|aron|es|a|an|ando|emos)?(?:le|lo|la)?|busc(?:ar|o|[eé]|ó|aron|es|a|an|ando|emos)?|comprob(?:ar|o|[eé]|ó|aron|es|a|an|ando|emos)?|detect(?:ar|o|[eé]|ó|aron|es|a|an|ando|emos)?|sentir|limpi(?:ar|o|[eé]|ando|emos))\b.{0,45}\b(?:la\s+mano|el\s+dedo|las\s+manos|los\s+dedos|la\s+piel|mano|dedo|mano\s+pelada|a\s+mano|al\s+tacto|(?:un\s+|una\s+)?(?:trapo|trapito|franela|tela|paño|papelito))\b.{0,60}\b(?:cañer[ií]a|caño|tuber[ií]a|tubo|riel|rail|inyector|alta\s+presi[oó]n|fuga|petr[oó]leo|di[eé]sel|combustible|chorro))|"
    r"(?:(?:cañer[ií]a|caño|tuber[ií]a|tubo|riel|rail|common\s*rail|inyector|alta\s+presi[oó]n|fuga\s+de\s+(?:di[eé]sel|petr[oó]leo)|chorro)\b.{0,60}\b(?:pas(?:ar|o|[eé]|es|a|an|ando)|toc(?:ar|o|[eé]|es|a|an|ando)|palp(?:ar|o|[eé]|es|a|an|ando)|tante(?:ar|o|[eé]|es|a|an|ando)|met(?:er|o|[ií]|es|a|an|iendo)|acerc(?:ar|o|[eé]|es|a|an|ando)|revis(?:ar|o|[eé]|es|a|an|ando)|afloj(?:ar|o|[eé]|es|a|an|ando)|limpi(?:ar|o|[eé]|ando))\b.{0,45}\b(?:la\s+mano|el\s+dedo|las\s+manos|los\s+dedos|la\s+piel|mano|con\s+(?:la\s+mano|el\s+dedo|un\s+trapo|trapito|una\s+franela|tela|paño)|(?:un\s+|una\s+)?(?:trapo|trapito|franela|tela|paño)|a\s+mano|a\s+mano\s+pelada|al\s+tacto))|"
    r"(?:(?:con\s+(?:la\s+mano|el\s+dedo|las\s+manos|los\s+dedos|un\s+trapo|trapito|trapos|una\s+franela|tela|paño|papelito)|a\s+mano|al\s+tacto|a\s+mano\s+pelada)\b.{0,45}\b(?:revis(?:ar|o|[eé]|es|a|an|ando)|busc(?:ar|o|[eé]|es|a|an|ando)|sentir|tante(?:ar|o|[eé]|es|a|an|ando)|comprob(?:ar|o|[eé]|es|a|an|ando)|detect(?:ar|o|[eé]|es|a|an|ando)|ver|palpar|tocar)\b.{0,45}\b(?:fuga|petr[oó]leo|di[eé]sel|cañer[ií]a|caño|tuber[ií]a|tubo|riel|inyector|chorro|alta\s+presi[oó]n))|"
    r"(?:(?:puedo|voy\s+a|se\s+puede|meter(?:le)?|quiere|dice\s+si\s+puede|pregunta\s+si\s+puede|va\s+a|dejo\s+que)\s+(?:tocar|pasar(?:le|lo)?\s+(?:la\s+mano|el\s+dedo|(?:un\s+|una\s+)?(?:trapo|trapito|franela|tela|paño))|usar\s+(?:un\s+|una\s+)?(?:trapo|trapito|franela|tela|paño)|palpar|tantear|meter\s+mano|sentir)\b.{0,60}\b(?:cañer[ií]a|caño|tuber[ií]a|tubo|inyector|fuga|petr[oó]leo|riel|rail|chorro|alta\s+presi[oó]n))|"
    r"(?:(?:buscar|encontrar|detectar|revisar|ubicar|localizar|sentir|ver|tocar)\b.{0,45}\b(?:la\s+)?fuga\b.{0,60}\b(?:con\s+(?:la\s+mano|el\s+dedo|las\s+manos|los\s+dedos|un\s+trapo|trapito|una\s+franela|tela|paño|papelito)|a\s+mano|al\s+tacto|con\s+el\s+tacto))|"
    r"(?:(?:qu[eé]\s+riesgo|peligro|es\s+peligroso|qu[eé]\s+pasa\s+si|qu[eé]\s+consecuencia(?:s)?|consecuencia\s+m[eé]dica)\b.{0,50}\b(?:fuga\s+de\s+alta\s+presi[oó]n|chorro\s+de\s+inyecci[oó]n|alta\s+presi[oó]n\s+(?:di[eé]sel|petr[oó]leo|common\s*rail)|fuga\s+en\s+(?:el\s+)?common\s*rail|chorro\s+de\s+(?:di[eé]sel|petr[oó]leo|inyecci[oó]n)))|"
    r"(?:(?:pinche|pinchazo|inyecci[oó]n)\b.{0,30}\b(?:chorro|alta\s+presi[oó]n|di[eé]sel|petr[oó]leo|common\s*rail)\b)"
    r")\b",
    re.IGNORECASE,
)

PATRON_SOLICITUD_REGENERACION_DPF = re.compile(
    r"\b("
    r"(?:(?:le\s+)?(?:tiro|tire|tira|tiran|meto|meta|mete|meten|hago|haga|hace|hacen|fuerzo|fuerce|fuerza|fuerzan|iniciar|inicie|activa|activo|active)|"
    r"tirar(?:le)?|meter(?:le)?|hacer(?:le)?|forzar(?:le)?|iniciar|activar|ejecutar|realizar|"
    r"puedo\s+(?:forzar|hacer|iniciar|activar|ejecutar|realizar|tirar|meter)|"
    r"voy\s+a\s+(?:forzar|hacer|iniciar|activar|ejecutar|realizar|tirar|meter)|"
    r"(?:quiere|insiste\s+en|pide|solicita|sugiere|manda)\s+(?:que\s+(?:le\s+)?(?:haga|tire|meta|fuerce)|(?:hacer|tirar|meter|forzar)))\s+"
    r"(?:(?:una|la|el)\s+)?(?:regeneraci[oó]n|regenerar|regenerada)\b|"
    r"\bregenerada\s+(?:est[aá]tica|forzada|con\s+esc[aá]ner|con\s+scanner|al\s+dpf)\b|"
    r"\bregeneraci[oó]n\s+(?:forzada|est[aá]tica|estacionaria|con\s+(?:el\s+)?esc[aá]ner|de\s+servicio|en\s+taller)\b|"
    r"\bregenerar\s+(?:el\s+)?(?:dpf|filtro|fap)\s+(?:con\s+(?:el\s+)?esc[aá]ner|en\s+(?:taller|est[aá]tico|parado)|a\s+la\s+fuerza)?\b|"
    r"\b(?:puedo|se\s+puede|quiere|insiste\s+en)\s+regenerar\b|"
    r"\bdestapar\s+(?:el\s+)?(?:filtro|dpf)\s+(?:con\s+(?:el\s+)?esc[aá]ner|forzando|est[aá]tico)\b"
    r")\b",
    re.IGNORECASE,
)

PATRON_INDICIOS_DILUCION_ACEITE = re.compile(
    r"\b("
    r"(?:varilla|nivel\s+de\s+aceite|aceite)\b.{0,50}(?:\d+\s*cm|por\s+encima|encima|sobre|alto|pasad[oa])\b|"
    r"varilla\b.{0,40}\bpasad[oa]\b|"
    r"aceite\b.{0,40}\b(?:diluido|mezclado|con\s+olor|huele|olor\s+a|pasad[oa]|contaminado)\b.{0,30}\b(?:di[eé]sel|petr[oó]leo|combustible)|"
    r"(?:olor\s+a\s+(?:di[eé]sel|petr[oó]leo)|huele\s+a\s+(?:di[eé]sel|petr[oó]leo))\b.{0,40}\baceite|"
    r"c[aá]rter\b.{0,40}\b(?:lleno|sobrellenado|con\s+(?:di[eé]sel|petr[oó]leo)|contaminado|diluido)|"
    r"subi[oó]\s+(?:el\s+)?nivel(?:\s+de\s+aceite)?|"
    r"nivel\s+de\s+aceite\s+subi[oó]|"
    r"aceite\s+est[aá]\s+pasado"
    r")\b",
    re.IGNORECASE,
)

PATRON_CORRECCION_ACEITE_COMPROBADA = re.compile(
    r"\b("
    r"(?:dren[eé]|vaci[eé]|bot[eé]|cambi[eé]|puse|coloqu[eé]|reemplac[eé]|correg[ií])\b.{0,50}\b(?:aceite|filtro|problema\s+del\s+aceite)|"
    r"aceite\s+(?:ya\s+)?(?:est[aá]\s+)?(?:nuevo|cambiado|reemplazado|a\s+nivel|en\s+su\s+nivel)|"
    r"nivel\s+(?:normal|correcto|en\s+el\s+m[aá]ximo|entre\s+marcas)"
    r")\b",
    re.IGNORECASE,
)

PATRON_ACCION_APERTURA_REFRIGERACION = re.compile(
    r"\b("
    r"(?:abr(?:ir|o|e|es|a|an|iendo)|ábr(?:elo|ala|ale)?|abrir(?:le|lo|la|los|las)?)|"
    r"(?:destap(?:ar|o|e|es|a|an|ando)|destáp(?:alo|ala|ale)?|destapar(?:le|lo|la)?)|"
    r"(?:afloj(?:ar|o|e|es|a|an|ando)|afl[oó]j(?:alo|ala|ale)?|aflojar(?:le|lo|la)?)|"
    r"(?:quit(?:ar|o|e|es|a|an|ando)|quít(?:alo|ala|ale)?|quitar(?:le|lo|la)?)|"
    r"(?:sac(?:ar|o|e|es|a|an|ando)|sáq(?:alo|ala|ale)?|sacar(?:le|lo|la)?)|"
    r"(?:volar(?:le)?|vuel(?:o|e|es|a|an)?)\b.{0,15}\b(?:la\s+)?tapa|"
    r"(?:retir(?:ar|o|e|es|a|an|ando)|retirar(?:le|lo|la)?)|"
    r"(?:desenrosc(?:ar|o|e|es|a|an|ando)|desenroscar(?:le|lo|la)?)|"
    r"(?:echar(?:le)?\s+agua\s+(?:fr[ií]a|al\s+toque|ahorita))|"
    r"(?:meter\s+mano\s+al\s+(?:radiador|dep[oó]sito|reservorio|circuito))"
    r")\b",
    re.IGNORECASE,
)

PATRON_OBJETO_REFRIGERACION = re.compile(
    r"\b("
    r"(?:tapa|tap[oó]n|tapones)\b(?:\s+(?:del?|de\s+la|al)\b.{0,30}\b(?:radiador|dep[oó]sito|reservorio|vaso|refrigerante|agua))?|"
    r"(?:radiador|radiadores)|"
    r"(?:dep[oó]sito|deposito|reservorio|vaso\s+de\s+expansi[oó]n|tacho)(?:\s+(?:de\s+)?(?:refrigerante|agua|anticongelante))?|"
    r"sistema\s+(?:de\s+)?refrigeraci[oó]n|circuito\s+(?:de\s+)?refrigeraci[oó]n"
    r")\b",
    re.IGNORECASE,
)

PATRON_CALOR_REFRIGERACION = re.compile(
    r"\b("
    r"caliente|hirviendo|hierve|hervir|vapor|ebullici[oó]n|"
    r"recalentado|recalienta|recalentando|sobrecalentado|sobrecalentamiento|"
    r"temperatura\s+(?:alta|elevada|al\s+m[aá]ximo|en\s+rojo|cr[ií]tica|peligrosa)|"
    r"agua\s+caliente|refrigerante\s+caliente|humo\s+(?:de\s+vapor|blanco)|"
    r"10[0-9]|1[1-9]\d|\d{3}\s*grados|\d{3}\s*°\s*c"
    r")\b",
    re.IGNORECASE,
)

PATRON_ENFRIAMIENTO_CONFIRMADO = re.compile(
    r"\b("
    r"(?:motor|refrigerante|radiador|sistema)\s+(?:ya\s+)?(?:est[aá]\s+)?(?:fr[ií]o|enfriado|a\s+temperatura\s+ambiente)|"
    r"dej(?:amos|e|aron|ó)\s+(?:enfriar|que\s+se\s+enfr[ií]e)|"
    r"(?:esper(?:amos|é|aron|ó)|dej(?:amos|e|aron|ó))\s+.{0,30}(?:enfri|45\s+minutos?|hora|tiempo\s+necesario)|"
    r"(?:marcó|marca|temperatura\s+(?:de\s+)?)(?:[234]\d)\s*(?:°|º)?\s*[cg]|"
    r"una\s+vez\s+fr[ií]o|ya\s+se\s+enfri[oó]|ya\s+enfri[oó]"
    r")\b",
    re.IGNORECASE,
)

PATRON_APERTURA_RADIADOR_CALIENTE = re.compile(
    r"\b("
    r"(?:(?:abr(?:ir|o|e|es|a|an|ando|irle|irles)?|destap(?:ar|o|e|es|a|an|ando|arle)?|retir(?:ar|o|e|es|a|an|ando|arle)?|quit(?:ar|o|e|es|a|an|ando|arle)?|sac(?:ar|o|e|es|a|an|ando|arle)?|afloj(?:ar|o|e|es|a|an|ando|arle)?|afl[oó]j(?:ale|alo|ala)?)\b.{0,60}\b(?:tapa|tap[oó]n|radiador|dep[oó]sito|reservorio|vaso|tacho)\b.{0,80}\b(?:caliente|hirviendo|temperatura\s+alta|10[0-9]|1[1-9]\d|vapor|grados))|"
    r"(?:(?:caliente|hirviendo|temperatura\s+alta|10[0-9]|1[1-9]\d|vapor|grados)\b.{0,80}\b(?:abr(?:ir|o|e|es|a|an|ando|irle|irles)?|destap(?:ar|o|e|es|a|an|ando|arle)?|retir(?:ar|o|e|es|a|an|ando|arle)?|quit(?:ar|o|e|es|a|an|ando|arle)?|sac(?:ar|o|e|es|a|an|ando|arle)?|afloj(?:ar|o|e|es|a|an|ando|arle)?|afl[oó]j(?:ale|alo|ala)?)\b.{0,60}\b(?:tapa|tap[oó]n|radiador|dep[oó]sito|reservorio|vaso|tacho))"
    r")\b",
    re.IGNORECASE,
)

