import { ShieldAlert } from 'lucide-react';
import { Button } from '../../../common/Button';

interface ConfirmacionOficialModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  fase: 'Pre-test' | 'Post-test' | 'Piloto';
  guardando: boolean;
}

export const ConfirmacionOficialModal: React.FC<ConfirmacionOficialModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  fase,
  guardando,
}) => {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.75)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10000,
        padding: '16px',
      }}
    >
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          width: '100%',
          maxWidth: '480px',
          padding: '24px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              backgroundColor: '#fef2f2',
              padding: '10px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#dc2626',
            }}
          >
            <ShieldAlert size={26} />
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '17px', fontWeight: 800, color: '#0f172a' }}>
              Confirmación de Registro Oficial
            </h3>
            <span style={{ fontSize: '12px', color: '#64748b' }}>Muestra Oficial de Tesis (N=60)</span>
          </div>
        </div>

        <div
          style={{
            backgroundColor: '#fff7ed',
            border: '1px solid #fed7aa',
            borderRadius: '8px',
            padding: '12px 14px',
            fontSize: '13px',
            color: '#9a3412',
            lineHeight: 1.45,
          }}
        >
          <strong>Este registro formará parte de la muestra oficial de la tesis.</strong>
          <p style={{ margin: '6px 0 0 0', fontSize: '12px', color: '#c2410c' }}>
            Una vez verificado, este caso será computado formalmente en el contraste estadístico oficial de la investigación.
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '10px',
            backgroundColor: '#f8fafc',
            padding: '12px',
            borderRadius: '8px',
            border: '1px solid #e2e8f0',
            fontSize: '12.5px',
          }}
        >
          <div>
            <span style={{ color: '#64748b', fontSize: '11px', display: 'block' }}>Fase Metodológica:</span>
            <strong style={{ color: '#0f172a' }}>{fase === 'Pre-test' ? 'PRETEST' : 'POSTTEST'}</strong>
          </div>
          <div>
            <span style={{ color: '#64748b', fontSize: '11px', display: 'block' }}>Entorno Destino:</span>
            <strong style={{ color: '#dc2626' }}>OFICIAL ({fase === 'Pre-test' ? 'THESIS_PRETEST' : 'THESIS_POSTTEST'})</strong>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '4px' }}>
          <Button type="button" variant="secondary" onClick={onClose} disabled={guardando}>
            Volver a revisar
          </Button>
          <Button
            type="button"
            variant="primary"
            onClick={onConfirm}
            disabled={guardando}
            style={{ backgroundColor: '#dc2626', borderColor: '#b91c1c' }}
          >
            {guardando ? 'Guardando...' : 'Confirmar e Insertar en Muestra'}
          </Button>
        </div>
      </div>
    </div>
  );
};
