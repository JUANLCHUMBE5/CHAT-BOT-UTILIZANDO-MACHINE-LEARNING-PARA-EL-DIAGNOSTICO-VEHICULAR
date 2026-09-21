"""
Schema RAG V2: Especificación estricta de estructura y metadatos para el RAG Candidato V1.
Cumple con las Secciones 14 y 15 del mandato técnico.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class EvidenceLevel(str, Enum):
    VERIFIED_SOURCE = "VERIFIED_SOURCE"
    PARTIAL_SOURCE = "PARTIAL_SOURCE"
    OEM_REQUIRED = "OEM_REQUIRED"
    PENDING_SOURCE = "PENDING_SOURCE"
    TRANSVERSAL = "TRANSVERSAL"
    LEGACY_BASELINE = "LEGACY_BASELINE"

class KnowledgeType(str, Enum):
    PROCEDURAL = "PROCEDURAL"
    TRANSVERSAL = "TRANSVERSAL"
    COMPONENT = "COMPONENT"
    SUBSYSTEM = "SUBSYSTEM"
    SYSTEM = "SYSTEM"
    SAFETY_NOTICE = "SAFETY_NOTICE"
    STUB = "STUB"

class ProceduralChunkV2(BaseModel):
    doc_id: str
    chunk_id: str
    position: int
    source_id: str
    source_type: str = "WORKSHOP_MANUAL"
    source_title: str
    procedure_title: str
    titulo: Optional[str] = None
    source_author_org: Optional[str] = None
    source_url: Optional[str] = None
    source_version: Optional[str] = None
    source_date: Optional[str] = None
    source_hash: Optional[str] = None
    archivo_fuente: Optional[str] = None

    system: str  # 7 macro-sistemas
    sistema: Optional[str] = None
    subsystem: Optional[str] = None
    component: Optional[str] = None

    knowledge_type: KnowledgeType = KnowledgeType.PROCEDURAL

    primary_fault_class: Optional[str] = None  # Exact C1 class or None if transversal
    falla: Optional[str] = None
    related_fault_classes: List[str] = Field(default_factory=list)

    symptoms: List[str] = Field(default_factory=list)
    customer_language: List[str] = Field(default_factory=list)
    mechanic_language: List[str] = Field(default_factory=list)

    dtc_codes: List[str] = Field(default_factory=list)

    discriminating_questions: List[str] = Field(default_factory=list)

    test_description: Optional[str] = None
    tool: Optional[str] = None
    preconditions: Optional[str] = None

    expected_quantity: Optional[str] = None
    units: Optional[str] = None

    possible_results: List[str] = Field(default_factory=list)
    interpretation: Optional[str] = None

    reinforces: List[str] = Field(default_factory=list)
    weakens: List[str] = Field(default_factory=list)
    discards: List[str] = Field(default_factory=list)

    next_action: Optional[str] = None

    vehicle_scope: str = "UNIVERSAL"
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[str] = None
    engine: Optional[str] = None
    platform: Optional[str] = None

    requires_oem_spec: bool = False

    safety_level: str = "STANDARD"  # STANDARD, CAUTION, HIGH_RISK, CRITICAL
    safety_warning: Optional[str] = None

    evidence_level: EvidenceLevel = EvidenceLevel.LEGACY_BASELINE
    candidate_version: str = "RAG_CANDIDATO_V1"
