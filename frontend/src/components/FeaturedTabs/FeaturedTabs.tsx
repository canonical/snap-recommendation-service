import { Tabs } from "@canonical/react-components";
import { Link, useLocation } from "react-router-dom";

const TABS = [
    { label: "Current list", to: "/dashboard/featured" },
    { label: "History", to: "/dashboard/featured_history" },
];

export function FeaturedTabs() {
    const { pathname } = useLocation();

    return (
        <Tabs
            links={TABS.map((tab) => ({
                label: tab.label,
                active: pathname === tab.to,
                component: Link,
                to: tab.to,
            }))}
        />
    );
}
