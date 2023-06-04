#!/usr/bin/env python3

import hashlib
import itertools
import logging
import os

import argparse
import coloredlogs

from challenge import *

parser = argparse.ArgumentParser(description='Скрипт для автоматической загрузки конфигураций заданий на CTFd')
parser.add_argument('url', help='Адрес борды')
parser.add_argument('token', help='Токен доступа')
parser.add_argument('-mode', dest="mode", choices=['all', 'one'], default='all', help='Режим загрузки - все конфиги / один указанный конфиг')
parser.add_argument('-task', dest='task', help='Шифр задания для загрузки')

args = parser.parse_args()
coloredlogs.install()

REPO_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

TOKEN = args.token
MODE = args.mode
TASK = args.task
URL = args.url

installed_challenges = load_installed_challenges(URL, TOKEN)
installed_challenges_names = set([x.get("name") for x in installed_challenges])
configured_challenges = []
requirements = []

if MODE == 'all':
    for task_dir in os.listdir(REPO_PATH):
        config_file = os.path.join(REPO_PATH, task_dir, 'ctfd', 'task.yaml')
        if os.path.exists(config_file) and '_template' not in config_file:
            challenge = load_challenge(config_file)
            challenge["file_hash"] = hashlib.md5(open(config_file, "rb").read()).hexdigest() # Берётся хэш от файла конфигурации задания
            configured_challenges.append(challenge)
    configured_challenges_names = set([x.get("name") for x in configured_challenges])
    present_chellenges = configured_challenges_names & installed_challenges_names
    challenges_to_delete = list(installed_challenges_names - present_chellenges)
    challenges_to_create = list(configured_challenges_names - present_chellenges)
    # Получение заданий на обновление (на основе хэшей от файлов конфигурации)
    challenges_to_modify = list(
        filter(
            lambda a: True if a[0].get("name") == a[1].get("name") and a[0].get("file_hash") != a[1].get("file_hash") else False, 
            itertools.product(installed_challenges, configured_challenges)
            )
        )
    logging.warning("Число заданий на удаление: {}".format(len(challenges_to_delete)))
    logging.warning("Число заданий на создание: {}".format(len(challenges_to_create)))
    logging.warning("Число заданий на изменение: {}".format(len(challenges_to_modify)))
    
    # Удаляются задания, конфигурации которых отсутствуют в данном репозиторие
    for ch in list(filter(lambda x: x.get("name") in challenges_to_delete, installed_challenges)):
        delete_challenge(ch, URL, TOKEN)
        logging.info("Таск {} удалён".format(ch["name"]))
    
    # Создаются новые задания
    for ch in list(filter(lambda x: x.get("name") in challenges_to_create, configured_challenges)):
        challenge_id = create_challenge(ch, URL, TOKEN)
        logging.info("Таск {} добавлен".format(ch["name"]))
        requirements.append((challenge_id, ch.get("requirements")))

    # Вносятся изменения
    for ch in challenges_to_modify:
        sync_challenge(ch[1], URL, TOKEN, ch[0]["id"])
        logging.info("Таск {} обновлен".format(ch[1]["name"]))
        requirements.append((ch[0]["id"], ch[1].get("requirements")))

elif MODE == 'one' and TASK:
    config_file = os.path.join(REPO_PATH, TASK, 'ctfd', 'task.yaml')
    if os.path.exists(config_file):
        challenge = load_challenge(config_file)
        challenge["file_hash"] = hashlib.md5(open(config_file, "rb").read()).hexdigest()
        if challenge["name"] in installed_challenges_names:
            for ch in installed_challenges:
                if ch["name"] == challenge["name"]:
                    challenge_id = ch["id"]
                    if challenge["file_hash"] == ch.get("file_hash"):
                        logging.info("Таск {} актуален".format(challenge["name"]))
                        exit()
            sync_challenge(challenge, URL, TOKEN, challenge_id)
            logging.info("Таск {} обновлен".format(challenge["name"]))
        else:
            challenge_id = create_challenge(challenge, URL, TOKEN)
            logging.info("Таск {} добавлен".format(challenge["name"]))
            
    else:
        print("Шифр задания указан неверно или файл конфиг отсутствует")


# ========================= Создание зависимостей ================================ # 
# * Делается в последнюю очередь, так как необходимо наличие всех заданий на борде #
if requirements != []:
    logging.warning("Начинаю формирование зависимостей")
else:
    exit()

installed_challenges = load_installed_challenges(URL, TOKEN)
s = generate_session(URL, TOKEN)
for req in requirements:
    required_challenges = []
    if req[1] != None:
        for r in req[1]:  
            if type(r) == str:
                for c in installed_challenges:
                    if c["name"] == r:
                        required_challenges.append(c["id"])
            elif type(r) == int:
                required_challenges.append(r)

    required_challenges = list(set(required_challenges))
    
    data = {"requirements": {"prerequisites": required_challenges, "anonymize": True}}
    r = s.patch(f"/api/v1/challenges/{req[0]}", json=data)
    r.raise_for_status()