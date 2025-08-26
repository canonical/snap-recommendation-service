import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

type AsideContextType = {
    content: ReactNode;
    isOpen: boolean;
    openAside: (content: ReactNode) => void;
    closeAside: () => void;
};

const AsideContext = createContext<AsideContextType | undefined>(undefined);

export function useAside() {
    const ctx = useContext(AsideContext);
    if (!ctx) throw new Error("useAside must be used within <AsideProvider>");
    return ctx;
}

export function AsideProvider({ children }: { children: ReactNode }) {
    const [content, setContent] = useState<ReactNode | null>(null);
    const [isOpen, setIsOpen] = useState(true);

    const openAside = useCallback((newContent: ReactNode) => {
        setContent(newContent);
        setIsOpen(true);
    }, []);

    const closeAside = useCallback(() => {
        setIsOpen(false);
    }, []);
    return (
        <AsideContext.Provider value={{ content, isOpen, openAside, closeAside }}>
            {children}
        </AsideContext.Provider>
    );
}