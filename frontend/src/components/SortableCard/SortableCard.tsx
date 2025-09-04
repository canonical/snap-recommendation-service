import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

import { Button, Card, Col, Icon } from "@canonical/react-components";
import type { FeaturedSnap } from "../../types/featuredSnap";

type SortableCardProps = {
    snap: FeaturedSnap;
    handleRemove: (id: string) => void;
};

export const SortableCard = ({ snap, handleRemove }: SortableCardProps) => {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({ id: snap.package_name });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1,
    };

    const developerValidation = snap.developer_validation === "starred"
        ? "star"
        : snap.developer_validation

    return (
        <Col size={3} style={{ marginBottom: "1.5rem", position: "relative" }}>
            <div style={{ ...style, height: "100%" }} ref={setNodeRef}  >
                <Card className="u-no-margin--bottom" style={{ height: "100%", paddingTop: "0.5rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                        <div style={{
                            cursor: "grab",
                            flexGrow: 1
                        }}
                            {...listeners} {...attributes}
                        >
                            <Icon name="drag" />
                        </div>

                        <Button
                            appearance="base"
                            style={{
                                margin: 0
                            }}
                            hasIcon
                            onClick={() => handleRemove(snap.package_name)}
                        >
                            <i className="p-icon--delete"></i>

                        </Button>
                    </div>


                    <div className="p-media-object" >
                        <img
                            src={snap.icon_url}
                            width={48}
                            height={48}
                            alt=""
                            className="p-media-object__image"
                            data-testid="package-icon"
                        />
                        <div className="sc-package-card p-media-o bject__details">
                            <div>{snap.title}</div>

                            <div style={{ display: "flex", gap: "0.5rem" }}>
                                <span>{snap.developer_name}</span>

                                {developerValidation === "verified" && (
                                    <img
                                        src="https://assets.ubuntu.com/v1/ba8a4b7b-Verified.svg"
                                        width={14}
                                        height={14}
                                        alt="Verified account"
                                        title="Verified account"
                                        className="sc-package-publisher-icon"
                                    />
                                )}

                                {(developerValidation === "star" ||
                                    developerValidation === "starred") && (
                                        <img
                                            src="https://assets.ubuntu.com/v1/d810dee9-Orange+Star.svg"
                                            width={14}
                                            height={14}
                                            alt="Star developer"
                                            title="Star developer"
                                            className="sc-package-publisher-icon"
                                        />
                                    )}

                            </div>

                        </div>

                    </div>
                    <div className="u-line-clamp">{snap.summary}</div>
                </Card>


                {/* <DefaultCard
                    data={{
                        categories: snap.sections,
                        package: {
                            description: snap.summary,
                            display_name: snap.title,
                            icon_url: snap.icon_url,
                            name: snap.package_name,
                        },
                        publisher: {
                            display_name: snap.developer_name,
                            name: snap.origin,
                            validation:
                                snap.developer_validation === "starred"
                                    ? "star"
                                    : snap.developer_validation,
                        },
                    }}
                /> */}
            </div>
        </Col>
    );
};