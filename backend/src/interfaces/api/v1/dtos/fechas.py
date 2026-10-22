from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def fecha_hora_peru(valor: datetime | None) -> str | None:
    if valor is None:
        return None
    if valor.tzinfo is None:
        valor = valor.replace(tzinfo=timezone.utc)
    return valor.astimezone(ZoneInfo("America/Lima")).strftime("%Y-%m-%d %H:%M")
