import { useState } from "react";
import { SnapCard } from "../components/SnapCard/SnapCard";
import { useFetchData } from "../hooks/useFetchData";
import type { Snap } from "../types/snap";
import { AsyncBoundary } from "../components/AsyncBoundary/AsyncBoundary";

type ExcludedSnapResponse = Array<{
    "category": {
        name: string,
        id: string,
    },
    "snaps": Snap[]
}>

export function ExcludeSnaps() {
    const { error, loading, data, refetch } = useFetchData<ExcludedSnapResponse>('/api/excluded_snaps');

    const [includeError, setIncludeError] = useState<string | null>(null)

    const includeSnap = async (snap: Snap, category: string) => {
        try {
            const response = await fetch("/api/include_snap", {
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
            setIncludeError(null)

            await refetch()
        } catch {
            setIncludeError("An error occurred")
        }
    }

    return (
        <div className="p-panel">
            <div className="p-panel__header">
                <h4 className="p-panel__title">Excluded Snaps</h4>
            </div>
            <div className="p-panel__content">
                <div className="u-fixed-width">
                    <AsyncBoundary label="Excluded snaps" loading={loading} error={includeError || error ? "An error occurred" : undefined}>
                        <ul className="p-list" style={{ maxHeight: "650px", overflow: "scroll" }}>
                            {data?.map((info) => (
                                <div key={info.category.id}>
                                    <h5>{info.category.name}</h5>
                                    {info.snaps.map(snap => <SnapCard
                                        key={snap.snap_id}
                                        snap={snap}
                                        actionButton={
                                            <button className="p-button--positive has-icon" onClick={() => includeSnap(snap, info.category.id)}>
                                                <i className="p-icon--plus is-dark"></i>
                                                <span>Include</span>
                                            </button>
                                        }
                                    />)}
                                </div>
                            ))}
                        </ul>
                    </AsyncBoundary>
                </div>
            </div>
        </div>
    )
}