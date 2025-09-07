from snaprecommend.auth.session import device_gateway 
from typing import List, Dict, TypedDict, Any, Union


Package = TypedDict(
    "Package",
    {
        "package": Dict[
            str, Union[Dict[str, str], List[str], List[Dict[str, str]]]
        ]
    },
)


Packages = TypedDict(
    "Packages",
    {
        "packages": List[
            Dict[
                str,
                Union[Dict[str, Union[str, List[str]]], List[Dict[str, str]]],
            ]
        ]
    },
)

def get_icon(media):
    icons = [m["url"] for m in media if m["type"] == "icon"]
    if len(icons) > 0:
        return icons[0]
    return ""


def get_fetaured_snaps():
    fields = ",".join(
        [
            "package_name",
            "title",
            "summary",
            "architecture",
            "media",
            "developer_name",
            "developer_id",
            "developer_validation",
            "origin",
            "apps",
            "sections",
            "snap_id",
        ]
    )

    # TODO add pagination
    featured_snaps_response = device_gateway.get_featured_snaps(fields=fields)
    featured_snaps = featured_snaps_response.get("_embedded", {}).get("clickindex:package", [])

    for snap in featured_snaps:
        snap["icon_url"] = get_icon(snap["media"])
    return featured_snaps


def fetch_packages(fields: List[str], query_params) -> Packages:
    query = query_params.get("q", "")

    args = {
        "fields": fields,
        "query": query,
    }

    packages = device_gateway.find(**args).get("results", [])

    return packages


def paginate(
    packages: List[Packages], page: int, size: int, total_pages: int
) -> List[Packages]:
    """
    Paginates a list of packages based on the specified page and size.

    :param: packages (List[Packages]): The list of packages to paginate.
    :param: page (int): The current page number.
    :param: size (int): The number of packages to include in each page.
    :param: total_pages (int): The total number of pages.
    :returns: a list of paginated packages.

    note:
        - If the provided page exceeds the total number of pages, the last
        page will be returned.
        - If the provided page is less than 1, the first page will be returned.
    """

    if page > total_pages:
        page = total_pages
    if page < 1:
        page = 1

    start = (page - 1) * size
    end = start + size
    if end > len(packages):
        end = len(packages)

    return packages[start:end]


def parse_package_for_card(package: Dict[str, Any]) -> Package:
    resp = {
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


def get_packages(
    fields: List[str],
    size: int = 10,
    query_params: Dict[str, Any] = {},
) -> List[Dict[str, Any]]:
    packages = fetch_packages(fields, query_params)

    total_pages = -(len(packages) // -size)

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
    