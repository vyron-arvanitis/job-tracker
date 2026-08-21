import sys


def progress(label: str, current: int, total: int, width: int = 30) -> None:
    """Render a small dependency-free terminal progress bar."""
    if total <= 0:
        return
    filled = int(width * current / total)
    bar = "=" * filled + ">" + " " * max(0, width - filled - 1)
    percent = current * 100 // total
    print(f"\r{label}: [{bar}] {current}/{total} ({percent}%)", end="", file=sys.stdout, flush=True)

