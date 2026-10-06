from unittest.mock import patch

import pytest
from flask import Flask

from snaprecommend import db
from snaprecommend.api import api_blueprint
from snaprecommend.featuredsnaps.api import featured_blueprint
from snaprecommend.models import EditorialSlice, RecommendationCategory
from snaprecommend.packages.api import store_packages_blueprint


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SECRET_KEY="test",
        SQLALCHEMY_DATABASE_URI="sqlite://",
    )
    db.init_app(app)
    app.register_blueprint(api_blueprint, url_prefix="/api")
    app.register_blueprint(featured_blueprint, url_prefix="/featured")
    app.register_blueprint(store_packages_blueprint, url_prefix="/store")

    with app.app_context():
        db.create_all()
        db.session.add_all([
            RecommendationCategory(
                id="popular", name="Popular", description="Popular snaps",
            ),
            EditorialSlice(
                id="test-slice", name="Test slice", description="Test snaps",
            ),
        ])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.mark.parametrize("path", [
    "/api/account",
    "/api/stats",
    "/api/categories",
    "/api/category/popular",
    "/api/slices",
    "/api/slice/test-slice",
    "/api/snaps",
    "/api/recently-updated",
    "/featured/",
    "/store/store.json?q=test",
])
def test_json_get_endpoints_are_public(app, path):
    with (
        patch(
            "snaprecommend.featuredsnaps.utils.device_gateway.get_featured_snaps",
            return_value={"_embedded": {"clickindex:package": []}},
        ),
        patch(
            "snaprecommend.packages.utils.device_gateway.find",
            return_value={"results": []},
        ),
    ):
        response = app.test_client().get(path)

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() is not None


@pytest.mark.parametrize("method,path", [
    ("GET", "/api/excluded_snaps"),
    ("GET", "/api/editorial_slices"),
    ("GET", "/api/editorial_slice/test-slice"),
    ("GET", "/api/settings"),
    ("GET", "/api/featured/settings"),
    ("GET", "/api/collected_snaps/search?q=test"),
    ("GET", "/featured/history"),
    ("GET", "/featured/history/test-snap"),
    ("POST", "/api/include_snap"),
    ("POST", "/api/exclude_snap"),
    ("POST", "/api/editorial_slice"),
    ("POST", "/api/editorial_slice/test-slice"),
    ("DELETE", "/api/editorial_slice/test-slice"),
    ("POST", "/api/editorial_slice/test-slice/snaps"),
    ("POST", "/api/editorial_slice/test-slice/remove_snap"),
    ("POST", "/api/run_pipeline_step"),
    ("POST", "/api/featured/select"),
    ("PATCH", "/api/featured/settings"),
    ("POST", "/featured/"),
])
def test_previously_protected_endpoints_still_require_login(app, method, path):
    response = app.test_client().open(path, method=method, json={})

    assert response.status_code == 401
    assert response.get_json() == {"success": False, "error": "Unauthorized"}


@pytest.mark.parametrize("method,path", [
    ("GET", "/featured/history"),
    ("GET", "/featured/history/test-snap"),
    ("POST", "/api/featured/select"),
    ("PATCH", "/api/featured/settings"),
    ("POST", "/featured/"),
])
def test_previously_admin_only_endpoints_still_require_admin(app, method, path):
    client = app.test_client()
    with client.session_transaction() as session:
        session["macaroon_root"] = "root"
        session["macaroon_discharge"] = "discharge"
        session["publisher"] = {"is_admin": False}

    response = client.open(path, method=method, json={})

    assert response.status_code == 403
    assert response.get_json() == {
        "success": False,
        "error": "Admin permissions needed",
    }
