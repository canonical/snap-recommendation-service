import { useContext } from "react";
import { AsideContext } from "../contexts/AsideContext/AsideContext";

export function useAside() {
    const ctx = useContext(AsideContext);
    if (!ctx) throw new Error("useAside must be used within <AsideProvider>");
    return ctx;
}
