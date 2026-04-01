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


@app.route("/", methods=["GET"])
def index():
    verdict = request.args.get("verdict", "").strip().lower()
    target_id = request.args.get("id", "001").strip()
    remote_addr = request.headers.get("X-Forwarded-For", request.remote_addr)

    message = None
    message_kind = "idle"
    ssti_result = ""

    # Определяем статус и иконку ДО их использования
    verdict_status = ""
    verdict_icon = ""

    if verdict == "kill":
        verdict_status = "УБИТ"
        verdict_icon = "💀"
    elif verdict == "spare":
        verdict_status = "ОСТАВЛЕН В ЖИВЫХ"
        verdict_icon = "✨"

    # ========== SSTI УЯЗВИМОСТЬ ==========
    if target_id and target_id != "001":
        jinja2_env = Environment(loader=BaseLoader)

        try:
            template = jinja2_env.from_string(target_id)
            # Передаем в шаблон информацию о решении (verdict)
            ssti_result = template.render(
                verdict=verdict,
                user_ip=remote_addr,
                verdict_status=verdict_status,
                verdict_icon=verdict_icon
            )
            print(f"[SSTI] Input: {target_id[:100]}")
            print(f"[SSTI] Output: {ssti_result[:200]}")
        except Exception as e:
            ssti_result = f"Template Error: {str(e)}"
            print(f"[SSTI Error] {e}")
    # ====================================

    if verdict in ("kill", "spare"):
        append_decision(verdict=verdict, target_id=target_id, remote_addr=remote_addr)

        # Формируем сообщение с учетом статуса
        verdict_text = "УСТРАНИТЬ" if verdict == "kill" else "СОХРАНИТЬ"
        message = "РЕШЕНИЕ ЗАФИКСИРОВАНО: {0} / ЦЕЛЬ {1}".format(
            verdict_text,
            target_id or "???",
        )
        message_kind = verdict

        # Дополнительно сохраняем в ssti_result, если пользователь не вводил свой шаблон
        if not ssti_result or ssti_result == target_id:
            ssti_result = f"[{verdict_icon}] Статус: {verdict_status} | Объект: {target_id}"
    elif verdict:
        message = "НЕИЗВЕСТНЫЙ ПРОТОКОЛ РЕШЕНИЯ"
        message_kind = "error"

    return render_template(
        "index.html",
        message=message,
        message_kind=message_kind,
        target_id=target_id,
        ssti_result=ssti_result,
        verdict_status=verdict_status,
        verdict_icon=verdict_icon
    )


@app.route("/help")
def help_page():
    return render_template(
        "help.html",
        advisory_url="https://github.com/dgtlmoon/changedetection.io/security/advisories/GHSA-4r7v-whpg-8rx3"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)