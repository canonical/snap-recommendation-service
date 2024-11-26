import logging
from typing import Tuple
import requests
import datetime
import json
from sqlalchemy.orm import Session
from models import Snap
from db import engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

FIELDS = (
    "snap_id",
    "package_name",
    "last_updated",
    "summary",
    "description",
    "title",
    "version",
    "publisher",
    "revision",
    "links",
    "media",
    "developer_validation",
    "license",
)

URL = f"http://api.snapcraft.io/api/v1/snaps/search?fields={','.join(FIELDS)}"

BATCH_SIZE = 100

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logger = logging.getLogger("collector")


def upsert_snap(session, snap):
    # website can be either a list of multiple websites or one string
    website = snap["links"].get("website", [])
    website = website[0] if len(website) else None

    # same for contact
    contact = snap["links"].get("contact", [])
    contact = contact[0] if len(contact) else None

    icon = next(filter(lambda x: x["type"] == "icon", snap["media"]), None)

    snap_object = Snap(
        snap_id=snap["snap_id"],
        name=snap["package_name"],
        icon=icon["url"] if icon else None,
        summary=snap["summary"],
        description=snap["description"],
        title=snap["title"],
        website=website,
        version=snap["version"],
        publisher=snap["publisher"],
        revision=snap["revision"],
        contact=contact,
        links=json.dumps(snap["links"]),
        media=json.dumps(snap["media"]),
        developer_validation=snap["developer_validation"],
        license=snap["license"],
        last_updated=datetime.datetime.fromisoformat(snap["last_updated"]),
    )

    logger.debug(f"Upserting snap: {snap['title']} (ID: {snap['snap_id']})")

    session.merge(snap_object)


def get_snap_page(page: int) -> Tuple[list, bool]:
    """
    Fetches a single page of snaps from the API.

    :param page: The page number to fetch.
    :return: A tuple containing the list of snaps and a
             boolean indicating if there are more pages.
    """
    response = requests.get(f"{URL}&page={page}")
    response.raise_for_status()
    data = response.json()
    snaps = data["_embedded"]["clickindex:package"]
    has_next = "next" in data["_links"]
    return snaps, has_next


def insert_snaps() -> int:
    """
    Inserts all searchable snaps from the API into the database.

    :return: The total number of snaps inserted.
    """
    page = 1
    total_snaps = 0
    session = Session(bind=engine)
    while True:
        snaps, has_next = get_snap_page(page)
        total_snaps += len(snaps)
        for snap in snaps:
            try:
                upsert_snap(session, snap)
            except Exception as e:
                logger.error(f"Error inserting snap {snap['snap_id']}: {e}")

        session.commit()
        logger.info(f"Page {page} inserted")
        if not has_next:
            break
        page += 1
    return total_snaps


def collect_initial_snap_data():
    logger.info("Starting the snap data ingestion process.")
    snaps_count = insert_snaps()
    logger.info(f"Snap data ingestion process completed. {snaps_count} snaps inserted.")


if __name__ == "__main__":
    collect_initial_snap_data()
