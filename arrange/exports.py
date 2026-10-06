"""SNS告知原稿・TimeTree用CSVの既存出力形式。"""
import csv
import re
from datetime import datetime, timedelta
from jinja2 import Template

newlive_template = """
🆕新規ライブ情報

『{{ title }}』

{{ date_formatted }}
⏰ 開場 {{ time_open }}｜開演 {{ time_start }}{% if time_end %}｜終演 {{ time_end }} {% endif %}
📍 {{ venue }}
🎫 {% if advance and door %}前売 ¥{{advance}}｜当日 ¥{{door}}{% elif advance %}前売 ¥{{advance}}{% elif door %}当日現金支払 ¥{{door}}{% endif %}　{{ url }}
{% if streaming_price %}🎥 配信あり {{ streaming_url }}
{% endif %}{% if preSaleStart %}
先行：{{ preSaleStart_formatted }} ~ {{ preSaleEnd_formatted }}{% endif %}{% if general %}
一般：{{ general_formatted }} ~ {% endif %}
"""

nextlive_template = """
◤ {{date_formatted}}の予定 ◢

『{{ title }}』
⏰ 開場 {{ time_open }}｜開演 {{ time_start }}{% if time_end %}｜終演 {{ time_end }} {% endif %}
📍 {{ venue }}
🎫 {% if advance and door %}前売 ¥{{advance}}｜当日 ¥{{door}}{% elif advance %}前売 ¥{{advance}}{% endif %} {{url}}
{% if streaming_url %}🎥 配信 ¥{{streaming_price}} {{streaming_url}}{% endif %}
"""

def format_timetree_datetime(datetime_str):
    """2026-05-02T11:00:00 → 2026-05-02 11:00"""
    if not datetime_str:
        return ""
    try:
        return datetime.strptime(
            datetime_str.strip(),
            "%Y-%m-%dT%H:%M:%S"
        ).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return datetime_str.strip()


def format_timetree_price(price):
    """数字のみの料金には「円」を付ける"""
    price = (price or "").strip()

    if not price:
        return ""

    if re.fullmatch(r"[\d,]+", price):
        return f"{price}円"

    return price


def write_exports(lives, output_dir, *, new_lives):
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, template, rows in [("newlive.txt", newlive_template, lives), ("nextlive.txt", nextlive_template, sorted(lives, key=lambda r: r["date"]))]:
        (output_dir / name).write_text("\n\n".join(Template(template).render(row) for row in rows), encoding="utf-8")
    write_timetree(new_lives, output_dir)


def write_timetree(lives, output_dir):
    """今回新しく追加されたライブだけをTimeTreeへ渡す。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    TIMETREE_FIELDS = [
        "予定タイトル",
        "終日/非終日",
        "開始日時",
        "終了日時",
        "予約投稿日時",
        "削除予約日時",
        "繰り返し条件",
        "繰り返し終了日",
        "ラベル",
        "説明",
        "場所",
        "GoogleMap URL",
        "URL",
    ]


    with open(output_dir / "timetree.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TIMETREE_FIELDS)
        writer.writeheader()

        for live in lives:

            date = (live.get("date") or "").strip()

            time_start = (live.get("time_start") or "").strip()
            time_end = (live.get("time_end") or "").strip()

            end_date = date

            # 終了時刻が未設定の場合は、開始時刻の1時間後を仮の終了時刻にする
            if not time_end and time_start:
                start_dt = datetime.strptime(
                    f"{date} {time_start}",
                    "%Y-%m-%d %H:%M"
                )

                end_dt = start_dt + timedelta(hours=1)

                time_end = end_dt.strftime("%H:%M")
                end_date = end_dt.strftime("%Y-%m-%d")

            # ── 説明欄作成 ──
            description = []

            time_open = (live.get("time_open") or "").strip()
            if time_open:
                description.append(f"開場：{time_open}")

            advance = format_timetree_price(live.get("advance"))
            if advance:
                description.append(f"前売：{advance}")

            door = format_timetree_price(live.get("door"))
            if door:
                description.append(f"当日：{door}")

            performer = (live.get("performer") or "").strip()
            if performer:
                description.append(f"出演：{performer}")

            streaming_price = format_timetree_price(
                live.get("streaming_price")
            )
            if streaming_price:
                description.append(f"配信料金：{streaming_price}")

            streaming_url = (live.get("streaming_url") or "").strip()
            if streaming_url:
                description.append(f"配信URL：{streaming_url}")

            pre_start = format_timetree_datetime(
                live.get("preSaleStart", "")
            )
            pre_end = format_timetree_datetime(
                live.get("preSaleEnd", "")
            )

            if pre_start:
                if pre_end:
                    description.append(
                        f"先行受付：{pre_start} ～ {pre_end}"
                    )
                else:
                    description.append(
                        f"先行受付：{pre_start}"
                    )

            general = format_timetree_datetime(
                live.get("general", "")
            )

            if general:
                description.append(
                    f"一般発売：{general}"
                )

            writer.writerow({
                "予定タイトル":
                    (live.get("title") or "").strip(),

                "終日/非終日":
                    "非終日",

                "開始日時":
                    f"{date} {time_start}"
                    if date and time_start else "",

                "終了日時":
                    f"{end_date} {time_end}"
                    if date and time_end else "",

                "予約投稿日時":
                    "",

                "削除予約日時":
                    "",

                "繰り返し条件":
                    "",

                "繰り返し終了日":
                    "",

                "ラベル":
                    "1",

                "説明":
                    "\n".join(description),

                "場所":
                    (live.get("venue") or "").strip(),

                "GoogleMap URL":
                    "",

                "URL":
                    (live.get("url") or "").strip(),
            })


