import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from './Button';
import styles from './ErrorBoundary.module.css';

interface Props {
    children: ReactNode;
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
        console.error('Uncaught error:', error, errorInfo);
    }

    private handleReset = () => {
        this.setState({ hasError: false, error: null });
        window.location.href = '/';
    };

    public render() {
        if (this.state.hasError) {
            return (
                <div className={styles.container}>
                    <div className={styles.content}>
                        <div className={styles.icon}>⚠️</div>
                        <h1 className={styles.title}>Oops! Algo salió mal</h1>
                        <p className={styles.message}>
                            Ha ocurrido un error inesperado. Por favor intenta de nuevo.
                        </p>
                        {this.state.error && (
                            <details className={styles.details}>
                                <summary>Detalles del error</summary>
                                <pre className={styles.error}>{this.state.error.toString()}</pre>
                            </details>
                        )}
                        <Button onClick={this.handleReset} size="lg">
                            Volver al Inicio
                        </Button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
