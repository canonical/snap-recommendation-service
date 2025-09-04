import { Button, Col, Panel, Row, Spinner } from "@canonical/react-components";
import { useFetchData } from "../hooks/useFetchData";

import {
    DndContext,
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
} from "@dnd-kit/core";

import {
    arrayMove,
    SortableContext,
    sortableKeyboardCoordinates,
    rectSortingStrategy,
} from "@dnd-kit/sortable";
import type { FeaturedSnap } from "../types/featuredSnap";
import { useEffect, useState } from "react";
import { FindSnap } from "../components/FindSnap/FindSnap";
import { SortableCard } from "../components/SortableCard/SortableCard";

export function FeaturedSnaps() {
    const { data } = useFetchData<FeaturedSnap[]>('/featured');

    const [featuredSnaps, setFeaturedSnaps] = useState<FeaturedSnap[]>([]);
    const [activeId, setActiveId] = useState<string | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    console.log(activeId)
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

    const handleDragStart = (event: any) => {
        setActiveId(event.active.id);
    };

    const handleDragEnd = (event: any) => {
        setActiveId(null);
        const { active, over } = event;

        if (active.id !== over.id) {
            setFeaturedSnaps((items: FeaturedSnap[]) => {
                if (items) {
                    const oldIndex = items.findIndex(
                        (item) => item.package_name === active.id,
                    );
                    const newIndex = items.findIndex(
                        (item) => item.package_name === over.id,
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


    // const handleAdd = (snap: any) => {
    //     const transformedSnap: FeaturedSnap = {
    //         sections: snap.categories,
    //         summary: snap.package.description,
    //         title: snap.package.display_name,
    //         icon_url: snap.package.icon_url,
    //         package_name: snap.package.name,
    //         developer_name: snap.publisher.display_name,
    //         origin: snap.publisher.name,
    //         developer_validation:
    //             snap.publisher.validation === "starred"
    //                 ? "star"
    //                 : snap.publisher.validation,
    //     };
    //     setFeaturedSnaps((items: FeaturedSnap[]) => {
    //         if (items) {
    //             return [transformedSnap, ...items];
    //         }

    //         return [transformedSnap];
    //     });
    // };

    const handleSave = async (event: any) => {
        event.preventDefault();
        const data = new FormData();
        data.append("snaps", featuredSnaps.map((snap) => snap.package_name).join(","));
        setIsSaving(true);

        const response = await fetch("/featured", {
            method: "POST",
            body: data,
        });

        setIsSaving(false);

        if (!response.ok) {
            console.error("Something went wrong");
        }
    };

    return <Panel title="Featured Snaps">

        <Row>
            <Col size={3}><FindSnap /></Col>
        </Row>

        <Row>
            {/* {isLoading &&
                    [...Array(16)].map((item, index) => (
                        <Col size={3} key={index}>
                            <LoadingCard />
                        </Col>
                    ))} */}
            {/* {isError && <div>Error</div>} */}
            {featuredSnaps && (
                <DndContext
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragStart={handleDragStart}
                    onDragEnd={handleDragEnd}
                >
                    <SortableContext
                        items={featuredSnaps.map((snap) => snap.package_name)}
                        strategy={rectSortingStrategy}
                    >
                        {featuredSnaps.map((snap: any) => (
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
                            <Spinner isLight /> <span>Saving</span>
                        </>
                    ) : (
                        "Save"
                    )}
                </Button>
            </p>
        </Row>

    </Panel>
}