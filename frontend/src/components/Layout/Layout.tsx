import { ApplicationLayout } from "@canonical/react-components";
import { Outlet, Link } from "react-router-dom";
import { LayoutLogo } from "./LayoutLogo/LayoutLogo";
import { useAside } from "../../hooks/useAside";
import { useAuth } from "../../hooks/useAuth";
import { LoginRequired } from "../LoginRequired/LoginRequired";



export function Layout() {
    const { content, isOpen } = useAside();
    const { authenticated, loading } = useAuth();

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
                    to: "/dashboard"
                }, {
                    icon: "delete",
                    component: Link,
                    label: "Excluded snaps",
                    to: "/dashboard/excluded_snaps"
                }, {
                    icon: "copy",
                    component: Link,
                    label: "Editorial Slices",
                    to: "/dashboard/editorial_slices"
                }, {
                    icon: "show",
                    component: Link,
                    label: "Featured",
                    to: "/dashboard/featured"
                }, {
                    icon: "menu",
                    component: Link,
                    label: "Settings",
                    to: "/dashboard/settings"
                }]
            }]}
            aside={isOpen ? content : null}
        >
            {loading ? null : authenticated ? <Outlet /> : <LoginRequired />}
        </ApplicationLayout>
    );
}
