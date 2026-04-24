import { useEffect, useRef, useState } from "react";
import type { SearchSnap } from "../../types/snap";
import { FindSnapResults } from "./FindSnapResults";
import "./FindSnap.scss";

type FindSnapProps = {
    addSnap: (snap: SearchSnap) => void;
    searchEndpoint?: string;
    excludedPackageNames?: string[];
    disabled?: boolean;
}

export function FindSnap({ addSnap, searchEndpoint = "/store/store.json", excludedPackageNames = [], disabled = false }: FindSnapProps) {
    const searchSnap = async (queryString: string): Promise<SearchSnap[]> => {
        const response = await fetch(`${searchEndpoint}?q=${queryString}`);
        const responseJson = await response.json();
        return responseJson.data ? responseJson.data.packages : responseJson.packages;
    };

    const inputRef = useRef<HTMLInputElement>(null);
    const [searchQuery, setSearchQuery] = useState<string>("");
    const [focused, setFocused] = useState(false);

    const [storePackages, setStorePackages] = useState<SearchSnap[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        (async () => {
            if (searchQuery && searchQuery.length > 2) {
                setLoading(true);
                setStorePackages([]);
                const packages = await searchSnap(searchQuery);
                setStorePackages(packages);
                setLoading(false);
            } else {
                setStorePackages([])
            }
        })()
    }, [searchQuery])

    const handleSearch = (e: React.FormEvent<HTMLInputElement>) => {
        e.preventDefault();
        setSearchQuery(e.currentTarget.value);
    };

    const handleClick = (snap: SearchSnap) => {
        setSearchQuery("");
        if (inputRef.current) {
            inputRef.current.value = "";
        }
        addSnap(snap);
    };

    const handleFocus = () => setFocused(true);
    const handleBlur = () => setFocused(false);

    return (
        <div className="snap-search">
            <input
                className="p-form-validation__input snap-search__input"
                type="text"
                name="snap"
                onChange={handleSearch}
                onFocus={handleFocus}
                onBlur={handleBlur}
                ref={inputRef}
                placeholder="Search for a snap"
                disabled={disabled}
            />
            {focused && searchQuery.length > 2 && (
                <FindSnapResults
                    loading={loading}
                    packages={storePackages?.filter((snap) => !excludedPackageNames.includes(snap.package.name)) ?? []}
                    onSelect={handleClick}
                />
            )}
        </div>

    );
}
