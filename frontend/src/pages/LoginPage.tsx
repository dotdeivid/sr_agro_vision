import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { authApi } from '../api/auth';
import { useAuthStore } from '../store/authStore';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Card } from '../components/common/Card';
import styles from './LoginPage.module.css';
import type { LoginRequest } from '../types/api';

export const LoginPage: React.FC = () => {
    const navigate = useNavigate();
    const { setAuth } = useAuthStore();
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { register, handleSubmit, formState: { errors } } = useForm<LoginRequest>();

    const onSubmit = async (data: LoginRequest) => {
        try {
            setLoading(true);
            setError('');

            const authResponse = await authApi.login(data);
            const user = await authApi.getMe();

            setAuth(user, authResponse.access_token);
            navigate('/dashboard');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Error al iniciar sesión');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <Card className={styles.card}>
                <div className={styles.header}>
                    <h1 className={styles.logo}>🌾 SR Agro Vision</h1>
                    <p className={styles.subtitle}>Agricultura de Precisión con IA</p>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
                    <Input
                        label="Email"
                        type="email"
                        fullWidth
                        placeholder="tu@email.com"
                        error={errors.email?.message}
                        {...register('email', {
                            required: 'Email es requerido',
                            pattern: {
                                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                                message: 'Email inválido'
                            }
                        })}
                    />

                    <Input
                        label="Contraseña"
                        type="password"
                        fullWidth
                        placeholder="••••••••"
                        error={errors.password?.message}
                        {...register('password', {
                            required: 'Contraseña es requerida',
                            minLength: {
                                value: 6,
                                message: 'Mínimo 6 caracteres'
                            }
                        })}
                    />

                    {error && (
                        <div className={styles.error}>{error}</div>
                    )}

                    <Button type="submit" fullWidth loading={loading}>
                        Iniciar Sesión
                    </Button>
                </form>

                <div className={styles.footer}>
                    ¿No tienes cuenta?{' '}
                    <Link to="/register" className={styles.link}>
                        Regístrate aquí
                    </Link>
                </div>
            </Card>
        </div>
    );
};
