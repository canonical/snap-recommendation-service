import { useMemo } from "react";
import { Chip, Notification, Panel, Spinner } from "@canonical/react-components";
import { FeaturedSnapAside, FeaturedTabs } from "../components";
import { useFetchData } from "../hooks/useFetchData";
import type { FeaturedHistoryEvent, FeaturedHistoryRun } from "../types/featuredHistory";
import {
    describeRunSource,
    groupIntoRuns,
    snapDisplayName,
    subjectFromHistoryEvent,
} from "../utils/featuredHistory";
import { useAside } from "../hooks/useAside";
import { formatDateTime } from "../utils/dateTime";
import { snapcraftUrl } from "../utils/snap";
import "./FeaturedHistory.scss";

const HISTORY_LIMIT = 500;

type SnapRowProps = {
    event: FeaturedHistoryEvent;
    position: number;
    onSelect: (event: FeaturedHistoryEvent) => void;
};

function SnapRow({ event, position, onSelect }: SnapRowProps) {
    const name = snapDisplayName(event);

    return (
        <li
            className="featured-history__snap featured-history__snap--selectable"
            role="button"
            tabIndex={0}
            aria-label={`Selection details for ${name}`}
            onClick={() => onSelect(event)}
            onKeyDown={(keyEvent) => {
                if (keyEvent.key === "Enter" || keyEvent.key === " ") {
                    keyEvent.preventDefault();
                    onSelect(event);
                }
            }}
        >
            <span className="featured-history__snap-position">{position}.</span>

            {event.icon ? (
                <img
                    src={event.icon}
                    width={32}
                    height={32}
                    alt=""
                    loading="lazy"
                    decoding="async"
                    className="featured-history__snap-icon"
                />
            ) : (
                <span className="featured-history__snap-icon featured-history__snap-icon--empty" />
            )}

            <span className="featured-history__snap-details">
                {event.name ? (
                    <a
                        href={snapcraftUrl(event.name)}
                        onClick={(linkEvent) => linkEvent.stopPropagation()}
                    >
                        {name}
                    </a>
                ) : (
                    <span>{name}</span>
                )}
                {event.publisher && (
                    <span className="p-text--small u-text--muted">{event.publisher}</span>
                )}
            </span>
        </li>
    );
}

type RunProps = {
    run: FeaturedHistoryRun;
    onSelect: (event: FeaturedHistoryEvent) => void;
};

function Run({ run, onSelect }: RunProps) {
    return (
        <section className="featured-history__run">
            <h5 className="featured-history__run-title">
                <span className="featured-history__run-date">
                    {formatDateTime(run.featured_at)}
                </span>
                <Chip
                    value={describeRunSource(run)}
                    appearance={run.is_manual ? "caution" : "information"}
                    isDense
                    isReadOnly
                />
                <span className="p-text--small u-text--muted">
                    {run.events.length} {run.events.length === 1 ? "snap" : "snaps"}
                </span>
            </h5>

            <ol className="featured-history__snaps p-list u-no-margin--bottom">
                {run.events.map((event, index) => (
                    <SnapRow
                        key={`${event.snap_id}-${event.featured_at}`}
                        event={event}
                        position={index + 1}
                        onSelect={onSelect}
                    />
                ))}
            </ol>
        </section>
    );
}

export function FeaturedHistory() {
    const { data, loading, error } = useFetchData<FeaturedHistoryEvent[]>(
        `/featured/history?limit=${HISTORY_LIMIT}`,
    );

    const runs = useMemo(() => groupIntoRuns(data), [data]);
    const { openAside } = useAside();

    const handleSelect = (event: FeaturedHistoryEvent) => {
        const subject = subjectFromHistoryEvent(event);
        openAside(
            <FeaturedSnapAside
                key={`${subject.snap_id}-${event.featured_at}`}
                snap={subject}
            />,
        );
    };

    return (
        <Panel title="Featured snaps">
            <div className="u-fixed-width">
                <FeaturedTabs />

                {error && (
                    <Notification severity="negative" title="Error">
                        {error}
                    </Notification>
                )}

                {loading && (
                    <div className="featured-history__loading">
                        <Spinner text="Loading history" />
                    </div>
                )}

                {!loading && !error && runs.length === 0 && (
                    <p>No featured history yet</p>
                )}

                {runs.map((run) => (
                    <Run
                        key={`${run.featured_at}|${run.is_manual}`}
                        run={run}
                        onSelect={handleSelect}
                    />
                ))}
            </div>
        </Panel>
    );
}
