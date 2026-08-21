import { useMemo } from "react";
import { Chip, Notification, Panel, Spinner } from "@canonical/react-components";
import { FeaturedTabs } from "../components";
import { useFetchData } from "../hooks/useFetchData";
import type { FeaturedHistoryEvent, FeaturedHistoryRun } from "../types/featuredHistory";
import { describeRunSource, groupIntoRuns, snapDisplayName } from "../utils/featuredHistory";
import { formatDateTime } from "../utils/dateTime";
import "./FeaturedHistory.scss";

const HISTORY_LIMIT = 500;

function SnapRow({ event, position }: { event: FeaturedHistoryEvent; position: number }) {
    const name = snapDisplayName(event);

    return (
        <li className="featured-history__snap">
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
                    <a href={`https://snapcraft.io/${event.name}`}>{name}</a>
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

function Run({ run }: { run: FeaturedHistoryRun }) {
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
                    <Run key={`${run.featured_at}|${run.is_manual}`} run={run} />
                ))}
            </div>
        </Panel>
    );
}
