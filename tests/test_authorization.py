from src.core.authorization import Permiso, tiene_permiso


def test_administrador_tiene_todos_los_permisos():
    payload = {"rol": "administrador"}
    assert all(tiene_permiso(payload, permiso) for permiso in Permiso)


def test_supervisor_valida_diagnosticos_sin_gestionar_usuarios_ni_colas():
    payload = {"rol": "supervisor"}
    assert tiene_permiso(payload, Permiso.DIAGNOSTICOS_CONFIRMAR)
    assert tiene_permiso(payload, Permiso.METRICAS_LEER)
    assert not tiene_permiso(payload, Permiso.USUARIOS_GESTIONAR)
    assert not tiene_permiso(payload, Permiso.TRABAJOS_GESTIONAR)


def test_mecanico_no_obtiene_permisos_administrativos():
    payload = {"rol": "mecanico"}
    assert tiene_permiso(payload, Permiso.DIAGNOSTICOS_CREAR)
    assert not tiene_permiso(payload, Permiso.DIAGNOSTICOS_CONFIRMAR)
    assert not tiene_permiso(payload, Permiso.VALIDACION_GESTIONAR)
