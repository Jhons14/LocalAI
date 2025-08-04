import {
  Component,
  type ErrorInfo,
  type ReactNode,
  type ComponentType,
} from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className='flex flex-col items-center justify-center p-8 text-center'>
          <div className='bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4'>
            <h2 className='text-lg font-semibold mb-2'>Something went wrong</h2>
            <p className='text-sm'>
              An unexpected error occurred. Please refresh the page and try
              again.
            </p>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className='mt-2 text-left'>
                <summary className='cursor-pointer'>Error details</summary>
                <pre className='mt-2 text-xs overflow-auto'>
                  {this.state.error.stack}
                </pre>
              </details>
            )}
          </div>
          <button
            onClick={() => this.setState({ hasError: false, error: undefined })}
            className='px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600'
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook-based error boundary for functional components
export const withErrorBoundary = <P extends object>(
  Component: ComponentType<P>,
  fallback?: ReactNode
) => {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary fallback={fallback}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${
    Component.displayName || Component.name
  })`;

  return WrappedComponent;
};
