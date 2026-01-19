from send2trash import send2trash
#!/usr/bin/env python3
import os
import re
import shutil
import subprocess
import webbrowser
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
DOWNLOADS_FOLDER = Path.home() / "Downloads"
SYNC_FOLDER = Path.home() / "Sync" / "comics"
REMOTE_HOST = os.getenv("REMOTE_HOST")
REMOTE_USER = os.getenv("REMOTE_USER")
REMOTE_PATH = os.getenv("REMOTE_PATH")
KOMGA_URL = os.getenv("KOMGA_URL")

def check_home_network():
    """Check if connected to home network"""
    try:
        result = subprocess.run(
            ['ping', '-c', '1', '-W', '1', REMOTE_HOST],
            capture_output=True,
            timeout=2
        )
        if result.returncode == 0:
            return True
        else:
            print(f"❌ Unable to connect to NAS ({REMOTE_HOST})")
            print(f"\n⚠️  This operation only works from home network!")
            return False
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        print(f"❌ Unable to connect to NAS ({REMOTE_HOST})")
        print(f"\n⚠️  This operation only works from home network!")
        return False

def prepare_comics():
    """Move comics from Downloads to Sync/comics organized in folders"""
    print("\n📖 STEP 1: Preparing comics from Downloads\n")

    SYNC_FOLDER.mkdir(parents=True, exist_ok=True)

    processed_count = 0

    # Search recursively for .cbr and .cbz files
    for file_path in DOWNLOADS_FOLDER.rglob('*'):
        if not file_path.is_file():
            continue

        filename = file_path.name

        if not filename.lower().endswith(('.cbr', '.cbz')):
            continue

        # Check if still downloading (Safari)
        download_file = file_path.parent / f"{filename}.download"
        if download_file.exists():
            print(f"⏳ Skipping (still downloading): '{filename}'")
            continue

        # Check if file is in use
        try:
            with open(file_path, 'rb') as f:
                pass
        except (PermissionError, IOError):
            print(f"🔒 Skipping (file in use): '{filename}'")
            continue

        print(f"\n📖 Processing: '{filename}'")

        # Remove " (*)" from name (mas mantém número do capítulo no arquivo)
        new_filename = re.sub(r'\s*\(.*?\)', '', filename)
        # Remove " GetComics.INFO" from name
        new_filename = re.sub(r'\s+GetComics\.INFO', '', new_filename, flags=re.IGNORECASE)

        # Remove extensão para manipular o nome base
        name_wo_ext = re.sub(r'\.[^.]+$', '', new_filename)
        # Remove sufixos como ' v01', ' v1', ' v02' do final do nome base
        base_name = re.sub(r'\s+v\d{1,2}$', '', name_wo_ext, flags=re.IGNORECASE)
        # Remove número do capítulo do final do nome base (ex: ' 014', ' 13')
        base_name = re.sub(r'\s+\d{1,4}$', '', base_name)

        if base_name:
            folder_path = SYNC_FOLDER / base_name.strip()

            if folder_path.exists() and not folder_path.is_dir():
                print(f"❌ Cannot create folder '{folder_path}'. Skipping.")
                continue

            folder_path.mkdir(exist_ok=True)
            dest_path = folder_path / new_filename

            if dest_path.exists():
                print(f"⚠️  File '{dest_path}' already exists. Skipping.")
            else:
                try:
                    shutil.move(str(file_path), str(dest_path))
                    print(f"✅ Moved: '{filename}' → '{dest_path}'")
                    if filename != new_filename:
                        print(f"   Renamed to: '{new_filename}'")
                    processed_count += 1
                except Exception as e:
                    print(f"❌ Error moving '{filename}': {e}")
        else:
            print(f"❌ File '{filename}' doesn't match expected pattern.")

    # Clean empty folders
    print("\n🗑️  Cleaning empty folders in Downloads...")
    for folder in sorted(DOWNLOADS_FOLDER.rglob('*'), reverse=True):
        if folder.is_dir() and folder != DOWNLOADS_FOLDER:
            try:
                folder.rmdir()
                print(f"🧹 Removed empty folder: '{folder.relative_to(DOWNLOADS_FOLDER)}'")
            except OSError:
                pass

    return processed_count

def sync_to_nas():
    """Sync comics to NAS"""
    print(f"\n📤 Syncing {SYNC_FOLDER} to {REMOTE_USER}@{REMOTE_HOST}:{REMOTE_PATH}\n")

    rsync_cmd = [
        'rsync',
        '-rltvz',
        '--progress',
        '--ignore-existing',
        '--no-perms',
        '--no-owner',
        '--no-group',
        '--partial',
        '--inplace',
        f'{SYNC_FOLDER}/',
        f'{REMOTE_USER}@{REMOTE_HOST}:{REMOTE_PATH}/'
    ]

    try:
        result = subprocess.run(rsync_cmd, capture_output=False)

        if result.returncode in [0, 23]:
            print("\n✅ Sync completed successfully!")
            return True
        else:
            print(f"\n❌ Error during sync: code {result.returncode}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error during sync: {e}")
        return False

def clean_sync_folder():
    """Remove all files from Sync/comics"""
    print(f"\n🧹 Cleaning local folder: {SYNC_FOLDER}")

    if not SYNC_FOLDER.exists():
        print("⚠️  Folder doesn't exist.")
        return

    deleted_count = 0
    for item in SYNC_FOLDER.iterdir():
        try:
            if item.is_dir():
                shutil.rmtree(item)
                print(f"   🗑️  Removed folder: {item.name}")
            else:
                send2trash(str(item))  # New: moves to Trash/Recycle Bin
                print(f"   🗑️  Moved to Trash: {item.name}")
            deleted_count += 1
        except Exception as e:
            print(f"❌ Error removing {item.name}: {e}")

    print(f"✅ Cleanup complete! {deleted_count} item(s) removed.")

def main():
    print("🚀 Manage Comics - Complete Workflow\n")
    print("=" * 60)

    # STEP 1: Prepare comics
    processed = prepare_comics()

    if processed == 0:
        print("\n⚠️  No comics found in Downloads.")
        return

    print(f"\n✅ {processed} comic(s) processed!")

    # PAUSE 1: Check organization
    print("\n" + "=" * 60)
    print("📂 Opening Finder to check organization...")
    subprocess.run(['open', str(SYNC_FOLDER)])

    response = input("\n⏸️  Check if everything looks good in ~/Sync/comics/\n   Continue to sync with NAS? (y/N): ").lower().strip()

    if response not in ['s', 'sim', 'y', 'yes']:
        print("⏹️  Operation cancelled. Files remain in ~/Sync/comics/")
        return

    # STEP 2: Check network
    print("\n" + "=" * 60)
    print("\n📡 STEP 2: Checking NAS connection\n")

    if not check_home_network():
        print("\n⏹️  Cannot sync now.")
        print("   Files remain in ~/Sync/comics/")
        return

    # STEP 3: Sync
    print("\n" + "=" * 60)
    print("\n🌐 STEP 3: Syncing with NAS\n")

    if not sync_to_nas():
        print("\n❌ Sync failed.")
        print("   Files remain in ~/Sync/comics/")
        return

    # PAUSE 2: Confirm cleanup
    print("\n" + "=" * 60)
    response = input("\n⏸️  Sync complete!\n   Clean up ~/Sync/comics/? (y/N): ").lower().strip()

    if response in ['s', 'sim', 'y', 'yes']:
        clean_sync_folder()
    else:
        print("⏭️  Skipping cleanup. Files kept in ~/Sync/comics/")

    # STEP 4: Open Komga
    print("\n" + "=" * 60)
    print("\n📚 STEP 4: Opening Komga\n")
    print("   You'll need to manually scan the library.")
    webbrowser.open(KOMGA_URL)

    print("\n" + "=" * 60)
    print("✨ Process complete!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
