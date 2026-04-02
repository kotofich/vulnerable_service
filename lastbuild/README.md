# Vulnerable Service

`Vulnerable Service` is a deliberately insecure Flask application designed for CTF labs, training environments, and local security exercises. The project combines a themed web UI, an intentionally exposed Server-Side Template Injection (SSTI) flow in Jinja2, and a Docker environment with SSH and privilege-escalation style challenge elements.

This README describes the current implementation located in this directory:

- [`/app.py`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/app.py)
- [`/templates/`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/templates)
- [`/static/`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/static)

## Purpose

The service is built as a practice target, not as a production application. It is meant to help with:

- understanding how SSTI in Jinja2 appears in real Flask code;
- demonstrating unsafe handling of user-controlled template input;
- running a small themed interface for CTF or lab scenarios;
- combining web exploitation with post-exploitation steps inside Docker;
- practicing enumeration of files, routes, logs, and environment behavior.

## Current Features

- Flask app with three routes: `/`, `/main`, and `/help`
- custom neon-styled interface in blue and pink tones
- fixed side images on the landing page
- meme-themed voting page for developer jokes
- help page with an advisory link and a pug image
- intentional Jinja2 SSTI behavior via `id` input on `/main`
- request logging to `decision.log`
- Docker environment with SSH enabled
- extra compiled helper binary for challenge behavior

## Project Structure

```text
├── README.md
├── app.py
├── decision.log
├── dockerfile
├── entrypoint.sh
├── requirements.txt
├── service_check.c
├── static/
│   ├── AP565404867764_2.jpg
│   ├── iii.jpeg
│   ├── mops.jpeg
│   └── style.css
└── templates/
    ├── help.html
    ├── index.html
    └── main.html
```

## Tech Stack

- Python 3
- Flask 0.12.2
- Jinja2 2.11.3
- Werkzeug 0.16.1
- HTML/CSS
- Docker
- OpenSSH
- GCC for compiling the helper binary inside the container

## Application Overview

The main server file is [`app.py`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/app.py).

### Route: `/`

The landing page renders [`templates/index.html`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/templates/index.html).

It currently includes:

- a title banner: `MAIN TERMINAL`
- a disabled textarea placeholder
- a navigation button to `/main`
- a fixed `HELP` button
- two side images with labels:
  - `JORDAN BELFORT`
  - `DONNIE AZOFF`

### Route: `/main`

The voting page renders [`templates/main.html`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/templates/main.html).

It includes:

- four meme-themed developer options;
- client-side selection via radio buttons;
- a `VOTE` button;
- result rendering when a vote is submitted;
- a `BACK` button linking to `/`.

The page expects these query parameters:

- `verdict`
- `id`

For example:

```text
/main?verdict=vote&id=opt1
```

### Route: `/help`

The help page renders [`templates/help.html`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/templates/help.html).

It includes:

- a link to the `changedetection.io` advisory;
- a back button to the landing page;
- a large pug image shown below the controls.

## Intentional Vulnerability

The core security issue is intentional SSTI in Jinja2.

Inside [`app.py`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/app.py), the `/main` route reads user-controlled `id` and passes it into:

- `Environment(loader=BaseLoader)`
- `from_string(target_id)`
- `template.render(...)`

That means attacker-controlled content can be interpreted as a Jinja2 template instead of plain text.

### Why this matters

Unsafe template rendering can lead to:

- data disclosure;
- server-side expression execution;
- access to Python objects depending on context;
- pivoting to further compromise inside the container.

### Example

Basic expression test:

```text
/main?id={{7*7}}
```

Vote flow with injected `id`:

```text
/main?verdict=vote&id={{7*7}}
```

## Logging

The application writes actions to [`decision.log`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/decision.log).

Current log format:

```text
[timestamp] ip=<ip> verdict=<verdict> id=<target_id>
```

The logging helper is implemented in `append_decision(...)`.

## Local Run

### Requirements

- Python 3
- `pip`
- a Unix-like environment is recommended

### Install dependencies

```bash
cd /Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Start the app

```bash
python3 app.py
```

The application listens on:

```text
http://127.0.0.1:5001
```

## Docker Run

The container definition is in [`dockerfile`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/dockerfile).

### Build

```bash
cd /Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild
docker build -t vulnerable-service -f dockerfile .
```

### Run

```bash
docker run --rm -p 5001:5001 -p 2222:22 vulnerable-service
```

After startup:

- web app: `http://127.0.0.1:5001`
- SSH: `ssh user@127.0.0.1 -p 2222`

## Docker Environment Notes

The Docker image currently:

- uses `python:3.8-slim`;
- installs `openssh-server`, `sudo`, `curl`, `gcc`, `libc6-dev`, `procps`, and `strace`;
- creates a `user` account;
- generates an SSH keypair for that user;
- installs and runs the Flask application;
- copies and compiles [`service_check.c`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/service_check.c);
- marks `/usr/local/bin/service_check` as SUID.

This is part of the challenge flavor and should be treated as intentionally unsafe.

## Static Assets

The UI styling lives in [`static/style.css`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/static/style.css).

Current image assets:

- [`iii.jpeg`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/static/iii.jpeg) — left-side character image
- [`AP565404867764_2.jpg`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/static/AP565404867764_2.jpg) — right-side character image
- [`mops.jpeg`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/static/mops.jpeg) — pug image on `/help`

## Templates

### `templates/index.html`

Landing page:

- fixed side portraits;
- main terminal headline;
- disabled textarea used as visual terminal filler;
- button leading to `/main`.

### `templates/main.html`

Voting page:

- meme-based developer choices;
- client-side radio selection;
- GET redirect for submitting a vote;
- optional result panel.

### `templates/help.html`

Support page:

- advisory link;
- back navigation;
- decorative pug image.

## Known Behaviors and Limitations

- The timestamp in logs is labeled `UTC`, but `datetime.now()` is used without explicit UTC conversion.
- The `/main` route maps `opt1` to `opt4` in Python, while the displayed labels/descriptions are defined in the template.
- The landing page textarea is decorative and currently disabled.
- The app is intentionally vulnerable and should not be exposed publicly.
- Dockerfile uses `EXPOSE 5000 22`, while the Flask app itself runs on port `5001`.

## Development Tips

Useful verification command:

```bash
python3 -m py_compile app.py
```

If you edit the UI, the files you will most likely touch are:

- [`templates/index.html`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/templates/index.html)
- [`templates/main.html`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/templates/main.html)
- [`templates/help.html`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/templates/help.html)
- [`static/style.css`](/Users/nikitagorosilov/Desktop/indDev/vulnerable_service/lastbuild/static/style.css)


