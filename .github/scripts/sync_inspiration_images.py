#!/usr/bin/env python3
import os
import subprocess
import hashlib
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SYNC_FOLDER = Path.home() / "Sync" / "inspiration"
DROPBOX_FOLDER = Path.home() / "Dropbox" / "apps" / "Savee"
REMOTE_HOST = os.getenv("REMOTE_HOST", "192.168.1.152")
REMOTE_USER = os.getenv("REMOTE_USER", "nonlinear")
REMOTE_PATH = "/serve/media/pictures/inspiration"

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
            print(f"❌ Unable to connect to server ({REMOTE_HOST})")
            print(f"\n⚠️  This operation only works from home network!")
            return False
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        print(f"❌ Unable to connect to server ({REMOTE_HOST})")
        print(f"\n⚠️  This operation only works from home network!")
        return False

def count_files(folder):
    """Count files in folder"""
    if not folder.exists():
        return 0
    return sum(1 for item in folder.rglob('*') if item.is_file() and not item.name.startswith('.'))

def get_file_hash(file_path):
    """Calculate MD5 hash of file content"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"❌ Error reading {file_path.name}: {e}")
        return None

def get_remote_files_info():
    """Get list of files in remote server with their hashes (only filenames that might conflict)"""
    print("\n🔍 Scanning remote server for potential conflicts...")

    # First, get list of local files to check
    local_files = set()
    for folder in [SYNC_FOLDER, DROPBOX_FOLDER]:
        if folder.exists():
            for f in folder.rglob('*'):
                if f.is_file() and not f.name.startswith('.'):
                    local_files.add(f.name)

    if not local_files:
        return {}

    print(f"   Checking {len(local_files)} local files against server...")

    # Build command to check only specific files
    remote_files = {}

    # Check files in batches to avoid command line too long
    local_list = list(local_files)
    batch_size = 50

    for i in range(0, len(local_list), batch_size):
        batch = local_list[i:i+batch_size]

        # Build find command to check only these specific filenames
        find_expr = " -o ".join([f'-name "{fn}"' for fn in batch])

        ssh_cmd = [
            'ssh',
            f'{REMOTE_USER}@{REMOTE_HOST}',
            f'cd {REMOTE_PATH} 2>/dev/null && find . -type f \\( {find_expr} \\) -exec md5sum {{}} \\; 2>/dev/null'
        ]

        try:
            result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and result.stdout:
                # Parse output: "hash  ./filename"
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        hash_value, filepath = parts
                        filename = Path(filepath.lstrip('./')).name
                        remote_files[filename] = hash_value

        except subprocess.TimeoutExpired:
            print(f"   ⚠️  Batch {i//batch_size + 1} timed out, skipping...")
            continue
        except Exception as e:
            print(f"   ⚠️  Error in batch {i//batch_size + 1}: {e}")
            continue

    if remote_files:
        print(f"✅ Found {len(remote_files)} matching files on server")
    else:
        print(f"✅ No conflicts detected - all files are new")

    return remote_files

def resolve_conflicts(source_folder, folder_name, remote_files):
    """Check for conflicts and rename duplicates if needed"""
    print(f"\n🔍 Checking for conflicts in {folder_name}...")

    conflicts_found = 0
    duplicates_found = 0
    renamed_files = []

    if not source_folder.exists():
        return conflicts_found, duplicates_found, renamed_files

    for file_path in source_folder.rglob('*'):
        if not file_path.is_file() or file_path.name.startswith('.'):
            continue

        filename = file_path.name

        # Check if file exists on server
        if filename in remote_files:
            # Calculate local file hash
            local_hash = get_file_hash(file_path)
            remote_hash = remote_files[filename]

            if local_hash == remote_hash:
                # Same file - will be ignored by rsync
                print(f"   ⏭️  Duplicate: {filename} (skipping)")
                duplicates_found += 1
            else:
                # Different file with same name - CONFLICT!
                print(f"   ⚠️  Conflict: {filename}")
                conflicts_found += 1

                # Rename local file to keep both
                base = file_path.stem
                ext = file_path.suffix
                counter = 1

                while True:
                    new_name = f"{base}_v{counter}{ext}"
                    new_path = file_path.parent / new_name

                    if not new_path.exists() and new_name not in remote_files:
                        file_path.rename(new_path)
                        print(f"      → Renamed to: {new_name}")
                        renamed_files.append((filename, new_name))
                        break
                    counter += 1

    return conflicts_found, duplicates_found, renamed_files

def sync_to_nas(source_folder, folder_name):
    """Sync files to NAS"""
    print(f"\n📤 Syncing {source_folder} to {REMOTE_USER}@{REMOTE_HOST}:{REMOTE_PATH}\n")

    rsync_cmd = [
        'rsync',
        '-rltvz',
        '--progress',
        '--ignore-existing',
        '--no-perms',
        '--no-owner',
        '--no-group',
        f'{source_folder}/',
        f'{REMOTE_USER}@{REMOTE_HOST}:{REMOTE_PATH}/'
    ]

    try:
        result = subprocess.run(rsync_cmd, capture_output=False)

        if result.returncode in [0, 23]:
            print(f"\n✅ {folder_name} sync completed successfully!")
            return True
        else:
            print(f"\n❌ Error during {folder_name} sync: code {result.returncode}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error during {folder_name} sync: {e}")
        return False

def clean_folder(folder, folder_name):
    """Remove all files from folder"""
    print(f"\n🧹 Cleaning local folder: {folder}")

    if not folder.exists():
        print(f"⚠️  {folder_name} folder doesn't exist.")
        return

    deleted_count = 0
    for item in folder.rglob('*'):
        if item.is_file() and not item.name.startswith('.'):
            try:
                item.unlink()
                print(f"   🗑️  Removed: {item.name}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Error removing {item.name}: {e}")

    print(f"✅ {folder_name} cleanup complete! {deleted_count} file(s) removed.")

def main():
    print("🎨 Manage Inspiration Files - Complete Workflow\n")
    print("=" * 60)

    # Count files
    sync_count = count_files(SYNC_FOLDER)
    dropbox_count = count_files(DROPBOX_FOLDER)

    print(f"\n📊 File count:")
    print(f"   ~/Sync/inspiration: {sync_count} files")
    print(f"   ~/Dropbox/apps/Savee: {dropbox_count} files")

    if sync_count == 0 and dropbox_count == 0:
        print("\n⚠️  No files found in either folder.")
        return

    # STEP 1: Check network
    print("\n" + "=" * 60)
    print("\n📡 STEP 1: Checking server connection\n")

    if not check_home_network():
        print("\n⏹️  Cannot sync now.")
        return

    # STEP 1.5: Get remote files info for conflict detection
    remote_files = get_remote_files_info()

    # STEP 2: Check conflicts in Sync/inspiration
    all_conflicts = []
    all_duplicates = []
    all_renamed = []

    if sync_count > 0:
        print("\n" + "=" * 60)
        print("\n🔎 STEP 2: Checking conflicts in ~/Sync/inspiration\n")

        conflicts, duplicates, renamed = resolve_conflicts(SYNC_FOLDER, "Sync/inspiration", remote_files)
        all_conflicts.append(conflicts)
        all_duplicates.append(duplicates)
        all_renamed.extend(renamed)

        if conflicts > 0:
            print(f"\n✅ Resolved {conflicts} conflict(s)")
        if duplicates > 0:
            print(f"\n✅ Found {duplicates} duplicate(s) (will be skipped)")

    # STEP 3: Check conflicts in Dropbox/apps/Savee
    if dropbox_count > 0:
        print("\n" + "=" * 60)
        print("\n🔎 STEP 3: Checking conflicts in ~/Dropbox/apps/Savee\n")

        conflicts, duplicates, renamed = resolve_conflicts(DROPBOX_FOLDER, "Dropbox/Savee", remote_files)
        all_conflicts.append(conflicts)
        all_duplicates.append(duplicates)
        all_renamed.extend(renamed)

        if conflicts > 0:
            print(f"\n✅ Resolved {conflicts} conflict(s)")
        if duplicates > 0:
            print(f"\n✅ Found {duplicates} duplicate(s) (will be skipped)")

    # Summary
    total_conflicts = sum(all_conflicts)
    total_duplicates = sum(all_duplicates)

    if total_conflicts > 0 or total_duplicates > 0:
        print("\n" + "=" * 60)
        print("\n📊 Conflict Resolution Summary:")
        print(f"   🔄 Files renamed: {total_conflicts}")
        print(f"   ⏭️  Duplicates to skip: {total_duplicates}")

        if all_renamed:
            print("\n   Renamed files:")
            for old, new in all_renamed:
                print(f"      • {old} → {new}")

    # STEP 4: Sync Sync/inspiration
    if sync_count > 0:
        print("\n" + "=" * 60)
        print("\n🌐 STEP 4: Syncing ~/Sync/inspiration\n")

        if not sync_to_nas(SYNC_FOLDER, "Sync/inspiration"):
            print("\n❌ Sync failed.")
            return

    # STEP 5: Sync Dropbox/apps/Savee
    if dropbox_count > 0:
        print("\n" + "=" * 60)
        print("\n🌐 STEP 5: Syncing ~/Dropbox/apps/Savee\n")

        if not sync_to_nas(DROPBOX_FOLDER, "Dropbox/Savee"):
            print("\n❌ Sync failed.")
            return

    # STEP 6: Confirm cleanup
    print("\n" + "=" * 60)
    response = input("\n⏸️  Sync complete!\n   Clean up local folders? (y/N): ").lower().strip()

    if response in ['s', 'sim', 'y', 'yes']:
        if sync_count > 0:
            clean_folder(SYNC_FOLDER, "Sync/inspiration")
        if dropbox_count > 0:
            clean_folder(DROPBOX_FOLDER, "Dropbox/Savee")
    else:
        print("⏭️  Skipping cleanup. Files kept locally.")

    print("\n" + "=" * 60)
    print("✨ Process complete!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
