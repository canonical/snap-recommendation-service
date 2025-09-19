import { Button, Col, Notification, Panel, Row, Spinner } from "@canonical/react-components";
import { useFetchData } from "../hooks/useFetchData";
import {
    DndContext,
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
    type DragEndEvent,
} from "@dnd-kit/core";

import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    rectSortingStrategy,
} from "@dnd-kit/sortable";
import type { FeaturedSnap, SearchSnap } from "../types/snap";
import { useEffect, useState } from "react";
import { FindSnap } from "../components/FindSnap/FindSnap";
import { SortableCard } from "../components/SortableCard/SortableCard";
import { LoadingCard } from "../components/LoadingCard/LoadingCard";

export function FeaturedSnaps() {
    const { data, loading, error } = useFetchData<FeaturedSnap[]>('/featured');

    const [featuredSnaps, setFeaturedSnaps] = useState<FeaturedSnap[]>([]);
    const [isSaving, setIsSaving] = useState(false);
    const [operationError, setOperationError] = useState("");

    const sensors = useSensors(
        useSensor(PointerSensor),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        }),
    );

    useEffect(() => {
        if (data) {
            setFeaturedSnaps(data)
        }
    }, [data])


    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;

        if (active.id !== over?.id) {
            setFeaturedSnaps((items: FeaturedSnap[]) => {
                if (items) {
                    const oldIndex = items.findIndex(
                        (item) => item.package_name === active.id,
                    );
                    const newIndex = items.findIndex(
                        (item) => item.package_name === over?.id,
                    );
                    return arrayMove(items, oldIndex, newIndex);
                }
                return items;
            });
        }
    };

    const handleRemove = (id: string) => {
        setFeaturedSnaps((items: FeaturedSnap[]) => {
            const index = items.findIndex((item) => item.package_name === id);
            return [...items.slice(0, index), ...items.slice(index + 1)];
        });
    };

    const handleAdd = (snap: SearchSnap) => {
        const transformedSnap: FeaturedSnap = {
            snap_id: snap.snap_id,
            sections: snap.categories,
            summary: snap.package.description,
            title: snap.package.display_name,
            icon_url: snap.package.icon_url,
            package_name: snap.package.name,
            developer_name: snap.publisher.display_name,
            origin: snap.publisher.name,
            developer_validation:
                snap.publisher.validation === "starred"
                    ? "star"
                    : snap.publisher.validation,

        };
        setFeaturedSnaps((items: FeaturedSnap[]) => {
            if (items) {
                return [transformedSnap, ...items];
            }

            return [transformedSnap];
        });
    };

    const handleSave = async (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
        event.preventDefault();
        setOperationError("");
        const data = new FormData();
        data.append("snaps", featuredSnaps.map((snap) => snap.snap_id).join(","));
        setIsSaving(true);

        const response = await fetch("/featured", {
            method: "POST",
            body: data,
        });

        setIsSaving(false);

        if (!response.ok) {
            if (response.status === 403 || response.status === 404) {
                setOperationError("Changes cannot be saved due to insufficient permissions.");
            } else {
                setOperationError("Something went wrong");
            }
        }
    };

    return <Panel title="Featured Snaps">
        <Row>
            <Col size={4}><FindSnap addSnap={handleAdd} /></Col>
        </Row>

        <Row>
            {
                (error || operationError) && <Notification severity="negative" title="Error">
                    {error || operationError}
                </Notification>
            }
            {loading &&
                [...Array(16)].map((_, index) => (
                    <Col size={3} key={index}>
                        <LoadingCard />
                    </Col>
                ))}
            {featuredSnaps && (
                <DndContext
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragEnd={handleDragEnd}
                >
                    <SortableContext
                        items={featuredSnaps.map((snap) => snap.package_name)}
                        strategy={rectSortingStrategy}
                    >
                        {featuredSnaps.map((snap) => (
                            <SortableCard
                                key={snap.package_name}
                                snap={snap}
                                handleRemove={handleRemove}
                            />
                        ))}
                    </SortableContext>
                </DndContext>
            )}
            <p style={{ textAlign: "right", maxWidth: "100%" }}>
                {featuredSnaps.length < 16 && (
                    <>Please add {16 - featuredSnaps.length} more snaps to save</>
                )}
                <Button
                    appearance="positive"
                    onClick={handleSave}
                    disabled={featuredSnaps.length < 16}
                    hasIcon={isSaving}
                    inline
                >
                    {isSaving ? (
                        <>
                            <Spinner isLight style={{ paddingRight: "0.5rem" }} /> <span>Saving</span>
                        </>
                    ) : (
                        "Save"
                    )}
                </Button>
            </p>
        </Row>

    </Panel>
}
