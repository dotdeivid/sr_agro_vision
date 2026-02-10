export type IndexType = 'ndvi' | 'evi' | 'savi' | 'ndwi';

export interface AnalysisRequest {
    image_id: string;
    index_type: IndexType;
}

export interface HealthDistribution {
    very_dense: number;
    dense: number;
    moderate: number;
    sparse: number;
    bare_soil: number;
    water: number;
}

export interface AnalysisStats {
    min_value: number;
    max_value: number;
    mean_value: number;
    median_value: number;
    std_dev: number;
    pixel_count: number;
    health_distribution: HealthDistribution;
    percentile_25: number;
    percentile_75: number;
}

export interface AnalysisResult {
    id: string;
    image_id: string;
    index_type: IndexType;
    result_filepath: string;
    colormap_filepath: string;
    stats: AnalysisStats;
    created_at: string;
}

export interface IndexInfo {
    id: IndexType;
    name: string;
    description: string;
    formula: string;
    range: string;
}
