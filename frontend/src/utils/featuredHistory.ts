import type {
    FeaturedHistoryEvent,
    FeaturedHistoryRun,
} from "../types/featuredHistory";
import type { FeaturedSnapSubject } from "../types/snap";
import { resolveActor } from "./selectionReason";

export function groupIntoRuns(
    events: FeaturedHistoryEvent[] | null,
): FeaturedHistoryRun[] {
    const runs = new Map<string, FeaturedHistoryRun>();

    (events ?? []).forEach((event) => {
        const key = `${event.featured_at}|${event.is_manual}`;
        const run = runs.get(key);

        if (run) {
            run.events.push(event);
        } else {
            runs.set(key, {
                featured_at: event.featured_at,
                is_manual: event.is_manual,
                events: [event],
            });
        }
    });
    return [...runs.values()];
}

export function describeRunSource(run: FeaturedHistoryRun): string {
    if (!run.is_manual) {
        return "Automated run";
    }

    const who = run.events
        .map((event) => resolveActor(event.selection_reason))
        .find(Boolean);

    return who ? `Manual edit by ${who}` : "Manual edit";
}

export function snapDisplayName(event: FeaturedHistoryEvent): string {
    return event.title || event.name || event.snap_id;
}

export function subjectFromHistoryEvent(
    event: FeaturedHistoryEvent,
): FeaturedSnapSubject {
    return {
        snap_id: event.snap_id,
        title: snapDisplayName(event),
        name: event.name,
        publisher: event.publisher,
        icon: event.icon,
        categories: event.categories ?? null,
        featured_at: event.featured_at,
        is_manual: event.is_manual,
        selection_reason: event.selection_reason,
    };
}
