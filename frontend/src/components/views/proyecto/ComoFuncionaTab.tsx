import React, { useState } from 'react';
import {
  MessageSquare,
  Server,
  Cpu,
  BookOpen,
  Sparkles,
  CheckCircle2,
  Users,
  Car,
  Terminal,
} from 'lucide-react';
import { Card } from '../../common/Card';

export const ComoFuncionaTab: React.FC = () => {
  const [etapaActiva, setEtapaActiva] = useState<number>(1);

  const etapasFlujo = [
    {
      paso: 1,
      titulo: '1. Mensaje en WhatsApp',
      icono: <MessageSquare size={18} color="#25D366" />,
      subtitulo: 'El cliente o mecánico escribe',
      descripcion:
        'La consulta ingresa mediante la API de WhatsApp (Meta Cloud API o Twilio). El webhook firmado por HMAC recibe el payload JSON y valida la identidad del remitente.',
      detalleTecnico: 'POST /api/v1/webhook/whatsapp (Validación de firma X-Hub-Signature-256 + Rate Limiting)',
      color: '#25D366',
    },
    {
      paso: 2,
      titulo: '2. Backend & Orquestación',
      icono: <Server size={18} color="#3b82f6" />,
      subtitulo: 'FastAPI + Normalización',
      descripcion:
        'FastAPI procesa la sesión, verifica el rol (Cliente vs Mecánico autorizado) y extrae los parámetros del vehículo (marca, modelo, año, motor, síntoma). El texto se normaliza y pasa por el vectorizador TF-IDF.',
      detalleTecnico: 'Extracción regex/heurística de placa y parámetros + Normalización n-gramas (1-2) con scikit-learn',
      color: '#3b82f6',
    },
    {
      paso: 3,
      titulo: '3. Clasificación con ML',
      icono: <Cpu size={18} color="#8b5cf6" />,
      subtitulo: 'Linear SVM Calibrado',
      descripcion:
        'El clasificador supervisado Linear SVM predice las 3 causas mecánicas más probables con su porcentaje de probabilidad calibrada en solo ~12 milisegundos.',
      detalleTecnico: 'CalibratedClassifierCV(LinearSVC) sobre 48 clases de fallas vehiculares con calibración Sigmoide/Isotónica',
      color: '#8b5cf6',
    },
    {
      paso: 4,
      titulo: '4. Recuperación RAG',
      icono: <BookOpen size={18} color="#06b6d4" />,
      subtitulo: 'Búsqueda en corpus preliminar',
      descripcion:
        'El motor RAG consulta el índice FAISS para recuperar el fragmento técnico preliminar más relacionado. La evidencia es referencial y requiere validación con documentación compatible y revisión mecánica.',
      detalleTecnico: 'FAISS IndexFlatIP sobre un corpus técnico preliminar de 64 procedimientos referenciales',
      color: '#06b6d4',
    },
    {
      paso: 5,
      titulo: '5. Síntesis Inteligente LLM',
      icono: <Sparkles size={18} color="#f97316" />,
      subtitulo: 'Gemini 2.5 Flash / Modo Degradado',
      descripcion:
        'Gemini redacta una respuesta estructurada, concisa y profesional combinando las hipótesis del ML y la evidencia del manual. Si hay saturación de cuota, el modo degradado responde con el manual sin fallar.',
      detalleTecnico: 'Worker asíncrono con cola, control de cuota y fallback local cuando la API externa falla',
      color: '#f97316',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
      {/* Breve descripción */}
      <p style={{ fontSize: '12px', color: 'var(--text-secondary)', margin: '0 0 2px 0' }}>
        Diagnóstico mediante WhatsApp, Machine Learning, RAG y Gemini.
      </p>

      {/* Interactive Step-by-Step Flow Pipeline */}
      <Card style={{ padding: '18px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
          <h4 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
            Flujo de Procesamiento de una Consulta
          </h4>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Haz clic en cada etapa para ver su funcionamiento técnico
          </span>
        </div>

        {/* Step Buttons Row */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
            gap: '8px',
            marginBottom: '16px',
          }}
        >
          {etapasFlujo.map((etapa) => {
            const esActivo = etapaActiva === etapa.paso;
            return (
              <button
                key={etapa.paso}
                type="button"
                onClick={() => setEtapaActiva(etapa.paso)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 12px',
                  backgroundColor: esActivo ? etapa.color : 'var(--bg-subtle)',
                  color: esActivo ? '#ffffff' : 'var(--text-main)',
                  border: esActivo ? `1px solid ${etapa.color}` : '1px solid var(--border-color)',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s ease',
                  boxShadow: esActivo ? '0 2px 6px rgba(0,0,0,0.12)' : 'none',
                }}
              >
                <span
                  style={{
                    backgroundColor: esActivo ? 'rgba(255,255,255,0.25)' : '#ffffff',
                    padding: '6px',
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {etapa.icono}
                </span>
                <div>
                  <div style={{ fontSize: '11px', fontWeight: 700 }}>{etapa.titulo}</div>
                  <div
                    style={{
                      fontSize: '10px',
                      opacity: esActivo ? 0.9 : 0.65,
                      fontWeight: 500,
                    }}
                  >
                    {etapa.subtitulo}
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Active Stage Technical Detail Card */}
        {(() => {
          const actual = etapasFlujo.find((e) => e.paso === etapaActiva) || etapasFlujo[0];
          return (
            <div
              style={{
                padding: '16px',
                backgroundColor: 'var(--bg-subtle)',
                borderRadius: '8px',
                borderLeft: `4px solid ${actual.color}`,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', fontWeight: 800, color: actual.color }}>
                  {actual.titulo}: {actual.subtitulo}
                </span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-main)', margin: '0 0 10px 0', lineHeight: 1.5 }}>
                {actual.descripcion}
              </p>
              <div
                style={{
                  padding: '8px 12px',
                  backgroundColor: '#1e293b',
                  borderRadius: '6px',
                  color: '#38bdf8',
                  fontSize: '11px',
                  fontFamily: 'monospace',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <Terminal size={13} color="#94a3b8" />
                <span>{actual.detalleTecnico}</span>
              </div>
            </div>
          );
        })()}
      </Card>

      {/* Grid: 3 User Roles & Data Requirements */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
        {/* Roles Differentiation Card */}
        <Card style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Users size={16} color="var(--primary)" />
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
              Diferenciación de Roles en el Sistema
            </h4>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div
              style={{
                padding: '10px',
                backgroundColor: 'var(--bg-subtle)',
                borderRadius: '8px',
                fontSize: '12px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <span style={{ fontWeight: 700, color: '#059669' }}>👤 Cliente (WhatsApp)</span>
                <span style={{ fontSize: '10px', backgroundColor: '#dcfce7', color: '#166534', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>
                  Acceso Público
                </span>
              </div>
              <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '11px', lineHeight: 1.4 }}>
                Consulta orientación rápida de fallas para saber si es seguro conducir, solicita citas de taller y recibe información del estado de su vehículo. No requiere credenciales.
              </p>
            </div>

            <div
              style={{
                padding: '10px',
                backgroundColor: 'var(--bg-subtle)',
                borderRadius: '8px',
                fontSize: '12px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <span style={{ fontWeight: 700, color: '#2563eb' }}>👨‍🔧 Mecánico de Taller (WhatsApp)</span>
                <span style={{ fontSize: '10px', backgroundColor: '#dbeafe', color: '#1e40af', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>
                  Previa Aprobación
                </span>
              </div>
              <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '11px', lineHeight: 1.4 }}>
                Solicita acceso mediante la Opción 4 de WhatsApp. Una vez autorizado por el administrador, accede a orientación técnica, hipótesis ML y fragmentos referenciales del corpus RAG, siempre sujetos a comprobación física.
              </p>
            </div>

            <div
              style={{
                padding: '10px',
                backgroundColor: 'var(--bg-subtle)',
                borderRadius: '8px',
                fontSize: '12px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <span style={{ fontWeight: 700, color: '#7c3aed' }}>👑 Administrador (Panel Web)</span>
                <span style={{ fontSize: '10px', backgroundColor: '#ede9fe', color: '#5b21b6', padding: '1px 6px', borderRadius: '4px', fontWeight: 700 }}>
                  Acceso Web Seguro
                </span>
              </div>
              <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '11px', lineHeight: 1.4 }}>
                Único usuario con acceso al panel web. Aprueba o bloquea mecánicos, audita el historial de diagnósticos, valida confirmaciones técnicas en taller y consulta métricas de tesis e investigación.
              </p>
            </div>
          </div>
        </Card>

        {/* Vehicle Data Inputs & Generation Process */}
        <Card style={{ padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Car size={16} color="var(--primary)" />
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
              Datos del Vehículo y Generación de Respuesta
            </h4>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              Para garantizar que el <strong>PRDC (Porcentaje de Registros Diagnósticos Completos)</strong> alcance el 100%, el bot recopila de forma estructurada los 8 campos reglamentarios:
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '6px',
                fontSize: '11px',
              }}
            >
              {[
                '1. Placa del Vehículo',
                '2. Marca y Modelo',
                '3. Año de Fabricación',
                '4. Tipo / Cilindrada Motor',
                '5. Síntoma o Ruido Percibido',
                '6. Condiciones de Falla',
                '7. Falla Predicha (ML Top 3)',
                '8. Procedimiento Técnico (RAG)',
              ].map((campo, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '6px 8px',
                    backgroundColor: 'var(--bg-subtle)',
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <CheckCircle2 size={12} color="#10b981" />
                  <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{campo}</span>
                </div>
              ))}
            </div>

            <div
              style={{
                marginTop: '6px',
                padding: '10px 12px',
                backgroundColor: '#fffbeb',
                border: '1px solid #fde68a',
                borderRadius: '8px',
                fontSize: '11px',
                color: '#92400e',
              }}
            >
              🛡️ <strong>Garantía de Resiliencia:</strong> Si la conexión a la API de Gemini tiene latencia alta o agota su cuota de tokens, el bot entrega inmediatamente el diagnóstico con el <strong>clasificador ML + el procedimiento RAG</strong> sin interrumpir el trabajo en el taller.
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
