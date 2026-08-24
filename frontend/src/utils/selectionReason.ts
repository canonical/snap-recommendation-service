import type { ReactNode } from "react";
import type { ChipProps } from "@canonical/react-components";
import type {
    FeaturedSnap,
    FeaturedSnapSubject,
    SelectionReason,
} from "../types/snap";
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

export function resolveActor(reason?: SelectionReason | null): string | null {
    return reason?.nickname || reason?.actor || null;
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

    const who = resolveActor(latest.selection_reason);
    return who ? `Last updated ${when} by ${who}` : `Last updated ${when} manually`;
}


const ROLE_LABELS: Record<string, string> = {
    "top-3": "Top 3",
    fill: "List fill",
    "category-development": "Development quota",
    "category-game": "Games quota",
    "category-development+game": "Development and games quota",
};

export function describeRole(reason?: SelectionReason | null): string | null {
    const role = reason?.role;
    if (!role) {
        return null;
    }
    return ROLE_LABELS[role] ?? formatCategory(role);
}

export function explainRole(reason?: SelectionReason | null): string | null {
    const role = reason?.role;
    if (!role) {
        return null;
    }

    const gates = reason?.gates ?? {};

    if (role === "top-3") {
        const pool = gates.candidate_pool_size;
        return pool
            ? `Drawn at random into the top 3 from the ${pool} highest-ranked eligible snaps.`
            : "Drawn at random into the top 3 highest-ranked eligible snaps.";
    }

    if (role.startsWith("category-")) {
        const roles = role.slice("category-".length).split("+");
        const quotas = roles.map((item) =>
            item === "development"
                ? "at least 2 development snaps"
                : "at least 1 game",
        );
        return `Reserved a slot so the list holds ${quotas.join(" and ")}.`;
    }

    if (role === "fill") {
        const cap = gates.category_cap;
        return cap
            ? `Filled a remaining slot in ranked order, capped at ${cap} snaps per category.`
            : "Filled a remaining slot in ranked order.";
    }

    return null;
}

export function describeRanking(reason?: SelectionReason | null): DetailRow[] {
    if (!reason) {
        return [];
    }

    const rows: DetailRow[] = [];

    if (typeof reason.ranking_value === "number") {
        rows.push({
            label: "Ranking score",
            detail: reason.ranking_value.toFixed(3),
        });
    }

    if (typeof reason.pool_rank === "number") {
        rows.push({
            label: "Rank among eligible snaps",
            detail: reason.candidate_count
                ? `${reason.pool_rank} of ${formatNumber(reason.candidate_count)}`
                : `${reason.pool_rank}`,
        });
    }

    return rows;
}

export type ConditionStatus = "met" | "unmet" | "unknown";

export type SelectionCondition = {
    label: string;
    detail?: string;
    status: ConditionStatus;
};

export type DetailRow = {
    label: string;
    detail?: ReactNode;
};

export type ListRule = {
    label: string;
    required: boolean;
};

const DEFAULT_GATES = {
    min_rating: 0,
    recency_days: 180,
    history_window_days: 365,
    excluded_category: "server-and-cloud",
    allowed_developer_validation: ["verified", "starred"],
    category_cap: 4,
};

function gatesFor(reason?: SelectionReason | null) {
    return { ...DEFAULT_GATES, ...(reason?.gates ?? {}) };
}

function formatNumber(value?: number | null): string | null {
    return typeof value === "number" ? value.toLocaleString("en-GB") : null;
}

function normaliseValidation(value?: string | null): string | null {
    if (!value) {
        return null;
    }
    return value === "star" ? "starred" : value;
}

export function snapValidation(subject: FeaturedSnapSubject): string | null {
    return (
        normaliseValidation(subject.selection_reason?.developer_validation) ??
        normaliseValidation(subject.developer_validation)
    );
}

function snapCategories(subject: FeaturedSnapSubject): string[] {
    const recorded = subject.selection_reason?.categories;
    return recorded?.length ? recorded : (subject.categories ?? []);
}

export function validationBadge(
    validation?: string | null,
): { src: string; label: string } | null {
    const normalised = normaliseValidation(validation);
    if (normalised === "verified") {
        return {
            src: "https://assets.ubuntu.com/v1/ba8a4b7b-Verified.svg",
            label: "Verified account",
        };
    }
    if (normalised === "starred") {
        return {
            src: "https://assets.ubuntu.com/v1/d810dee9-Orange+Star.svg",
            label: "Star developer",
        };
    }
    return null;
}

function statusFor(
    subject: FeaturedSnapSubject,
    liveCheck?: boolean | null,
): ConditionStatus {
    if (subject.is_manual === false) {
        return "met";
    }
    if (typeof liveCheck === "boolean") {
        return liveCheck ? "met" : "unmet";
    }
    return "unknown";
}

export function describeConditions(
    subject: FeaturedSnapSubject,
): SelectionCondition[] {
    const reason = subject.selection_reason;
    const gates = gatesFor(reason);

    const allowed = gates.allowed_developer_validation;
    const validation = snapValidation(subject);
    const validationCheck = validation ? allowed.includes(validation) : null;

    const categories = snapCategories(subject);
    const categoryCheck = categories.length
        ? !categories.includes(gates.excluded_category)
        : null;

    return [
        {
            label: `Publisher is ${allowed.join(" or ")}`,
            status: statusFor(subject, validationCheck),
        },
        {
            label: "Meets the minimum install threshold",
            status: statusFor(subject),
        },
        {
            label: `Updated in the last ${gates.recency_days} days`,
            status: statusFor(subject),
        },
        {
            label: `Not featured in the last ${gates.history_window_days} days`,
            status: statusFor(subject),
        },
        {
            label: `Rating of at least ${gates.min_rating}`,
            status: statusFor(subject),
        },
        {
            label: `Not in the ${formatCategory(gates.excluded_category)} category`,
            status: statusFor(subject, categoryCheck),
        },
        {
            label: "Not on the exclusion list",
            status: statusFor(subject),
        },
    ];
}

export function describeSnapFacts(subject: FeaturedSnapSubject): DetailRow[] {
    const facts = subject.selection_reason?.snap_facts ?? {};
    const categories = snapCategories(subject);
    const rows: DetailRow[] = [];

    rows.push({
        label: "Categories",
        detail: categories.length
            ? categories.map(formatCategory).join(", ")
            : "None recorded",
    });

    const devices = formatNumber(facts.active_devices);
    if (devices) {
        rows.push({ label: "Installs", detail: `${devices} active devices` });
    }

    if (typeof facts.rating === "number") {
        const votes = formatNumber(facts.total_votes);
        rows.push({
            label: "Rating",
            detail: `${facts.rating.toFixed(2)}${votes ? ` from ${votes} votes` : ""}`,
        });
    }

    if (facts.last_updated) {
        rows.push({
            label: "Last updated",
            detail: formatDateTime(facts.last_updated),
        });
    }

    return rows;
}

export function describeListRules(subject: FeaturedSnapSubject): ListRule[] {
    if (subject.is_manual || subject.is_manual === null || subject.is_manual === undefined) {
        return [];
    }

    const reason = subject.selection_reason;
    const gates = gatesFor(reason);
    const role = reason?.role;

    const rules: (ListRule & { appliesTo: (role: string) => boolean })[] = [
        {
            label: "1 to 2 Canonical snaps in the top 3",
            required: true,
            appliesTo: (r) => r === "top-3",
        },
        {
            label: "At least 2 development snaps and 1 game",
            required: true,
            appliesTo: (r) => r.startsWith("category-"),
        },
        {
            label: `At most ${gates.category_cap} snaps per category`,
            required: false,
            appliesTo: (r) => r === "fill",
        },
    ];

    return rules
        .filter((rule) => !role || rule.appliesTo(role))
        .map((rule) => ({ label: rule.label, required: rule.required }));
}

export function describeSource(subject: {
    is_manual?: boolean | null;
    selection_reason?: SelectionReason | null;
}): string | null {
    if (subject.is_manual === null || subject.is_manual === undefined) {
        return null;
    }

    if (!subject.is_manual) {
        return "Automated run";
    }

    const who = resolveActor(subject.selection_reason);
    return who ? `Manual edit by ${who}` : "Manual edit";
}

export function subjectFromFeaturedSnap(
    snap: FeaturedSnap,
): FeaturedSnapSubject {
    return {
        snap_id: snap.snap_id,
        title: snap.title,
        name: snap.package_name,
        publisher: snap.developer_name,
        summary: snap.summary,
        icon: snap.icon_url,
        developer_validation: snap.developer_validation,
        categories: (snap.sections ?? []).map((section) => section.name),
        featured_at: snap.featured_at,
        is_manual: snap.is_manual,
        selection_reason: snap.selection_reason,
    };
}
