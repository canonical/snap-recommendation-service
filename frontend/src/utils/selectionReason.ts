import type { ChipProps } from "@canonical/react-components";
import type { FeaturedSnap } from "../types/snap";
import { formatDateTime } from "./dateTime";

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
        return [{ label: "No reason recorded" }];
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

export function describeLastFeatured(snap: FeaturedSnap): string | null {
    if (!snap.featured_at) {
        return null;
    }
    return `Last featured ${formatDateTime(snap.featured_at)}`;
}

export function describeLastUpdate(snaps: FeaturedSnap[] | null): string | null {
    const latest = (snaps ?? []).reduce<FeaturedSnap | null>((newest, snap) => {
        if (!snap.featured_at) {
            return newest;
        }
        if (!newest?.featured_at) {
            return snap;
        }
        return Date.parse(snap.featured_at) > Date.parse(newest.featured_at)
            ? snap
            : newest;
    }, null);

    if (!latest?.featured_at) {
        return null;
    }

    const when = formatDateTime(latest.featured_at);

    if (!latest.is_manual) {
        return `Last updated ${when} by the automated run`;
    }

    const who = latest.selection_reason?.nickname || latest.selection_reason?.actor;
    return who ? `Last updated ${when} by ${who}` : `Last updated ${when} manually`;
}
