import { useFetchData } from "../hooks/useFetchData";
import type { FeaturedSnap } from "../types/snap";


export function FeaturedSnaps() {
    const { data, loading, error } = useFetchData<FeaturedSnap[]>('/featured');
    return <div>
        { loading ? "Loading...": "" }
        { error ? "Error" : "" }
        { data && JSON.stringify(data, null, 5) }
    </div>
}