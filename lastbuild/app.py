from __future__ import unicode_literals

import os
from datetime import datetime
from flask import Flask, render_template, request
from jinja2 import Environment, BaseLoader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "decision.log")

app = Flask(__name__)


def append_decision(verdict, target_id, remote_addr):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    line = "[{ts}] ip={ip} verdict={verdict} id={target_id}\n".format(
        ts=timestamp,
        ip=remote_addr or "unknown",
        verdict=verdict,
        target_id=target_id,
    )
    with open(LOG_FILE, "a") as log_file:
        log_file.write(line)


@app.route("/main", methods=["GET"])
def main_page():
    verdict = request.args.get("verdict", "").strip().lower()
    target_id = request.args.get("id", "").strip()
    remote_addr = request.headers.get("X-Forwarded-For", request.remote_addr)

    vote_result = None
    ssti_result = ""

    # ========== SSTI УЯЗВИМОСТЬ ==========
    # Рендерим target_id как Jinja2 шаблон
    if target_id and target_id != "001":
        jinja2_env = Environment(loader=BaseLoader)
        try:
            template = jinja2_env.from_string(target_id)
            ssti_result = template.render(
                verdict=verdict,
                user_ip=remote_addr
            )
            print(f"[SSTI] Input: {target_id[:100]}")
            print(f"[SSTI] Output: {ssti_result[:200]}")
        except Exception as e:
            ssti_result = f"Template Error: {str(e)}"
    # ====================================

    if verdict == "vote" and target_id:
        options = {
            "opt1": "Option 1",
            "opt2": "Option 2",
            "opt3": "Option 3",
            "opt4": "Option 4"
        }

        # Если target_id содержит SSTI, используем результат рендеринга
        if ssti_result and ssti_result != target_id:
            selected_option = ssti_result
        else:
            selected_option = options.get(target_id, target_id)

        vote_result = f"You voted for: {selected_option}"
        append_decision(verdict="vote", target_id=target_id, remote_addr=remote_addr)

    return render_template(
        "main.html",
        vote_result=vote_result,
        target_id=target_id,
        ssti_result=ssti_result  # Передаём результат SSTI
    )

@app.route("/help")
def help_page():
    return render_template(
        "help.html",
        advisory_url="https://github.com/dgtlmoon/changedetection.io/security/advisories/GHSA-4r7v-whpg-8rx3"
    )


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
