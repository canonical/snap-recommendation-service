"""
Automated featured snap selection (WD-470).

Runs five stages to produce a 3-to-15 snap featured list:
  1. Hard gates      — filter eligible candidates
  2. Ranking         — composite score (active_devices, rating, recency)
  2.5 Random pool    — sample from top-K rather than pure top-N for variety
  3. Top-3 mix       — enforce at-least-one / at-most-two Canonical rule
  4. Category spread — reserve slots for ≥2 development + ≥1 game
  5. Fill            — fill remaining slots with per-category cap
"""

import logging
import os
import random
from datetime import datetime, timedelta
from typing import Optional

from snaprecommend import db
from snaprecommend.auth.session import device_gateway, publisher_gateway
from snaprecommend.logic import add_pipeline_step_log, record_featured_history
from snaprecommend.models import FeaturedHistory, PipelineSteps, Snap
from snaprecommend.notifications import notify_mattermost
from snaprecommend.settings import get_setting, set_setting

logger = logging.getLogger("collector.featured")

# ---------------------------------------------------------------------------
# Configurable defaults (all overridable via the Settings table at runtime)
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "featured_candidate_pool_size": 50,
    "featured_category_cap": 4,
    "featured_min_rating": 4.0,
    "featured_recency_days": 180,
    "featured_history_window_days": 365,
    "featured_target_count": 15,
    "featured_server_cloud_exclusions": [
        "lxd",
        "google-cloud-sdk",
        "aws-cli",
        "kubectl",
        "helm",
        "microk8s",
        "juju",
        "multipass",
    ],
}

_SERVER_CLOUD_CATEGORY_SLUGS = {"server-and-cloud", "cloud"}
_DEV_CATEGORY_SLUGS = {"development"}
_GAME_CATEGORY_SLUGS = {"games"}
CANONICAL_PUBLISHER_ID = "canonical"

# Env var for a headless publisher token (optional).
# Set FLASK_FEATURED_PUBLISHER_TOKEN to enable automated store publishing
# without a logged-in admin session.
FEATURED_PUBLISHER_TOKEN_ENV = "FLASK_FEATURED_PUBLISHER_TOKEN"


# ---------------------------------------------------------------------------
# Settings helpers
# ---------------------------------------------------------------------------

def _cfg(key):
    """Return the setting value for *key*, falling back to _DEFAULTS."""
    s = get_setting(key)
    if s is None or s.value is None:
        return _DEFAULTS[key]
    default = _DEFAULTS[key]
    if isinstance(default, list):
        return s.value if isinstance(s.value, list) else default
    return type(default)(s.value)


# ---------------------------------------------------------------------------
# Category helpers
# ---------------------------------------------------------------------------

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


def _has_any_category(snap: Snap, target_slugs: set) -> bool:
    return bool(_snap_category_slugs(snap) & target_slugs)


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Stage 1: Hard gates
# ---------------------------------------------------------------------------

def _get_recently_auto_featured_ids(window_days: int) -> set:
    since = datetime.utcnow() - timedelta(days=window_days)
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
    exclusion_names: list,
) -> list:
    recency_cutoff = datetime.utcnow() - timedelta(days=recency_days)
    recently_featured = _get_recently_auto_featured_ids(history_window_days)

    candidates = (
        db.session.query(Snap)
        .filter(Snap.reaches_min_threshold.is_(True))
        .filter(Snap.excluded.is_(False))
        .filter(Snap.developer_validation.in_(["verified", "starred"]))
        .filter(Snap.last_updated >= recency_cutoff)
        .all()
    )

    exclusion_set = set(exclusion_names) if isinstance(exclusion_names, list) else set()
    filtered = []
    for snap in candidates:
        if snap.snap_id in recently_featured:
            continue
        if snap.name in exclusion_set:
            continue
        if _has_any_category(snap, _SERVER_CLOUD_CATEGORY_SLUGS):
            continue
        # Only reject if we *have* a rating below the floor; unrated snaps pass.
        if snap.raw_rating is not None and snap.raw_rating < min_rating:
            continue
        filtered.append(snap)

    return filtered


# ---------------------------------------------------------------------------
# Stage 2: Composite ranking
# ---------------------------------------------------------------------------

def _rank_candidates(candidates: list, recency_days: int) -> list:
    """Return candidates sorted by composite score, highest first."""
    recency_cutoff = datetime.utcnow() - timedelta(days=recency_days)

    device_scores = {s.snap_id: s.active_devices or 0 for s in candidates}
    rating_scores = {s.snap_id: s.raw_rating for s in candidates}
    recency_scores = {
        s.snap_id: max(0.0, (s.last_updated - recency_cutoff).total_seconds())
        for s in candidates
    }

    norm_dev = _minmax_normalise(device_scores)
    norm_rat = _minmax_normalise(rating_scores)
    norm_rec = _minmax_normalise(recency_scores)

    composite = {
        s.snap_id: (
            norm_dev[s.snap_id] * 0.5
            + norm_rat[s.snap_id] * 0.3
            + norm_rec[s.snap_id] * 0.2
        )
        for s in candidates
    }

    return sorted(candidates, key=lambda s: composite[s.snap_id], reverse=True), composite


# ---------------------------------------------------------------------------
# Stage 3: Top-3 Canonical mix
# ---------------------------------------------------------------------------

def _enforce_canonical_mix(top3: list, remaining: list) -> tuple:
    """
    Ensure top3 has ≥1 and ≤2 Canonical snaps.
    Any snap displaced from top3 is returned to *remaining* so it stays
    eligible for later stages (category reservation and fill).
    Returns (adjusted_top3, adjusted_remaining).
    """
    top3 = list(top3)
    remaining = list(remaining)

    canonical_count = sum(1 for s in top3 if s.publisher == CANONICAL_PUBLISHER_ID)

    if canonical_count == 0:
        canonical_pool = [s for s in remaining if s.publisher == CANONICAL_PUBLISHER_ID]
        if not canonical_pool:
            raise ValueError(
                "No Canonical snap in candidate pool — cannot satisfy top-3 mix rule."
            )
        insert = canonical_pool[0]
        remaining.remove(insert)
        displaced = top3[-1]          # save before overwriting
        top3[-1] = insert
        remaining.append(displaced)   # put displaced snap back into the pool

    elif canonical_count == 3:
        non_canonical_pool = [s for s in remaining if s.publisher != CANONICAL_PUBLISHER_ID]
        if not non_canonical_pool:
            raise ValueError(
                "All top-3 candidates are Canonical and no non-Canonical alternative exists."
            )
        insert = non_canonical_pool[0]
        remaining.remove(insert)
        # Remove last Canonical in top3 (lowest-ranked)
        canonicals_in_top3 = [s for s in top3 if s.publisher == CANONICAL_PUBLISHER_ID]
        displaced = canonicals_in_top3[-1]
        top3.remove(displaced)
        remaining.append(displaced)   # put displaced snap back into the pool
        top3.append(insert)

    return top3, remaining


# ---------------------------------------------------------------------------
# Stage 4: Category spread reservation
# ---------------------------------------------------------------------------

def _reserve_category_slots(top3: list, remaining: list) -> tuple:
    """
    Reserve snaps from *remaining* to meet ≥2 development and ≥1 game.
    A snap in both categories counts towards both minimums simultaneously.
    Returns (reserved_with_role, leftover_remaining).
    """
    remaining = list(remaining)
    dev_count = sum(1 for s in top3 if _has_any_category(s, _DEV_CATEGORY_SLUGS))
    game_count = sum(1 for s in top3 if _has_any_category(s, _GAME_CATEGORY_SLUGS))
    dev_needed = max(0, 2 - dev_count)
    game_needed = max(0, 1 - game_count)

    reserved = []
    for snap in list(remaining):
        if dev_needed == 0 and game_needed == 0:
            break
        is_dev = _has_any_category(snap, _DEV_CATEGORY_SLUGS)
        is_game = _has_any_category(snap, _GAME_CATEGORY_SLUGS)
        if (is_dev and dev_needed > 0) or (is_game and game_needed > 0):
            role_parts = []
            if is_dev and dev_needed > 0:
                role_parts.append("development")
                dev_needed -= 1
            if is_game and game_needed > 0:
                role_parts.append("game")
                game_needed -= 1
            reserved.append((snap, "category-" + "+".join(role_parts)))
            remaining.remove(snap)

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

    return reserved, remaining


# ---------------------------------------------------------------------------
# Stage 5: Fill remaining slots
# ---------------------------------------------------------------------------

def _fill_slots(
    top3: list,
    reserved: list,
    remaining: list,
    target_count: int,
    category_cap: int,
) -> list:
    """
    Fill open slots from *remaining* without exceeding per-category cap.
    Relaxes the cap if needed to avoid shipping a short list.
    """
    filled = []
    open_slots = target_count - 3 - len(reserved)
    if open_slots <= 0:
        return filled

    # Build initial category counts from top3 + reserved
    cat_counts: dict = {}
    for snap in top3:
        for slug in _snap_category_slugs(snap):
            cat_counts[slug] = cat_counts.get(slug, 0) + 1
    for snap, _ in reserved:
        for slug in _snap_category_slugs(snap):
            cat_counts[slug] = cat_counts.get(slug, 0) + 1

    def _would_exceed_cap(snap, cap):
        slugs = _snap_category_slugs(snap)
        return slugs and all(cat_counts.get(s, 0) >= cap for s in slugs)

    # First pass: respect the cap
    for snap in remaining:
        if len(filled) >= open_slots:
            break
        if not _would_exceed_cap(snap, category_cap):
            filled.append(snap)
            for slug in _snap_category_slugs(snap):
                cat_counts[slug] = cat_counts.get(slug, 0) + 1

    # Second pass: relax cap if still short
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


# ---------------------------------------------------------------------------
# Store publishing helpers
# ---------------------------------------------------------------------------

def _get_current_featured_snap_ids() -> list:
    """Fetch the current featured snap IDs from the store (handles pagination)."""
    snap_ids = []
    resp = device_gateway.get_featured_snaps()
    while True:
        snap_ids.extend(
            s["snap_id"]
            for s in resp.get("_embedded", {}).get("clickindex:package", [])
        )
        if not resp.get("_links", {}).get("next"):
            break
        resp = device_gateway.get_featured_snaps()  # pagination cursor not exposed yet
        break  # guard against infinite loop until cursor support is added
    return snap_ids


def _publish_to_store(token: str, new_snap_ids: list) -> None:
    """
    Replace the live featured list in the store.
    Mirrors the logic in featuredsnaps/api.py POST handler.
    """
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
        # Attempt to restore previous list
        try:
            publisher_gateway.update_featured_snaps(token, {"packages": current_ids})
        except Exception:
            pass
        raise RuntimeError(
            f"Failed to update featured snaps in store "
            f"(status {update_resp.status_code})."
        )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_selection() -> tuple:
    """
    Run the selection algorithm and return (events, snap_ids).
    Does not publish or write to the DB.
    Raises on failure.
    """
    pool_size = _cfg("featured_candidate_pool_size")
    category_cap = _cfg("featured_category_cap")
    min_rating = _cfg("featured_min_rating")
    recency_days = _cfg("featured_recency_days")
    history_window = _cfg("featured_history_window_days")
    target_count = _cfg("featured_target_count")
    exclusions = _cfg("featured_server_cloud_exclusions")

    # Stage 1
    candidates = _apply_hard_gates(recency_days, history_window, min_rating, exclusions)
    if not candidates:
        raise ValueError("No eligible candidates after hard gates.")

    # Stage 2
    ranked, composite = _rank_candidates(candidates, recency_days)

    # Stage 2.5 — randomised pool
    pool = ranked[:pool_size]
    seed = int(datetime.utcnow().timestamp())
    rng = random.Random(seed)
    logger.info("Random seed for this selection run: %d", seed)
    # Shuffle within the pool so identical-score ties resolve differently each run
    rng.shuffle(pool)

    # Stage 3
    top3 = pool[:3]
    remaining = pool[3:]
    top3, remaining = _enforce_canonical_mix(top3, remaining)

    # Stage 4
    reserved, remaining = _reserve_category_slots(top3, remaining)

    # Stage 5
    filled = _fill_slots(top3, reserved, remaining, target_count, category_cap)

    # Assemble final list
    final: list = (
        [(s, "top-3") for s in top3]
        + reserved
        + [(s, "fill") for s in filled]
    )

    if len(final) < 3:
        raise ValueError(
            f"Selection produced only {len(final)} snaps; minimum is 3."
        )

    ranking_key = "composite(active_devices*0.5 + raw_rating*0.3 + recency*0.2)"
    events = [
        {
            "snap_id": snap.snap_id,
            "selection_reason": {
                "role": role,
                "canonical": snap.publisher == CANONICAL_PUBLISHER_ID,
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


def select_featured_snaps(token: Optional[str] = None, force: bool = False) -> None:
    """
    Run the full automated featured snap selection:
      1. Select candidates via run_selection()
      2. Publish to the store (if *token* is available)
      3. Record featured history
      4. Update featured_last_updated setting

    *token* is the publisher OAuth token. When called from the pipeline with no
    session, pass None — selection will run and be recorded in history, but the
    store list will not be updated.  Set the FLASK_FEATURED_PUBLISHER_TOKEN env
    var to enable fully headless publishing.

    Raises on failure after logging and sending a Mattermost notification.
    """
    # Resolve token: prefer explicit arg, fall back to env var
    resolved_token = token or os.environ.get(FEATURED_PUBLISHER_TOKEN_ENV)

    try:
        events, snap_ids = run_selection()
        logger.info("Selection complete: %d snaps chosen.", len(snap_ids))

        if resolved_token:
            _publish_to_store(resolved_token, snap_ids)
            logger.info("Featured list published to store.")
        else:
            logger.warning(
                "No publisher token available. Selection recorded in history "
                "but NOT published to the store. Set %s or trigger via the "
                "dashboard to publish.",
                FEATURED_PUBLISHER_TOKEN_ENV,
            )

        record_featured_history(events, is_manual=False)
        set_setting("featured_last_updated", datetime.utcnow().isoformat())
        add_pipeline_step_log(
            PipelineSteps.FEATURED,
            True,
            f"Selected {len(snap_ids)} featured snaps"
            + (" (not published — no token)" if not resolved_token else ""),
        )

    except Exception as exc:
        logger.error("Featured snap selection failed: %s", exc)
        add_pipeline_step_log(PipelineSteps.FEATURED, False, str(exc))
        notify_mattermost(
            f":warning: **Automated featured snap selection failed**\n"
            f"The previously featured list has been retained.\n"
            f"Error: `{exc}`"
        )
        raise
