import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useDownloadStore } from '../../store/downloadStore';
import styles from './Header.module.css';

export const Header: React.FC = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const activeCount = useDownloadStore((s) =>
        s.tasks.filter((t) => t.status === 'queued' || t.status === 'processing').length,
    );

    return (
        <header className={styles.header}>
            <div className={styles.container}>
                <div className={styles.logo}>
                    🌾 SR Agro Vision
                </div>

                <div className={styles.actions}>
                    {activeCount > 0 && (
                        <button
                            className={styles.downloadIndicator}
                            onClick={() => navigate('/satellite')}
                            title={`${activeCount} descarga${activeCount > 1 ? 's' : ''} en curso`}
                        >
                            <span className={styles.downloadIcon}>⏬</span>
                            <span className={styles.downloadBadge}>{activeCount}</span>
                        </button>
                    )}
                    {user && (
                        <>
                            <span className={styles.userName}>{user.email}</span>
                            <button onClick={logout} className={styles.logoutButton}>
                                Salir
                            </button>
                        </>
                    )}
                </div>
            </div>
        </header>
    );
};
