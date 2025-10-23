import { createContext, type ReactNode } from "react";

type AsideContextType = {
    content: ReactNode;
    isOpen: boolean;
    openAside: (content: ReactNode) => void;
    closeAside: () => void;
};

export const AsideContext = createContext<AsideContextType | undefined>(undefined);

