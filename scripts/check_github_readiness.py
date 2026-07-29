from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    checks = []
    checks.append(("github_repo_configured", bool(settings.github_repo)))
    checks.append(("github_token_configured", bool(settings.github_token)))
    checks.append(("env_ignored", _gitignore_contains(".env")))
    checks.append(("seed_dir_exists", Path("data/seed_knowledge").exists()))

    if settings.github_repo and settings.github_token:
        checks.append(("github_repo_accessible", _repo_accessible(settings.github_repo, settings.github_token)))

    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'} | {name}")

    if not all(passed for _, passed in checks):
        raise SystemExit(1)


def _gitignore_contains(pattern: str) -> bool:
    gitignore = Path(".gitignore")
    if not gitignore.exists():
        return False
    lines = [line.strip() for line in gitignore.read_text(encoding="utf-8").splitlines()]
    return pattern in lines


def _repo_accessible(repo: str, token: str) -> bool:
    response = httpx.get(
        f"https://api.github.com/repos/{repo}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=20,
    )
    return response.status_code == 200


if __name__ == "__main__":
    main()
