"""Entrada de compatibilidad para el gestor seguro de administradores.

Este nombre se conserva para no romper accesos directos existentes. Las
credenciales y los datos del taller ya no se incluyen en el código.
"""

from scripts.gestionar_admin import main

if __name__ == "__main__":
    main()
