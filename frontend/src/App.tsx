import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { UploadPage } from './pages/UploadPage';
import { ProcessPage } from './pages/ProcessPage';
import { ComparisonPage } from './pages/ComparisonPage';
import { SatellitePage } from './pages/SatellitePage';
import { AnalysisPage } from './pages/AnalysisPage';
import { Layout } from './components/layout/Layout';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { useAuthStore } from './store/authStore';

// Protected route component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const isAuthenticated = useAuthStore(state => state.isAuthenticated);

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
};

function App() {
    return (
        <ErrorBoundary>
            <BrowserRouter>
                <Routes>
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />

                    <Route
                        path="/dashboard"
                        element={
                            <ProtectedRoute>
                                <Layout>
                                    <DashboardPage />
                                </Layout>
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/upload"
                        element={
                            <ProtectedRoute>
                                <Layout>
                                    <UploadPage />
                                </Layout>
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/process/:imageId"
                        element={
                            <ProtectedRoute>
                                <Layout>
                                    <ProcessPage />
                                </Layout>
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/comparison/:resultId"
                        element={
                            <ProtectedRoute>
                                <Layout>
                                    <ComparisonPage />
                                </Layout>
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/satellite"
                        element={
                            <ProtectedRoute>
                                <Layout>
                                    <SatellitePage />
                                </Layout>
                            </ProtectedRoute>
                        }
                    />

                    <Route
                        path="/analysis/:imageId"
                        element={
                            <ProtectedRoute>
                                <Layout>
                                    <AnalysisPage />
                                </Layout>
                            </ProtectedRoute>
                        }
                    />

                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                </Routes>
            </BrowserRouter>
        </ErrorBoundary>
    );
}

export default App;
