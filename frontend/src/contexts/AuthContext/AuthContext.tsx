import { createContext } from "react";
import type { Publisher } from "../../types/publisher";

type AuthContextType = {
    authenticated: boolean;
    loading: boolean;
    publisher: Publisher | null;
    setUnauthenticated: () => void;
};

export const AuthContext = createContext<AuthContextType | undefined>(undefined);
