import { useCallback, useEffect, useState, type ReactNode } from "react";
import { AuthContext } from "./AuthContext";
import type { AccountResponse, Publisher } from "../../types/publisher";

export function AuthProvider({ children }: { children: ReactNode }) {
    const [authenticated, setAuthenticated] = useState(false);
    const [publisher, setPublisher] = useState<Publisher | null>(null);
    const [loading, setLoading] = useState(true);

    const setUnauthenticated = useCallback(() => {
        setAuthenticated(false);
        setPublisher(null);
    }, []);

    useEffect(() => {
        let active = true;

        const fetchAccount = async () => {
            try {
                const response = await fetch("/api/account");
                if (!response.ok) throw new Error("Failed to fetch account.");
                const account: AccountResponse = await response.json();
                if (!active) return;
                setAuthenticated(account.authenticated);
                setPublisher(account.publisher ?? null);
            } catch {
                if (!active) return;
                setAuthenticated(false);
                setPublisher(null);
            } finally {
                if (active) setLoading(false);
            }
        };

        void fetchAccount();
        return () => {
            active = false;
        };
    }, []);

    return (
        <AuthContext.Provider value={{ authenticated, loading, publisher, setUnauthenticated }}>
            {children}
        </AuthContext.Provider>
    );
}
