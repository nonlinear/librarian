import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base projects from .env
projects = [
    Path.home() / p.strip()
    for p in os.getenv("SYNC_PROJECTS", "").split(",")
    if p.strip()
]

def get_latest_folder(folders):
    """Find folder with most recently modified file"""
    latest_time = 0
    latest_folder = None
    for folder in folders:
        if not folder.exists():
            continue
        for root, _, files in os.walk(folder):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    mtime = os.path.getmtime(fp)
                    if mtime > latest_time:
                        latest_time = mtime
                        latest_folder = folder
                except:
                    continue
    return latest_folder

def sync_folders(source, targets, exclude=None):
    """Sync source folder to all targets"""
    for target in targets:
        if target == source:
            continue

        cmd = ["rsync", "-av", "--delete"]
        if exclude:
            for exc in exclude:
                cmd.extend(["--exclude", exc])
        cmd.extend([f"{source}/", f"{target}/"])

        subprocess.run(cmd)

if __name__ == "__main__":
    # Sync .github folders (excluding copilot-instructions.md)
    github_folders = [p / ".github" for p in projects]
    latest_github = get_latest_folder(github_folders)
    if latest_github:
        print(f"📁 Syncing .github from: {latest_github.parent.name}")
        sync_folders(latest_github, github_folders, exclude=["copilot-instructions.md"])
        print("✅ .github sync complete.\n")

    # Sync .vscode folders (excluding extensions)
    vscode_folders = [p / ".vscode" for p in projects]
    latest_vscode = get_latest_folder(vscode_folders)
    if latest_vscode:
        print(f"📁 Syncing .vscode from: {latest_vscode.parent.name}")
        sync_folders(latest_vscode, vscode_folders, exclude=["extensions"])
        print("✅ .vscode sync complete.\n")

    # Sync .env files (contains sensitive configuration)
    env_files = [p / ".env" for p in projects]
    latest_env = get_latest_folder([f.parent for f in env_files if f.exists()])
    if latest_env:
        latest_env_file = latest_env / ".env"
        if latest_env_file.exists():
            print(f"📁 Syncing .env from: {latest_env.name}")
            for target_project in projects:
                if target_project != latest_env:
                    target_env = target_project / ".env"
                    subprocess.run(["rsync", "-av", str(latest_env_file), str(target_env)])
            print("✅ .env sync complete.\n")

    print("✨ All syncs complete!")
