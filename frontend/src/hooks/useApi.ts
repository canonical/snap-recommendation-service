import { useContext, useState } from "react";
import { AuthContext } from "../contexts/AuthContext/AuthContext";

export function useApi<T>() {
    const auth = useContext(AuthContext);
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const sendRequest = async (path: string, options?: RequestInit) => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(path, options);
            if (!response.ok) {
                if (response.status === 401) {
                    auth?.setUnauthenticated();
                }
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

    return { data, loading, error, sendRequest };
}