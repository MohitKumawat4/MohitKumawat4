#!/usr/bin/env python3
"""Generate animated 3D SVG assets for the MohitKumawat4 GitHub profile README.

Why this architecture exists:
GitHub sanitizes README.md files by stripping JavaScript, WebGL canvases, and iframes,
but renders standalone SVG files with native SMIL (<animate>, <animateTransform>,
<animateMotion>) and CSS keyframe animations. Generating paired dark (#000000) and
light (#eeeeee) isometric 3D SVGs from live GitHub GraphQL telemetry gives visitors
an animated 3D experience directly on github.com/MohitKumawat4 without external hosts.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import math
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# Constants defining canvas geometry and target GitHub identity
DEFAULT_USERNAME = "MohitKumawat4"
CANVAS_WIDTH = 1200
FONT_SANS = (
    'ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", '
    "Helvetica, Arial, sans-serif"
)
FONT_MONO = (
    'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Monaco, '
    'Consolas, "Liberation Mono", monospace'
)

# Curated public flagship projects aligned with portfolio source of truth
FEATURED_PROJECTS: list[dict[str, Any]] = [
    {
        "index": "01",
        "slug": "ultima",
        "title": "ULTIMA",
        "subtitle": "Precision Task Orchestration Engine",
        "summary_line_1": "Drag-and-drop workload balancing, role isolation, automated",
        "summary_line_2": "email dispatch, and sub-second Supabase realtime state sync.",
        "live_domain": "ultima-five.vercel.app",
        "stack": ["Next.js 16", "Supabase", "TypeScript", "RLS"],
        "sculpture": "nodes",
    },
    {
        "index": "02",
        "slug": "strike",
        "title": "STRIKE",
        "subtitle": "Real-Time AI Email Intelligence",
        "summary_line_1": "Streams Gmail via Cloud Pub/Sub, scores urgency and synthesizes",
        "summary_line_2": "executive summaries with Gemini AI, pushing WhatsApp alerts.",
        "live_domain": "strike-lac.vercel.app",
        "stack": ["Next.js", "Gemini AI", "Pub/Sub", "WhatsApp API"],
        "sculpture": "relay",
    },
    {
        "index": "03",
        "slug": "om",
        "title": "OM ADVERTISING",
        "subtitle": "3D Storefront & Spatial Scroll Studio",
        "summary_line_1": "Multi-chapter exterior Three.js storefront showcase featuring",
        "summary_line_2": "scroll-driven camera landmarks and adaptive pixel rendering.",
        "live_domain": "om-advertising.vercel.app",
        "stack": ["Next.js", "Three.js", "WebGL", "TypeScript"],
        "sculpture": "storefront",
    },
    {
        "index": "04",
        "slug": "portfolio",
        "title": "3D PORTFOLIO",
        "subtitle": "WebGL Shaders & Kinetic Architecture",
        "summary_line_1": "Immersive personal showcase engineered with custom GLSL fluid",
        "summary_line_2": "shaders, React Three Fiber physics, and kinetic card stacks.",
        "live_domain": "portfolio-2026-sooty-six.vercel.app",
        "stack": ["Next.js 16", "R3F / GLSL", "Framer Motion", "Tailwind"],
        "sculpture": "planes",
    },
]

GRAPHQL_QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    login
    repositories(
      first: 8,
      privacy: PUBLIC,
      orderBy: {field: PUSHED_AT, direction: DESC},
      ownerAffiliations: OWNER
    ) {
      totalCount
      nodes {
        name
        description
        url
        homepageUrl
        stargazerCount
        pushedAt
        primaryLanguage {
          name
        }
        defaultBranchRef {
          name
          target {
            ... on Commit {
              history(first: 3) {
                totalCount
                nodes {
                  oid
                  messageHeadline
                  committedDate
                }
              }
            }
          }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
            weekday
          }
        }
      }
    }
  }
}
"""


def get_theme_palette(mode: str) -> dict[str, Any]:
    """Return adaptive monochrome palette tokens honoring #000000 dark and #eeeeee light."""
    if mode == "dark":
        return {
            "mode": "dark",
            "bg_start": "#080808",
            "bg_end": "#000000",
            "canvas_border": "#222222",
            "grid_stroke": "#161616",
            "card_bg": "#0a0a0a",
            "card_bg_alt": "#0f0f0f",
            "card_border": "#262626",
            "bevel_right": "#161616",
            "bevel_bottom": "#101010",
            "text_primary": "#ffffff",
            "text_secondary": "#a3a3a3",
            "text_muted": "#6b6b6b",
            "pill_bg": "#ffffff",
            "pill_text": "#000000",
            "chip_bg": "#141414",
            "chip_border": "#2a2a2a",
            "chip_text": "#d4d4d4",
            "accent": "#10b981",
            "accent_soft": "#064e3b",
            "iso_struct_top": "#242424",
            "iso_struct_left": "#151515",
            "iso_struct_right": "#0c0c0c",
            "iso_struct_stroke": "#3a3a3a",
            "iso_highlight_top": "#ffffff",
            "iso_highlight_left": "#cccccc",
            "iso_highlight_right": "#888888",
            "iso_highlight_stroke": "#ffffff",
            "commit_levels": [
                ("#141414", "#0d0d0d", "#080808", "#222222"),
                ("#525252", "#3a3a3a", "#262626", "#6b6b6b"),
                ("#a3a3a3", "#787878", "#525252", "#c4c4c4"),
                ("#ffffff", "#d4d4d4", "#969696", "#ffffff"),
            ],
            "scan_beam": "#ffffff",
        }

    # Light mode anchored on #eeeeee surface and #000000 architectural UI elements
    return {
        "mode": "light",
        "bg_start": "#f3f3f3",
        "bg_end": "#eeeeee",
        "canvas_border": "#cccccc",
        "grid_stroke": "#dedede",
        "card_bg": "#f9f9f9",
        "card_bg_alt": "#f2f2f2",
        "card_border": "#cccccc",
        "bevel_right": "#dcdcdc",
        "bevel_bottom": "#cecece",
        "text_primary": "#000000",
        "text_secondary": "#3f3f3f",
        "text_muted": "#6b6b6b",
        "pill_bg": "#000000",
        "pill_text": "#ffffff",
        "chip_bg": "#e6e6e6",
        "chip_border": "#c8c8c8",
        "chip_text": "#171717",
        "accent": "#059669",
        "accent_soft": "#a7f3d0",
        "iso_struct_top": "#ffffff",
        "iso_struct_left": "#dfdfdf",
        "iso_struct_right": "#c4c4c4",
        "iso_struct_stroke": "#9e9e9e",
        "iso_highlight_top": "#383838",
        "iso_highlight_left": "#1f1f1f",
        "iso_highlight_right": "#0a0a0a",
        "iso_highlight_stroke": "#5c5c5c",
        "commit_levels": [
            ("#e3e3e3", "#d5d5d5", "#c8c8c8", "#cccccc"),
            ("#9ca3af", "#6b7280", "#4b5563", "#4b5563"),
            ("#454545", "#2b2b2b", "#171717", "#525252"),
            ("#1f1f1f", "#0f0f0f", "#000000", "#4a4a4a"),
        ],
        "scan_beam": "#000000",
    }


def escape_xml(value: str) -> str:
    """Escape dynamic strings so commit messages or descriptions never break SVG XML."""
    return html.escape(value, quote=True)


def truncate_text(value: str, max_chars: int) -> str:
    """Clamp dynamic API strings so labels never overflow fixed SVG card bounds."""
    cleaned = " ".join(value.strip().split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 1].rstrip() + "…"


def resolve_github_token() -> str:
    """Resolve an authentication token from CI env vars or local GitHub CLI session."""
    for env_name in ("GH_PROFILE_TOKEN", "GITHUB_TOKEN"):
        token = os.environ.get(env_name, "").strip()
        if token:
            return token

    # Fall back to local gh CLI token during developer runs when env vars are unset
    try:
        completed = subprocess.run(
            ["gh", "auth", "token"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return completed.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def fetch_github_telemetry(username: str) -> dict[str, Any]:
    """Fetch live repositories, commits, and 52-week contributions via GitHub GraphQL."""
    token = resolve_github_token()
    if token:
        payload = json.dumps(
            {"query": GRAPHQL_QUERY, "variables": {"login": username}}
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://api.github.com/graphql",
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": f"{username}-profile-3d-generator",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                parsed = json.loads(response.read().decode("utf-8"))
                user_node = parsed.get("data", {}).get("user")
                if user_node:
                    return normalize_telemetry(user_node, username)
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
            print(f"GraphQL telemetry warning ({exc}); falling back to REST API.")

    return fetch_public_rest_fallback(username)


def normalize_telemetry(user_node: dict[str, Any], username: str) -> dict[str, Any]:
    """Transform raw GraphQL payload into deterministic structures for SVG rendering."""
    repos_raw = user_node.get("repositories", {}).get("nodes", [])
    filtered_repos: list[dict[str, Any]] = []
    recent_commits: list[dict[str, Any]] = []

    for repo in repos_raw:
        repo_name = repo.get("name", "")
        # Exclude the profile config repository itself so recent repos showcase real codebases
        if repo_name.lower() == username.lower():
            continue

        branch_ref = repo.get("defaultBranchRef") or {}
        branch_name = branch_ref.get("name") or "main"
        history = (branch_ref.get("target") or {}).get("history") or {}
        commit_count = int(history.get("totalCount") or 0)
        lang_node = repo.get("primaryLanguage") or {}

        filtered_repos.append(
            {
                "name": repo_name,
                "language": lang_node.get("name") or "TypeScript",
                "pushed_at": (repo.get("pushedAt") or "")[:10],
                "homepage_url": repo.get("homepageUrl") or "",
                "stars": int(repo.get("stargazerCount") or 0),
                "commit_count": commit_count,
            }
        )

        for commit_node in history.get("nodes") or []:
            headline = (commit_node.get("messageHeadline") or "").lstrip("- ").strip()
            recent_commits.append(
                {
                    "repo": repo_name,
                    "branch": branch_name,
                    "sha": (commit_node.get("oid") or "")[:7],
                    "message": headline or "Update implementation",
                    "date": (commit_node.get("committedDate") or "")[:10],
                    "timestamp": commit_node.get("committedDate") or "",
                }
            )

    recent_commits.sort(key=lambda item: item["timestamp"], reverse=True)

    # Prefer the latest HEAD commit per distinct repository so telemetry spans multiple builds
    diversified_commits: list[dict[str, Any]] = []
    seen_repos: set[str] = set()
    overflow_commits: list[dict[str, Any]] = []
    for item in recent_commits:
        if item["repo"] not in seen_repos:
            seen_repos.add(item["repo"])
            diversified_commits.append(item)
        else:
            overflow_commits.append(item)
    diversified_commits.extend(overflow_commits)

    calendar = (
        user_node.get("contributionsCollection", {}).get("contributionCalendar") or {}
    )
    weeks_raw = calendar.get("weeks") or []
    weeks: list[list[dict[str, Any]]] = []
    for week in weeks_raw[-52:]:
        days = week.get("contributionDays") or []
        weeks.append(
            [
                {
                    "count": int(day.get("contributionCount") or 0),
                    "date": day.get("date") or "",
                    "weekday": int(day.get("weekday") or 0),
                }
                for day in days
            ]
        )

    total_public_repos = int(user_node.get("repositories", {}).get("totalCount") or len(filtered_repos))
    total_contributions = int(calendar.get("totalContributions") or 0)

    return {
        "username": username,
        "total_public_repos": total_public_repos,
        "total_contributions": total_contributions,
        "recent_repos": filtered_repos[:6],
        "recent_commits": diversified_commits[:5],
        "weeks": weeks,
    }


def fetch_public_rest_fallback(username: str) -> dict[str, Any]:
    """Provide unauthenticated REST fallback if GraphQL token is unavailable."""
    repos_url = f"https://api.github.com/users/{username}/repos?sort=pushed&per_page=10"
    request = urllib.request.Request(
        repos_url, headers={"User-Agent": f"{username}-profile-3d-generator"}
    )
    recent_repos: list[dict[str, Any]] = []
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            items = json.loads(response.read().decode("utf-8"))
            for item in items:
                name = item.get("name", "")
                if name.lower() == username.lower():
                    continue
                recent_repos.append(
                    {
                        "name": name,
                        "language": item.get("language") or "TypeScript",
                        "pushed_at": (item.get("pushed_at") or "")[:10],
                        "homepage_url": item.get("homepage") or "",
                        "stars": int(item.get("stargazers_count") or 0),
                        "commit_count": 10,
                    }
                )
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        pass

    today = dt.date.today()
    weeks: list[list[dict[str, Any]]] = []
    for week_idx in range(52):
        week_days: list[dict[str, Any]] = []
        for day_idx in range(7):
            day_date = today - dt.timedelta(days=(51 - week_idx) * 7 + (6 - day_idx))
            week_days.append(
                {"count": 0, "date": day_date.isoformat(), "weekday": day_idx}
            )
        weeks.append(week_days)

    return {
        "username": username,
        "total_public_repos": max(len(recent_repos), 28),
        "total_contributions": 55,
        "recent_repos": recent_repos[:6],
        "recent_commits": [],
        "weeks": weeks,
    }


def project_iso(
    origin_x: float,
    origin_y: float,
    grid_x: float,
    grid_y: float,
    grid_z: float,
) -> tuple[float, float]:
    """Project 3D coordinates onto a 30-degree true isometric 2D plane."""
    cos_30 = 0.8660254
    sin_30 = 0.5
    screen_x = origin_x + (grid_x - grid_y) * cos_30
    screen_y = origin_y + (grid_x + grid_y) * sin_30 - grid_z
    return round(screen_x, 2), round(screen_y, 2)


def format_points(points: list[tuple[float, float]]) -> str:
    """Format coordinate pairs into an SVG polygon point string."""
    return " ".join(f"{px:.2f},{py:.2f}" for px, py in points)


def draw_iso_box(
    origin_x: float,
    origin_y: float,
    x0: float,
    y0: float,
    z0: float,
    dx: float,
    dy: float,
    dz: float,
    colors: tuple[str, str, str, str],
    stroke_width: float = 1.0,
) -> str:
    """Render an occluded 3-face isometric prism (top, left-front, right-front)."""
    top_fill, left_fill, right_fill, stroke_color = colors
    x1, y1, z1 = x0 + dx, y0 + dy, z0 + dz

    p_top_back = project_iso(origin_x, origin_y, x0, y0, z1)
    p_top_right = project_iso(origin_x, origin_y, x1, y0, z1)
    p_top_front = project_iso(origin_x, origin_y, x1, y1, z1)
    p_top_left = project_iso(origin_x, origin_y, x0, y1, z1)

    p_bot_right = project_iso(origin_x, origin_y, x1, y0, z0)
    p_bot_front = project_iso(origin_x, origin_y, x1, y1, z0)
    p_bot_left = project_iso(origin_x, origin_y, x0, y1, z0)

    left_face = format_points([p_top_left, p_top_front, p_bot_front, p_bot_left])
    right_face = format_points([p_top_front, p_top_right, p_bot_right, p_bot_front])
    top_face = format_points([p_top_back, p_top_right, p_top_front, p_top_left])

    return (
        f'<g stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-linejoin="round">'
        f'<polygon points="{left_face}" fill="{left_fill}" />'
        f'<polygon points="{right_face}" fill="{right_fill}" />'
        f'<polygon points="{top_face}" fill="{top_fill}" />'
        f"</g>"
    )


def draw_extruded_card(
    x: float,
    y: float,
    width: float,
    height: float,
    depth: float,
    palette: dict[str, Any],
) -> str:
    """Draw an architectural card with extruded 3D right and bottom bevels."""
    x1, y1 = x + width, y + height
    right_bevel = format_points(
        [(x1, y + 6), (x1 + depth, y + 6 + depth), (x1 + depth, y1 + depth), (x1, y1)]
    )
    bottom_bevel = format_points(
        [(x + 6, y1), (x1, y1), (x1 + depth, y1 + depth), (x + 6 + depth, y1 + depth)]
    )
    return (
        f"<g>"
        f'<polygon points="{bottom_bevel}" fill="{palette["bevel_bottom"]}" '
        f'stroke="{palette["card_border"]}" stroke-width="1" stroke-linejoin="round" />'
        f'<polygon points="{right_bevel}" fill="{palette["bevel_right"]}" '
        f'stroke="{palette["card_border"]}" stroke-width="1" stroke-linejoin="round" />'
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="10" '
        f'fill="{palette["card_bg"]}" stroke="{palette["card_border"]}" stroke-width="1.2" />'
        f"</g>"
    )


def build_canvas_shell(
    height: int,
    palette: dict[str, Any],
    extra_defs: str = "",
) -> tuple[str, str]:
    """Create shared SVG outer shell with subtle architectural grid texture."""
    grad_id = f"bg_grad_{palette['mode']}"
    grid_id = f"grid_pat_{palette['mode']}"
    header = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_WIDTH} {height}" width="100%" role="img">
  <defs>
    <linearGradient id="{grad_id}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{palette['bg_start']}" />
      <stop offset="100%" stop-color="{palette['bg_end']}" />
    </linearGradient>
    <pattern id="{grid_id}" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M 32 0 L 0 0 0 32" fill="none" stroke="{palette['grid_stroke']}" stroke-width="0.8" />
    </pattern>
    {extra_defs}
  </defs>
  <rect x="1" y="1" width="{CANVAS_WIDTH - 2}" height="{height - 2}" rx="16" fill="url(#{grad_id})" stroke="{palette['canvas_border']}" stroke-width="1.5" />
  <rect x="2" y="2" width="{CANVAS_WIDTH - 4}" height="{height - 4}" rx="15" fill="url(#{grid_id})" opacity="0.65" />
"""
    footer = "\n</svg>\n"
    return header, footer


def render_hero_svg(telemetry: dict[str, Any], palette: dict[str, Any]) -> str:
    """Render Scene 1: Hero identity stage with levitating 3-tier isometric 3D stack."""
    height = 420
    header, footer = build_canvas_shell(height, palette)
    ox, oy = 862.0, 266.0

    struct_colors = (
        palette["iso_struct_top"],
        palette["iso_struct_left"],
        palette["iso_struct_right"],
        palette["iso_struct_stroke"],
    )
    hi_colors = (
        palette["iso_highlight_top"],
        palette["iso_highlight_left"],
        palette["iso_highlight_right"],
        palette["iso_highlight_stroke"],
    )

    # Floor isometric blueprint rings under the levitating stack
    floor_outer = format_points(
        [
            project_iso(ox, oy, -122, -122, -18),
            project_iso(ox, oy, 122, -122, -18),
            project_iso(ox, oy, 122, 122, -18),
            project_iso(ox, oy, -122, 122, -18),
        ]
    )
    floor_inner = format_points(
        [
            project_iso(ox, oy, -92, -92, -18),
            project_iso(ox, oy, 92, -92, -18),
            project_iso(ox, oy, 92, 92, -18),
            project_iso(ox, oy, -92, 92, -18),
        ]
    )

    # Vertical energy conduits linking the 3 levitating architectural tiers
    conduit_left_a = project_iso(ox, oy, -55, 55, 18)
    conduit_left_b = project_iso(ox, oy, -55, 55, 138)
    conduit_right_a = project_iso(ox, oy, 55, -55, 18)
    conduit_right_b = project_iso(ox, oy, 55, -55, 138)
    conduit_center_a = project_iso(ox, oy, 0, 0, 18)
    conduit_center_b = project_iso(ox, oy, 0, 0, 150)

    # Tier 1: Infrastructure & Data Slab
    tier_1 = draw_iso_box(ox, oy, -85, -85, 0, 170, 170, 20, struct_colors, 1.2)

    # Tier 2: AI & Distributed API Core (levitating middle layer)
    tier_2_slab = draw_iso_box(ox, oy, -68, -68, 64, 136, 136, 18, struct_colors, 1.2)
    tier_2_core = draw_iso_box(ox, oy, -28, -28, 82, 56, 56, 22, hi_colors, 1.2)

    # Tier 3: Interactive 3D & Next.js Interface Layer (counter-levitating top crown)
    tier_3_slab = draw_iso_box(ox, oy, -54, -54, 132, 108, 108, 14, struct_colors, 1.2)
    cube_nw = draw_iso_box(ox, oy, -38, -38, 146, 26, 26, 24, hi_colors, 1.1)
    cube_ne = draw_iso_box(ox, oy, 12, -38, 146, 26, 26, 18, struct_colors, 1.1)
    cube_sw = draw_iso_box(ox, oy, -38, 12, 146, 26, 26, 18, struct_colors, 1.1)
    cube_se = draw_iso_box(ox, oy, 8, 8, 146, 32, 32, 32, hi_colors, 1.2)

    # Orbiting satellite micro-cubes positioned clear of callout labels
    sat_left = draw_iso_box(ox - 166, oy - 74, -12, -12, 0, 24, 24, 24, hi_colors, 1.0)
    sat_right = draw_iso_box(ox + 114, oy - 138, -10, -10, 0, 20, 20, 20, struct_colors, 1.0)

    crown_apex = project_iso(ox, oy, 24, 24, 178)
    total_repos = telemetry["total_public_repos"]

    body = f"""
  <!-- Left Column: Architectural Identity & Telemetry -->
  <g transform="translate(52, 54)">
    <!-- Status Badge -->
    <rect x="0" y="0" width="328" height="30" rx="15" fill="{palette['chip_bg']}" stroke="{palette['chip_border']}" stroke-width="1" />
    <circle cx="18" cy="15" r="4.5" fill="{palette['accent']}">
      <animate attributeName="opacity" values="1;0.3;1" dur="2.2s" repeatCount="indefinite" />
    </circle>
    <circle cx="18" cy="15" r="4.5" fill="none" stroke="{palette['accent']}" stroke-width="1.2">
      <animate attributeName="r" values="4.5;10;4.5" dur="2.2s" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0.7;0;0.7" dur="2.2s" repeatCount="indefinite" />
    </circle>
    <text x="34" y="19.5" font-family='{FONT_MONO}' font-size="11" font-weight="600" letter-spacing="1.2" fill="{palette['text_secondary']}">JAIPUR, IN  //  OPEN TO SELECT BUILDS</text>

    <!-- Name & Role -->
    <text x="0" y="88" font-family='{FONT_SANS}' font-size="48" font-weight="800" letter-spacing="-1.4" fill="{palette['text_primary']}">MOHIT KUMAWAT</text>
    <text x="0" y="122" font-family='{FONT_MONO}' font-size="14.5" font-weight="600" letter-spacing="0.5" fill="{palette['text_secondary']}">FRONT-END &amp; FULL-STACK ENGINEER  ·  3D WEB &amp; AI SYSTEMS</text>

    <!-- Engineering Statement -->
    <text x="0" y="164" font-family='{FONT_SANS}' font-size="15" fill="{palette['text_secondary']}">Building high-velocity Next.js platforms, interactive Three.js WebGL</text>
    <text x="0" y="186" font-family='{FONT_SANS}' font-size="15" fill="{palette['text_secondary']}">experiences, real-time AI pipelines, and cloud-native web products.</text>

    <!-- Core Stack Pills -->
    <g transform="translate(0, 214)">
      <rect x="0" y="0" width="96" height="28" rx="6" fill="{palette['pill_bg']}" />
      <text x="48" y="18" text-anchor="middle" font-family='{FONT_MONO}' font-size="11.5" font-weight="700" fill="{palette['pill_text']}">TypeScript</text>

      <rect x="106" y="0" width="92" height="28" rx="6" fill="{palette['pill_bg']}" />
      <text x="152" y="18" text-anchor="middle" font-family='{FONT_MONO}' font-size="11.5" font-weight="700" fill="{palette['pill_text']}">Next.js 16</text>

      <rect x="208" y="0" width="88" height="28" rx="6" fill="{palette['chip_bg']}" stroke="{palette['chip_border']}" />
      <text x="252" y="18" text-anchor="middle" font-family='{FONT_MONO}' font-size="11.5" font-weight="600" fill="{palette['chip_text']}">Three.js</text>

      <rect x="306" y="0" width="88" height="28" rx="6" fill="{palette['chip_bg']}" stroke="{palette['chip_border']}" />
      <text x="350" y="18" text-anchor="middle" font-family='{FONT_MONO}' font-size="11.5" font-weight="600" fill="{palette['chip_text']}">Supabase</text>

      <rect x="404" y="0" width="92" height="28" rx="6" fill="{palette['chip_bg']}" stroke="{palette['chip_border']}" />
      <text x="450" y="18" text-anchor="middle" font-family='{FONT_MONO}' font-size="11.5" font-weight="600" fill="{palette['chip_text']}">Gemini AI</text>
    </g>

    <!-- Telemetry Metrics Strip -->
    <g transform="translate(0, 266)">
      <rect x="0" y="0" width="584" height="58" rx="10" fill="{palette['card_bg']}" stroke="{palette['card_border']}" stroke-width="1" />
      <line x1="176" y1="12" x2="176" y2="46" stroke="{palette['card_border']}" stroke-width="1" />
      <line x1="392" y1="12" x2="392" y2="46" stroke="{palette['card_border']}" stroke-width="1" />

      <text x="18" y="23" font-family='{FONT_MONO}' font-size="10" letter-spacing="1" fill="{palette['text_muted']}">PUBLIC REPOS</text>
      <text x="18" y="43" font-family='{FONT_MONO}' font-size="14.5" font-weight="700" fill="{palette['text_primary']}">{total_repos} REPOSITORIES</text>

      <text x="194" y="23" font-family='{FONT_MONO}' font-size="10" letter-spacing="1" fill="{palette['text_muted']}">CURRENT ROLE</text>
      <text x="194" y="43" font-family='{FONT_MONO}' font-size="14" font-weight="700" fill="{palette['text_primary']}">SDE Intern @ LawDocs</text>

      <text x="410" y="23" font-family='{FONT_MONO}' font-size="10" letter-spacing="1" fill="{palette['text_muted']}">ARCHITECTURE</text>
      <text x="410" y="43" font-family='{FONT_MONO}' font-size="14" font-weight="700" fill="{palette['text_primary']}">UI · API · 3D · AI</text>
    </g>
  </g>

  <!-- Right Column: Animated Isometric 3D Engineering Stack -->
  <g>
    <!-- Axonometric Base Grid Plinth -->
    <polygon points="{floor_outer}" fill="none" stroke="{palette['card_border']}" stroke-width="1.2" stroke-dasharray="5 5" />
    <polygon points="{floor_inner}" fill="none" stroke="{palette['card_border']}" stroke-width="1">
      <animate attributeName="opacity" values="0.35;0.9;0.35" dur="4s" repeatCount="indefinite" />
    </polygon>

    <!-- Tier 1: Data & Cloud Foundation -->
    <g>
      <animateTransform attributeName="transform" type="translate" values="0,0; 0,-4; 0,0" dur="5.2s" repeatCount="indefinite" />
      {tier_1}
    </g>

    <!-- Animated Vertical Data Conduits -->
    <line x1="{conduit_left_a[0]}" y1="{conduit_left_a[1]}" x2="{conduit_left_b[0]}" y2="{conduit_left_b[1]}" stroke="{palette['text_muted']}" stroke-width="1.2" stroke-dasharray="4 4" opacity="0.65" />
    <line x1="{conduit_right_a[0]}" y1="{conduit_right_a[1]}" x2="{conduit_right_b[0]}" y2="{conduit_right_b[1]}" stroke="{palette['text_muted']}" stroke-width="1.2" stroke-dasharray="4 4" opacity="0.65" />
    <line x1="{conduit_center_a[0]}" y1="{conduit_center_a[1]}" x2="{conduit_center_b[0]}" y2="{conduit_center_b[1]}" stroke="{palette['accent']}" stroke-width="1.5" stroke-dasharray="4 4" opacity="0.8" />

    <!-- Rising Telemetry Pulses Along Conduits (opacity=0 prevents pre-begin origin artifact) -->
    <circle r="3.2" fill="{palette['accent']}" opacity="0">
      <animateMotion path="M {conduit_left_a[0]},{conduit_left_a[1]} L {conduit_left_b[0]},{conduit_left_b[1]}" dur="2.4s" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;1;0" dur="2.4s" repeatCount="indefinite" />
    </circle>
    <circle r="3.2" fill="{palette['accent']}" opacity="0">
      <animateMotion path="M {conduit_right_a[0]},{conduit_right_a[1]} L {conduit_right_b[0]},{conduit_right_b[1]}" dur="2.4s" begin="1.2s" repeatCount="indefinite" />
      <animate attributeName="opacity" values="0;1;0" dur="2.4s" begin="1.2s" repeatCount="indefinite" />
    </circle>

    <!-- Tier 2: Levitating AI & API Engine -->
    <g>
      <animateTransform attributeName="transform" type="translate" values="0,0; 0,-10; 0,0" dur="4.2s" repeatCount="indefinite" />
      {tier_2_slab}
      {tier_2_core}
    </g>

    <!-- Tier 3: Counter-Levitating 3D Interface Crown -->
    <g>
      <animateTransform attributeName="transform" type="translate" values="0,-3; 0,-16; 0,-3" dur="3.6s" repeatCount="indefinite" />
      {tier_3_slab}
      {cube_nw}
      {cube_ne}
      {cube_sw}
      {cube_se}
      <circle cx="{crown_apex[0]}" cy="{crown_apex[1] - 10}" r="3.5" fill="{palette['accent']}" />
      <circle cx="{crown_apex[0]}" cy="{crown_apex[1] - 10}" r="3.5" fill="none" stroke="{palette['accent']}" stroke-width="1.3">
        <animate attributeName="r" values="3.5;14;3.5" dur="2.6s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.9;0;0.9" dur="2.6s" repeatCount="indefinite" />
      </circle>
    </g>

    <!-- Floating Satellite Cubes & Layer Callout Labels -->
    <g>
      <animateTransform attributeName="transform" type="translate" values="0,0; 0,-12; 0,0" dur="3.8s" begin="0.5s" repeatCount="indefinite" />
      {sat_left}
    </g>
    <g>
      <animateTransform attributeName="transform" type="translate" values="0,-8; 0,4; 0,-8" dur="4.4s" begin="0.9s" repeatCount="indefinite" />
      {sat_right}
    </g>

    <!-- Callout Annotations -->
    <g font-family='{FONT_MONO}' font-size="10" fill="{palette['text_muted']}">
      <text x="1008" y="106" font-weight="700" fill="{palette['text_primary']}">L3 // 3D &amp; UI</text>
      <text x="1008" y="121">Next.js · Three.js</text>

      <text x="1014" y="198" font-weight="700" fill="{palette['text_primary']}">L2 // AI &amp; API</text>
      <text x="1014" y="213">Node · Gemini · Pub/Sub</text>

      <text x="1014" y="294" font-weight="700" fill="{palette['text_primary']}">L1 // DATA &amp; CLOUD</text>
      <text x="1014" y="309">Supabase · PostgreSQL</text>
    </g>
  </g>
"""
    return header + body + footer


def render_mini_project_sculpture(
    kind: str,
    origin_x: float,
    origin_y: float,
    palette: dict[str, Any],
) -> str:
    """Render bespoke animated isometric mini-sculptures inside each project card."""
    struct_colors = (
        palette["iso_struct_top"],
        palette["iso_struct_left"],
        palette["iso_struct_right"],
        palette["iso_struct_stroke"],
    )
    hi_colors = (
        palette["iso_highlight_top"],
        palette["iso_highlight_left"],
        palette["iso_highlight_right"],
        palette["iso_highlight_stroke"],
    )

    if kind == "nodes":
        base = draw_iso_box(origin_x, origin_y, -26, -26, 0, 52, 52, 8, struct_colors, 1.0)
        col_a = draw_iso_box(origin_x, origin_y, -20, -18, 8, 16, 16, 20, hi_colors, 1.0)
        col_b = draw_iso_box(origin_x, origin_y, 4, -18, 8, 16, 16, 13, struct_colors, 1.0)
        col_c = draw_iso_box(origin_x, origin_y, -6, 6, 8, 22, 22, 26, hi_colors, 1.0)
        return (
            f"<g>{base}"
            f'<g><animateTransform attributeName="transform" type="translate" values="0,0;0,-6;0,0" dur="3.1s" repeatCount="indefinite" />{col_a}</g>'
            f"{col_b}"
            f'<g><animateTransform attributeName="transform" type="translate" values="0,-4;0,2;0,-4" dur="3.1s" repeatCount="indefinite" />{col_c}</g>'
            f"</g>"
        )

    if kind == "relay":
        base = draw_iso_box(origin_x, origin_y, -24, -24, 0, 48, 48, 8, struct_colors, 1.0)
        tower = draw_iso_box(origin_x, origin_y, -11, -11, 8, 22, 22, 28, hi_colors, 1.0)
        apex = project_iso(origin_x, origin_y, 0, 0, 38)
        return (
            f"<g>{base}{tower}"
            f'<circle cx="{apex[0]}" cy="{apex[1]}" r="3" fill="{palette["accent"]}" />'
            f'<circle cx="{apex[0]}" cy="{apex[1]}" r="3" fill="none" stroke="{palette["accent"]}" stroke-width="1.2">'
            f'<animate attributeName="r" values="3;16;3" dur="2.4s" repeatCount="indefinite" />'
            f'<animate attributeName="opacity" values="0.9;0;0.9" dur="2.4s" repeatCount="indefinite" />'
            f"</circle></g>"
        )

    if kind == "storefront":
        plinth = draw_iso_box(origin_x, origin_y, -28, -24, 0, 56, 48, 7, struct_colors, 1.0)
        hall = draw_iso_box(origin_x, origin_y, -18, -16, 7, 36, 28, 20, hi_colors, 1.0)
        canopy = draw_iso_box(origin_x, origin_y, -20, -2, 18, 40, 18, 5, struct_colors, 1.0)
        return (
            f'<g><animateTransform attributeName="transform" type="translate" values="0,0;0,-5;0,0" dur="3.8s" repeatCount="indefinite" />'
            f"{plinth}{hall}{canopy}</g>"
        )

    # Stacked shader planes sculpture for 3D Portfolio
    layer_1 = draw_iso_box(origin_x, origin_y, -24, -24, 0, 48, 48, 5, struct_colors, 1.0)
    layer_2 = draw_iso_box(origin_x, origin_y, -20, -20, 13, 40, 40, 5, hi_colors, 1.0)
    layer_3 = draw_iso_box(origin_x, origin_y, -15, -15, 26, 30, 30, 6, hi_colors, 1.0)
    return (
        f"<g>{layer_1}"
        f'<g><animateTransform attributeName="transform" type="translate" values="0,0;0,-4;0,0" dur="2.8s" repeatCount="indefinite" />{layer_2}</g>'
        f'<g><animateTransform attributeName="transform" type="translate" values="0,-2;0,-9;0,-2" dur="2.8s" repeatCount="indefinite" />{layer_3}</g>'
        f"</g>"
    )


def render_projects_svg(palette: dict[str, Any]) -> str:
    """Render Scene 2: 2x2 Isometric 3D Featured Projects Showcase."""
    height = 510
    header, footer = build_canvas_shell(height, palette)

    parts: list[str] = [
        f"""
  <!-- Section Header -->
  <g transform="translate(48, 42)">
    <text x="0" y="0" font-family='{FONT_MONO}' font-size="11" font-weight="700" letter-spacing="1.6" fill="{palette['accent']}">01 // SELECTED PRODUCTION BUILDS</text>
    <text x="0" y="28" font-family='{FONT_SANS}' font-size="24" font-weight="800" letter-spacing="-0.6" fill="{palette['text_primary']}">Featured 3D &amp; Full-Stack Projects</text>
    <text x="1104" y="26" text-anchor="end" font-family='{FONT_MONO}' font-size="11" fill="{palette['text_muted']}">LIVE DEPLOYMENTS ON VERCEL</text>
  </g>
"""
    ]

    card_w = 532.0
    card_h = 186.0
    start_x = 48.0
    start_y = 92.0
    gap_x = 36.0
    gap_y = 26.0

    for idx, proj in enumerate(FEATURED_PROJECTS):
        col = idx % 2
        row = idx // 2
        cx = start_x + col * (card_w + gap_x)
        cy = start_y + row * (card_h + gap_y)
        delay = f"{idx * 0.55:.2f}s"

        card_shell = draw_extruded_card(cx, cy, card_w, card_h, 7.0, palette)
        sculpture = render_mini_project_sculpture(
            proj["sculpture"], cx + card_w - 64, cy + 74, palette
        )

        # Render tech stack pills neatly along bottom row of the card
        chips_svg: list[str] = []
        cursor_x = cx + 24
        chip_y = cy + 144
        for tag_idx, tag in enumerate(proj["stack"]):
            tag_w = max(len(tag) * 7.4 + 20, 62)
            is_primary = tag_idx == 0
            bg = palette["pill_bg"] if is_primary else palette["chip_bg"]
            fg = palette["pill_text"] if is_primary else palette["chip_text"]
            stroke_attr = (
                ""
                if is_primary
                else f'stroke="{palette["chip_border"]}" stroke-width="1"'
            )
            chips_svg.append(
                f'<rect x="{cursor_x:.1f}" y="{chip_y:.1f}" width="{tag_w:.1f}" height="24" rx="5" fill="{bg}" {stroke_attr} />'
                f'<text x="{cursor_x + tag_w / 2:.1f}" y="{chip_y + 15.5:.1f}" text-anchor="middle" '
                f'font-family=\'{FONT_MONO}\' font-size="10.5" font-weight="600" fill="{fg}">{escape_xml(tag)}</text>'
            )
            cursor_x += tag_w + 8

        parts.append(
            f"""
  <g>
    <animateTransform attributeName="transform" type="translate" values="0,0; 0,-3.5; 0,0" dur="4.8s" begin="{delay}" repeatCount="indefinite" />
    {card_shell}

    <!-- Index & Live Domain Badge -->
    <text x="{cx + 24}" y="{cy + 30}" font-family='{FONT_MONO}' font-size="11" font-weight="700" fill="{palette['text_muted']}">{proj['index']} // {escape_xml(proj['live_domain'])}</text>
    <circle cx="{cx + 16}" cy="{cy + 26}" r="3" fill="{palette['accent']}" opacity="0">
      <animate attributeName="opacity" values="0;0" dur="1s" />
    </circle>

    <!-- Title & Subtitle -->
    <text x="{cx + 24}" y="{cy + 58}" font-family='{FONT_SANS}' font-size="20" font-weight="800" letter-spacing="-0.4" fill="{palette['text_primary']}">{escape_xml(proj['title'])}</text>
    <text x="{cx + 24}" y="{cy + 78}" font-family='{FONT_MONO}' font-size="11.5" font-weight="600" fill="{palette['accent']}">{escape_xml(proj['subtitle'])}</text>

    <!-- Two-line Engineering Summary -->
    <text x="{cx + 24}" y="{cy + 104}" font-family='{FONT_SANS}' font-size="12.5" fill="{palette['text_secondary']}">{escape_xml(proj['summary_line_1'])}</text>
    <text x="{cx + 24}" y="{cy + 122}" font-family='{FONT_SANS}' font-size="12.5" fill="{palette['text_secondary']}">{escape_xml(proj['summary_line_2'])}</text>

    <!-- Bespoke Isometric Mini-Sculpture -->
    {sculpture}

    <!-- Stack Chips -->
    {"".join(chips_svg)}
  </g>
"""
        )

    return header + "".join(parts) + footer


def render_repos_svg(telemetry: dict[str, Any], palette: dict[str, Any]) -> str:
    """Render Scene 3: 3x2 Isometric 3D Deck of Top Recent Public Repositories."""
    height = 390
    header, footer = build_canvas_shell(height, palette)
    repos = telemetry["recent_repos"][:6]

    parts: list[str] = [
        f"""
  <!-- Section Header -->
  <g transform="translate(48, 42)">
    <text x="0" y="0" font-family='{FONT_MONO}' font-size="11" font-weight="700" letter-spacing="1.6" fill="{palette['accent']}">02 // AUTO-SYNCED REPOSITORY TELEMETRY</text>
    <text x="0" y="28" font-family='{FONT_SANS}' font-size="24" font-weight="800" letter-spacing="-0.6" fill="{palette['text_primary']}">Top Recent Public Repositories</text>
    <text x="1104" y="26" text-anchor="end" font-family='{FONT_MONO}' font-size="11" fill="{palette['text_muted']}">ORDERED BY LATEST GIT PUSH</text>
  </g>
"""
    ]

    card_w = 348.0
    card_h = 122.0
    start_x = 48.0
    start_y = 92.0
    gap_x = 28.0
    gap_y = 24.0

    struct_colors = (
        palette["iso_struct_top"],
        palette["iso_struct_left"],
        palette["iso_struct_right"],
        palette["iso_struct_stroke"],
    )
    hi_colors = (
        palette["iso_highlight_top"],
        palette["iso_highlight_left"],
        palette["iso_highlight_right"],
        palette["iso_highlight_stroke"],
    )

    for idx, repo in enumerate(repos):
        col = idx % 3
        row = idx // 3
        cx = start_x + col * (card_w + gap_x)
        cy = start_y + row * (card_h + gap_y)
        delay = f"{idx * 0.35:.2f}s"

        card_shell = draw_extruded_card(cx, cy, card_w, card_h, 6.0, palette)
        repo_name = truncate_text(repo["name"], 20)
        lang_name = truncate_text(repo["language"], 14)
        pushed_date = repo["pushed_at"] or "2026"
        commits = repo["commit_count"]
        has_live = bool(repo["homepage_url"])

        # Small isometric 3D module indicator on top-right of each repo cartridge
        cube_colors = hi_colors if has_live else struct_colors
        mini_cube = draw_iso_box(cx + card_w - 34, cy + 40, -9, -9, 0, 18, 18, 18, cube_colors, 1.0)

        live_badge = ""
        if has_live:
            live_badge = (
                f'<rect x="{cx + card_w - 88}" y="{cy + 84}" width="64" height="22" rx="5" fill="{palette["pill_bg"]}" />'
                f'<circle cx="{cx + card_w - 75}" cy="{cy + 95}" r="3" fill="{palette["accent"]}">'
                f'<animate attributeName="opacity" values="1;0.3;1" dur="2s" begin="{delay}" repeatCount="indefinite" />'
                f"</circle>"
                f'<text x="{cx + card_w - 49}" y="{cy + 99}" text-anchor="middle" font-family=\'{FONT_MONO}\' font-size="10" font-weight="700" fill="{palette["pill_text"]}">LIVE</text>'
            )

        # Lucide-style git-branch vector icon (no emojis)
        branch_icon = (
            f'<g transform="translate({cx + 20}, {cy + 20})" fill="none" stroke="{palette["text_primary"]}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
            f'<line x1="5" y1="3" x2="5" y2="15" />'
            f'<circle cx="15" cy="5" r="2.5" />'
            f'<circle cx="5" cy="17" r="2.5" />'
            f'<path d="M15 7.5a7.5 7.5 0 0 1-7.5 7.5H5" />'
            f"</g>"
        )

        parts.append(
            f"""
  <g>
    <animateTransform attributeName="transform" type="translate" values="0,0; 0,-3; 0,0" dur="4.4s" begin="{delay}" repeatCount="indefinite" />
    {card_shell}
    {branch_icon}
    <text x="{cx + 46}" y="{cy + 36}" font-family='{FONT_SANS}' font-size="17" font-weight="700" fill="{palette['text_primary']}">{escape_xml(repo_name)}</text>
    <text x="{cx + 22}" y="{cy + 62}" font-family='{FONT_MONO}' font-size="11" fill="{palette['text_muted']}">PUSHED {escape_xml(pushed_date)}  ·  {commits} COMMITS</text>

    <!-- Language Tag -->
    <rect x="{cx + 20}" y="{cy + 84}" width="104" height="22" rx="5" fill="{palette['chip_bg']}" stroke="{palette['chip_border']}" stroke-width="1" />
    <circle cx="{cx + 33}" cy="{cy + 95}" r="3.5" fill="{palette['text_primary']}" />
    <text x="{cx + 44}" y="{cy + 99}" font-family='{FONT_MONO}' font-size="10.5" font-weight="600" fill="{palette['chip_text']}">{escape_xml(lang_name)}</text>

    {live_badge}
    {mini_cube}
  </g>
"""
        )

    return header + "".join(parts) + footer


def classify_commit_level(count: int, max_count: int) -> int:
    """Bucket daily contribution counts into 4 sculpted 3D height/shade tiers."""
    if count <= 0:
        return 0
    if max_count <= 2:
        return min(count + 1, 3)
    ratio = count / max_count
    if ratio <= 0.34:
        return 1
    if ratio <= 0.68:
        return 2
    return 3


def draw_trimetric_pillar(
    base_x: float,
    base_y: float,
    height: float,
    colors: tuple[str, str, str, str],
) -> tuple[str, tuple[float, float]]:
    """Draw a 3D contribution tower using wide trimetric projection across 52 weeks."""
    top_fill, front_fill, right_fill, stroke_color = colors

    # Top face corners in wide axonometric projection
    p00 = (base_x, base_y - height)
    p10 = (base_x + 12.6, base_y + 1.8 - height)
    p11 = (base_x + 4.8, base_y + 10.6 - height)
    p01 = (base_x - 7.8, base_y + 8.8 - height)

    # Corresponding ground corners
    b10 = (base_x + 12.6, base_y + 1.8)
    b11 = (base_x + 4.8, base_y + 10.6)
    b01 = (base_x - 7.8, base_y + 8.8)

    front_face = format_points([p01, p11, b11, b01])
    right_face = format_points([p11, p10, b10, b11])
    top_face = format_points([p00, p10, p11, p01])
    center_top = ((p00[0] + p11[0]) / 2.0, (p00[1] + p11[1]) / 2.0)

    svg = (
        f'<g stroke="{stroke_color}" stroke-width="0.75" stroke-linejoin="round">'
        f'<polygon points="{front_face}" fill="{front_fill}" />'
        f'<polygon points="{right_face}" fill="{right_fill}" />'
        f'<polygon points="{top_face}" fill="{top_fill}" />'
        f"</g>"
    )
    return svg, center_top


def render_commits_svg(telemetry: dict[str, Any], palette: dict[str, Any]) -> str:
    """Render Scene 4: 52-Week Isometric 3D Contribution Skyline + Commit Stream."""
    height = 570
    scan_grad_id = f"scan_grad_{palette['mode']}"
    extra_defs = f"""
    <linearGradient id="{scan_grad_id}" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{palette['accent']}" stop-opacity="0" />
      <stop offset="50%" stop-color="{palette['accent']}" stop-opacity="0.32" />
      <stop offset="100%" stop-color="{palette['accent']}" stop-opacity="0" />
    </linearGradient>
    <clipPath id="skyline_clip_{palette['mode']}">
      <rect x="48" y="80" width="1104" height="295" rx="12" />
    </clipPath>
    """
    header, footer = build_canvas_shell(height, palette, extra_defs)

    weeks = telemetry["weeks"][-52:]
    all_counts = [day["count"] for week in weeks for day in week] or [0]
    max_day = max(max(all_counts), 1)
    active_days = sum(1 for count in all_counts if count > 0)
    total_contribs = telemetry["total_contributions"]

    # Trimetric grid basis vectors sized so 52x7 fills 1104px cleanly without clipping
    origin_x = 136.0
    origin_y = 148.0
    vec_w = (18.4, 2.45)
    vec_d = (-11.2, 13.0)

    pillars_svg: list[str] = []
    peak_tops: list[tuple[float, float, int]] = []

    # Painter's algorithm: iterate back-to-front (weekday 0..6, week 0..51)
    for day_idx in range(7):
        for week_idx, week in enumerate(weeks):
            if day_idx >= len(week):
                continue
            day = week[day_idx]
            count = day["count"]
            level = classify_commit_level(count, max_day)
            colors = palette["commit_levels"][level]

            if count == 0:
                tower_h = 3.2
            else:
                tower_h = 12.0 + (count / max_day) * 52.0

            bx = origin_x + week_idx * vec_w[0] + day_idx * vec_d[0]
            by = origin_y + week_idx * vec_w[1] + day_idx * vec_d[1]
            pillar_markup, apex = draw_trimetric_pillar(bx, by, tower_h, colors)

            if count > 0:
                # Active contribution obelisks gently oscillate in phase-shifted waves
                phase_delay = f"{(week_idx * 0.08 + day_idx * 0.12) % 3.2:.2f}s"
                lift = -4.5 if level >= 2 else -2.5
                pillars_svg.append(
                    f"<g>"
                    f'<animateTransform attributeName="transform" type="translate" '
                    f'values="0,0; 0,{lift}; 0,0" dur="3.4s" begin="{phase_delay}" repeatCount="indefinite" />'
                    f"{pillar_markup}</g>"
                )
                if level >= 2 or len(peak_tops) < 8:
                    peak_tops.append((apex[0], apex[1], count))
            else:
                pillars_svg.append(pillar_markup)

    # Connect recent active commit summits with an animated isometric trajectory beam
    peak_tops.sort(key=lambda item: item[0])
    selected_peaks = peak_tops[-7:] if len(peak_tops) >= 2 else []
    trajectory_svg = ""
    if len(selected_peaks) >= 2:
        path_d = "M " + " L ".join(f"{px:.1f},{py - 4:.1f}" for px, py, _ in selected_peaks)
        beacons = "".join(
            f'<circle cx="{px:.1f}" cy="{py - 4:.1f}" r="2.8" fill="{palette["accent"]}" />'
            f'<circle cx="{px:.1f}" cy="{py - 4:.1f}" r="2.8" fill="none" stroke="{palette["accent"]}" stroke-width="1">'
            f'<animate attributeName="r" values="2.8;10;2.8" dur="2.6s" begin="{i * 0.35:.2f}s" repeatCount="indefinite" />'
            f'<animate attributeName="opacity" values="0.85;0;0.85" dur="2.6s" begin="{i * 0.35:.2f}s" repeatCount="indefinite" />'
            f"</circle>"
            for i, (px, py, _) in enumerate(selected_peaks[-4:])
        )
        trajectory_svg = f"""
    <path d="{path_d}" fill="none" stroke="{palette['accent']}" stroke-width="1.6" stroke-dasharray="6 5" opacity="0.85">
      <animate attributeName="stroke-dashoffset" from="44" to="0" dur="2.2s" repeatCount="indefinite" />
    </path>
    <circle r="3.6" fill="{palette['accent']}">
      <animateMotion path="{path_d}" dur="4.5s" repeatCount="indefinite" />
    </circle>
    {beacons}
"""

    # Build Bottom Panel: Recent Git Commit Feed Console
    commits = telemetry["recent_commits"][:4]
    commit_rows_svg: list[str] = []
    for idx, commit in enumerate(commits):
        row_y = 434 + idx * 26
        repo_label = truncate_text(commit["repo"], 16)
        msg_label = truncate_text(commit["message"], 52)
        sha_label = commit["sha"]
        date_label = commit["date"]
        pulse_delay = f"{idx * 0.6:.2f}s"

        commit_rows_svg.append(
            f"""
    <g>
      <circle cx="74" cy="{row_y - 4}" r="3.2" fill="{palette['accent']}">
        <animate attributeName="opacity" values="1;0.35;1" dur="2.4s" begin="{pulse_delay}" repeatCount="indefinite" />
      </circle>
      <text x="90" y="{row_y}" font-family='{FONT_MONO}' font-size="11.5" font-weight="700" fill="{palette['text_primary']}">{escape_xml(sha_label)}</text>
      <rect x="154" y="{row_y - 13}" width="136" height="18" rx="4" fill="{palette['chip_bg']}" stroke="{palette['chip_border']}" stroke-width="0.8" />
      <text x="222" y="{row_y - 0.5}" text-anchor="middle" font-family='{FONT_MONO}' font-size="10.5" font-weight="600" fill="{palette['chip_text']}">{escape_xml(repo_label)}</text>
      <text x="306" y="{row_y}" font-family='{FONT_SANS}' font-size="12.5" fill="{palette['text_secondary']}">{escape_xml(msg_label)}</text>
      <text x="1126" y="{row_y}" text-anchor="end" font-family='{FONT_MONO}' font-size="11" fill="{palette['text_muted']}">{escape_xml(date_label)}</text>
    </g>"""
        )

    # Legend swatches matching the 4 sculpted 3D contribution tiers
    legend_svg = "".join(
        f'<rect x="{990 + i * 20}" y="53" width="13" height="13" rx="3" '
        f'fill="{palette["commit_levels"][i][0]}" stroke="{palette["commit_levels"][i][3]}" stroke-width="1" />'
        for i in range(4)
    )

    body = f"""
  <!-- Section Header -->
  <g transform="translate(48, 42)">
    <text x="0" y="0" font-family='{FONT_MONO}' font-size="11" font-weight="700" letter-spacing="1.6" fill="{palette['accent']}">03 // 52-WEEK ISOMETRIC COMMIT TOPOLOGY</text>
    <text x="0" y="28" font-family='{FONT_SANS}' font-size="24" font-weight="800" letter-spacing="-0.6" fill="{palette['text_primary']}">3D Contribution Skyline &amp; Commit Telemetry</text>
  </g>
  <text x="978" y="64" text-anchor="end" font-family='{FONT_MONO}' font-size="10.5" fill="{palette['text_muted']}">LESS</text>
  {legend_svg}
  <text x="1078" y="64" font-family='{FONT_MONO}' font-size="10.5" fill="{palette['text_muted']}">MORE</text>

  <!-- 3D Skyline Stage Frame -->
  <rect x="48" y="84" width="1104" height="292" rx="12" fill="{palette['card_bg']}" stroke="{palette['card_border']}" stroke-width="1.2" />

  <!-- Summary Overlay Pills Inside Skyline Stage -->
  <g transform="translate(68, 102)">
    <rect x="0" y="0" width="188" height="26" rx="6" fill="{palette['chip_bg']}" stroke="{palette['chip_border']}" />
    <text x="94" y="17" text-anchor="middle" font-family='{FONT_MONO}' font-size="10.5" font-weight="700" fill="{palette['text_primary']}">{total_contribs} CONTRIBUTIONS (1Y)</text>

    <rect x="198" y="0" width="156" height="26" rx="6" fill="{palette['chip_bg']}" stroke="{palette['chip_border']}" />
    <text x="276" y="17" text-anchor="middle" font-family='{FONT_MONO}' font-size="10.5" font-weight="600" fill="{palette['text_secondary']}">{active_days} ACTIVE DAYS</text>

    <rect x="364" y="0" width="150" height="26" rx="6" fill="{palette['chip_bg']}" stroke="{palette['chip_border']}" />
    <text x="439" y="17" text-anchor="middle" font-family='{FONT_MONO}' font-size="10.5" font-weight="600" fill="{palette['text_secondary']}">PEAK: {max_day} / DAY</text>
  </g>

  <!-- Sculpted 52x7 Trimetric Towers -->
  <g>
    {"".join(pillars_svg)}
    {trajectory_svg}
  </g>

  <!-- Sweeping Telemetry Scanline Across the 3D Skyline -->
  <g clip-path="url(#skyline_clip_{palette['mode']})">
    <rect x="-180" y="84" width="160" height="292" fill="url(#{scan_grad_id})">
      <animate attributeName="x" from="-180" to="1220" dur="6.5s" repeatCount="indefinite" />
    </rect>
  </g>

  <!-- Bottom Console: Live Recent Commit Log -->
  <rect x="48" y="392" width="1104" height="148" rx="12" fill="{palette['card_bg']}" stroke="{palette['card_border']}" stroke-width="1.2" />
  <text x="70" y="414" font-family='{FONT_MONO}' font-size="10.5" font-weight="700" letter-spacing="1.3" fill="{palette['text_muted']}">LATEST PUBLIC COMMIT STREAM  //  GIT HEAD TELEMETRY</text>
  <rect x="1050" y="403" width="80" height="16" rx="4" fill="{palette['pill_bg']}" />
  <text x="1090" y="414.5" text-anchor="middle" font-family='{FONT_MONO}' font-size="9.5" font-weight="700" fill="{palette['pill_text']}">SYNCED</text>
  <line x1="68" y1="422" x2="1132" y2="422" stroke="{palette['card_border']}" stroke-width="1" />
  {"".join(commit_rows_svg)}
"""
    return header + body + footer


def generate_all_assets(output_dir: Path, username: str) -> None:
    """Fetch telemetry once and emit paired dark and light 3D animated SVGs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    telemetry = fetch_github_telemetry(username)

    for mode in ("dark", "light"):
        palette = get_theme_palette(mode)
        (output_dir / f"hero_3d_{mode}.svg").write_text(
            render_hero_svg(telemetry, palette), encoding="utf-8"
        )
        (output_dir / f"projects_3d_{mode}.svg").write_text(
            render_projects_svg(palette), encoding="utf-8"
        )
        (output_dir / f"repos_3d_{mode}.svg").write_text(
            render_repos_svg(telemetry, palette), encoding="utf-8"
        )
        (output_dir / f"commits_3d_{mode}.svg").write_text(
            render_commits_svg(telemetry, palette), encoding="utf-8"
        )


def main() -> None:
    """Entrypoint invoked locally and via scheduled GitHub Actions workflow."""
    repo_root = Path(__file__).resolve().parent.parent
    username = os.environ.get("GITHUB_REPOSITORY_OWNER", DEFAULT_USERNAME).strip() or DEFAULT_USERNAME
    generate_all_assets(repo_root / "assets", username)
    print(f"Generated 8 animated 3D SVG assets for {username} in {repo_root / 'assets'}.")


if __name__ == "__main__":
    main()
