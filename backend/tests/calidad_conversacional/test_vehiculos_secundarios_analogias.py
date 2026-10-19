# -*- coding: utf-8 -*-
"""
Pruebas de regresión: Discriminación de vehículos secundarios, analogías
y preservación del vehículo activo durante el diagnóstico conversacional.
"""

import pytest

from src.core.conversacion.extraccion_hechos.actualizador_estado import extraer_y_actualizar
from src.core.conversacion.models import ConversationState
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


class TestVehiculosSecundariosYAnalogias:
    """Valida que vehículos secundarios, analogías o autos de clientes no sustituyan el vehículo activo."""

    def test_caso_principal_otro_auto_del_cliente(self):
        """Caso principal: El cliente menciona que su otro auto es un Ford, revisando Nissan Tiida."""
        estado = ConversationState(session_id="test_sec_01")
        extraer_y_actualizar(estado, "Tengo un Nissan Tiida 2015 con tironeo en subida")

        assert estado.marca == "Nissan"
        assert estado.modelo == "Tiida"
        assert estado.anio == "2015"

        extraer_y_actualizar(
            estado,
            "El cliente mencionó que su otro auto es un Ford, pero estamos revisando este.",
        )

        assert estado.marca == "Nissan", "La marca activa debe seguir siendo Nissan"
        assert estado.modelo == "Tiida", "El modelo activo debe seguir siendo Tiida"
        assert estado.anio == "2015"
        assert "vehiculo_mencionado_ford" in estado.hechos
        assert estado.hechos["vehiculo_mencionado_ford"].valor == "Ford"
        assert estado.hechos["vehiculo_mencionado_ford"].categoria == "antecedente"

    def test_vehiculo_anterior_con_modelo(self):
        """Mención de vehículo anterior con marca y modelo conocido (Chevrolet Sail)."""
        estado = ConversationState(session_id="test_sec_02")
        extraer_y_actualizar(estado, "Toyota Yaris 2018 no acelera parejo")

        assert estado.marca == "Toyota"
        assert estado.modelo == "Yaris"

        extraer_y_actualizar(
            estado,
            "El vehículo anterior era un Chevrolet Sail, pero este tiembla al frenar.",
        )

        assert estado.marca == "Toyota"
        assert estado.modelo == "Yaris"
        assert "vehiculo_mencionado_chevrolet" in estado.hechos
        assert estado.hechos["vehiculo_mencionado_chevrolet"].categoria == "antecedente"
        assert "modelo_mencionado_sail" in estado.hechos
        assert estado.hechos["modelo_mencionado_sail"].categoria == "antecedente"

    def test_auto_de_ayer_y_camioneta(self):
        """Expresiones como 'el auto de ayer era un Hyundai Tucson' o 'la camioneta de ayer'."""
        estado = ConversationState(session_id="test_sec_03")
        extraer_y_actualizar(estado, "Kia Rio 2017 con humo negro")

        extraer_y_actualizar(estado, "El auto de ayer era un Hyundai Tucson que tenía lo mismo.")
        assert estado.marca == "Kia"
        assert estado.modelo == "Rio"
        assert "vehiculo_mencionado_hyundai" in estado.hechos

        extraer_y_actualizar(estado, "Y la camioneta de ayer era una Toyota Hilux.")
        assert estado.marca == "Kia"
        assert estado.modelo == "Rio"
        assert "vehiculo_mencionado_toyota" in estado.hechos

    def test_otro_carro_del_cliente_variaciones(self):
        """Variaciones de redacción sobre otro carro perteneciente al cliente."""
        estado = ConversationState(session_id="test_sec_04")
        extraer_y_actualizar(estado, "Nissan Sentra 2020 pierde fuerza")

        extraer_y_actualizar(
            estado,
            "El cliente tiene otro carro del cliente que es un Ford Fiesta, pero aquí estamos con el Nissan",
        )
        assert estado.marca == "Nissan"
        assert estado.modelo == "Sentra"
        assert "vehiculo_mencionado_ford" in estado.hechos

    def test_analogia_comparativa_al_igual_que(self):
        """Analogía técnica comparativa ('Como en un Chevrolet Sail que tuve')."""
        estado = ConversationState(session_id="test_sec_05")
        extraer_y_actualizar(estado, "Hyundai Accent 2016 con ralentí inestable")

        extraer_y_actualizar(estado, "Como en un Chevrolet Sail que tuve, pero aquí ratea en frío.")
        assert estado.marca == "Hyundai"
        assert estado.modelo == "Accent"
        assert "vehiculo_mencionado_chevrolet" in estado.hechos
        assert "modelo_mencionado_sail" in estado.hechos

    def test_correcciones_legitimas_siguen_funcionando_positivas(self):
        """Las correcciones auténticas del mecánico DEBEN actualizar el vehículo activo."""
        estado = ConversationState(session_id="test_sec_06")
        extraer_y_actualizar(estado, "Tengo un Toyota Yaris con vibración al frenar")
        assert estado.marca == "Toyota"
        assert estado.modelo == "Yaris"

        # Corrección con 'No es X, es Y'
        extraer_y_actualizar(estado, "No es Toyota, es Nissan Sentra")
        assert estado.marca == "Nissan"
        assert estado.modelo == "Sentra"

        # Corrección con 'Corrijo'
        extraer_y_actualizar(estado, "Corrijo, me equivoqué de ficha: es un Kia Cerato")
        assert estado.marca == "Kia"
        assert estado.modelo == "Cerato"

        # Corrección con 'En realidad es'
        extraer_y_actualizar(estado, "En realidad es un Honda Civic 2019")
        assert estado.marca == "Honda"
        assert estado.modelo == "Civic"
        assert estado.anio == "2019"

    @pytest.mark.asyncio
    async def test_multiturno_e2e_orquestador(self):
        """Flujo multiturno con OrquestadorConversacion verificando memoria y retención vehicular."""
        repo = InMemoryConversationRepository()
        orquestador = OrquestadorConversacion(repositorio=repo)
        gestor = GestorDiagnostico()
        sesion_id = "test_e2e_secundario_flow"

        # Turno 1: Reporte del vehículo y síntoma inicial
        res1 = await orquestador.procesar_turno(
            sesion_id,
            "Tengo un Nissan Tiida 2015 gasolina que pierde potencia al acelerar en pendiente.",
            gestor,
        )
        assert res1 is not None

        estado1 = await repo.get_session(sesion_id)
        assert estado1.marca == "Nissan"
        assert estado1.modelo == "Tiida"
        assert estado1.anio == "2015"
        assert len(estado1.historial_mensajes_usuario) == 1

        # Turno 2: Mención de otro vehículo del cliente + síntoma adicional
        res2 = await orquestador.procesar_turno(
            sesion_id,
            "El cliente mencionó que su otro auto es un Ford, pero estamos revisando este y además bota humo negro.",
            gestor,
        )
        assert res2 is not None

        # Verificar estado tras turno 2: Nissan Tiida retenido intacto sin sobreescritura
        estado2 = await repo.get_session(sesion_id)
        assert estado2.marca == "Nissan", "La marca activa debe ser Nissan"
        assert estado2.modelo == "Tiida", "El modelo activo debe ser Tiida"
        assert estado2.anio == "2015", "El año debe ser 2015"
        assert "vehiculo_mencionado_ford" in estado2.hechos
        assert estado2.hechos["vehiculo_mencionado_ford"].categoria == "antecedente"
        assert len(estado2.historial_mensajes_usuario) == 2

        # Turno 3: Consulta técnica o medición
        res3 = await orquestador.procesar_turno(
            sesion_id,
            "La presión en rampa me da 45 psi, ¿está dentro de rango?",
            gestor,
        )
        assert res3 is not None
        estado3 = await repo.get_session(sesion_id)
        assert estado3.marca == "Nissan"
        assert estado3.modelo == "Tiida"
        assert "medicion_presion_combustible" in estado3.hechos or "presion" in str(estado3.hechos)
