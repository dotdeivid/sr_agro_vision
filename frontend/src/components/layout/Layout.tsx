import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { ToastContainer } from '../common/Toast';
import { useToast } from '../../hooks/useToast';
import styles from './Layout.module.css';

interface LayoutProps {
    children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
    const { toasts, removeToast } = useToast();

    return (
        <div className={styles.layout}>
            <Header />
            <div className={styles.container}>
                <Sidebar />
                <main className={styles.main}>
                    {children}
                </main>
            </div>
            <ToastContainer toasts={toasts} onClose={removeToast} />
        </div>
    );
};
