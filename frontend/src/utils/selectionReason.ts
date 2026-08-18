import type { ChipProps } from "@canonical/react-components";
import type { FeaturedHistoryEvent, FeaturedSnap } from "../types/snap";

export type ReasonChip = {
    label: string;
    appearance?: ChipProps["appearance"];
};

const CATEGORY_NAMES: Record<string, string> = {
    "devices-and-iot": "Devices and IoT",
    photo: "Photo and video",
};

function formatCategory(slug: string): string {
    if (CATEGORY_NAMES[slug]) {
        return CATEGORY_NAMES[slug];
    }
    const spaced = slug.replace(/-/g, " ");
    return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

function publisherLabel(validation?: string): string | null {
    if (validation === "starred" || validation === "star") {
        return "Starred publisher";
    }
    if (validation === "verified") {
        return "Verified publisher";
    }
    return null;
}

export function describeReason(snap: FeaturedSnap): ReasonChip[] {
    const reason = snap.selection_reason;

    if (!reason) {
        return snap.featured_history ? [{ label: "No reason recorded" }] : [];
    }

    if (snap.is_manual) {
        return [{ label: "Manual", appearance: "caution" }];
    }

    const chips: ReasonChip[] = [];
    if (reason.canonical) {
        chips.push({ label: "Canonical" });
    }
    const publisher = publisherLabel(reason.developer_validation);
    if (publisher) {
        chips.push({ label: publisher });
    }
    (reason.categories ?? []).forEach((slug) => chips.push({ label: formatCategory(slug) }));

    return chips;
}

export function describeFeaturedCount(snap: FeaturedSnap): string | null {
    const events = snap.featured_history;
    if (!events) {
        return null;
    }
    if (events.length === 0) {
        return "First time featured";
    }
    if (events.length === 1) {
        return "Featured once";
    }
    return `Featured ${events.length} times`;
}

export function describeLastUpdate(snaps: FeaturedSnap[] | null): string | null {
    const newestPerSnap = (snaps ?? [])
        .map((snap) => snap.featured_history?.[0])
        .filter((event): event is FeaturedHistoryEvent => Boolean(event));

    if (newestPerSnap.length === 0) {
        return null;
    }

    const latest = newestPerSnap.reduce((newest, event) =>
        event.featured_at > newest.featured_at ? event : newest,
    );

    const when = new Date(latest.featured_at).toLocaleString("en-GB", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    });

    if (!latest.is_manual) {
        return `Last updated ${when} by the automated run`;
    }

    const who = latest.selection_reason?.nickname || latest.selection_reason?.actor;
    return who ? `Last updated ${when} by ${who}` : `Last updated ${when} manually`;
}
