from pathlib import Path
import yaml
import click
from binascii import hexlify
import json
import os
from urllib.parse import urljoin
from requests import Session

class APISession(Session):
    def __init__(self, prefix_url=None, *args, **kwargs):
        super(APISession, self).__init__(*args, **kwargs)
        self.prefix_url = prefix_url

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.prefix_url, url)
        return super(APISession, self).request(method, url, *args, **kwargs)

def generate_session(url, access_token):
    url = url.strip("/")
    s = APISession(url)
    s.headers.update({"Authorization": f"Token {access_token}"})
    return s


class Yaml(dict):
    def __init__(self, data, file_path=None):
        super().__init__(data)
        self.file_path = Path(file_path)
        self.directory = self.file_path.parent


def load_challenge(path):
    try:
        with open(path, encoding='utf8') as f:
            return Yaml(data=yaml.safe_load(f.read()), file_path=path)
    except FileNotFoundError:
        click.secho(f"No challenge.yml was found in {path}", fg="red")
        return


def load_installed_challenges(url, access_token):
    s = generate_session(url, access_token)
    return s.get("/api/v1/challenges?view=admin", json=True).json()["data"]

def delete_challenge(challenge, url, access_token):
    s = generate_session(url, access_token)
    return s.delete("/api/v1/challenges/{}?view=admin".format(challenge["id"]), json=True)

# ============ Функция обновления инфы о задании ============
def sync_challenge(challenge, url, access_token, challenge_id):
    data = {
        "name": challenge["name"],
        "category": challenge["category"],
        "description": challenge["description"],
        "type": challenge.get("type", "standard"),
        "challenge_token": challenge.get("challenge_token", ""), #! Закомментировать если CTFd не поддерживает античит
        "value": int(challenge["value"]),
        "file_hash": challenge["file_hash"], #! Закомментировать если CTFd не поддерживает проверку на наличие заданий
    }
    if challenge.get("attempts"):
        data["max_attempts"] = challenge.get("attempts")

    if challenge.get("decay"):
        data["decay"] = challenge.get("decay")
        data["initial"] = challenge.get("initial")
        data["minimum"] = challenge.get("minimum")

    data["state"] = "hidden"

    s = generate_session(url, access_token)

    original_challenge = s.get(f"/api/v1/challenges/{challenge_id}", json=data).json()[
        "data"
    ]

    r = s.patch(f"/api/v1/challenges/{challenge_id}", json=data)
    r.raise_for_status()

    # --- Удаление существующих флагов ---
    current_flags = s.get(f"/api/v1/flags", json=data).json()["data"]
    for flag in current_flags:
        if flag["challenge_id"] == challenge_id:
            flag_id = flag["id"]
            r = s.delete(f"/api/v1/flags/{flag_id}", json=True)
            r.raise_for_status()

    # --- Создание новых флагов ---
    if challenge.get("flags"):
        for flag in challenge["flags"]:
            if type(flag) == str:
                data = {"content": flag, "type": "static", "challenge": challenge_id}
                r = s.post(f"/api/v1/flags", json=data)
                r.raise_for_status()
            elif type(flag) == dict:
                flag["challenge"] = challenge_id
                r = s.post(f"/api/v1/flags", json=flag)
                r.raise_for_status()

    # --- Удаление существующих тэгов ---
    current_tags = s.get(f"/api/v1/tags", json=data).json()["data"]
    for tag in current_tags:
        if tag["challenge_id"] == challenge_id:
            tag_id = tag["id"]
            r = s.delete(f"/api/v1/tags/{tag_id}", json=True)
            r.raise_for_status()

    # --- Изменение тэгов ---
    if challenge.get("tags"):
        for tag in challenge["tags"]:
            r = s.post(f"/api/v1/tags", json={"challenge": challenge_id, "value": tag})
            r.raise_for_status()

    # --- Удаление существующих файлов ---
    all_current_files = s.get(f"/api/v1/files?type=challenge", json=data).json()["data"]
    for f in all_current_files:
        for used_file in original_challenge["files"]:
            if f["location"] in used_file:
                file_id = f["id"]
                r = s.delete(f"/api/v1/files/{file_id}", json=True)
                r.raise_for_status()
    if challenge.get("topic"):
        data = {"topic": "None"}
        if challenge["topic"] in ["spacex","quest","ussr"]:
            data["topic"] = challenge["topic"]
            r = s.patch(f"/api/v1/challenges/{challenge_id}", json=data)
            r.raise_for_status()
    if challenge.get("postdescription"):
        data["postdescription"] = challenge["postdescription"]
        r = s.patch(f"/api/v1/challenges/{challenge_id}", json=data)
        r.raise_for_status()
    # --- Загрузка файлов ---
    if challenge.get("files"):
        files = []
        for f in challenge["files"]:
            file_path = Path(challenge.directory, f)
            if file_path.exists():
                file_object = ("file", file_path.open(mode="rb"))
                files.append(file_object)
            else:
                click.secho(f"File {file_path} was not found", fg="red")
                raise Exception(f"File {file_path} was not found")

        data = {"challenge": challenge_id, "type": "challenge"}
        r = s.post(f"/api/v1/files", files=files, data=data)
        r.raise_for_status()

    # --- Удаление существующих подсказок ---
    current_hints = s.get(f"/api/v1/hints", json=data).json()["data"]
    for hint in current_hints:
        if hint["challenge_id"] == challenge_id:
            hint_id = hint["id"]
            r = s.delete(f"/api/v1/hints/{hint_id}", json=True)
            r.raise_for_status()

    # --- Создание хинтов ---
    if challenge.get("hints"):
        for hint in challenge["hints"]:
            if type(hint) == str:
                data = {"content": hint, "cost": 0, "challenge": challenge_id}
            else:
                data = {
                    "content": hint["content"],
                    "cost": hint["cost"],
                    "challenge": challenge_id,
                }

            r = s.post(f"/api/v1/hints", json=data)
            r.raise_for_status()
    # --- Сделать таск видимым ---
    data = {"state": "visible"}
    if challenge.get("state"):
        if challenge["state"] in ["hidden", "visible"]:
            data["state"] = challenge["state"]

    r = s.patch(f"/api/v1/challenges/{challenge_id}", json=data)
    r.raise_for_status()
    return False
# ========= Добавление нового задания =========
def create_challenge(challenge, url, access_token):
    data = {
        "name": challenge["name"],
        "category": challenge["category"],
        "description": challenge["description"],
        "type": challenge.get("type", "standard"),
        "challenge_token": challenge.get("challenge_token", ""), #! Закомментировать если CTFd не поддерживает античит
        "value": int(challenge["value"]),
        "file_hash": challenge["file_hash"] #! Закомментировать если CTFd не поддерживает проверку на наличие заданий
    }
    if challenge.get("attempts"):
        data["max_attempts"] = challenge.get("attempts")

    if challenge.get("decay"):
        data["decay"] = challenge.get("decay")
        data["initial"] = challenge.get("initial")
        data["minimum"] = challenge.get("minimum")

    if challenge.get("postdescription"):
        data["postdescription"] = challenge["postdescription"]
        
    s = generate_session(url, access_token)

    r = s.post("/api/v1/challenges", json=data)
    r.raise_for_status()

    challenge_data = r.json()
    challenge_id = challenge_data["data"]["id"]

    # --- Создание флагов ---
    if challenge.get("flags"):
        for flag in challenge["flags"]:
            if type(flag) == str:
                data = {"content": flag, "type": "static", "challenge": challenge_id}
                r = s.post(f"/api/v1/flags", json=data)
                r.raise_for_status()
            elif type(flag) == dict:
                flag["challenge"] = challenge_id
                r = s.post(f"/api/v1/flags", json=flag)
                r.raise_for_status()

    # --- Создание тэгов ---
    if challenge.get("tags"):
        for tag in challenge["tags"]:
            r = s.post(f"/api/v1/tags", json={"challenge": challenge_id, "value": tag})
            r.raise_for_status()

    # --- Загрузка файлов ---
    if challenge.get("files"):
        files = []
        for f in challenge["files"]:
            file_path = Path(challenge.directory, f)
            if file_path.exists():
                file_object = ("file", file_path.open(mode="rb"))
                files.append(file_object)
            else:
                click.secho(f"File {file_path} was not found", fg="red")
                raise Exception(f"File {file_path} was not found")

        data = {"challenge": challenge_id, "type": "challenge"}
        r = s.post(f"/api/v1/files", files=files, data=data)
        r.raise_for_status()

    # --- Добавление хинтов ---
    if challenge.get("hints"):
        for hint in challenge["hints"]:
            if type(hint) == str:
                data = {"content": hint, "cost": 0, "challenge": challenge_id}
            else:
                data = {
                    "content": hint["content"],
                    "cost": hint["cost"],
                    "challenge": challenge_id,
                }

            r = s.post(f"/api/v1/hints", json=data)
            r.raise_for_status()

    # --- Выставление доступности задания ---
    if challenge.get("state"):
        data = {"state": "hidden"}
        if challenge["state"] in ["hidden", "visible"]:
            data["state"] = challenge["state"]

        r = s.patch(f"/api/v1/challenges/{challenge_id}", json=data)
        r.raise_for_status()
    if challenge.get("topic"):
        data = {"topic": "None"}
        if challenge["topic"] in ["spacex","quest","ussr"]:
            data["topic"] = challenge["topic"]
            r = s.patch(f"/api/v1/challenges/{challenge_id}", json=data)
            r.raise_for_status()
    return challenge_id

def lint_challenge(path):
    try:
        challenge = load_challenge(path)
    except yaml.YAMLError as e:
        click.secho(f"Error parsing challenge.yml: {e}", fg="red")
        exit(1)

    required_fields = ["name", "author", "category", "description", "value"]
    errors = []
    for field in required_fields:
        if challenge.get(field) is None:
            errors.append(field)

    if len(errors) > 0:
        print("Missing fields: ", ", ".join(errors))
        exit(1)

    exit(0)
