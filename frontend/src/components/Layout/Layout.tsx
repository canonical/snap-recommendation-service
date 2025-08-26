import { ApplicationLayout } from "@canonical/react-components";
import { Outlet, Link } from "react-router-dom";
import { LayoutLogo } from "./LayoutLogo/LayoutLogo";
import { AsideProvider, useAside } from "../../contexts/AsideContext";



export function Layout() {
    const { content, isOpen } = useAside();


    return (

        <ApplicationLayout
            logo={{
                name: "",
                icon: "",
                component: LayoutLogo,
            }}
            navItems={[{
                items: [{
                    icon: "information",
                    component: Link,
                    label: "Dashboard",
                    to: "/v2/dashboard"
                }, {
                    icon: "delete",
                    component: Link,
                    label: "Excluded snaps",
                    to: "/v2/dashboard/excluded_snaps"
                }, {
                    icon: "copy",
                    component: Link,
                    label: "Editorial Slices",
                    to: "/v2/dashboard/editorial_slices"
                }, {
                    icon: "menu",
                    component: Link,
                    label: "Settings",
                    to: "/v2/dashboard/settings"
                }]
            }]}
            aside={isOpen ? content : null}
        >
            <Outlet />
        </ApplicationLayout>
    );
}
