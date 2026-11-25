import type { Snap } from "./snap";

export interface SnapCollection {
    name: string;
    id: string;
    description: string;
}

export interface SnapCollectionListItem extends SnapCollection {
    snaps_count: number;
}

export interface SnapCollectionDetail extends SnapCollection {
    snaps: Snap[];
}
