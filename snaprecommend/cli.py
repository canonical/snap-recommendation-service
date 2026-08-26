from flask import Blueprint
import click

cli_blueprint = Blueprint("cli", __name__, cli_group=None)


@cli_blueprint.cli.group()
def collector():
    """Commands related to the collector"""
    pass


@collector.command()
@click.option(
    "--force",
    is_flag=True,
    help="Force the full data collection pipeline to run",
)
def start(force):
    """Start the full data collection pipeline"""
    from collector.main import collect_data

    collect_data(force_update=force)


@collector.command()
def initial():
    """Collect initial snap data"""
    from collector.collect import collect_initial_snap_data

    collect_initial_snap_data()


@collector.command()
def filter():
    """Filter snaps meeting minimum criteria"""
    from collector.filter import filter_snaps_meeting_minimum_criteria

    filter_snaps_meeting_minimum_criteria()


@collector.command()
def extra_fields():
    """Collect extra fields for snaps"""
    from collector.extra_fields import fetch_extra_fields

    fetch_extra_fields()


@collector.command()
def score():
    """Calculate scores for snaps"""
    from collector.score import calculate_scores

    calculate_scores()


@collector.command()
@click.option(
    "--force",
    is_flag=True,
    help="Run selection even if it is not due according to the schedule",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Compute and print the selection without publishing or recording history",
)
@click.option(
    "--notify-webhook",
    is_flag=True,
    help="When combined with --dry-run, also fire the success webhook notification",
)
def featured(force, dry_run, notify_webhook):
    """Run automated featured snap selection"""
    from collector.featured_selector import (
        _notify_webhook,
        run_selection,
        select_featured_snaps,
    )
    from collector.main import (
        featured_schedule_description,
        featured_selection_due,
    )
    from flask import current_app
    from snaprecommend.models import Snap

    if dry_run:
        events, snap_ids = run_selection()
        names = dict(
            Snap.query.filter(Snap.snap_id.in_(snap_ids))
            .with_entities(Snap.snap_id, Snap.name)
            .all()
        )
        click.echo(f"Dry run: {len(events)} snaps would be selected (nothing published).\n")
        for event in events:
            reason = event["selection_reason"]
            score = reason["ranking_value"]
            score_display = f"{score:.4f}" if score is not None else "n/a"
            click.echo(
                f"- {names.get(event['snap_id'], event['snap_id'])} "
                f"({event['snap_id']}) "
                f"role={reason['role']} "
                f"canonical={reason['canonical']} "
                f"categories={','.join(reason['categories']) or '-'} "
                f"score={score_display}"
            )

        if notify_webhook:
            webhook_url = current_app.config.get("SNAP_SELECTION_WEBHOOK_URL")
            if not webhook_url:
                click.echo(
                    "\nSNAP_SELECTION_WEBHOOK_URL not configured - skipping webhook notification."
                )
            else:
                snap_objects = (
                    Snap.query.filter(Snap.snap_id.in_(snap_ids)).all()
                )
                snaps_payload = [
                    {"name": snap.name, "snap_id": snap.snap_id}
                    for snap in snap_objects
                ]
                _notify_webhook(
                    webhook_url,
                    {"success": True, "snaps": snaps_payload},
                )
                click.echo(f"\nWebhook notified at {webhook_url}")
        return

    if not force and not featured_selection_due():
        click.echo(
            "Featured selection is not due yet "
            f"(schedule: {featured_schedule_description()}). "
            "Use --force to override."
        )
        return

    select_featured_snaps()


@collector.command()
def service():
    """Start the collector server to run periodically"""
    from collector.main import collector_service

    collector_service()
