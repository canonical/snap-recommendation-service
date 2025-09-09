import { useEffect } from "react";
import { useApi } from "./useApi";

export function useFetchData<T>(path: string) {
    const { data, error, loading, sendRequest } = useApi<T>()

    const fetchData = async () => sendRequest(path);

    useEffect(() => {
        void fetchData();
    }, []);

    return {
        data, loading, error, refetch: fetchData
    }
}