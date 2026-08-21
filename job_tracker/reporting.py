from collections import Counter
from pathlib import Path

from .database.models import ApplicationStatus

ONGOING_STATUSES = {
    ApplicationStatus.APPLIED.value,
    ApplicationStatus.NO_RESPONSE.value,
    ApplicationStatus.HR_INTERVIEW.value,
    ApplicationStatus.TECHNICAL_INTERVIEW.value,
    ApplicationStatus.ASSESSMENT.value,
    ApplicationStatus.FINAL_INTERVIEW.value,
}


def status_counts(applications) -> Counter:
    return Counter(application.status for application in applications)


def create_status_chart(applications, output_path: str | Path = "applications_status.png") -> Path:
    """Create a polished local donut chart and return its output path."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Chart generation requires matplotlib. Install it with: pip install matplotlib") from exc

    counts = status_counts(applications)
    total = len(applications)
    if not total:
        raise ValueError("No applications found. Run `python -m job_tracker sync` first.")

    labels = list(counts)
    values = [counts[label] for label in labels]
    colors = {
        "applied": "#4C78A8", "no_response": "#F2CF5B", "hr_interview": "#59A14F",
        "technical_interview": "#2E86AB", "assessment": "#76B7B2", "final_interview": "#B279A2",
        "rejected": "#E15759", "offer": "#F28E2B", "withdrawn": "#79706E", "unknown": "#BAB0AC",
    }
    figure, axis = plt.subplots(figsize=(10, 7), facecolor="#F7F8FA")
    axis.set_facecolor("#F7F8FA")
    wedges, _ = axis.pie(values, startangle=90, counterclock=False,
                         colors=[colors.get(label, "#BAB0AC") for label in labels],
                         wedgeprops={"width": 0.38, "edgecolor": "#F7F8FA", "linewidth": 3})
    axis.text(0, 0.08, str(total), ha="center", va="center", fontsize=30, fontweight="bold", color="#1F2937")
    axis.text(0, -0.12, "applications", ha="center", va="center", fontsize=11, color="#6B7280")
    ongoing = sum(counts.get(status, 0) for status in ONGOING_STATUSES)
    axis.set_title("Job Application Pipeline", fontsize=20, fontweight="bold", color="#111827", pad=24)
    axis.text(0.5, 0.96, f"{ongoing} ongoing  ·  {total - ongoing} closed", transform=figure.transFigure,
              ha="center", fontsize=11, color="#6B7280")
    legend_labels = [f"{label.replace('_', ' ').title()}  ·  {counts[label]}" for label in labels]
    axis.legend(wedges, legend_labels, title="Current status", loc="center left", bbox_to_anchor=(0.98, 0.5),
                frameon=False, fontsize=10, title_fontsize=11)
    axis.axis("equal")
    figure.tight_layout()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=180, bbox_inches="tight", facecolor=figure.get_facecolor())
    plt.close(figure)
    return output
