from snaprecommend.auth.session import device_gateway
from snaprecommend.utils import get_icon


def fetch_packages(fields, query_params):
    query = query_params.get("q", "")
    args = {
        "fields": fields,
        "query": query,
    }

    packages = device_gateway.find(**args).get("results", [])

    return packages


def paginate(
    packages, page: int, size: int, total_pages: int
):
    if page > total_pages:
        page = total_pages
    if page < 1:
        page = 1

    start = (page - 1) * size
    end = start + size
    if end > len(packages):
        end = len(packages)

    return packages[start:end]


def parse_package_for_card(package):
    resp = {
        "snap_id": "",
        "package": {
            "description": "",
            "display_name": "",
            "icon_url": "",
            "name": "",
            "platforms": [],
            "type": "",
        },
        "publisher": {"display_name": "", "name": "", "validation": ""},
        "categories": [],
    }
    snap = package.get("snap", {})
    publisher = snap.get("publisher", {})
    resp["snap_id"] = package.get("snap-id", "")
    resp["package"]["description"] = snap.get("summary", "")
    resp["package"]["display_name"] = snap.get("title", "")
    resp["package"]["type"] = "snap"
    resp["package"]["name"] = package.get("name", "")
    resp["publisher"]["display_name"] = publisher.get("display-name", "")
    resp["publisher"]["name"] = publisher.get("username", "")
    resp["publisher"]["validation"] = publisher.get("validation", "")
    resp["categories"] = snap.get("categories", [])
    resp["package"]["icon_url"] = get_icon(package["snap"]["media"])

    return resp


def get_packages(fields, size=10, query_params={}):
    packages = fetch_packages(fields, query_params)
    total_pages = -(len(packages) // -size)

    total_items = len(packages)
    page = int(query_params.get("page", 1))
    packages_per_page = paginate(packages, page, size, total_pages)
    parsed_packages = []
    for package in packages_per_page:
        parsed_packages.append(parse_package_for_card(package))
    res = parsed_packages

    return {
        "packages": res,
        "total_pages": total_pages,
        "total_items": total_items,
    }
