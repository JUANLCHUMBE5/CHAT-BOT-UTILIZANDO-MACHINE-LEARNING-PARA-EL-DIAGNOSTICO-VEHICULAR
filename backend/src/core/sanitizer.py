import re
import unicodedata

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous\s+)?(instructions|prompts|rules)",
    r"olv[ií]da(te)?\s+(de\s+)?(todas\s+)?(las|tus)\s+(instrucciones|reglas)([\s_]+anteriores)?",
    r"you\s+are\s+now\s+(an\s+)?(unrestricted|dan|jailbroken)",
    r"act[uú]a\s+como\s+(un\s+)?(hacker|robot|sistema|llm)",
    r"system\s*prompt",
    r"override\s+system",
    r"reveal\s+(your|tu)\s+(prompt|instructions|system)",
    r"muestra\s+(tu|tus)\s+(prompt|instrucciones)",
    r"drop\s+table",
    r"delete\s+from",
    r"insert\s+into",
    r"update\s+.*\s+set",
    r"<script\b[^>]*>",
    r"jailbreak",
    r"dan\s+mode",
    r"do\s+anything\s+now"
]

def normalizar_texto_para_inspeccion(texto: str) -> str:
    """Normaliza acentos, espacios cero-ancho y caracteres invisibles para prevenir evasiones."""
    # Eliminar acentos y diacríticos
    norm = unicodedata.normalize('NFD', texto)
    norm = "".join(c for c in norm if unicodedata.category(c) != 'Mn')
    # Reemplazar múltiples espacios o caracteres invisibles por espacio único
    norm = re.sub(r'[\s\x00-\x1f\x7f-\x9f\u200b-\u200d\ufeff]+', ' ', norm)
    return norm.lower()

def sanitizar_prompt_usuario(texto: str, max_length: int = 500) -> str:
    """
    Sanitiza y acota el texto ingresado por el usuario para prevenir ataques de Prompt Injection
    y ataques de denegación de servicio por longitud excesiva.
    """
    if not texto:
        return ""
        
    # 1. Remover caracteres de control nulos y retornos de carro
    texto_limpio = texto.replace("\x00", "").replace("\r", " ")
    
    # 2. Limitar longitud máxima (evita saturar tokens del LLM)
    texto_limpio = texto_limpio[:max_length].strip()
    
    # 3. Inspeccionar versión normalizada para detectar encubrimiento por acentos/espacios
    norm = normalizar_texto_para_inspeccion(texto_limpio)
    
    for patron in PROMPT_INJECTION_PATTERNS:
        if re.search(patron, norm, re.IGNORECASE) or re.search(patron, texto_limpio, re.IGNORECASE):
            # Neutralizar la inyección en el texto final
            texto_limpio = re.sub(patron, "[INTENTO_INYECCION_BLOQUEADO]", texto_limpio, flags=re.IGNORECASE)
            # Si el texto normalizado hizo match pero el regex original no capturó por acentos/espacios, reemplazar por defecto
            if "[INTENTO_INYECCION_BLOQUEADO]" not in texto_limpio:
                texto_limpio = "[INTENTO_INYECCION_BLOQUEADO] " + texto_limpio
            
    return texto_limpio
