import { Spinner } from "@canonical/react-components";
import type { SearchSnap } from "../../types/snap";

type FindSnapResultsProps = {
    loading: boolean;
    packages: SearchSnap[];
    onSelect: (snap: SearchSnap) => void;
};

export function FindSnapResults({ loading, packages, onSelect }: FindSnapResultsProps) {
    return (
        <div className="snap-search__list" onMouseDown={(e) => e.preventDefault()}>
            {loading && (
                <div>
                    <Spinner isLight className="snap-search__spinner" /> <span>Loading...</span>
                </div>
            )}
            {!loading && packages.length === 0 && (
                <div className="snap-search__item u-text--muted">No results</div>
            )}
            {packages.map((snap) => (
                <div
                    key={snap.package.name}
                    onClick={() => onSelect(snap)}
                    className="snap-search__item"
                >
                    {snap.package.icon_url && (
                        <div>
                            <img
                                src={snap.package.icon_url}
                                alt={snap.package.name}
                                width="32"
                                className="snap-search__item-img"
                            />
                        </div>
                    )}
                    <div>
                        <h3 className="p-heading--5 u-no-margin u-no-padding">
                            {snap.package.display_name}
                        </h3>
                        <p className="u-no-margin u-text--muted">
                            <em>{snap.publisher.display_name}</em>
                        </p>
                        <p className="u-no-margin">{snap.package.description}</p>
                    </div>
                </div>
            ))}
        </div>
    );
}
