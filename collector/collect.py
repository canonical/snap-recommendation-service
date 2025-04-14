import logging
from typing import Tuple
import requests
import datetime
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from snaprecommend import db
from snaprecommend.models import Snap, PipelineSteps
from snaprecommend.logic import add_pipeline_step_log


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

URL = f"http://api.snapcraft.io/api/v1/snaps/search?fields={','.join(FIELDS)}&confinement=strict,classic"


logger = logging.getLogger("collector")


def parse_snap_from_response(snap: dict) -> dict:
    website = snap["links"].get("website", [])
    website = website[0] if len(website) else None

    # same for contact
    contact = snap["links"].get("contact", [])
    contact = contact[0] if len(contact) else None

    icon = next(filter(lambda x: x["type"] == "icon", snap["media"]), None)
    return {
        "snap_id": snap["snap_id"],
        "name": snap["package_name"],
        "icon": icon["url"] if icon else None,
        "summary": snap["summary"],
        "description": snap["description"],
        "title": snap["title"],
        "website": website,
        "version": snap["version"],
        "publisher": snap["publisher"],
        "revision": snap["revision"],
        "contact": contact,
        "links": snap["links"],
        "media": snap["media"],
        "developer_validation": snap["developer_validation"],
        "license": snap["license"],
        "last_updated": datetime.datetime.fromisoformat(snap["last_updated"]),
    }


def upsert_snap(session: Session, snap):
    """
    Upserts a snap into the database.

    :param session: The database session.
    :param snap: The snap to upsert (from the API response)
    """

    snap_object = Snap(**parse_snap_from_response(snap))

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
    has_next = True

    while has_next:
        snaps, has_next = get_snap_page(page)
        total_snaps += len(snaps)
        try:
            bulk_upsert_snaps(db.session, snaps)
        except Exception as e:
            logger.error(f"Error during bulk upsert on page {page}: {e}")
            raise

        db.session.commit()
        logger.info(f"Page {page} processed with {len(snaps)} snaps.")
        if not has_next:
            break
        page += 1
    return total_snaps


def bulk_upsert_snaps(session: Session, snaps: list):
    """
    Performs a bulk upsert of snaps into the database.

    :param session: The database session.
    :param snaps: A list of snaps to upsert.
    """
    logger.debug("Preparing bulk upsert.")

    snap_data = []
    for snap in snaps:

        snap_data.append(parse_snap_from_response(snap))

    if snap_data:
        stmt = insert(Snap).values(snap_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=["snap_id"],
            set_={
                "name": stmt.excluded.name,
                "icon": stmt.excluded.icon,
                "summary": stmt.excluded.summary,
                "description": stmt.excluded.description,
                "title": stmt.excluded.title,
                "website": stmt.excluded.website,
                "version": stmt.excluded.version,
                "publisher": stmt.excluded.publisher,
                "revision": stmt.excluded.revision,
                "contact": stmt.excluded.contact,
                "links": stmt.excluded.links,
                "media": stmt.excluded.media,
                "developer_validation": stmt.excluded.developer_validation,
                "license": stmt.excluded.license,
                "last_updated": stmt.excluded.last_updated,
            },
        )

        session.execute(stmt)


def collect_initial_snap_data():
    logger.info("Starting the snap data ingestion process.")
    try:
        snaps_count = insert_snaps()
        add_pipeline_step_log(PipelineSteps.COLLECT, True)
        logger.info(
            f"Snap data ingestion process completed. {snaps_count} snaps inserted."
        )
    except Exception as e:
        logger.error(f"Error during snap data ingestion: {e}")
        add_pipeline_step_log(PipelineSteps.COLLECT, False, str(e))
        raise
