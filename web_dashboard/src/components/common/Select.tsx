import React from 'react';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: SelectOption[];
  error?: string;
}

export const Select: React.FC<SelectProps> = ({
  label,
  options,
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
      <select
        style={{
          width: '100%',
          padding: '9px 12px',
          fontSize: '14px',
          borderRadius: '8px',
          border: error ? '1px solid #be123c' : '1px solid var(--border-color)',
          backgroundColor: '#ffffff',
          color: 'var(--text-main)',
          outline: 'none',
          cursor: 'pointer',
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
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <span style={{ fontSize: '12px', color: '#be123c' }}>{error}</span>}
    </div>
  );
};
