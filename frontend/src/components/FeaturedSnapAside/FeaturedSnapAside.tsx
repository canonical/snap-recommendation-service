import {
    Accordion,
    AppAside,
    Chip,
    Col,
    Icon,
    List,
    Notification,
    Panel,
    Row,
    Spinner,
} from "@canonical/react-components";
import { AsideCloseButton } from "../AsideCloseButton/AsideCloseButton";
// import { useFetchData } from "../../hooks/useFetchData"; // TEMP MOCK
import { useAside } from "../../hooks/useAside";
import type { FeaturedHistoryEvent } from "../../types/featuredHistory";
import type { FeaturedSnapSubject } from "../../types/snap";
import { formatDateTime } from "../../utils/dateTime";
import {
    describeConditions,
    describeListRules,
    describeRanking,
    describeRole,
    describeSnapFacts,
    describeSource,
    explainRole,
    snapValidation,
    validationBadge,
    type DetailRow,
    type SelectionCondition,
} from "../../utils/selectionReason";
import { snapcraftUrl } from "../../utils/snap";
import mockData from "../../mocks/featuredData.json"; // TEMP MOCK
import "./FeaturedSnapAside.scss";

const STATUS: Record<
    SelectionCondition["status"],
    { icon: string; label: string }
> = {
    met: { icon: "success", label: "Met" },
    unmet: { icon: "error", label: "Not met" },
    unknown: { icon: "minus", label: "Not checked" },
};

function Section({
    title,
    children,
}: {
    title: string;
    children: React.ReactNode;
}) {
    return (
        <section className="featured-aside__section">
            <hr className="p-rule--muted" />
            <h5 className="p-muted-heading">{title}</h5>
            {children}
        </section>
    );
}

function FactList({ rows }: { rows: DetailRow[] }) {
    return (
        <>
            {rows.map((row) => (
                <Row className="p-form__group" key={row.label}>
                    <Col size={4}>
                        <p className="u-text--muted">{row.label}</p>
                    </Col>
                    <Col size={8}>
                        <p>{row.detail}</p>
                    </Col>
                </Row>
            ))}
        </>
    );
}

function ConditionList({ conditions }: { conditions: SelectionCondition[] }) {
    return (
        <List
            items={conditions.map((condition) => ({
                key: condition.label,
                className:
                    condition.status === "unknown" ? "u-text--muted" : undefined,
                content: (
                    <>
                        <Icon
                            name={STATUS[condition.status].icon}
                            aria-label={STATUS[condition.status].label}
                        />{" "}
                        {condition.label}
                    </>
                ),
            }))}
        />
    );
}

function HistoryTimeline({ snapId }: { snapId: string }) {
    // TEMP MOCK: swap these two blocks back to re-enable the real endpoint.
    // const { data, loading, error } = useFetchData<FeaturedHistoryEvent[]>(
    //     `/featured/history/${snapId}`,
    // );
    const { data, loading, error } = {
        data: (mockData.history as unknown as FeaturedHistoryEvent[]).filter(
            (event) => event.snap_id === snapId,
        ),
        loading: false,
        error: "",
    };

    if (loading) {
        return <Spinner text="Loading history" />;
    }

    if (error) {
        return (
            <Notification severity="negative" title="Error">
                {error}
            </Notification>
        );
    }

    if (!data || data.length === 0) {
        return (
            <p className="u-text--muted u-no-margin--bottom">
                No recorded featuring for this snap yet.
            </p>
        );
    }

    return (
        <List
            divided
            items={data.map((event) => {
                const role = describeRole(event.selection_reason);
                const source = describeSource(event);
                return {
                    key: `${event.featured_at}-${event.is_manual}`,
                    content: (
                        <Row>
                            <Col size={5}>{formatDateTime(event.featured_at)}</Col>
                            <Col size={7}>
                                <span className="p-text--small u-text--muted">
                                    {[source, role].filter(Boolean).join(" · ")}
                                </span>
                            </Col>
                        </Row>
                    ),
                };
            })}
        />
    );
}

export function FeaturedSnapAside({ snap }: { snap: FeaturedSnapSubject }) {
    const { closeAside } = useAside();

    const reason = snap.selection_reason;
    const facts = describeSnapFacts(snap);
    const conditions = describeConditions(snap);
    const listRules = describeListRules(snap);
    const ranking = describeRanking(reason);
    const roleExplanation = explainRole(reason);
    const source = describeSource(snap);
    const badge = validationBadge(snapValidation(snap));
    const unrecorded = source === null;

    const featuringFacts: DetailRow[] = [
        { label: "Source", detail: source ?? "Not recorded" },
        ...(snap.featured_at
            ? [{ label: "Added", detail: formatDateTime(snap.featured_at) }]
            : []),
        ...ranking,
    ];

    return (
        <AppAside className="featured-aside">
            <Panel
                title={snap.title}
                controls={<AsideCloseButton close={closeAside} />}
            >
                <div className="u-fixed-width">
                    <div className="p-media-object featured-aside__header">
                        {snap.icon && (
                            <img
                                src={snap.icon}
                                width={48}
                                height={48}
                                alt=""
                                className="p-media-object__image"
                            />
                        )}
                        <div className="p-media-object__content">
                            {snap.name && (
                                <a href={snapcraftUrl(snap.name)} target="_blank">
                                    {snap.name}
                                </a>
                            )}
                            <span className="featured-aside__publisher p-text--small u-text--muted">
                                {snap.publisher}
                                {badge && (
                                    <img
                                        src={badge.src}
                                        width={14}
                                        height={14}
                                        alt={badge.label}
                                        title={badge.label}
                                    />
                                )}
                            </span>
                        </div>
                    </div>

                    {snap.summary && (
                        <p>{snap.summary}</p>
                    )}

                    <Section title="About this snap">
                        <FactList rows={facts} />
                    </Section>

                    <Section title="Why it's featured">
                        <div className="u-sv1">
                            <Chip
                                value={source ?? "Not recorded"}
                                appearance={
                                    snap.is_manual ? "caution" : "information"
                                }
                                isDense
                                isReadOnly
                            />
                            {reason?.canonical && (
                                <Chip value="Canonical" isDense isReadOnly />
                            )}
                        </div>

                        {unrecorded && (
                            <p className="u-text--muted">
                                It is on the store's featured list, but this
                                dashboard holds no record of how it got there.
                                It's most likely featured before selections were
                                recorded.
                            </p>
                        )}

                        {snap.is_manual && (
                            <p>
                                Picked manually so the automated conditions below
                                were not applied.
                            </p>
                        )}

                        {roleExplanation && <p>{roleExplanation}</p>}

                        <FactList rows={featuringFacts} />
                    </Section>

                    <Section title="Conditions">
                        {!reason?.gates && (
                            <p className="p-text--small u-text--muted">
                                Thresholds are the current defaults. This run did
                                not record its own.
                            </p>
                        )}
                        <ConditionList conditions={conditions} />

                        {listRules.length > 0 && (
                            <Accordion
                                sections={[
                                    {
                                        key: "list-rules",
                                        title: "Rules that decided this slot",
                                        content: (
                                            <FactList
                                                rows={listRules.map((rule) => ({
                                                    label: rule.required
                                                        ? "Required"
                                                        : "Preferred",
                                                    detail: (
                                                        <>
                                                            {rule.label}
                                                            <span className="p-text--small u-text--muted">
                                                                {rule.detail}
                                                            </span>
                                                        </>
                                                    ),
                                                }))}
                                            />
                                        ),
                                    },
                                ]}
                            />
                        )}
                    </Section>

                    <Section title="Featured history">
                        <HistoryTimeline snapId={snap.snap_id} />
                    </Section>
                </div>
            </Panel>
        </AppAside>
    );
}
