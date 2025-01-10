from flask import Blueprint


cli_blueprint = Blueprint("cli", __name__, cli_group=None)


@cli_blueprint.cli.group()
def collector():
    """Commands related to the collector"""
    pass


@collector.command()
def start():
    """Start the full data collection pipeline"""
    from collector.main import collect_data

    collect_data()


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
