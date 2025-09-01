import { useFetchData } from "../../hooks/useFetchData";
import { useState } from "react";
import "./CategoryList.scss";
import type { Snap } from "../../types/snap";
import { SnapCard } from "../SnapCard/SnapCard";
import { AsyncBoundary } from "../AsyncBoundary/AsyncBoundary";

type SnapResponse = {
    snaps: Snap[]
}

export const CategoryList = ({ category, label }: { category: string, label: string }) => {
    const { error, loading, data, refetch } = useFetchData<SnapResponse>(`/api/snaps?category=${category}`);

    const [excludeError, setExcludeError] = useState<string | null>(null)

    const excludeSnap = async (snap: Snap) => {
        try {
            const response = await fetch("/api/exclude_snap", {
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

    return <AsyncBoundary label={label} loading={loading} error={excludeError || error ? "An error occurred" : undefined}>
        {data &&
            <ul className="p-list category-list">
                {
                    data.snaps.map((snap) => <SnapCard
                        key={snap.snap_id}
                        snap={snap}
                        actionButton={
                            <button className="p-button--negative has-icon" onClick={() => excludeSnap(snap)}>
                                <i className="p-icon--delete is-dark"></i>
                                <span>Exclude</span>
                            </button>
                        }
                    />)
                }
            </ul>
        }
    </AsyncBoundary>
}