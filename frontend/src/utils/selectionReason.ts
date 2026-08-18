import type { FeaturedHistoryEvent, FeaturedSnap } from "../types/snap";

export type ReasonChip = {
    label: string;
    appearance?: "information" | "caution";
};

export type ReasonSummary = {
    chips: ReasonChip[];
    headline: string | null;
};

const CATEGORY_NAMES: Record<string, string> = {
    "art-and-design": "Art and design",
    "books-and-reference": "Books and reference",
    development: "Development",
    "devices-and-iot": "Devices and IoT",
    education: "Education",
    entertainment: "Entertainment",
    featured: "Featured",
    finance: "Finance",
    games: "Games",
    "health-and-fitness": "Health and fitness",
    "music-and-audio": "Music and audio",
    "news-and-weather": "News and weather",
    personalisation: "Personalisation",
    photo: "Photo and video",
    productivity: "Productivity",
    science: "Science",
    security: "Security",
    "server-and-cloud": "Server and cloud",
    social: "Social",
    utilities: "Utilities",
};

const ROLE_HEADLINES: Record<string, string> = {
    "top-3": "Drawn first in the monthly shuffle.",
    "category-development": "Meets the development minimum.",
    "category-game": "Meets the game minimum.",
    "category-development+game": "Meets the development and game minimums.",
    fill: "Fills a remaining slot.",
};

export function formatCategory(slug: string): string {
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

export function describeReason(snap: FeaturedSnap): ReasonSummary {
    const reason = snap.selection_reason;

    if (!reason) {
        if (!snap.featured_history) {
            return { chips: [], headline: "Reason recorded when you save." };
        }
        return { chips: [{ label: "No reason recorded" }], headline: null };
    }

    if (snap.is_manual) {
        const who = reason.nickname || reason.actor || "an admin";
        return {
            chips: [{ label: "Manual", appearance: "caution" }],
            headline: `Chosen by ${who}.`,
        };
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

    return { chips, headline: ROLE_HEADLINES[reason.role ?? ""] ?? "Automated pick." };
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
    if (!snaps) {
        return null;
    }

    const latest = snaps
        .flatMap((snap) => snap.featured_history ?? [])
        .reduce<FeaturedHistoryEvent | null>(
            (newest, event) =>
                !newest || event.featured_at > newest.featured_at ? event : newest,
            null,
        );

    if (!latest) {
        return null;
    }

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
