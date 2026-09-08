import { Panel } from "@canonical/react-components";
import { useLocation } from "react-router-dom";
import "./LoginRequired.scss";

export function LoginRequired() {
    const { pathname, search } = useLocation();
    const next = encodeURIComponent(`${pathname}${search}`);

    return (
        <Panel contentClassName="login-required__content">
            <div className="login-required__body">
                <h4>Please log in to see this page</h4>
                <p>You need to be signed in to view the snap recommendations dashboard.</p>
                <a className="p-button--positive" href={`/login?next=${next}`}>
                    Log in
                </a>
            </div>
        </Panel>
    );
}
