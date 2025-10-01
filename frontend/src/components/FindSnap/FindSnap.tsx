import { useEffect, useRef, useState } from "react";
import type { SearchSnap } from "../../types/snap";
import { Spinner } from "@canonical/react-components";
import "./FindSnap.scss";

export function FindSnap({ addSnap }: { addSnap: (snap: SearchSnap) => void }) {
    const searchSnap = async (queryString: string): Promise<SearchSnap[]> => {
        const response = await fetch(`/store/store.json?q=${queryString}`);
        const responseJson = await response.json();
        return responseJson.packages;
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
        setFocused(false);
        addSnap(snap);
    };

    const handleFocus = () => setFocused(true);

    return (
        <div className="snap-search">
            <input
                className="p-form-validation__input snap-search__input"
                type="text"
                name="snap"
                onChange={handleSearch}
                onFocus={handleFocus}
                ref={inputRef}
                placeholder="Search for a snap"
            />
            {focused && searchQuery.length > 2 && (
                <div className="snap-search__list">
                    {
                        loading && <div>
                            <Spinner isLight className="snap-search__spinner" /> <span>Loading...</span>
                        </div>
                    }
                    {storePackages?.map((snap) => (
                        <div
                            key={snap.package.name}
                            onClick={() => handleClick(snap)}
                            className="snap-search__item"
                        >
                            {snap.package.icon_url && <div>
                                <img
                                    src={snap.package.icon_url}
                                    alt={snap.package.name}
                                    width="32"
                                    className="snap-search__item-img"
                                />
                            </div>
                            }
                            <div>
                                <h3 className="p-heading--5 u-no-margin u-no-padding">
                                    {snap.package.display_name}
                                </h3>
                                <p className="u-no-margin u-text--muted">
                                    <em>{snap.publisher.display_name}</em>
                                </p>
                                <p className="u-no-margin">{snap.package.description}</p>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>

    );
}
