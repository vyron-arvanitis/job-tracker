import argparse

from .commands import authenticate_gmail, export_applications, generate_chart, list_applications, show_stats, sync_gmail
from .config import get_settings
from .database.session import make_session_factory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="job_tracker")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("auth", help="Authenticate with Gmail")
    sub.add_parser("sync", help="Fetch and process recruiting emails")
    sub.add_parser("stats", help="Show application status counts")
    listing = sub.add_parser("list", help="List applications")
    listing.add_argument("--status")
    export = sub.add_parser("export", help="Export applications as CSV")
    export.add_argument("path")
    chart = sub.add_parser("chart", help="Generate a visual application-status chart")
    chart.add_argument("--output", default="applications_status.png", help="PNG output path")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    settings = get_settings()
    if args.command == "auth":
        authenticate_gmail(settings)
        return
    factory = make_session_factory(settings.database_url)
    if args.command == "sync":
        sync_gmail(settings, factory)
    elif args.command == "list":
        list_applications(factory, args.status)
    elif args.command == "stats":
        show_stats(factory)
    elif args.command == "export":
        export_applications(factory, args.path)
    elif args.command == "chart":
        generate_chart(factory, args.output)

