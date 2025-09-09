import { useFetchData } from "../../hooks/useFetchData";
import "./CategoryList.scss";
import type { Snap } from "../../types/snap";
import { SnapCard } from "../SnapCard/SnapCard";
import { AsyncBoundary } from "../AsyncBoundary/AsyncBoundary";
import { useApi } from "../../hooks/useApi";

type SnapResponse = {
    snaps: Snap[]
}

export const CategoryList = ({ category, label }: { category: string, label: string }) => {
    const { error, loading, data, refetch } = useFetchData<SnapResponse>(`/api/snaps?category=${category}`);
    const { sendRequest, error: excludeError } = useApi();

    const excludeSnap = async (snap: Snap) => {
        await sendRequest("/api/exclude_snap", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                "snap_id": snap.snap_id,
                "category": category
            }),
        });
        await refetch();
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