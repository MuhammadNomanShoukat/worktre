import requests
import os
import time
import subprocess
import tempfile

GITHUB_REPO = "MuhammadNomanShoukat/worktre"
APP_NAME = "WorkTre"

update_status = "Checking for updates..."

def get_current_version():
    version_file = os.path.join(os.path.dirname(__file__), "version.txt")
    if os.path.exists(version_file):
        with open(version_file) as f:
            return f.read().strip()
    return "0.0.0"

def set_current_version(version):
    version_file = os.path.join(os.path.dirname(__file__), "version.txt")
    with open(version_file, "w") as f:
        f.write(version.strip())

def check_for_update():
    global update_status
    try:
        current_version = get_current_version()

        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        response = requests.get(url)
        response.raise_for_status()
        release = response.json()

        latest_version = release.get("tag_name", "").strip()
        if not latest_version:
            update_status = "Failed to get latest version info."
            return None

        if latest_version != current_version:
            update_status = f"New version available: {latest_version}"
            print(update_status)
            asset = next((a for a in release.get("assets", []) if a["name"].endswith(".exe")), None)
            if asset:
                return {
                    "version": latest_version,
                    "download_url": asset["browser_download_url"]
                }
            else:
                update_status = "No .exe installer found."
                return None
        else:
            update_status = "Already up to date"
            print(update_status)
            return None

    except Exception as e:
        update_status = f"Update check failed: {e}"
        print(update_status)
        return None

def download_and_install(download_url, latest_version):
    global update_status
    try:
        update_status = "Downloading update..."
        print(update_status)

        temp_dir = tempfile.gettempdir()
        installer_path = os.path.join(temp_dir, "update_installer.exe")

        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(installer_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        update_status = "Installing update..."
        print(update_status)

        # ✅ Do NOT update version.txt now
        # We'll let the new version package overwrite it

        subprocess.Popen([installer_path], shell=True)
        time.sleep(1)
        os._exit(0)

    except Exception as e:
        update_status = f"Download failed: {e}"
        print(update_status)
