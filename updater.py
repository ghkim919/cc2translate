"""자동 업데이트 모듈 - GitHub에서 최신 버전 확인 및 업데이트 실행"""

import json
import os
import subprocess
import sys
import threading
import urllib.request
import urllib.error

GITHUB_REPO = "ghkim919/cc2translate"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "cc2translate")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


def _load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def get_current_version():
    """번들된 version.txt에서 현재 커밋 해시를 읽는다."""
    # PyInstaller 번들 내부 경로
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))

    version_file = os.path.join(base, "version.txt")
    try:
        with open(version_file, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def get_remote_version():
    """GitHub API로 master 브랜치의 최신 커밋 해시를 조회한다."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/master"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data["sha"]
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, OSError):
        return None


def check_for_update():
    """업데이트 여부를 확인한다.

    Returns:
        (has_update: bool, remote_sha: str | None, error: str | None)
    """
    current = get_current_version()
    if not current:
        return False, None, "현재 버전 정보를 찾을 수 없습니다"

    remote = get_remote_version()
    if not remote:
        return False, None, None  # 네트워크 오류는 조용히 무시

    if current == remote or remote.startswith(current) or current.startswith(remote):
        return False, remote, None

    # 건너뛴 버전 확인
    config = _load_config()
    if config.get("skipped_version") == remote:
        return False, remote, None

    return True, remote, None


def skip_version(sha):
    """특정 버전을 건너뛰기로 설정한다."""
    config = _load_config()
    config["skipped_version"] = sha
    _save_config(config)


def _get_repo_path():
    """소스 repo 경로를 반환한다. 없으면 자동 clone한다."""
    config = _load_config()
    repo_path = config.get("repo_path")

    if repo_path and os.path.isdir(os.path.join(repo_path, ".git")):
        return repo_path

    # 기본 경로에 clone
    default_repo = os.path.join(CONFIG_DIR, "repo")
    if os.path.isdir(os.path.join(default_repo, ".git")):
        return default_repo

    os.makedirs(CONFIG_DIR, exist_ok=True)
    subprocess.run(
        ["git", "clone", f"https://github.com/{GITHUB_REPO}.git", default_repo],
        check=True,
        capture_output=True,
    )
    config["repo_path"] = default_repo
    _save_config(config)
    return default_repo


def run_update(on_progress=None, on_done=None, on_error=None):
    """백그라운드 스레드에서 git pull + install.sh를 실행한다."""

    def _worker():
        try:
            repo_path = _get_repo_path()

            if on_progress:
                on_progress("소스 코드 업데이트 중...")
            subprocess.run(
                ["git", "pull", "origin", "master"],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )

            if on_progress:
                on_progress("빌드 및 설치 중... (1-2분 소요)")
            install_script = os.path.join(repo_path, "install.sh")
            subprocess.run(
                ["bash", install_script],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )

            if on_done:
                on_done()
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if e.stderr else str(e)
            if on_error:
                on_error(f"업데이트 실패: {stderr}")
        except Exception as e:
            if on_error:
                on_error(f"업데이트 실패: {e}")

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread


def get_restart_command():
    """현재 앱을 재시작하는 명령을 반환한다."""
    if getattr(sys, "frozen", False):
        # PyInstaller 번들
        return [sys.executable]
    else:
        return [sys.executable] + sys.argv
