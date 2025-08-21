import { useEffect, useState } from "react";


export function useFetchSnaps(path: string) {
    const [snaps, setSnaps] = useState<{ snaps: any[] } | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = () => {
        fetch(path)
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Failed to fetch snaps.");
                }
                return response.json();
            })
            .then((json) => {
                setSnaps(json);
                setLoading(false);
            })
            .catch((err) => {
                setError(err.message);
                setLoading(false);
            });
    }

    return {
        snaps, loading, error, refetch: fetchData
    }
}