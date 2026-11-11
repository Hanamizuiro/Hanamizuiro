"""Generate the profile cards using public GitHub data."""

import json
import os
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = "Hanamizuiro"
ASSETS = Path(__file__).resolve().parents[1] / "assets"
THEMES = {
    "dark": ("#141722", "#1d2130", "#adbacd", "#ffe08a", "#a8d3ff"),
    "light": ("#fffdf6", "#f4edda", "#505a6b", "#795600", "#174d91"),
}


def github_profile():
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Hanamizuiro-profile"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com/users/{USERNAME}", headers=headers)
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def braille_art():
    # Unicode Braille orders dots by column, with the fourth row last.
    dots = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (0, 3), (1, 3))
    lines = (ASSETS / "profile-art.txt").read_text(encoding="utf-8").splitlines()
    for row, line in enumerate(lines):
        for column, char in enumerate(line):
            pattern = ord(char) - 0x2800
            if not 0 <= pattern <= 255:
                raise ValueError(f"Expected a Braille character on line {row + 1}")
            for bit, (dx, dy) in enumerate(dots):
                if pattern & (1 << bit):
                    x = 28 + column * 7 + dx * 3
                    y = 129 + row * 16 + dy * 3
                    yield f'<circle cx="{x}" cy="{y}" r="1.35"/>'


def render(theme, profile, uptime_days):
    bg, bar, muted, heading, value = theme
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="520" viewBox="0 0 1100 520" role="img" aria-labelledby="title">',
        '<title id="title">Robin Navarro’s GitHub profile</title>',
        f'<rect width="1100" height="520" rx="14" fill="{bg}"/>',
        f'<path d="M14 0h1072a14 14 0 0 1 14 14v26H0V14A14 14 0 0 1 14 0Z" fill="{bar}"/>',
        f'<path d="M405 64v424" stroke="{muted}" stroke-opacity=".3"/>',
    ]
    for x, color in zip((22, 39, 56), (heading, muted, value)):
        parts.append(f'<circle cx="{x}" cy="20" r="4" fill="{color}"/>')
    parts.extend([f'<g fill="{value}" aria-hidden="true">', *braille_art(), '</g>'])
    parts.append('<g font-family="Consolas, Liberation Mono, monospace" font-size="16">')

    for y, title in ((76, "robin@navarro"), (372, "Contact"), (451, "GitHub Stats")):
        parts.append(f'<text x="430" y="{y}" font-size="20" font-weight="bold" fill="{heading}">{title}</text>')
        line_start = 430 + len(title) * 13 + 14
        parts.append(f'<path d="M{line_start} {y - 6}H1072" stroke="{muted}" stroke-opacity=".45" stroke-dasharray="4 3"/>')

    rows = (
        (105, "OS", "Windows 11, Arc Linux"),
        (128, "Uptime", f"{uptime_days:,} days on GitHub"),
        (151, "Host", "B550M Pro4"),
        (174, "Kernel", "Windows NT 10.0.26200"),
        (197, "IDE", "VSCode, Neovim"),
        (232, "Languages.Programming", "Python, TypeScript, JavaScript, SQL"),
        (255, "Languages.Web", "HTML, CSS, Tailwind, React, TanStack Starter"),
        (278, "Languages.Data", "NumPy, Pandas, Matplotlib, Seaborn, LaTeX"),
        (301, "Languages.Real", "English, Filipino"),
        (331, "Education", "Bachelor of Science in Mathematics"),
        (351, "", "with Specialization in Computer Science"),
        (399, "Email.Personal", "navarrorobin23@gmail.com"),
        (422, "LinkedIn", "robin-christian-navarro"),
    )
    for y, label, content in rows:
        if label:
            parts.append(f'<text x="430" y="{y}" fill="{heading}">{label}:</text>')
        parts.append(f'<text x="662" y="{y}" fill="{value}">{escape(content)}</text>')

    for x, label, number in (
        (430, "Public repos", profile["public_repos"]),
        (662, "Followers", profile["followers"]),
    ):
        parts.append(
            f'<text x="{x}" y="488" fill="{heading}">{label}: '
            f'<tspan fill="{value}">{number:,}</tspan></text>'
        )
    return "\n".join([*parts, "</g>", "</svg>", ""])


if __name__ == "__main__":
    profile = github_profile()
    joined = datetime.fromisoformat(profile["created_at"])
    uptime_days = (datetime.now(UTC).date() - joined.date()).days
    for name, theme in THEMES.items():
        (ASSETS / f"profile-{name}.svg").write_text(
            render(theme, profile, uptime_days), encoding="utf-8", newline="\n"
        )
