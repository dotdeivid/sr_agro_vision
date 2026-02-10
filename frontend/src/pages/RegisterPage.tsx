import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { authApi } from '../api/auth';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { Card } from '../components/common/Card';
import styles from './RegisterPage.module.css';
import type { RegisterRequest } from '../types/api';

interface RegisterFormData extends RegisterRequest {
    confirmPassword: string;
}

export const RegisterPage: React.FC = () => {
    const navigate = useNavigate();
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const { register, handleSubmit, formState: { errors }, watch } = useForm<RegisterFormData>();
    const password = watch('password');

    const onSubmit = async (data: RegisterFormData) => {
        try {
            setLoading(true);
            setError('');

            const { confirmPassword, ...registerData } = data;
            await authApi.register(registerData);

            navigate('/login', { state: { message: 'Cuenta creada exitosamente' } });
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Error al crear la cuenta');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <Card className={styles.card}>
                <div className={styles.header}>
                    <h1 className={styles.logo}>🌾 SR Agro Vision</h1>
                    <p className={styles.subtitle}>Crear Cuenta Nueva</p>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
                    <Input
                        label="Nombre Completo (opcional)"
                        type="text"
                        fullWidth
                        placeholder="Juan Pérez"
                        {...register('full_name')}
                    />

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

                    <Input
                        label="Confirmar Contraseña"
                        type="password"
                        fullWidth
                        placeholder="••••••••"
                        error={errors.confirmPassword?.message}
                        {...register('confirmPassword', {
                            required: 'Confirma tu contraseña',
                            validate: value => value === password || 'Las contraseñas no coinciden'
                        })}
                    />

                    {error && (
                        <div className={styles.error}>{error}</div>
                    )}

                    <Button type="submit" fullWidth loading={loading}>
                        Crear Cuenta
                    </Button>
                </form>

                <div className={styles.footer}>
                    ¿Ya tienes cuenta?{' '}
                    <Link to="/login" className={styles.link}>
                        Inicia sesión aquí
                    </Link>
                </div>
            </Card>
        </div>
    );
};
