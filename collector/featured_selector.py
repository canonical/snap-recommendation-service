import logging
import os
import random
from datetime import datetime, timedelta, timezone

from collector.score import calculate_dev_score, calculate_metadata_score
from config import MACAROON_ENV_PATH
from snaprecommend import db
from snaprecommend.auth.session import device_gateway, publisher_gateway
from snaprecommend.logic import (
    acquire_featured_selection_lock,
    add_pipeline_step_log,
    record_featured_history,
    release_featured_selection_lock,
)
from snaprecommend.models import FeaturedHistory, PipelineSteps, Snap
from snaprecommend.settings import get_settings_by_keys, set_setting

logger = logging.getLogger("collector.featured")

_DEFAULTS = {
    "featured_candidate_pool_size": 50,  # Number of top-ranked snaps to pick randomly from.
    "featured_category_cap": 4,  # Max category repeats allowed per category during fill.
    "featured_min_rating": 0.0,  # Minimum allowed rating; 0 because snap ratings are borked.
    "featured_recency_days": 180,  # Snap must have been updated within this many days.
    "featured_history_window_days": 365,  # Exclude snaps auto-featured in this lookback window.
    "featured_target_count": 15,  # Desired size of the final featured list.
}

SERVER_CLOUD_CATEGORY_SLUG = "server-and-cloud"
DEV_CATEGORY_SLUG = "development"
GAME_CATEGORY_SLUG = "games"
CANONICAL_PUBLISHER_ID = "canonical"


def _is_canonical(snap: Snap) -> bool:
    """Return whether the snap publisher is Canonical."""
    return (snap.publisher or "").lower() == CANONICAL_PUBLISHER_ID.lower()


FEATURED_PUBLISHER_TOKEN_ENV = "FLASK_FEATURED_PUBLISHER_TOKEN"


def _cfg(keys: list[str]) -> dict:
    """Return typed settings for *keys*, using defaults when unset."""
    settings = get_settings_by_keys(keys)
    resolved = {}

    for key in keys:
        setting = settings.get(key)
        value = setting.value if setting and setting.value is not None else None
        if value is None:
            resolved[key] = _DEFAULTS[key]
            continue

        default = _DEFAULTS[key]
        if isinstance(default, list):
            resolved[key] = value if isinstance(value, list) else default
        else:
            resolved[key] = type(default)(value)

    return resolved


def _snap_category_slugs(snap: Snap) -> set:
    """Return a set of category slugs for a snap."""
    slugs = set()
    for item in snap.categories or []:
        if isinstance(item, dict):
            slug = item.get("slug") or item.get("name") or ""
        else:
            slug = str(item)
        if slug:
            slugs.add(slug)
    return slugs


def _has_category(snap: Snap, target_slug: str) -> bool:
    return target_slug in _snap_category_slugs(snap)


def _has_any_category(snap: Snap, target_slugs: set) -> bool:
    return bool(_snap_category_slugs(snap) & target_slugs)


def _minmax_normalise(values: dict) -> dict:
    """Min-max normalise a {snap_id: value} dict to 0-1. None → 0."""
    valid = [v for v in values.values() if v is not None]
    if not valid:
        return {k: 0.0 for k in values}
    mn, mx = min(valid), max(valid)
    if mn == mx:
        return {k: 1.0 if v is not None else 0.0 for k, v in values.items()}
    return {
        k: (v - mn) / (mx - mn) if v is not None else 0.0
        for k, v in values.items()
    }


def _get_recently_auto_featured_ids(window_days: int) -> set:
    since = datetime.now(timezone.utc) - timedelta(days=window_days)
    rows = (
        db.session.query(FeaturedHistory.snap_id)
        .filter(FeaturedHistory.is_manual.is_(False))
        .filter(FeaturedHistory.featured_at >= since)
        .all()
    )
    return {r.snap_id for r in rows}


def _apply_hard_gates(
    recency_days: int,
    history_window_days: int,
    min_rating: float,
) -> list:
    recency_cutoff = datetime.now(timezone.utc) - timedelta(days=recency_days)
    recently_featured = _get_recently_auto_featured_ids(history_window_days)

    candidates = (
        db.session.query(Snap)
        .filter(Snap.reaches_min_threshold.is_(True))
        .filter(Snap.excluded.is_(False))
        .filter(Snap.developer_validation.in_(["verified", "starred"]))
        .filter(Snap.last_updated >= recency_cutoff)
        .all()
    )

    filtered = []
    for snap in candidates:
        if snap.snap_id in recently_featured:
            continue
        if _has_category(snap, SERVER_CLOUD_CATEGORY_SLUG):
            continue
        # Only reject if we have a rating below the floor.
        if snap.raw_rating is not None and snap.raw_rating < min_rating:
            continue
        filtered.append(snap)

    return filtered


def _rank_candidates(candidates: list, recency_days: int) -> tuple[list, dict]:
    """Return candidates sorted by composite score (highest first)."""
    recency_cutoff = (
        datetime.now(timezone.utc) - timedelta(days=recency_days)
    ).replace(tzinfo=None)

    downloads_scores = {s.snap_id: s.active_devices or 0 for s in candidates}
    recency_scores = {
        s.snap_id: max(0.0, (s.last_updated - recency_cutoff).total_seconds())
        for s in candidates
    }
    metadata_scores = {s.snap_id: calculate_metadata_score(s) for s in candidates}
    dev_scores = {s.snap_id: calculate_dev_score(s) for s in candidates}

    norm_dev = _minmax_normalise(downloads_scores)
    norm_rec = _minmax_normalise(recency_scores)

    composite = {
        s.snap_id: (
            norm_dev[s.snap_id] * 0.4
            + metadata_scores[s.snap_id] * 0.3
            + dev_scores[s.snap_id] * 0.2
            + norm_rec[s.snap_id] * 0.1
        )
        for s in candidates
    }

    return sorted(candidates, key=lambda s: composite[s.snap_id], reverse=True), composite


def _enforce_canonical_mix(top3: list, remaining: list) -> tuple:
    """Ensure top3 has at least 1 and at most 2 Canonical snaps."""
    top3 = list(top3)
    remaining = list(remaining)

    canonical_count = sum(1 for s in top3 if _is_canonical(s))

    if canonical_count == 0:
        pool = [s for s in remaining if _is_canonical(s)]
        if not pool:
            raise ValueError(
                "No Canonical snap in candidate pool — cannot satisfy top-3 mix rule."
            )
    elif canonical_count == 3:
        pool = [s for s in remaining if not _is_canonical(s)]
        if not pool:
            raise ValueError(
                "All top-3 candidates are Canonical and no non-Canonical alternative exists."
            )
    else:
        return top3, remaining

    insert = pool[0]
    displaced = top3[-1]
    top3[-1] = insert
    remaining.remove(insert)
    remaining.append(displaced)

    return top3, remaining


def _reserve_category_slots(top3: list, remaining: list) -> tuple:
    """Reserve snaps to satisfy category minimums."""
    dev_needed = max(0, 2 - sum(1 for s in top3 if _has_category(s, DEV_CATEGORY_SLUG)))
    game_needed = max(0, 1 - sum(1 for s in top3 if _has_category(s, GAME_CATEGORY_SLUG)))

    reserved = []
    leftover = []
    for snap in remaining:
        is_dev = dev_needed > 0 and _has_category(snap, DEV_CATEGORY_SLUG)
        is_game = game_needed > 0 and _has_category(snap, GAME_CATEGORY_SLUG)
        if is_dev or is_game:
            roles = (["development"] if is_dev else []) + (["game"] if is_game else [])
            reserved.append((snap, "category-" + "+".join(roles)))
            dev_needed -= is_dev
            game_needed -= is_game
        else:
            leftover.append(snap)

    if dev_needed > 0:
        raise ValueError(
            f"Not enough development snaps in candidate pool "
            f"(still need {dev_needed} more)."
        )
    if game_needed > 0:
        raise ValueError(
            f"Not enough game snaps in candidate pool "
            f"(still need {game_needed} more)."
        )

    return reserved, leftover


def _fill_slots(
    top3: list,
    reserved: list,
    remaining: list,
    target_count: int,
    category_cap: int,
) -> list:
    """Fill remaining slots, relaxing category cap only if needed."""
    filled = []
    open_slots = target_count - len(top3) - len(reserved)
    if open_slots <= 0:
        return filled

    cat_counts: dict = {}
    for snap in top3:
        for slug in _snap_category_slugs(snap):
            cat_counts[slug] = cat_counts.get(slug, 0) + 1
    for snap, _ in reserved:
        for slug in _snap_category_slugs(snap):
            cat_counts[slug] = cat_counts.get(slug, 0) + 1

    def _would_exceed_cap(snap, cap):
        slugs = _snap_category_slugs(snap)
        return slugs and any(cat_counts.get(s, 0) >= cap for s in slugs)

    for snap in remaining:
        if len(filled) >= open_slots:
            break
        if not _would_exceed_cap(snap, category_cap):
            filled.append(snap)
            for slug in _snap_category_slugs(snap):
                cat_counts[slug] = cat_counts.get(slug, 0) + 1

    if len(filled) < open_slots:
        logger.warning(
            "Category cap prevented filling all slots; relaxing cap to complete the list."
        )
        for snap in remaining:
            if len(filled) >= open_slots:
                break
            if snap not in filled:
                filled.append(snap)

    return filled


def _get_current_featured_snap_ids() -> list:
    """Fetch current featured snap IDs from the store."""
    snaps = device_gateway.get_featured_snaps()
    currently_featured_snaps = snaps.get("_embedded", {}).get("clickindex:package", [])
    return [snap["snap_id"] for snap in currently_featured_snaps]


def _publish_to_store(token: str, new_snap_ids: list) -> list:
    """Replace the live featured list and return the previous snap IDs."""
    current_ids = _get_current_featured_snap_ids()

    if current_ids:
        delete_resp = publisher_gateway.delete_featured_snaps(
            token, {"packages": current_ids}
        )
        if delete_resp.status_code != 201:
            raise RuntimeError(
                f"Failed to delete current featured snaps "
                f"(status {delete_resp.status_code})."
            )

    update_resp = publisher_gateway.update_featured_snaps(
        token, {"packages": new_snap_ids}
    )
    if update_resp.status_code not in (200, 201):
        try:
            publisher_gateway.update_featured_snaps(token, {"packages": current_ids})
        except Exception:
            logger.exception("Failed to restore previous featured list after update failure.")
        raise RuntimeError(
            f"Failed to update featured snaps in store "
            f"(status {update_resp.status_code})."
        )

    return current_ids


def _rollback_store(token: str, previous_ids: list) -> None:
    """Best-effort restore of the store to *previous_ids* after a failure."""
    try:
        publisher_gateway.update_featured_snaps(token, {"packages": previous_ids})
    except Exception:
        logger.exception(
            "Failed to roll back featured list in store after history recording failure."
        )


def run_selection() -> tuple:
    """Run selection and return (events, snap_ids)."""
    cfg = _cfg([
        "featured_candidate_pool_size",
        "featured_category_cap",
        "featured_min_rating",
        "featured_recency_days",
        "featured_history_window_days",
        "featured_target_count",
    ])
    pool_size = cfg["featured_candidate_pool_size"]
    category_cap = cfg["featured_category_cap"]
    min_rating = cfg["featured_min_rating"]
    recency_days = cfg["featured_recency_days"]
    history_window = cfg["featured_history_window_days"]
    target_count = cfg["featured_target_count"]

    candidates = _apply_hard_gates(recency_days, history_window, min_rating)
    if not candidates:
        raise ValueError("No eligible candidates after hard gates.")

    ranked, composite = _rank_candidates(candidates, recency_days)

    pool = ranked[:pool_size]
    seed = int(datetime.now(timezone.utc).timestamp())
    rng = random.Random(seed)
    logger.info("Random seed for this selection run: %d", seed)
    rng.shuffle(pool)

    top3 = pool[:3]
    remaining = pool[3:]
    top3, remaining = _enforce_canonical_mix(top3, remaining)

    reserved, remaining = _reserve_category_slots(top3, remaining)

    filled = _fill_slots(top3, reserved, remaining, target_count, category_cap)

    final: list = (
        [(s, "top-3") for s in top3]
        + reserved
        + [(s, "fill") for s in filled]
    )

    if len(final) < 3:
        raise ValueError(
            f"Selection produced only {len(final)} snaps; minimum is 3."
        )

    ranking_key = (
        "composite(active_devices*0.4 + metadata*0.3 + dev_validation*0.2 "
        "+ recency*0.1)"
    )
    events = [
        {
            "snap_id": snap.snap_id,
            "selection_reason": {
                "role": role,
                "canonical": _is_canonical(snap),
                "developer_validation": snap.developer_validation,
                "categories": list(_snap_category_slugs(snap)),
                "ranking_key": ranking_key,
                "ranking_value": composite.get(snap.snap_id),
                "random_seed": seed,
            },
        }
        for snap, role in final
    ]
    snap_ids = [e["snap_id"] for e in events]
    return events, snap_ids


def select_featured_snaps() -> None:
    """Run selection, publish it, and persist history/settings."""
    if not acquire_featured_selection_lock():
        logger.info(
            "Featured selection already in progress; skipping duplicate run request."
        )
        return

    try:
        resolved_token = (
            os.environ.get(FEATURED_PUBLISHER_TOKEN_ENV)
            or os.environ.get(MACAROON_ENV_PATH)
        )

        events, snap_ids = run_selection()
        logger.info("Selection complete: %d snaps chosen.", len(snap_ids))

        if not resolved_token:
            message = (
                f"Selection computed {len(snap_ids)} snaps but did NOT publish "
                f"or record history - no publisher token available. Set "
                f"{FEATURED_PUBLISHER_TOKEN_ENV} or {MACAROON_ENV_PATH}, or "
                f"trigger via the dashboard to publish."
            )
            logger.warning(message)
            add_pipeline_step_log(PipelineSteps.FEATURED, False, message)
            return

        previous_ids = _publish_to_store(resolved_token, snap_ids)
        logger.info("Featured list published to store.")

        try:
            record_featured_history(events, is_manual=False)
        except Exception:
            _rollback_store(resolved_token, previous_ids)
            raise

        set_setting("featured_last_updated", datetime.now(timezone.utc).isoformat())
        add_pipeline_step_log(
            PipelineSteps.FEATURED,
            True,
            f"Selected and published {len(snap_ids)} featured snaps",
        )

    except Exception as exc:
        logger.error("Featured snap selection failed: %s", exc)
        add_pipeline_step_log(PipelineSteps.FEATURED, False, str(exc))
        raise
    finally:
        release_featured_selection_lock()
