import { useMemo } from "react";
import {
    Chip,
    Col,
    Notification,
    Panel,
    Row,
    Spinner,
} from "@canonical/react-components";
import { FeaturedSnapAside, FeaturedTabs } from "../components";
// import { useFetchData } from "../hooks/useFetchData"; // TEMP MOCK
import type { FeaturedHistoryEvent, FeaturedHistoryRun } from "../types/featuredHistory";
import {
    describeRunSource,
    groupIntoRuns,
    snapDisplayName,
    subjectFromHistoryEvent,
} from "../utils/featuredHistory";
import { useAside } from "../hooks/useAside";
import mockData from "../mocks/featuredData.json"; // TEMP MOCK
import { formatDateTime } from "../utils/dateTime";
import { snapcraftUrl } from "../utils/snap";
import "./FeaturedHistory.scss";

// const HISTORY_LIMIT = 500; // TEMP MOCK

type SnapRowProps = {
    event: FeaturedHistoryEvent;
    position: number;
    onSelect: (event: FeaturedHistoryEvent) => void;
};

function SnapRow({ event, position, onSelect }: SnapRowProps) {
    const name = snapDisplayName(event);

    return (
        <Col
            size={4}
            className="p-media-object featured-history__snap"
            role="button"
            tabIndex={0}
            aria-label={`Selection details for ${name}`}
            onClick={() => onSelect(event)}
            onKeyDown={(keyEvent: React.KeyboardEvent) => {
                if (keyEvent.key === "Enter" || keyEvent.key === " ") {
                    keyEvent.preventDefault();
                    onSelect(event);
                }
            }}
        >
            <span className="u-text--muted">{position}.</span>

            <img
                src={event.icon ?? undefined}
                width={32}
                height={32}
                alt=""
                loading="lazy"
                decoding="async"
                className="p-media-object__image"
            />

            <div className="p-media-object__content">
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
                    <span className="p-text--small u-text--muted">
                        {event.publisher}
                    </span>
                )}
            </div>
        </Col>
    );
}

type RunProps = {
    run: FeaturedHistoryRun;
    onSelect: (event: FeaturedHistoryEvent) => void;
};

function Run({ run, onSelect }: RunProps) {
    return (
        <section>
            <hr className="p-rule--muted" />
            <h5 className="featured-history__run-title">
                <span>{formatDateTime(run.featured_at)}</span>
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

            <Row>
                {run.events.map((event, index) => (
                    <SnapRow
                        key={`${event.snap_id}-${event.featured_at}`}
                        event={event}
                        position={index + 1}
                        onSelect={onSelect}
                    />
                ))}
            </Row>
        </section>
    );
}

export function FeaturedHistory() {
    // TEMP MOCK: swap these two blocks back to re-enable the real endpoint.
    // const { data, loading, error } = useFetchData<FeaturedHistoryEvent[]>(
    //     `/featured/history?limit=${HISTORY_LIMIT}`,
    // );
    const { data, loading, error } = {
        data: mockData.history as unknown as FeaturedHistoryEvent[],
        loading: false,
        error: "",
    };

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
                    <Spinner text="Loading history" />
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
