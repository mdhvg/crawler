import json
import requests
from typing import Union
import os
import subprocess
import glob

RUNS = 100


def load_json(path: str) -> Union[dict, list]:
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def save_json(data: Union[dict, list], path: str) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


INFO = load_json("info.json")
QUEUE = load_json("queue.json")
VISITED = set(load_json("visited.json"))
TREE = load_json("tree.json")
DOWNLOAD_LIMIT = 10
download_dir = "downloads"
pfp_dir = "pfp"

os.makedirs(download_dir, exist_ok=True)
os.makedirs(pfp_dir, exist_ok=True)


def find_usernames(data: dict) -> list[str]:
    usernames = []
    for key, value in data.items():
        if key == "username":
            usernames.append(value)
        elif isinstance(value, dict):
            usernames.extend(find_usernames(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    usernames.extend(find_usernames(item))

    return usernames


def main():
    for _ in range(RUNS):
        # perform fetch
        username = QUEUE.pop(0)
        if username in VISITED:
            continue
        print(f"Fetching {username}")
        command = [
            "gallery-dl",
            "-d",
            download_dir,
            f"https://www.instagram.com/{username}",
            "--write-metadata",
            "--write-info-json",
            "--range",
            f"1-{DOWNLOAD_LIMIT}",
            "--no-download",
        ]
        subprocess.run(command)
        # Find new usernames
        new_usernames = []
        for file in glob.glob(f"{download_dir}/**/{username}/*.json", recursive=True):
            data = load_json(file)
            new_usernames.extend(find_usernames(data))
        # Add new usernames to queue
        new_usernames = list(set(new_usernames))
        for new_username in new_usernames:
            if new_username not in VISITED:
                QUEUE.append(new_username)
        # Create Trees
        if username in new_usernames:
            new_usernames.remove(username)
        TREE[username] = new_usernames
        # Save queue
        save_json(QUEUE, "queue.json")
        # Save visited
        VISITED.add(username)
        save_json(list(VISITED), "visited.json")
        # Save tree
        save_json(TREE, "tree.json")
        # Extract info
        info_dict = {
            "id": "",
            "username": "",
            "full_name": "",
            "bio_links": [],
            "bio": "",
            "pfp_path": "",
            "scraped": False,
        }
        for file in glob.glob(f"{download_dir}/**/{username}/*.json", recursive=True):
            if info_dict["scraped"]:
                break
            try:
                data = load_json(file)
                info_dict["id"] = data["user"]["id"]
                info_dict["username"] = data["username"]
                info_dict["full_name"] = data["user"]["full_name"]
                info_dict["bio_links"] = data["user"]["bio_links"]
                info_dict["bio"] = data["user"]["biography"]
                url = data["user"]["profile_pic_url_hd"]
                response = requests.get(url)
                pfp_path = os.path.join(pfp_dir, f"{username}.jpg")
                with open(pfp_path, "wb") as file:
                    file.write(response.content)
                    file.close()
                info_dict["pfp_path"] = pfp_path
                info_dict["scraped"] = True
            except KeyError:
                info_dict["scraped"] = False

        if len(info_dict["bio_links"]) > 0:
            info_dict["bio_links"] = [i["url"] for i in info_dict["bio_links"]]

        INFO[username] = info_dict
        # Save info
        save_json(INFO, "info.json")
    # Redo...


if __name__ == "__main__":
    main()
