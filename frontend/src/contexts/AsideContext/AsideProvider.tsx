import { useCallback, useState, type ReactNode } from "react";
import { AsideContext } from "./AsideContext";

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