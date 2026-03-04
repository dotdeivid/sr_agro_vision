import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { projectsApi } from '../api/projects';
import type { Project } from '../api/projects';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { useToastStore } from '../store/toastStore';
import styles from './ProjectsPage.module.css';

export const ProjectsPage: React.FC = () => {
    const navigate = useNavigate();
    const toast = useToastStore();
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Create form
    const [showForm, setShowForm] = useState(false);
    const [newName, setNewName] = useState('');
    const [newDesc, setNewDesc] = useState('');
    const [creating, setCreating] = useState(false);

    useEffect(() => {
        fetchProjects();
    }, []);

    const fetchProjects = async () => {
        try {
            setLoading(true);
            const data = await projectsApi.list();
            setProjects(data);
        } catch {
            setError('Error al cargar los proyectos');
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newName.trim()) return;
        try {
            setCreating(true);
            const created = await projectsApi.create({
                name: newName.trim(),
                description: newDesc.trim(),
            });
            setProjects(prev => [created, ...prev]);
            setNewName('');
            setNewDesc('');
            setShowForm(false);
            toast.success('Proyecto creado correctamente');
        } catch (err: any) {
            const msg = err?.response?.data?.detail || 'Error al crear proyecto';
            toast.error(msg);
        } finally {
            setCreating(false);
        }
    };

    const handleDelete = async (id: string, name: string) => {
        if (!window.confirm(`¿Eliminar el proyecto "${name}" y todas sus imágenes?`)) return;
        try {
            await projectsApi.delete(id);
            setProjects(prev => prev.filter(p => p.id !== id));
            toast.success('Proyecto eliminado');
        } catch (err: any) {
            const msg = err?.response?.data?.detail || 'Error al eliminar proyecto';
            toast.error(msg);
        }
    };

    const formatDate = (dateStr: string) => {
        if (!dateStr) return '—';
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return '—';
        return d.toLocaleDateString('es-ES', {
            day: '2-digit', month: 'short', year: 'numeric',
        });
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div>
                    <h1 className={styles.title}>Proyectos</h1>
                    <p className={styles.subtitle}>
                        {loading ? 'Cargando…' : `${projects.length} proyecto${projects.length !== 1 ? 's' : ''}`}
                    </p>
                </div>
                <Button onClick={() => setShowForm(!showForm)} size="sm">
                    {showForm ? 'Cancelar' : 'Nuevo Proyecto'}
                </Button>
            </div>

            {error && <div className={styles.error}>{error}</div>}

            {/* Create form */}
            {showForm && (
                <Card className={styles.formCard}>
                    <form onSubmit={handleCreate} className={styles.form}>
                        <div className={styles.formGroup}>
                            <label htmlFor="projectName">Nombre</label>
                            <input
                                id="projectName"
                                type="text"
                                value={newName}
                                onChange={e => setNewName(e.target.value)}
                                placeholder="Ej: Cultivo Soja 2024"
                                required
                                autoFocus
                            />
                        </div>
                        <div className={styles.formGroup}>
                            <label htmlFor="projectDesc">Descripción (opcional)</label>
                            <input
                                id="projectDesc"
                                type="text"
                                value={newDesc}
                                onChange={e => setNewDesc(e.target.value)}
                                placeholder="Ej: Monitoreo de campo norte"
                            />
                        </div>
                        <Button type="submit" disabled={creating || !newName.trim()}>
                            {creating ? 'Creando…' : 'Crear Proyecto'}
                        </Button>
                    </form>
                </Card>
            )}

            {/* Empty state */}
            {!loading && projects.length === 0 && (
                <div className={styles.empty}>
                    <div className={styles.emptyIcon}>📁</div>
                    <p>No tenés proyectos aún</p>
                    <Button onClick={() => setShowForm(true)}>Crear Proyecto</Button>
                </div>
            )}

            {/* Project cards */}
            <div className={styles.grid}>
                {projects.map(project => (
                    <Card key={project.id} className={styles.card}>
                        <div
                            className={styles.cardBody}
                            onClick={() => navigate(`/projects/${project.id}`)}
                        >
                            <div className={styles.cardIcon}>📁</div>
                            <h3 className={styles.cardTitle}>{project.name}</h3>
                            {project.description && (
                                <p className={styles.cardDesc}>{project.description}</p>
                            )}
                            <div className={styles.cardMeta}>
                                <span>{project.image_count} imagen{project.image_count !== 1 ? 'es' : ''}</span>
                                <span>{formatDate(project.created_at)}</span>
                            </div>
                        </div>
                        {project.name !== 'default' && (
                            <div className={styles.cardActions}>
                                <Button
                                    size="sm"
                                    variant="danger"
                                    onClick={() => handleDelete(project.id, project.name)}
                                >
                                    Eliminar
                                </Button>
                            </div>
                        )}
                    </Card>
                ))}
            </div>
        </div>
    );
};
