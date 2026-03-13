from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
import json

REPO_NAME = "tmnm-newsroom"
GOOGLE_DRIVE_ROOT_NAME = "TMNM"

DESKS = [
    "Politic_Al",
    "RetiredTrader",
    "BallisticBen",
    "AshaObserves",
    "ConspiracyCousin",
    "ThePeopleSay",
]

REPO_FOLDERS = [
    "characters",
    "prompts",
    "branding",
    "automation",
    "obs",
    "workflows",
]

GOOGLE_DRIVE_FOLDERS = [
    "Avatars",
    "Studios",
    "Graphics",
    "Daily Output",
    "Ready To Post",
]

@dataclass(frozen=True)
class Config:
    base_dir: Path
    drive_base_dir: Path
    date_str: str
    create_daily_output: bool = True

def ensure_dirs(paths: Iterable[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
        print(f"[OK] {path}")

def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        print(f"[SKIP] File already exists: {path}")
        return
    path.write_text(content, encoding="utf-8")
    print(f"[NEW] {path}")

def build_repo_structure(repo_root: Path) -> None:
    ensure_dirs(repo_root / folder for folder in REPO_FOLDERS)
    # Useful subfolders
    ensure_dirs(
        [
            repo_root / "characters" / "core",
            repo_root / "characters" / "satire",
            repo_root / "prompts" / "articles",
            repo_root / "prompts" / "graphics",
            repo_root / "prompts" / "screens",
            repo_root / "prompts" / "social",
            repo_root / "branding" / "logos",
            repo_root / "branding" / "guidelines",
            repo_root / "branding" / "overlays",
            repo_root / "automation" / "scripts",
            repo_root / "automation" / "templates",
            repo_root / "obs" / "scenes",
            repo_root / "obs" / "overlays",
            repo_root / "obs" / "transitions",
            repo_root / "workflows" / "daily",
            repo_root / "workflows" / "publishing",
            repo_root / "workflows" / "desks",
        ]
    )

def build_drive_structure(drive_root: Path, date_str: str, create_daily_output: bool) -> None:
    ensure_dirs(drive_root / folder for folder in GOOGLE_DRIVE_FOLDERS)
    if create_daily_output:
        ensure_dirs(
            drive_root / "Daily Output" / date_str / desk
            for desk in DESKS
        )

def write_sample_files(repo_root: Path) -> None:
    write_text_file(
        repo_root / ".gitignore",
        """__pycache__/
*.pyc
.env
.vscode/
.DS_Store
Thumbs.db
""",
    )
    write_text_file(
        repo_root / "characters" / "core" / "Politic_Al.json",
        json.dumps(
            {
                "name": "Politic_Al",
                "role": "Editor-in-Chief",
                "desk": "Politics",
                "voice": "Sophisticated, analytical, fact-based",
                "signature_phrase": "Let’s look at the facts, shall we?",
                "hashtags": ["#Politic_Al", "#TruthMattersNewsMedia", "#TMNM"],
            },
            indent=2,
        )
        + "\n",
    )
    write_text_file(
        repo_root / "characters" / "core" / "RetiredTrader.json",
        json.dumps(
            {
                "name": "RetiredTrader",
                "role": "Senior Market Analyst",
                "desk": "Markets",
                "voice": "Polished, wise, simple explanations",
                "mandatory_disclaimer": "This content is not financial or investment advice.",
                "hashtags": ["#RetiredTrader", "#TruthMattersNewsMedia", "#TMNM"],
            },
            indent=2,
        )
        + "\n",
    )
    write_text_file(
        repo_root / "prompts" / "articles" / "political_article_template.md",
        """# Headline

By #Politic_Al

#Politic_Al

[Political analysis body]

🔹

[Supporting facts / implications]

🔹

#TruthMattersNewsMedia #TMNM
""",
    )
    write_text_file(
        repo_root / "prompts" / "articles" / "market_article_template.md",
        """# Headline

By #RetiredTrader

## Pro Report
[Professional market analysis]

◇◇◇

## Making Markets Simple
[Plain-English explanation]

Disclaimer: This content is not financial or investment advice.

#TruthMattersNewsMedia #TMNM #RetiredTrader
""",
    )
    write_text_file(
        repo_root / "workflows" / "daily" / "daily_newsroom_run.md",
        """# Daily Newsroom Run

1. Review top stories for politics, markets, conflict, and society.
2. Generate article drafts by desk.
3. Generate supporting graphics.
4. Save all output into Google Drive:
   - TMNM / Daily Output / YYYY-MM-DD / DeskName
5. Review and move approved files into:
   - TMNM / Ready To Post
""",
    )
    write_text_file(
        repo_root / "automation" / "templates" / "project_config.json",
        json.dumps(
            {
                "repo_name": REPO_NAME,
                "drive_root_name": GOOGLE_DRIVE_ROOT_NAME,
                "desks": DESKS,
                "default_graphic_size": "1920x1080",
                "master_studio": "TMNM_Studio_Master_v1",
            },
            indent=2,
        )
        + "\n",
    )

def create_project(config: Config) -> None:
    repo_root = config.base_dir / REPO_NAME
    drive_root = config.drive_base_dir / GOOGLE_DRIVE_ROOT_NAME
    print("\n=== Creating TMNM repo structure ===")
    build_repo_structure(repo_root)
    print("\n=== Creating TMNM Google Drive mirror structure ===")
    build_drive_structure(drive_root, config.date_str, config.create_daily_output)
    print("\n=== Writing sample files ===")
    write_sample_files(repo_root)
    print("\n=== Done ===")
    print(f"Repo root: {repo_root}")
    print(f"Drive root: {drive_root}")

def main() -> None:
    # Change these paths to suit your machine.
    # Example Windows paths:
    # base_dir = Path(r"C:\Users\Alan\Documents")
    # drive_base_dir = Path(r"C:\Users\Alan\Google Drive")
    # Always use the workspace root (two levels up from this script)
    script_dir = Path(__file__).resolve().parent
    workspace_root = script_dir.parent.parent
    base_dir = workspace_root
    drive_base_dir = workspace_root
    today = datetime.now().strftime("%Y-%m-%d")
    config = Config(
        base_dir=base_dir,
        drive_base_dir=drive_base_dir,
        date_str=today,
        create_daily_output=True,
    )
    create_project(config)

if __name__ == "__main__":
    main()
