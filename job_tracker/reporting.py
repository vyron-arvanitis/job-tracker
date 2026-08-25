from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch

from .database.models import ApplicationStatus


ONGOING_STATUSES = {
    ApplicationStatus.APPLIED.value,
    ApplicationStatus.NO_RESPONSE.value,
    ApplicationStatus.HR_INTERVIEW.value,
    ApplicationStatus.TECHNICAL_INTERVIEW.value,
    ApplicationStatus.ASSESSMENT.value,
    ApplicationStatus.FINAL_INTERVIEW.value,
}


STATUS_ORDER = [
    "applied",
    "no_response",
    "hr_interview",
    "technical_interview",
    "assessment",
    "final_interview",
    "offer",
    "rejected",
    "withdrawn",
    "unknown",
]


STATUS_COLORS = {
    "applied": "#4F7DF3",
    "no_response": "#F5C451",
    "hr_interview": "#38C793",
    "technical_interview": "#3AA7D8",
    "assessment": "#67C7D4",
    "final_interview": "#9B72CF",
    "offer": "#2FC89B",
    "rejected": "#EF6262",
    "withdrawn": "#7E8799",
    "unknown": "#B7BDC8",
}


def status_counts(applications) -> Counter:
    return Counter(application.status for application in applications)


def create_status_chart(
    applications,
    output_path: str | Path = "applications_status.png",
) -> Path:

    counts = status_counts(applications)
    total = len(applications)

    if not total:
        raise ValueError(
            "No applications found. Run `python -m job_tracker sync` first."
        )

    labels = [
        status
        for status in STATUS_ORDER
        if counts.get(status, 0) > 0
    ]

    labels.extend(
        status
        for status in counts
        if status not in labels and counts[status] > 0
    )

    values = [counts[label] for label in labels]
    colors = [STATUS_COLORS.get(label, "#B7BDC8") for label in labels]

    ongoing = sum(counts.get(status, 0) for status in ONGOING_STATUSES)
    closed = total - ongoing

    interviews = sum(
        counts.get(status, 0)
        for status in {
            ApplicationStatus.HR_INTERVIEW.value,
            ApplicationStatus.TECHNICAL_INTERVIEW.value,
            ApplicationStatus.FINAL_INTERVIEW.value,
        }
    )

    offers = counts.get(ApplicationStatus.OFFER.value, 0)

    # ------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------

    background = "#F3F6FA"
    card = "#FFFFFF"

    primary = "#111827"
    secondary = "#7B8495"
    border = "#E5E9F0"

    # ------------------------------------------------------------
    # Figure
    # ------------------------------------------------------------

    fig = plt.figure(
        figsize=(14, 8),
        facecolor=background,
    )

    # ------------------------------------------------------------
    # Main card
    # ------------------------------------------------------------

    dashboard_card = FancyBboxPatch(
        (0.035, 0.055),
        0.93,
        0.87,
        transform=fig.transFigure,
        boxstyle="round,pad=0.012,rounding_size=0.025",
        facecolor=card,
        edgecolor="none",
        zorder=-10,
    )

    dashboard_card.set_path_effects([
        pe.SimplePatchShadow(
            offset=(0, -4),
            alpha=0.12,
            rho=0.95,
        ),
        pe.Normal(),
    ])

    fig.patches.append(dashboard_card)

    # ------------------------------------------------------------
    # Header
    # ------------------------------------------------------------

    fig.text(
        0.085,
        0.865,
        "Job Application Pipeline",
        fontsize=24,
        fontweight="bold",
        color=primary,
    )

    fig.text(
        0.085,
        0.825,
        "Live overview of your current job search",
        fontsize=10.5,
        color=secondary,
    )

    # ------------------------------------------------------------
    # Donut
    # ------------------------------------------------------------

    ax = fig.add_axes([0.07, 0.22, 0.46, 0.58])

    ax.set_facecolor("none")

    # Slightly separate the most interesting statuses
    explode = [
        0.035 if label in {"offer", "final_interview"} else 0.0
        for label in labels
    ]

    wedges, _ = ax.pie(
        values,
        startangle=90,
        counterclock=False,
        colors=colors,
        explode=explode,
        radius=1.0,
        wedgeprops={
            "width": 0.28,
            "edgecolor": "#FFFFFF",
            "linewidth": 4,
            "antialiased": True,
        },
    )

    # Soft floating / 3D shadow
    for wedge in wedges:
        wedge.set_path_effects([
            pe.SimplePatchShadow(
                offset=(0, -4),
                shadow_rgbFace="#000000",
                alpha=0.16,
            ),
            pe.Normal(),
        ])

    ax.axis("equal")

    # ------------------------------------------------------------
    # Center
    # ------------------------------------------------------------

    ax.text(
        0,
        0.12,
        str(total),
        ha="center",
        va="center",
        fontsize=39,
        fontweight="bold",
        color=primary,
    )

    ax.text(
        0,
        -0.08,
        "APPLICATIONS",
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color=secondary,
    )

    ax.text(
        0,
        -0.22,
        f"{ongoing} active",
        ha="center",
        va="center",
        fontsize=10,
        color="#38A57C",
        fontweight="bold",
    )

    # ------------------------------------------------------------
    # Status breakdown panel
    # ------------------------------------------------------------

    panel = fig.add_axes([0.57, 0.25, 0.34, 0.53])

    panel.set_xlim(0, 1)
    panel.set_ylim(0, 1)
    panel.axis("off")

    panel.text(
        0,
        1.03,
        "STATUS BREAKDOWN",
        fontsize=9,
        fontweight="bold",
        color=secondary,
    )

    row_height = min(0.10, 0.88 / max(len(labels), 1))
    y = 0.92

    for label, value, color in zip(labels, values, colors):

        percentage = value / total * 100

        # Row card
        row = FancyBboxPatch(
            (0, y - 0.04),
            1,
            0.075,
            boxstyle="round,pad=0.008,rounding_size=0.015",
            facecolor="#F8FAFC",
            edgecolor="none",
            transform=panel.transAxes,
        )

        panel.add_patch(row)

        # Status dot
        panel.scatter(
            0.045,
            y,
            s=85,
            color=color,
            zorder=3,
        )

        panel.text(
            0.10,
            y,
            label.replace("_", " ").title(),
            fontsize=10,
            fontweight="medium",
            color=primary,
            va="center",
        )

        panel.text(
            0.78,
            y,
            str(value),
            fontsize=11,
            fontweight="bold",
            color=primary,
            va="center",
            ha="right",
        )

        panel.text(
            0.95,
            y,
            f"{percentage:.0f}%",
            fontsize=9.5,
            color=secondary,
            va="center",
            ha="right",
        )

        y -= row_height

    # ------------------------------------------------------------
    # KPI cards
    # ------------------------------------------------------------

    kpis = [
        ("ACTIVE", ongoing, "currently open"),
        ("INTERVIEWS", interviews, "in pipeline"),
        ("OFFERS", offers, "received"),
        ("CLOSED", closed, "finished"),
    ]

    x_positions = [0.085, 0.285, 0.485, 0.685]

    for x, (title, value, subtitle) in zip(x_positions, kpis):

        kpi_card = FancyBboxPatch(
            (x, 0.095),
            0.17,
            0.10,
            transform=fig.transFigure,
            boxstyle="round,pad=0.012,rounding_size=0.015",
            facecolor="#F8FAFC",
            edgecolor=border,
            linewidth=0.8,
        )

        kpi_card.set_path_effects([
            pe.SimplePatchShadow(
                offset=(0, -2),
                alpha=0.06,
            ),
            pe.Normal(),
        ])

        fig.patches.append(kpi_card)

        fig.text(
            x + 0.018,
            0.155,
            str(value),
            fontsize=19,
            fontweight="bold",
            color=primary,
        )

        fig.text(
            x + 0.018,
            0.128,
            title,
            fontsize=8,
            fontweight="bold",
            color=secondary,
        )

        fig.text(
            x + 0.085,
            0.128,
            subtitle,
            fontsize=8,
            color="#A0A7B4",
        )

    # ------------------------------------------------------------
    # Save
    # ------------------------------------------------------------

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(
        output,
        dpi=220,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
    )

    plt.close(fig)

    return output