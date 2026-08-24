export type Snap = {
    snap_id: string;
    title: string;
    name: string;
    version: string;
    summary: string;
    description: string;
    icon: string;
    contact: string | null;
    publisher: string;
    revision: string;
    links: Array<{ [key: string]: string[] }>;
    media: Array<{
        name: string;
        height: number;
        type: string;
        url: string;
        width: number;
    }>;
    developer_validation: string;
    license: string;
    last_updated: string;
}


type SnapCategory = {
    display_name: string;
    name: string;
    featured: boolean;
}

export type SelectionGates = {
    min_rating?: number;
    recency_days?: number;
    history_window_days?: number;
    excluded_category?: string;
    allowed_developer_validation?: string[];
    candidate_pool_size?: number;
    category_cap?: number;
    target_count?: number;
}

export type SelectionSnapFacts = {
    rating?: number | null;
    total_votes?: number | null;
    active_devices?: number | null;
    last_updated?: string | null;
}

export type SelectionReason = {
    role?: string;
    canonical?: boolean;
    developer_validation?: string;
    categories?: string[];
    ranking_key?: string;
    ranking_value?: number | null;
    random_seed?: number;
    actor?: string | null;
    nickname?: string | null;
    gates?: SelectionGates | null;
    snap_facts?: SelectionSnapFacts | null;
    pool_rank?: number | null;
    candidate_count?: number | null;
}

export type FeaturedSnapSubject = {
    snap_id: string;
    title: string;
    name?: string | null;
    publisher?: string | null;
    summary?: string | null;
    icon?: string | null;
    developer_validation?: string | null;
    categories?: string[] | null;
    featured_at?: string | null;
    is_manual?: boolean | null;
    selection_reason?: SelectionReason | null;
}

export type FeaturedSnap = {
    sections: SnapCategory[];
    summary: string;
    title: string;
    icon_url: string;
    package_name: string;
    developer_name: string;
    origin: string;
    developer_validation: string;
    snap_id: string;
    selection_reason?: SelectionReason | null;
    is_manual?: boolean | null;
    featured_at?: string | null;
}

export type SearchSnap = {
    categories: SnapCategory[];
    package: {
        description: string;
        display_name: string;
        icon_url: string;
        name: string;
        platforms: string[];
        type: string;
    }
    publisher: {
        display_name: string;
        validation: string;
        name: string;
    }
    snap_id: string;
}
