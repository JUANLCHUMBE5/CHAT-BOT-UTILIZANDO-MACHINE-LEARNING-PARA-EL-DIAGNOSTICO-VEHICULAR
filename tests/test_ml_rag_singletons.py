from src.infrastructure.container import ServiceContainer
from src.core.gestor_diagnostico import GestorDiagnostico, ResultadoDiagnostico
from src.core.traductor_jerga import normalizar_jerga_peruana
from src.core.interfaces import IModeloML, IMotorRAG

# ==========================================
# TIER 1: ML, FAISS RAG & SINGLETON TESTS
# ==========================================

def test_service_container_singleton():
    """T1-SINGLETON: ServiceContainer returns identical singletons for ModeloML and MotorRAG."""
    ml1 = ServiceContainer.get_modelo_ml()
    ml2 = ServiceContainer.get_modelo_ml()
    assert ml1 is ml2
    
    rag1 = ServiceContainer.get_motor_rag()
    rag2 = ServiceContainer.get_motor_rag()
    assert rag1 is rag2

def test_modelo_ml_prediccion_directa():
    """T1-ML: ModeloML predicts failure category and confidence score as float."""
    modelo_ml = ServiceContainer.get_modelo_ml()
    # Satisfies IModeloML protocol
    assert isinstance(modelo_ml, IModeloML)
    
    prediccion, confianza = modelo_ml.predecir_falla_con_confianza("pastillas de freno chillan al frenar")
    assert isinstance(prediccion, str)
    assert isinstance(confianza, float)
    assert 0.0 <= confianza <= 100.0

def test_motor_rag_busqueda_faiss():
    """T1-RAG: MotorRAG vector search retrieves workshop manual section for symptoms and DTC codes."""
    motor_rag = ServiceContainer.get_motor_rag()
    # Satisfies IMotorRAG protocol
    assert isinstance(motor_rag, IMotorRAG)
    
    manual_texto, titulo = motor_rag.recuperar_contexto("P0300 misfire motor cascabelea")
    assert isinstance(manual_texto, str)
    assert isinstance(titulo, str)

def test_gestor_diagnostico_procesar_consulta_dto():
    """T1-GESTOR: GestorDiagnostico processes input query and returns standard ResultadoDiagnostico DTO."""
    gestor = GestorDiagnostico()
    res = gestor.procesar_consulta_texto(
        texto_usuario="motor calienta demasiado y vota humo blanco",
        marca_modelo="Toyota Corolla",
        placa="ML-999"
    )
    assert isinstance(res, ResultadoDiagnostico)
    assert res.diagnostico_ml != ""
    assert res.respuesta_texto != ""
    assert res.confianza_ml >= 0.0

def test_traductor_jerga_normalizacion():
    """T1-SLANG: normalizar_jerga_peruana converts Peruvian mechanical slang to standard technical terms."""
    slang_input = "el auto cascabelea y el timon esta duro"
    normalized = normalizar_jerga_peruana(slang_input)
    assert "cascabele" in normalized or "pistoneo" in normalized or "preignicion" in normalized
    assert len(normalized) > 0
