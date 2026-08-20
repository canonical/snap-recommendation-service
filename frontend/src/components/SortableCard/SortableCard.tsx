import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Button, Card, Chip, Col, Icon } from "@canonical/react-components";
import type { FeaturedSnap } from "../../types/snap";
import { describeLastFeatured, describeReason } from "../../utils/selectionReason";
import "./SortableCard.scss";

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
        : snap.developer_validation;

    const chips = describeReason(snap);
    const lastFeatured = describeLastFeatured(snap);

        return (
            <Col size={4} className="card" style={style} ref={setNodeRef}>
                <Card className="u-no-margin--bottom card-content">
                    <div className="card-content__buttons">
                        <div className="card-content__drag" {...listeners} {...attributes}>
                            <Icon name="drag" />
                        </div>

                        <Button
                            appearance="base"
                            className="card-content__delete"
                            hasIcon
                            onClick={() => handleRemove(snap.package_name)}
                        >
                            <Icon name="delete" />
                        </Button>
                    </div>

                    <div className="p-media-object">
                        <img
                            src={snap.icon_url}
                            width={48}
                            height={48}
                            alt=""
                            className="p-media-object__image"
                            data-testid="package-icon"
                        />
                        <div className="sc-package-card p-media-object__details">
                            <a href={`https://snapcraft.io/${snap.package_name}`}>{snap.title}</a>
                            <div className="card-content__dev_info">
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
                    <div className="u-truncate">{snap.summary}</div>

                    <hr className="p-rule--muted" />

                    <div className="card-content__reason">
                        {chips.length > 0 && (
                            <div className="card-content__signals">
                                {chips.map((chip) => (
                                    <Chip
                                        key={chip.label}
                                        value={chip.label}
                                        appearance={chip.appearance}
                                        isDense
                                        isReadOnly
                                    />
                                ))}
                            </div>
                        )}

                        {lastFeatured && (
                            <p className="p-text--small u-text--muted u-no-margin--bottom">
                                {lastFeatured}
                            </p>
                        )}
                    </div>
                </Card>
            </Col>
        );
}


