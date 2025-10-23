import type { Snap } from "./snap";

export interface Slice {
    name: string;
    id: string;
    description: string;
}

export interface SliceListItem extends Slice {
    snaps_count: number;
}

export interface SliceDetail extends Slice {
    snaps: Snap[];
}
