import { Link } from "react-router-dom";
import "./LayoutLogo.scss";

export function LayoutLogo() {
    return <Link to="/v2/dashboard" className=" p-panel__logo">
        <img src="https://assets.ubuntu.com/v1/dae35907-Snapcraft%20tag.svg"
            alt="Snapcraft Recommendations"
            className="layout-logo__img p-panel__logo-image"
        />
        <div className="is-fading-when-collapsed">
            <h4 className="layout-logo__title u-no-margin p-text--default u-align-text--left u-text-light">
                Snap recommendations
            </h4>
        </div>
    </Link>
}