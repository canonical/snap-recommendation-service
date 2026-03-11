import { SnapCard } from "../components/SnapCard/SnapCard";
import { useFetchData } from "../hooks/useFetchData";
import type { Snap } from "../types/snap";
import { AsyncBoundary } from "../components/AsyncBoundary/AsyncBoundary";
import { useApi } from "../hooks/useApi";

export function ExcludeSnaps() {
    const { error, loading, data, refetch } = useFetchData<Snap[]>('/api/excluded_snaps');
    const { sendRequest, error: includeError } = useApi();

    const includeSnap = async (snap: Snap) => {
        await sendRequest("/api/include_snap", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                "snap_id": snap.snap_id
            }),
        });
        await refetch();
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
                            <h5>Globally excluded (all categories)</h5>
                            {data?.map(snap => <SnapCard
                                key={snap.snap_id}
                                snap={snap}
                                actionButton={
                                    <button className="p-button--positive has-icon" onClick={() => includeSnap(snap)}>
                                        <i className="p-icon--plus is-dark"></i>
                                        <span>Include</span>
                                    </button>
                                }
                            />)}
                        </ul>
                    </AsyncBoundary>
                </div>
            </div>
        </div>
    )
}
