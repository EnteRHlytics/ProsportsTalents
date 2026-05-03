"""PDF export service for athlete profiles, search results, and rankings.

Uses ReportLab to render polished, print-ready PDFs with the agency's
"professional" branding: clean typography, dark gray header rows, subtle
borders, and consistent spacing. All public functions return a ``BytesIO``
that the API layer can stream as an attachment.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Branding / shared style helpers
# ---------------------------------------------------------------------------

BRAND_NAVY = colors.HexColor("#0F1F3D")
BRAND_ORANGE = colors.HexColor("#E07A1F")
HEADER_GRAY = colors.HexColor("#374151")
ROW_ALT = colors.HexColor("#F3F4F6")
BORDER_GRAY = colors.HexColor("#D1D5DB")
TEXT_MUTED = colors.HexColor("#6B7280")


def _styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "AgencyTitle",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=BRAND_NAVY,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "AgencySubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=14,
            textColor=TEXT_MUTED,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "AgencyH2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=BRAND_NAVY,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "AgencyBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=colors.black,
        ),
        "label": ParagraphStyle(
            "AgencyLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=HEADER_GRAY,
        ),
        "footer": ParagraphStyle(
            "AgencyFooter",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10,
            textColor=TEXT_MUTED,
        ),
    }
    return styles


def _table_style(header_rows: int = 1) -> TableStyle:
    """Default table appearance: dark gray header, subtle grid, alt rows."""
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, header_rows - 1), HEADER_GRAY),
        ("TEXTCOLOR", (0, 0), (-1, header_rows - 1), colors.white),
        ("FONTNAME", (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, header_rows - 1), 9),
        ("ALIGN", (0, 0), (-1, header_rows - 1), "LEFT"),
        ("BOTTOMPADDING", (0, 0), (-1, header_rows - 1), 6),
        ("TOPPADDING", (0, 0), (-1, header_rows - 1), 6),
        ("FONTNAME", (0, header_rows), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, header_rows), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, header_rows), (-1, -1), [colors.white, ROW_ALT]),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER_GRAY),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ])


def _on_page(canvas, doc):
    """Footer with page number + agency mark."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawString(0.5 * inch, 0.4 * inch, "Pro Sports Talents | Confidential")
    canvas.drawRightString(
        LETTER[0] - 0.5 * inch, 0.4 * inch, f"Page {doc.page}"
    )
    canvas.restoreState()


def _new_doc(buf: BytesIO, title: str) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.7 * inch,
        title=title,
        author="Pro Sports Talents",
    )


def _photo_flowable(url: str | None, initials: str, width=1.1 * inch, height=1.4 * inch):
    """Return an Image if URL is local + readable, else a placeholder Table."""
    if url:
        try:
            # Only treat local file paths as embeddable; URLs are skipped to
            # avoid blocking network calls during rendering.
            if not url.lower().startswith(("http://", "https://")):
                return Image(url, width=width, height=height)
        except Exception:
            pass
    placeholder = Table(
        [[Paragraph(f"<b>{initials or '--'}</b>", ParagraphStyle(
            "ph", fontName="Helvetica-Bold", fontSize=22,
            textColor=colors.white, alignment=1
        ))]],
        colWidths=[width],
        rowHeights=[height],
    )
    placeholder.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_NAVY),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, BRAND_NAVY),
    ]))
    return placeholder


# ---------------------------------------------------------------------------
# Data extraction helpers
# ---------------------------------------------------------------------------

def _athlete_basics(athlete) -> dict:
    """Pull display-friendly fields off an AthleteProfile-like object."""
    user = getattr(athlete, "user", None)
    name = user.full_name if user else (
        f"Athlete {getattr(athlete, 'athlete_id', '')}"
    )
    initials = "".join([n[0] for n in name.split()][:2]).upper() if name else "--"

    sport = getattr(athlete, "primary_sport", None)
    sport_label = (
        getattr(sport, "name", None)
        or getattr(sport, "code", None)
        or "--"
    )
    position = getattr(athlete, "primary_position", None)
    position_label = (
        getattr(position, "name", None)
        or getattr(position, "code", None)
        or "--"
    )
    return {
        "name": name,
        "initials": initials,
        "sport": sport_label,
        "position": position_label,
        "team": getattr(athlete, "current_team", None) or "Free Agent",
        "jersey": getattr(athlete, "jersey_number", None) or "--",
        "dob": getattr(athlete, "date_of_birth", None),
        "age": getattr(athlete, "age", None),
        "height_cm": getattr(athlete, "height_cm", None),
        "weight_kg": getattr(athlete, "weight_kg", None),
        "nationality": getattr(athlete, "nationality", None) or "--",
        "bio": getattr(athlete, "bio", None) or "",
        "rating": getattr(athlete, "overall_rating", None),
        "photo_url": getattr(athlete, "profile_image_url", None),
        "email": getattr(user, "email", None) if user else None,
    }


def _format_height(height_cm) -> str:
    if not height_cm:
        return "--"
    try:
        cm = int(height_cm)
        total_in = round(cm / 2.54)
        ft, inches = divmod(total_in, 12)
        return f"{cm} cm ({ft}'{inches}\")"
    except Exception:
        return str(height_cm)


def _format_weight(weight_kg) -> str:
    if not weight_kg:
        return "--"
    try:
        kg = float(weight_kg)
        return f"{kg:.1f} kg ({round(kg * 2.205)} lbs)"
    except Exception:
        return str(weight_kg)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def athlete_profile_pdf(athlete_id: str) -> BytesIO:
    """Render a single athlete's profile to PDF.

    Looks up the athlete via SQLAlchemy and assembles a polished one-pager
    (header, bio, season stats, recent games, skills, contact). Raises
    ``ValueError`` if the athlete cannot be found.
    """
    from app.models import AthleteProfile, AthleteSkill, AthleteStat

    athlete = (
        AthleteProfile.query
        .filter_by(athlete_id=athlete_id, is_deleted=False)
        .first()
    )
    if athlete is None:
        raise ValueError(f"Athlete {athlete_id} not found")

    season_stats = (
        AthleteStat.query
        .filter_by(athlete_id=athlete_id)
        .order_by(AthleteStat.season.desc().nullslast(), AthleteStat.name)
        .all()
    )
    skills = (
        AthleteSkill.query
        .filter_by(athlete_id=athlete_id)
        .order_by(AthleteSkill.level.desc().nullslast(), AthleteSkill.name)
        .all()
    )

    # Recent games - best-effort (NBA/NHL share Game; otherwise skip)
    recent_games = _recent_games_for(athlete)

    return _render_athlete_pdf(athlete, season_stats, skills, recent_games)


def _recent_games_for(athlete, limit: int = 5):
    """Return up to ``limit`` recent games for the athlete's team if available.

    Mirrors the logic in ``api/routes.py::AthleteGameLog`` but kept defensive
    so that missing teams or sport mappings simply return an empty list.
    """
    try:
        from app.models import NBAGame, NBATeam, NHLGame, NHLTeam
    except Exception:
        return []

    if not (athlete.current_team and athlete.primary_sport):
        return []
    code = athlete.primary_sport.code
    games = []
    try:
        if code == "NBA":
            team = NBATeam.query.filter(
                (NBATeam.name.ilike(athlete.current_team))
                | (NBATeam.full_name.ilike(athlete.current_team))
                | (NBATeam.abbreviation.ilike(athlete.current_team))
            ).first()
            if team:
                games = (
                    NBAGame.query
                    .filter((NBAGame.home_team_id == team.team_id)
                            | (NBAGame.visitor_team_id == team.team_id))
                    .order_by(NBAGame.date.desc())
                    .limit(limit)
                    .all()
                )
        elif code == "NHL":
            team = NHLTeam.query.filter(
                (NHLTeam.name.ilike(athlete.current_team))
                | (NHLTeam.location.ilike(athlete.current_team))
                | (NHLTeam.abbreviation.ilike(athlete.current_team))
            ).first()
            if team:
                games = (
                    NHLGame.query
                    .filter((NHLGame.home_team_id == team.team_id)
                            | (NHLGame.visitor_team_id == team.team_id))
                    .order_by(NHLGame.date.desc())
                    .limit(limit)
                    .all()
                )
    except Exception:
        return []
    return games


def _render_athlete_pdf(athlete, season_stats, skills, recent_games) -> BytesIO:
    s = _styles()
    info = _athlete_basics(athlete)
    buf = BytesIO()
    doc = _new_doc(buf, f"{info['name']} - Athlete Profile")

    story: list = []

    # ---- Header band ---------------------------------------------------
    photo = _photo_flowable(info["photo_url"], info["initials"])

    header_lines = [
        Paragraph(info["name"], s["title"]),
        Paragraph(
            f"{info['sport']} &nbsp;|&nbsp; {info['position']} &nbsp;|&nbsp; "
            f"{info['team']} &nbsp;|&nbsp; #{info['jersey']}",
            s["subtitle"],
        ),
    ]
    if info["rating"] is not None:
        header_lines.append(Paragraph(
            f"<b>Overall rating:</b> {float(info['rating']):.2f}", s["body"]
        ))

    header = Table(
        [[photo, header_lines]],
        colWidths=[1.3 * inch, 5.6 * inch],
    )
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header)
    story.append(Spacer(1, 0.18 * inch))

    # Divider
    story.append(Table(
        [[""]], colWidths=[6.9 * inch], rowHeights=[1.2],
        style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), BRAND_ORANGE)])
    ))
    story.append(Spacer(1, 0.15 * inch))

    # ---- Bio -----------------------------------------------------------
    if info["bio"]:
        story.append(Paragraph("Biography", s["h2"]))
        story.append(Paragraph(info["bio"], s["body"]))

    # ---- Vitals --------------------------------------------------------
    story.append(Paragraph("Vitals", s["h2"]))
    vitals_data = [
        ["Date of Birth", str(info["dob"]) if info["dob"] else "--",
         "Age", str(info["age"]) if info["age"] is not None else "--"],
        ["Height", _format_height(info["height_cm"]),
         "Weight", _format_weight(info["weight_kg"])],
        ["Nationality", info["nationality"] or "--",
         "Status", _career_status(athlete)],
    ]
    vitals = Table(vitals_data, colWidths=[1.4 * inch, 2.0 * inch, 1.4 * inch, 2.1 * inch])
    vitals.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), HEADER_GRAY),
        ("TEXTCOLOR", (2, 0), (2, -1), HEADER_GRAY),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, ROW_ALT]),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER_GRAY),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(vitals)

    # ---- Season stats --------------------------------------------------
    story.append(Paragraph("Season Statistics", s["h2"]))
    if season_stats:
        rows = [["Season", "Stat", "Value", "Type"]]
        for stat in season_stats:
            rows.append([
                stat.season or "--",
                stat.name or "--",
                stat.value if stat.value is not None else "--",
                stat.stat_type or "--",
            ])
        tbl = Table(rows, colWidths=[1.0 * inch, 2.6 * inch, 1.5 * inch, 1.8 * inch])
        tbl.setStyle(_table_style())
        story.append(tbl)
    else:
        story.append(Paragraph("No season statistics on file.", s["body"]))

    # ---- Recent games --------------------------------------------------
    story.append(Paragraph("Recent Games", s["h2"]))
    if recent_games:
        rows = [["Date", "Home", "Score", "Away"]]
        for g in recent_games:
            home = _team_label(getattr(g, "home_team", None))
            away = _team_label(getattr(g, "visitor_team", None))
            score = f"{g.home_team_score or 0} - {g.visitor_team_score or 0}"
            rows.append([str(g.date) if g.date else "--", home, score, away])
        tbl = Table(rows, colWidths=[1.1 * inch, 2.3 * inch, 1.2 * inch, 2.3 * inch])
        tbl.setStyle(_table_style())
        story.append(tbl)
    else:
        story.append(Paragraph(
            "No recent games available. See web profile for video highlights.",
            s["body"],
        ))

    # ---- Skills --------------------------------------------------------
    story.append(Paragraph("Skills", s["h2"]))
    if skills:
        rows = [["Skill", "Level"]]
        for sk in skills:
            rows.append([sk.name or "--",
                         str(sk.level) if sk.level is not None else "--"])
        tbl = Table(rows, colWidths=[4.4 * inch, 2.5 * inch])
        tbl.setStyle(_table_style())
        story.append(tbl)
    else:
        story.append(Paragraph("No skills recorded.", s["body"]))

    # ---- Contact -------------------------------------------------------
    story.append(Paragraph("Contact / Representation", s["h2"]))
    contact_rows = [
        ["Athlete email", info["email"] or "--"],
        ["Agency", "Pro Sports Talents (representation)"],
        ["Web profile", "See web app for video and live updates."],
    ]
    contact = Table(contact_rows, colWidths=[1.6 * inch, 5.3 * inch])
    contact.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), HEADER_GRAY),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, ROW_ALT]),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER_GRAY),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(contact)

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        f"Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        s["footer"],
    ))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    buf.seek(0)
    return buf


def _career_status(athlete) -> str:
    status = getattr(athlete, "career_status", None)
    if status is None:
        return "--"
    val = getattr(status, "value", None) or str(status)
    return str(val).title()


def _team_label(team) -> str:
    if team is None:
        return "--"
    return (
        getattr(team, "full_name", None)
        or getattr(team, "name", None)
        or getattr(team, "abbreviation", None)
        or "--"
    )


# ---------------------------------------------------------------------------
# Search results PDF
# ---------------------------------------------------------------------------

def search_results_pdf(athletes_list: Iterable, filters_summary: dict) -> BytesIO:
    """Render search results as a multi-page PDF.

    Page 1 is a title page describing the filters that were applied; the
    remaining pages list one row per athlete in a tabular format.
    """
    s = _styles()
    buf = BytesIO()
    doc = _new_doc(buf, "Athlete Search Results")
    story: list = []

    # ---- Title page ----------------------------------------------------
    story.append(Paragraph("Athlete Search Results", s["title"]))
    story.append(Paragraph(
        "Pro Sports Talents | Curated short list",
        s["subtitle"],
    ))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Table(
        [[""]], colWidths=[6.9 * inch], rowHeights=[1.2],
        style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), BRAND_ORANGE)])
    ))
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Filters Applied", s["h2"]))
    if filters_summary:
        rows = [["Filter", "Value"]]
        for k, v in filters_summary.items():
            if v in (None, "", []):
                continue
            rows.append([str(k).replace("_", " ").title(), str(v)])
        if len(rows) == 1:
            rows.append(["(none)", "All athletes"])
        tbl = Table(rows, colWidths=[2.0 * inch, 4.9 * inch])
        tbl.setStyle(_table_style())
        story.append(tbl)
    else:
        story.append(Paragraph("No filters applied — all athletes.", s["body"]))

    athletes_list = list(athletes_list)
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        f"<b>Total results:</b> {len(athletes_list)}", s["body"]
    ))
    story.append(Paragraph(
        f"Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        s["footer"],
    ))

    # ---- Results page --------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("Results", s["h2"]))
    if not athletes_list:
        story.append(Paragraph(
            "No athletes matched the supplied filters.", s["body"]
        ))
    else:
        rows = [["#", "Name", "Sport", "Position", "Team", "Age", "Rating"]]
        for i, ath in enumerate(athletes_list, start=1):
            info = _athlete_basics(ath)
            rating = (
                f"{float(info['rating']):.2f}"
                if info["rating"] is not None else "--"
            )
            rows.append([
                str(i),
                info["name"],
                info["sport"],
                info["position"],
                info["team"],
                str(info["age"]) if info["age"] is not None else "--",
                rating,
            ])
        tbl = Table(
            rows,
            colWidths=[0.4 * inch, 1.9 * inch, 0.9 * inch, 1.0 * inch,
                       1.5 * inch, 0.5 * inch, 0.7 * inch],
            repeatRows=1,
        )
        tbl.setStyle(_table_style())
        story.append(tbl)

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Rankings PDF
# ---------------------------------------------------------------------------

def rankings_pdf(rankings: Iterable, sport: str | None = None,
                 weights: dict | None = None) -> BytesIO:
    """Render rankings to PDF.

    ``rankings`` is an iterable of dict-like rows with at least ``name`` and
    ``score``. Optional ``rank``, ``team``, ``position``, and ``id`` keys are
    surfaced when available. ``weights`` describes the metric weights used by
    the ranking algorithm and is rendered as a transparency table.
    """
    s = _styles()
    buf = BytesIO()
    doc = _new_doc(buf, f"Athlete Rankings - {sport or 'All Sports'}")
    story: list = []

    title_sport = sport.upper() if sport else "All Sports"
    story.append(Paragraph(f"Athlete Rankings — {title_sport}", s["title"]))
    story.append(Paragraph(
        "Pro Sports Talents | Performance ranking",
        s["subtitle"],
    ))
    story.append(Table(
        [[""]], colWidths=[6.9 * inch], rowHeights=[1.2],
        style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), BRAND_ORANGE)])
    ))
    story.append(Spacer(1, 0.18 * inch))

    if weights:
        story.append(Paragraph("Ranking Weights", s["h2"]))
        rows = [["Metric", "Weight"]]
        for k, v in weights.items():
            rows.append([str(k), str(v)])
        tbl = Table(rows, colWidths=[3.5 * inch, 3.4 * inch])
        tbl.setStyle(_table_style())
        story.append(tbl)
        story.append(Spacer(1, 0.15 * inch))

    rankings = list(rankings)
    story.append(Paragraph("Top Athletes", s["h2"]))
    if not rankings:
        story.append(Paragraph("No ranking data available.", s["body"]))
    else:
        rows = [["Rank", "Athlete", "Team", "Score"]]
        for i, r in enumerate(rankings, start=1):
            rank = r.get("rank", i) if isinstance(r, dict) else i
            name = (
                r.get("name") if isinstance(r, dict)
                else getattr(r, "name", "--")
            )
            team = (
                r.get("team") if isinstance(r, dict)
                else getattr(r, "team", "--")
            ) or "--"
            score = (
                r.get("score") if isinstance(r, dict)
                else getattr(r, "score", None)
            )
            score_str = f"{float(score):.1f}" if score is not None else "--"
            rows.append([str(rank), str(name), str(team), score_str])
        tbl = Table(
            rows,
            colWidths=[0.7 * inch, 3.0 * inch, 1.9 * inch, 1.3 * inch],
            repeatRows=1,
        )
        tbl.setStyle(_table_style())
        story.append(tbl)

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        f"Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        s["footer"],
    ))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    buf.seek(0)
    return buf
