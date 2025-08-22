import { useEffect, useState } from "react";
import type { Snap } from "../types/snap";


export function useFetchSnaps(path: string) {
    const [snaps, setSnaps] = useState<Snap[] | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        void fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const response = await fetch(path);
            if (!response.ok) {
                throw new Error("Failed to fetch snaps.");
            }

            const parsedResult = await response.json();
            setSnaps(parsedResult.snaps);
            setLoading(false);
        } catch (err: any) {
            setError(err.message);
            setLoading(false);
        }
    }

    return {
        snaps, loading, error, refetch: fetchData
    }
}