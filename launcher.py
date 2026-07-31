import json
import os
import shutil
import sys
import tempfile
import urllib.request
import zipfile

# CONFIGURAZIONE
GITHUB_USER = "leo6720"
GITHUB_REPO = "cam_motion_designer"
BRANCH = "main"
MAIN_SCRIPT = "main.py"

COMMIT_API = (
    f"https://api.github.com/repos/"
    f"{GITHUB_USER}/{GITHUB_REPO}/commits/{BRANCH}"
)

ZIP_URL = (
    f"https://github.com/"
    f"{GITHUB_USER}/{GITHUB_REPO}"
    f"/archive/refs/heads/{BRANCH}.zip"
)

COMMIT_FILE = ".last_commit"


def get_remote_commit():
    with urllib.request.urlopen(COMMIT_API) as response:
        data = json.loads(response.read().decode())
        return data["sha"]


def get_local_commit():
    if not os.path.exists(COMMIT_FILE):
        return None

    with open(COMMIT_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


def save_local_commit(commit):
    with open(COMMIT_FILE, "w", encoding="utf-8") as f:
        f.write(commit)


def update_project():

    remote_commit = get_remote_commit()
    local_commit = get_local_commit()

    if remote_commit == local_commit:
        print("Nessun aggiornamento.")
        return

    print("Nuovo aggiornamento trovato.")

    with tempfile.TemporaryDirectory() as temp_dir:

        zip_path = os.path.join(temp_dir, "repo.zip")

        urllib.request.urlretrieve(ZIP_URL, zip_path)

        extract_dir = os.path.join(temp_dir, "extract")

        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_dir)

        repo_folder = os.path.join(
            extract_dir,
            f"{GITHUB_REPO}-{BRANCH}"
        )

        current_dir = os.path.dirname(
            os.path.abspath(__file__)
        )

        for item in os.listdir(repo_folder):

            src = os.path.join(repo_folder, item)
            dst = os.path.join(current_dir, item)

            if item in [".git", "launcher.py", COMMIT_FILE]:
                continue

            if os.path.isdir(src):

                if os.path.exists(dst):
                    shutil.rmtree(dst)

                shutil.copytree(src, dst)

            else:
                shutil.copy2(src, dst)

    save_local_commit(remote_commit)

    print("Aggiornamento completato.")


def start_program():

    main_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        MAIN_SCRIPT
    )

    os.execv(
        sys.executable,
        [sys.executable, main_path]
    )


if __name__ == "__main__":

    try:
        update_project()

    except Exception as e:
        print(f"Errore aggiornamento: {e}")

    start_program()
