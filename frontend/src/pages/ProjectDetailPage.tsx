import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { projectsApi } from '../api/projects';
import { imagesApi } from '../api/images';
import type { Project, ProjectUpdate } from '../api/projects';
import type { ImageMetadata } from '../types/image';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { useToastStore } from '../store/toastStore';
import styles from './ProjectDetailPage.module.css';

export const ProjectDetailPage: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const navigate = useNavigate();
    const toast = useToastStore();

    const [project, setProject] = useState<Project | null>(null);
    const [images, setImages] = useState<ImageMetadata[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Edit state
    const [editing, setEditing] = useState(false);
    const [editName, setEditName] = useState('');
    const [editDesc, setEditDesc] = useState('');
    const [saving, setSaving] = useState(false);

    // Add images picker state
    const [showPicker, setShowPicker] = useState(false);
    const [allImages, setAllImages] = useState<ImageMetadata[]>([]);
    const [loadingPicker, setLoadingPicker] = useState(false);

    useEffect(() => {
        if (!projectId) return;
        fetchProjectData();
    }, [projectId]);

    const fetchProjectData = async () => {
        if (!projectId) return;
        try {
            setLoading(true);
            const [proj, imgs] = await Promise.all([
                projectsApi.getById(projectId),
                projectsApi.getImages(projectId),
            ]);
            setProject(proj);
            setImages(imgs);
            setEditName(proj.name);
            setEditDesc(proj.description || '');
        } catch {
            setError('Error al cargar el proyecto');
        } finally {
            setLoading(false);
        }
    };

    const openPicker = async () => {
        try {
            setLoadingPicker(true);
            const all = await imagesApi.list();
            // Show images NOT in this project
            const otherImages = all.filter(img => img.project_id !== projectId);
            setAllImages(otherImages);
            setShowPicker(true);
        } catch {
            toast.error('Error al cargar imágenes');
        } finally {
            setLoadingPicker(false);
        }
    };

    const handleAddImage = async (imageId: string) => {
        if (!projectId) return;
        try {
            const updated = await imagesApi.moveToProject(imageId, projectId);
            setImages(prev => [...prev, updated]);
            setAllImages(prev => prev.filter(img => img.id !== imageId));
            toast.success('Imagen agregada al proyecto');
        } catch {
            toast.error('Error al agregar imagen');
        }
    };

    const handleSave = async () => {
        if (!projectId || !editName.trim()) return;
        try {
            setSaving(true);
            const updated = await projectsApi.update(projectId, {
                name: editName.trim(),
                description: editDesc.trim(),
            } as ProjectUpdate);
            setProject(updated);
            setEditing(false);
            toast.success('Proyecto actualizado');
        } catch (err: any) {
            const msg = err?.response?.data?.detail || 'Error al actualizar';
            toast.error(msg);
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async () => {
        if (!project || !projectId) return;
        if (!window.confirm(`¿Eliminar "${project.name}" y todas sus imágenes?`)) return;
        try {
            await projectsApi.delete(projectId);
            toast.success('Proyecto eliminado');
            navigate('/projects');
        } catch (err: any) {
            const msg = err?.response?.data?.detail || 'Error al eliminar';
            toast.error(msg);
        }
    };

    const handleDeleteImage = async (imageId: string, filename: string) => {
        if (!window.confirm(`¿Eliminar ${filename}?`)) return;
        try {
            await imagesApi.delete(imageId);
            setImages(prev => prev.filter(img => img.id !== imageId));
            toast.success('Imagen eliminada');
        } catch {
            toast.error('Error al eliminar la imagen');
        }
    };

    const handleRemoveFromProject = async (imageId: string) => {
        // Move image back to "default" project
        if (!projectId) return;
        try {
            // Find the default project — get all projects and find it
            const projects = await projectsApi.list();
            const defaultProject = projects.find(p => p.name === 'default');
            if (!defaultProject) {
                toast.error('No se encontró el proyecto default');
                return;
            }
            await imagesApi.moveToProject(imageId, defaultProject.id);
            setImages(prev => prev.filter(img => img.id !== imageId));
            toast.success('Imagen removida del proyecto');
        } catch {
            toast.error('Error al remover la imagen');
        }
    };

    const formatDate = (dateStr?: string) => {
        if (!dateStr) return '—';
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return '—';
        return d.toLocaleDateString('es-ES', {
            day: '2-digit', month: 'short', year: 'numeric',
        });
    };

    const formatSize = (bytes: number): string => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    };

    if (loading) return <div className={styles.container}><p>Cargando…</p></div>;
    if (error) return <div className={styles.container}><div className={styles.error}>{error}</div></div>;
    if (!project) return null;

    const isDefault = project.name === 'default';

    return (
        <div className={styles.container}>
            {/* Header */}
            <div className={styles.header}>
                <div className={styles.headerLeft}>
                    <button className={styles.back} onClick={() => navigate('/projects')}>
                        ← Proyectos
                    </button>
                    {editing ? (
                        <div className={styles.editForm}>
                            <input
                                type="text"
                                value={editName}
                                onChange={e => setEditName(e.target.value)}
                                className={styles.editInput}
                                autoFocus
                            />
                            <input
                                type="text"
                                value={editDesc}
                                onChange={e => setEditDesc(e.target.value)}
                                className={styles.editInput}
                                placeholder="Descripción"
                            />
                            <div className={styles.editActions}>
                                <Button size="sm" onClick={handleSave} disabled={saving}>
                                    {saving ? 'Guardando…' : 'Guardar'}
                                </Button>
                                <Button size="sm" variant="secondary" onClick={() => setEditing(false)}>
                                    Cancelar
                                </Button>
                            </div>
                        </div>
                    ) : (
                        <>
                            <h1 className={styles.title}>📁 {project.name}</h1>
                            {project.description && (
                                <p className={styles.subtitle}>{project.description}</p>
                            )}
                            <p className={styles.meta}>
                                {images.length} imagen{images.length !== 1 ? 'es' : ''} · Creado {formatDate(project.created_at)}
                            </p>
                        </>
                    )}
                </div>
                <div className={styles.headerActions}>
                    <Button
                        size="sm"
                        onClick={openPicker}
                        disabled={loadingPicker}
                    >
                        {loadingPicker ? 'Cargando…' : 'Agregar Imágenes'}
                    </Button>
                    {!isDefault && !editing && (
                        <>
                            <Button size="sm" variant="secondary" onClick={() => setEditing(true)}>
                                Editar
                            </Button>
                            <Button size="sm" variant="danger" onClick={handleDelete}>
                                Eliminar
                            </Button>
                        </>
                    )}
                </div>
            </div>

            {/* Image picker */}
            {showPicker && (
                <Card className={styles.pickerCard}>
                    <div className={styles.pickerHeader}>
                        <h3>Agregar imágenes de otros proyectos</h3>
                        <Button size="sm" variant="secondary" onClick={() => setShowPicker(false)}>
                            Cerrar
                        </Button>
                    </div>
                    {allImages.length === 0 ? (
                        <p className={styles.pickerEmpty}>No hay imágenes disponibles en otros proyectos</p>
                    ) : (
                        <div className={styles.pickerGrid}>
                            {allImages.map(img => (
                                <div key={img.id} className={styles.pickerItem}>
                                    <span className={styles.pickerName} title={img.filename}>
                                        {img.filename}
                                    </span>
                                    <span className={styles.pickerSize}>{formatSize(img.file_size)}</span>
                                    <Button size="sm" onClick={() => handleAddImage(img.id)}>
                                        Agregar
                                    </Button>
                                </div>
                            ))}
                        </div>
                    )}
                </Card>
            )}

            {/* Empty state */}
            {images.length === 0 && !showPicker && (
                <div className={styles.empty}>
                    <div className={styles.emptyIcon}>🖼️</div>
                    <p>Este proyecto no tiene imágenes</p>
                    <Button onClick={openPicker}>Agregar Imágenes</Button>
                </div>
            )}

            {/* Image grid */}
            <div className={styles.grid}>
                {images.map(img => (
                    <Card key={img.id} className={styles.imageCard}>
                        <div className={styles.thumbnail}>
                            <div className={styles.icon}>🛰️</div>
                            {(img.num_channels || img.bands) && (
                                <div className={styles.badge}>
                                    {img.num_channels ?? img.bands} bandas
                                </div>
                            )}
                        </div>
                        <div className={styles.info}>
                            <h3 className={styles.filename} title={img.filename}>
                                {img.filename}
                            </h3>
                            <div className={styles.imageMeta}>
                                <span>{formatSize(img.file_size)}</span>
                                {img.width && img.height && (
                                    <span>{img.width} × {img.height}</span>
                                )}
                            </div>
                        </div>
                        <div className={styles.imageActions}>
                            <Button size="sm" onClick={() => navigate(`/process/${img.id}`)}>
                                Procesar
                            </Button>
                            <Button size="sm" variant="secondary" onClick={() => navigate(`/analysis/${img.id}`)}>
                                Análisis
                            </Button>
                            {!isDefault && (
                                <Button size="sm" variant="secondary" onClick={() => handleRemoveFromProject(img.id)}>
                                    Quitar
                                </Button>
                            )}
                            <Button size="sm" variant="danger" onClick={() => handleDeleteImage(img.id, img.filename)}>
                                Eliminar
                            </Button>
                        </div>
                    </Card>
                ))}
            </div>
        </div>
    );
};
