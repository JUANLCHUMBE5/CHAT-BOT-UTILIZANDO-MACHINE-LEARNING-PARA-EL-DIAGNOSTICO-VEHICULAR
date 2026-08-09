import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  icon?: React.ReactNode;
  error?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  icon,
  error,
  className = '',
  style,
  ...props
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%' }}>
      {label && (
        <label style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-main)' }}>
          {label}
        </label>
      )}
      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        {icon && (
          <span
            style={{
              position: 'absolute',
              left: '12px',
              color: 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              pointerEvents: 'none',
            }}
          >
            {icon}
          </span>
        )}
        <input
          style={{
            width: '100%',
            padding: icon ? '9px 12px 9px 38px' : '9px 12px',
            fontSize: '14px',
            borderRadius: '8px',
            border: error ? '1px solid #be123c' : '1px solid var(--border-color)',
            backgroundColor: '#ffffff',
            color: 'var(--text-main)',
            outline: 'none',
            transition: 'border-color 0.15s ease, box-shadow 0.15s ease',
            ...style,
          }}
          className={className}
          onFocus={(e) => {
            e.currentTarget.style.borderColor = 'var(--primary)';
            e.currentTarget.style.boxShadow = '0 0 0 3px var(--primary-focus)';
          }}
          onBlur={(e) => {
            e.currentTarget.style.borderColor = error ? '#be123c' : 'var(--border-color)';
            e.currentTarget.style.boxShadow = 'none';
          }}
          {...props}
        />
      </div>
      {error && <span style={{ fontSize: '12px', color: '#be123c' }}>{error}</span>}
    </div>
  );
};
