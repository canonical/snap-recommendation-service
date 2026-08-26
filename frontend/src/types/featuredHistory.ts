import type { SelectionReason } from "./snap";

export type FeaturedHistoryEvent = {
    snap_id: string;
    featured_at: string;
    is_manual: boolean;
    selection_reason?: SelectionReason | null;
    title?: string | null;
    name?: string | null;
    publisher?: string | null;
    icon?: string | null;
};

export type FeaturedHistoryRun = {
    featured_at: string;
    is_manual: boolean;
    events: FeaturedHistoryEvent[];
};
