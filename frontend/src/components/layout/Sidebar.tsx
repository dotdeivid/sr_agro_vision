import React from 'react';
import { NavLink } from 'react-router-dom';
import styles from './Sidebar.module.css';

export const Sidebar: React.FC = () => {
    return (
        <aside className={styles.sidebar}>
            <nav className={styles.nav}>
                <NavLink
                    to="/dashboard"
                    className={({ isActive }) =>
                        isActive ? `${styles.navItem} ${styles.active}` : styles.navItem
                    }
                >
                    📊 Dashboard
                </NavLink>

                <NavLink
                    to="/upload"
                    className={({ isActive }) =>
                        isActive ? `${styles.navItem} ${styles.active}` : styles.navItem
                    }
                >
                    📤 Subir Imagen
                </NavLink>

                <NavLink
                    to="/satellite"
                    className={({ isActive }) =>
                        isActive ? `${styles.navItem} ${styles.active}` : styles.navItem
                    }
                >
                    🛰️ Satélite
                </NavLink>

                <NavLink
                    to="/my-images"
                    className={({ isActive }) =>
                        isActive ? `${styles.navItem} ${styles.active}` : styles.navItem
                    }
                >
                    🖼️ Mis Imágenes
                </NavLink>

                <NavLink
                    to="/projects"
                    className={({ isActive }) =>
                        isActive ? `${styles.navItem} ${styles.active}` : styles.navItem
                    }
                >
                    📁 Proyectos
                </NavLink>

            </nav>
        </aside>
    );
};
