import React from 'react';
import { useAuth } from '../../hooks/useAuth';
import styles from './Header.module.css';

export const Header: React.FC = () => {
    const { user, logout } = useAuth();

    return (
        <header className={styles.header}>
            <div className={styles.container}>
                <div className={styles.logo}>
                    🌾 SR Agro Vision
                </div>

                <div className={styles.actions}>
                    {user && (
                        <>
                            <span className={styles.userName}>{user.email}</span>
                            <button onClick={logout} className={styles.logoutButton}>
                                Cerrar Sesión
                            </button>
                        </>
                    )}
                </div>
            </div>
        </header>
    );
};
