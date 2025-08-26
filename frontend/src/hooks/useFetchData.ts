import { useEffect, useState } from "react";

export function useFetchData<T>(path: string) {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = async () => {
        try {
            const response = await fetch(path);
            if (!response.ok) {
                throw new Error("Failed to fetch data.");
            }

            const parsedResult = await response.json();
            setData(parsedResult);
            setLoading(false);
        } catch {
            setError("An error occurred.");
            setLoading(false);
        }
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
    useEffect(() => {
        void fetchData();
    }, []);

    return {
        data, loading, error, refetch: fetchData
    }
}