"""Escritura CSV atómica y bloqueo interproceso del fallback de desarrollo."""

import os
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import pandas as pd


def _es_proceso_vivo(pid: int) -> bool:
    """Comprueba si un proceso sigue en ejecución en el sistema operativo."""
    if pid <= 0:
        return False

    if sys.platform == "win32":
        try:
            import ctypes

            synchronize = 0x00100000
            wait_timeout = 0x00000102
            handle = ctypes.windll.kernel32.OpenProcess(synchronize, False, pid)
            if not handle:
                return False
            try:
                return ctypes.windll.kernel32.WaitForSingleObject(handle, 0) == wait_timeout
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            return False

    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except (OSError, SystemError):
        return False


@contextmanager
def _bloqueo_archivo_interproceso(lock_path: Path, timeout: float = 6.0, max_stale_seconds: float = 12.0):
    """Garantiza exclusividad de archivo entre múltiples procesos/workers con auto-recuperación de locks huérfanos."""
    lock_file = lock_path.with_suffix(".lock")
    start = time.time()
    adquirido = False
    while time.time() - start < timeout:
        try:
            # os.O_CREAT | os.O_EXCL garantiza exclusividad atómica en el kernel
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            try:
                lock_info = f"{os.getpid()}:{time.time():.4f}\n".encode("utf-8")
                os.write(fd, lock_info)
            finally:
                os.close(fd)
            adquirido = True
            break
        except FileExistsError:
            # Comprobar si el lock existente es huérfano / abandonado tras un crash forzado
            try:
                st = lock_file.stat()
                edad_lock = time.time() - st.st_mtime
                if edad_lock > max_stale_seconds:
                    try:
                        lock_file.unlink()
                        continue
                    except Exception:
                        pass
                else:
                    # Comprobar si el PID que tomó el lock sigue existiendo en el sistema
                    try:
                        contenido = lock_file.read_text(encoding="utf-8").strip()
                        if contenido and ":" in contenido:
                            pid_str, _ = contenido.split(":", 1)
                            pid = int(pid_str)
                            if not _es_proceso_vivo(pid):
                                lock_file.unlink()
                                continue
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(0.02)
        except Exception:
            break

    if not adquirido:
        raise TimeoutError(
            f"No se pudo adquirir el bloqueo de archivo exclusivo en {lock_file} tras {timeout}s"
        )

    try:
        yield
    finally:
        try:
            if lock_file.exists():
                lock_file.unlink()
        except Exception:
            pass


def _guardar_df_tracker_atomico(df: pd.DataFrame, csv_path: Path) -> None:
    """Escribe a un archivo temporal en el mismo directorio y ejecuta reemplazo atómico en el SO."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = csv_path.parent
    with tempfile.NamedTemporaryFile("w", dir=temp_dir, delete=False, encoding="utf-8", newline="") as tf:
        temp_name = tf.name
        df.to_csv(tf, index=False, encoding="utf-8")
        tf.flush()
        os.fsync(tf.fileno())
    os.replace(temp_name, str(csv_path))
