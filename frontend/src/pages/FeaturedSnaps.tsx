import { Col, Notification, Panel, Row } from "@canonical/react-components";
import { useFetchData } from "../hooks/useFetchData";
import type { FeaturedSnap } from "../types/snap";
import { useEffect, useState } from "react";
import { SortableCard } from "../components/SortableCard/SortableCard";
import { LoadingCard } from "@canonical/store-components";

export function FeaturedSnaps() {
    const { data, loading, error } = useFetchData<FeaturedSnap[]>('/featured');

    const [featuredSnaps, setFeaturedSnaps] = useState<FeaturedSnap[]>([]);

    useEffect(() => {
        if (data) {
            setFeaturedSnaps(data)
        }
    }, [data])

    return <Panel title="Featured Snaps">
        <Row>
            {
                (error) && <Notification severity="negative" title="Error">
                    {error}
                </Notification>
            }
            {loading &&
                [...Array(16)].map((_, index) => (
                    <Col size={3} key={index}>
                        <LoadingCard />
                    </Col>
                ))}
            {featuredSnaps && (
                <div>
                    {featuredSnaps.map((snap) => (
                        <SortableCard
                            key={snap.package_name}
                            snap={snap}
                        />
                    ))}
                </div>
            )}
        </Row>
    </Panel>
}