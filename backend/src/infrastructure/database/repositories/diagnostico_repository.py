"""Repositorio para la persistencia de diagnósticos vehiculares e hipótesis generadas."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.database.models.diagnostics import Diagnostico, HipotesisDiagnostico


class DiagnosticoRepository:
    """Acceso a datos asíncrono para diagnósticos de ML/RAG e hipótesis técnicas."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def crear_diagnostico(
        self,
        taller_id: uuid.UUID,
        mecanico_id: uuid.UUID,
        sintoma_original: str,
        fuente: str = "hibrido",
        modo_diagnostico: str = "completo_ml_rag_llm",
        conversacion_id: Optional[uuid.UUID] = None,
        vehiculo_id: Optional[uuid.UUID] = None,
        sintoma_normalizado: Optional[str] = None,
        falla_predicha: Optional[str] = None,
        confianza: Optional[float | Decimal] = None,
        similitud_rag: Optional[float | Decimal] = None,
        estado: str = "generado",
        duracion_ms: Optional[int] = None,
        conclusion_mecanico: Optional[str] = None,
        sintesis_llm: Optional[str] = None,
        diagnostico_id: Optional[uuid.UUID] = None,
        version_modelo_ml: Optional[str] = None,
        version_corpus_rag: Optional[str] = None,
        trazabilidad: Optional[dict[str, Any]] = None,
    ) -> Diagnostico:
        """Persiste un nuevo diagnóstico vehicular con sus métricas y fuentes."""
        conf_decimal = Decimal(str(round(float(confianza), 4))) if confianza is not None else None
        similitud_decimal = (
            Decimal(str(round(float(similitud_rag), 4)))
            if similitud_rag is not None
            else None
        )
        diag = Diagnostico(
            id=diagnostico_id or uuid.uuid4(),
            taller_id=taller_id,
            mecanico_id=mecanico_id,
            vehiculo_id=vehiculo_id,
            conversacion_id=conversacion_id,
            sintoma_original=sintoma_original,
            sintoma_normalizado=sintoma_normalizado,
            falla_predicha=falla_predicha,
            confianza=conf_decimal,
            similitud_rag=similitud_decimal,
            fuente=fuente,
            modo_diagnostico=modo_diagnostico,
            estado=estado,
            duracion_ms=duracion_ms,
            conclusion_mecanico=conclusion_mecanico,
            sintesis_llm=sintesis_llm,
            version_modelo_ml=version_modelo_ml,
            version_corpus_rag=version_corpus_rag,
            trazabilidad=trazabilidad,
        )
        self.session.add(diag)
        await self.session.flush()
        return diag

    async def agregar_hipotesis(
        self,
        diagnostico_id: uuid.UUID,
        orden: int,
        falla_probable: str,
        confianza: Optional[float | Decimal] = None,
        evidencia: Optional[str] = None,
        prueba_recomendada: Optional[str] = None,
        resultado: str = "pendiente",
        hipotesis_id: Optional[uuid.UUID] = None,
    ) -> HipotesisDiagnostico:
        """Agrega una hipótesis técnica priorizada al diagnóstico."""
        conf_decimal = Decimal(str(round(float(confianza), 4))) if confianza is not None else None
        hipotesis = HipotesisDiagnostico(
            id=hipotesis_id or uuid.uuid4(),
            diagnostico_id=diagnostico_id,
            orden=orden,
            falla_probable=falla_probable,
            confianza=conf_decimal,
            evidencia=evidencia,
            prueba_recomendada=prueba_recomendada,
            resultado=resultado,
        )
        self.session.add(hipotesis)
        await self.session.flush()
        return hipotesis

    async def obtener_por_id(self, diagnostico_id: uuid.UUID) -> Optional[Diagnostico]:
        """Obtiene un diagnóstico completo con sus hipótesis cargadas."""
        stmt = (
            select(Diagnostico)
            .options(
                selectinload(Diagnostico.hipotesis),
                selectinload(Diagnostico.mecanico),
                selectinload(Diagnostico.vehiculo),
            )
            .where(Diagnostico.id == diagnostico_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def listar_por_taller(
        self,
        taller_id: uuid.UUID,
        busqueda: Optional[str] = None,
        estado: Optional[str] = None,
        modo: Optional[str] = None,
        mecanico_id: Optional[uuid.UUID] = None,
        limite: Optional[int] = 100,
        offset: int = 0,
    ) -> Sequence[Diagnostico]:
        """Lista los diagnósticos realizados en un taller automotriz con opciones de filtrado y paginación."""
        stmt = (
            select(Diagnostico)
            .options(
                selectinload(Diagnostico.mecanico),
                selectinload(Diagnostico.vehiculo),
                selectinload(Diagnostico.hipotesis),
            )
            .where(Diagnostico.taller_id == taller_id)
        )

        if estado and estado != "todos":
            stmt = stmt.where(Diagnostico.estado == estado)

        if modo and modo != "todos":
            stmt = stmt.where(Diagnostico.modo_diagnostico == modo)

        if mecanico_id:
            stmt = stmt.where(Diagnostico.mecanico_id == mecanico_id)

        if busqueda:
            term = f"%{busqueda.strip()}%"
            from src.infrastructure.database.models.catalogs import Usuario
            from src.infrastructure.database.models.diagnostics import Vehiculo
            stmt = stmt.outerjoin(Diagnostico.vehiculo).outerjoin(Diagnostico.mecanico).where(
                (Diagnostico.sintoma_original.ilike(term))
                | (Diagnostico.falla_predicha.ilike(term))
                | (Vehiculo.placa_ultimos4.ilike(term))
                | (Usuario.nombres.ilike(term))
            )

        stmt = stmt.order_by(Diagnostico.creado_en.desc())
        if offset > 0:
            stmt = stmt.offset(offset)
        if limite is not None and limite > 0:
            stmt = stmt.limit(limite)

        result = await self.session.execute(stmt)
        return result.scalars().all()
