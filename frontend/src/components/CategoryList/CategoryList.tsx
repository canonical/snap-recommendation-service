import { Notification } from "@canonical/react-components";
import { useFetchSnaps } from "../../hooks/useFetchSnaps";
import { useState } from "react";
import "./CategoryList.scss";
import type { Snap } from "../../types/snap";

export const CategoryList = ({ category, label }: { category: string, label: string }) => {
    const { error, loading, snaps, refetch } = useFetchSnaps(`/api/snaps?category=${category}`);

    const [excludeError, setExcludeError] = useState<string | null>(null)

    const excludeSnap = async (snap: Snap) => {
        try {
            const response = await fetch("/dashboard/api/exclude_snap", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    "snap_id": snap.snap_id,
                    "category": category
                }),
            })

            if (!response.ok) {
                throw new Error("Failed to exclude snap.");
            }
            setExcludeError(null)

            await refetch()
        } catch {
            setExcludeError("An error occurred")
        }
    }

    return <div>
        <h5>{label}</h5>
        {
            (excludeError || error) && <Notification
                severity="negative"
                title="Error"
            >
                An error occurred
            </Notification>
        }
        {
            loading && <div>Loading</div>
        }
        {snaps &&
            <ul className="p-list category-list">
                {
                    snaps.map((snap) => <li key={snap.snap_id} className="p-list__item">
                        <div className="p-card">
                            <div className="category-list__item">
                                <div className="category-list__item-info">
                                    <img
                                        src={snap.icon}
                                        alt={snap.name}
                                        className="u-icon category-list__item-img" />
                                    <h4>
                                        <a href={`https://snapcraft.io/${snap.name}`} target="_blank">{snap.name}</a>
                                    </h4>
                                </div>

                                <button className="p-button--negative has-icon" onClick={() => excludeSnap(snap)}>
                                    <i className="p-icon--delete is-dark"></i>
                                    <span>Exclude</span>
                                </button>
                            </div>
                            <p className="card__content u-truncate">{snap.summary}</p>
                        </div>
                    </li>)
                }
            </ul>
        }
    </div>
}