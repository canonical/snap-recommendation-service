import type { ReactNode } from "react";
import type { Snap } from "../../types/snap";

export function SnapCard({ snap, actionButton }: { snap: Snap, actionButton: ReactNode }) {

    return <li className="p-list__item">
        <div className="p-card">
            <div className="category-list__item">
                <div className="category-list__item-info">
                    {snap.icon && (
                        <img
                            src={snap.icon}
                            alt={snap.name}
                            className="category-list__item-img" />
                    )}
                    <h4>
                        <a href={`https://snapcraft.io/${snap.name}`} target="_blank">{snap.name}</a>
                    </h4>
                </div>

                {actionButton}
            </div>
            <p className="card__content u-truncate">{snap.summary}</p>
        </div>
    </li>
}