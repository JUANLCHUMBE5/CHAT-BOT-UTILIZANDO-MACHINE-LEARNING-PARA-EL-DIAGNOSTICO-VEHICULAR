import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            padding: '24px',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            margin: '16px 0',
            textAlign: 'center',
          }}
        >
          <h4 style={{ color: '#991b1b', margin: '0 0 8px 0', fontSize: '15px', fontWeight: 700 }}>
            {this.props.fallbackTitle || 'Hubo un problema al renderizar esta sección'}
          </h4>
          <p style={{ color: '#7f1d1d', fontSize: '12px', margin: '0 0 14px 0' }}>
            {this.state.error?.message || 'Error inesperado del navegador'}
          </p>
          <button
            type="button"
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              padding: '6px 14px',
              backgroundColor: '#dc2626',
              color: '#ffffff',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 600,
              cursor: 'pointer',
              fontSize: '12px',
            }}
          >
            Reintentar vista
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
