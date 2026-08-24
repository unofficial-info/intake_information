import csv
import os
import re
import yaml
from jinja2 import Template
from datetime import datetime
import locale

# 日本語曜日にする
try:
    locale.setlocale(locale.LC_TIME, "ja_JP.UTF-8")
except locale.Error:
    pass  # Windows等では別処理

# ─────────────────────────────────────────────
# ユーティリティ関数
# ─────────────────────────────────────────────

def format_date(date_str):
    """YYYY-MM-DD → YYYY/M/D(曜日) に変換"""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%Y/%-m/%-d(%a)")
    except:
        return date_str

def format_datetime(datetime_str):
    """YYYY-MM-DDTHH:MM:SS → M/D HH:MM に変換"""
    try:
        dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%S")
        return dt.strftime("%-m/%-d(%a) %H:%M")
    except (ValueError, TypeError):
        return datetime_str

def format_google_cal(date_str, time_str):
    if not date_str or not time_str:
        return ""
    clean_date = date_str.replace("-", "")
    clean_time = time_str.replace(":", "")
    return f"{clean_date}T{clean_time}00"

def format_google_cal_for_ticket(datetime_str):
    if not datetime_str:
        return ""
    return datetime_str.replace("-","").replace(":","")

def safe_filename(title):
    """タイトルをファイル名に使えるよう変換（記号・スペース除去）"""
    title = re.sub(r'[\\/*?:"<>|　\s]', '_', title)
    title = re.sub(r'_+', '_', title)
    return title.strip('_')[:40]  # 長すぎ防止


# ─────────────────────────────────────────────
# テンプレート定義
# ─────────────────────────────────────────────

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

yml_template = """
- date: "{{ date }}"
  title: "{{ title }}"
  venue: "{{ venue }}"
  {% if advance %}advance: "{{ advance }}"{% endif %}
  {% if door %}door: "{{ door }}"{% endif %}
  time_open: "{{ time_open }}"
  time_start: "{{ time_start }}"
  {% if time_end %}time_end: "{{ time_end }}"{% endif %}
  {% if preSaleStart %}preSale_start: "{{ preSaleStart }}"
  preSale_end: "{{ preSaleEnd }}"{% endif %}
  {% if general %}general: "{{ general }}"{% endif %}
  url: "{{ url }}"
  {% if streaming_url %}streaming_url: "{{ streaming_url }}"{% endif %}
  {% if streaming_price %}streaming_price: "{{ streaming_price }}"{% endif %}
"""

calender_template = """
{{ date }}
<div style="background-color:#cfe6da;"><font color="#696969">{{ title }}</div>
[詳細]
{{ time_start }}~{{ time_end }}(開場 {{ time_open }})
<b>『{{ title }}』</b>
📍 {{ venue }}
🎫 <a href="{{ url }}" target="_blank">{% if advance %}前売 ¥{{ advance }}{% elif door %}当日現金支払 ¥{{ door }}{% endif %}</a>{% if advance and door %}(¥{{ door }}){% endif %}
{% if streaming_url %}🎥 <a href="{{ streaming_url }}" target="_blank">{{streaming_price}}</a>{% elif streaming_price %}◎配信あり{% endif %}
🗓️ <a href="https://www.google.com/calendar/render?action=TEMPLATE&text={{title}}&dates={{google_start}}/{{google_end}}&location={{venue}}" target="_blank" class="btn-calendar">Googleカレンダーに追加</a>
"""

NEWS_DATE_PLACEHOLDER = "%%TODAY%%"
news_template = """---
layout: post
date: %%TODAY%% 17:00:00 + 0900
category: "LIVE"
title: "【 / 】{{ title }}【出演決定】"
---

<a href="https://www.google.com/calendar/render?action=TEMPLATE&text={{title}}&dates={{google_start}}/{{google_end}}&location={{venue}}" target="_blank" class="btn-calendar">
<i class="fa-solid fa-calendar-check"></i> Googleカレンダーに追加
</a>

# {{ title }}<br>

<i class="fa-regular fa-calendar-alt"></i> {{ date_formatted }}<br>
<i class="fa-regular fa-clock"></i> 開場 {{ time_open }} ｜開演 {{ time_start }} {% if time_end %}｜終演 {{ time_end }} {% endif %}<br>
<i class="fa-solid fa-location-dot"></i> {{ venue }}<br>
<i class="fa-solid fa-ticket"></i>  {% if advance and door %}前売 ¥{{advance}}｜当日 ¥{{door}}{% elif advance %}前売 ¥{{advance}}{% elif door %}当日現金支払 ¥{{door}}{% endif %}<br>
<i class="fa-solid fa-users"></i> {{ performer }}

{% if preSaleStart %}先行：{{ preSaleStart_formatted }} ~ {{ preSaleEnd_formatted }}
<a href="https://www.google.com/calendar/render?action=TEMPLATE&text=【先行】{{title}}&dates={{google_pre_start}}/{{google_pre_end}}&location={{url}}" target="_blank" class="btn-calendar">
<i class="fa-solid fa-calendar-check"></i>
</a><br>{% endif %}
{% if general %}一般：{{ general_formatted }}
<a href="https://www.google.com/calendar/render?action=TEMPLATE&text=【チケ発】{{title}}&dates={{google_general}}/{{google_general}}&location={{url}}" target="_blank" class="btn-calendar">
<i class="fa-solid fa-calendar-check"></i> 
</a>{% endif %}

チケットの購入は<a href="{{ url }}" target="_blank">こちら</a>
"""

mainlive_template = """
- date: "{{ date }}"
  title: "{{ title }}"
  venue: "{{ venue }}"
  open: "{{ time_open }}"
  start: "{{ time_start }}"
  {% if time_end %}end: "{{ time_end }}"{% endif %}
  url: "{{ url }}"
"""



# ─────────────────────────────────────────────
# lives.yml 重複チェック付き追記
# ─────────────────────────────────────────────

def load_yml_keys(yml_path):
    """既存YMLからキー集合（date+title+time_start+url）を読み込む"""
    if not os.path.exists(yml_path):
        return set()
    with open(yml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data:
        return set()
    keys = set()
    for item in data:
        key = (
            str(item.get("date", "")),
            str(item.get("title", "")),
            str(item.get("time_start", "")),
            str(item.get("url", "")),
        )
        keys.add(key)
    return keys


# ─────────────────────────────────────────────
# メイン処理
# ─────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# print.pyを arrange/ に置いている場合でも、Jekyll本体のルートを正しく参照する
# - arrange/print.py で実行 → PROJECT_DIR は1つ上のサイトルート
# - ルート直下の print.py で実行 → PROJECT_DIR はSCRIPT_DIRのまま
PROJECT_DIR = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == "arrange" else SCRIPT_DIR

# ── Jekyllサイト用パス ──
YML_PATH   = os.path.join(PROJECT_DIR, "_data", "lives.yml")   # _data/lives.yml
NEWS_BASE  = os.path.join(PROJECT_DIR, "_news")                 # _news/{year}/YYMMDD_title.md
CSV_PATH   = os.path.join(SCRIPT_DIR, "lives.csv")              # arrange/lives.csv または ルート/lives.csv

# ── ローカル確認用（ツイート原稿など） ──
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(PROJECT_DIR, "_data"), exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
today_file = datetime.now().strftime("%y%m%d")  # ファイル名用: 260528 形式

# CSV読み込み
# utf-8-sig にしておくと、CSV先頭にBOMが付いていても title/date などの列名が崩れません。
with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    lives = list(reader)

# DictReaderは、CSVの1行にヘッダーより多い列があると、余った値を None キーに入れます。
# Jinja2のTemplate.render(dict)はキーが文字列でないと落ちるため、後で行番号付きで除去します。

# 既存YMLのキーを取得
existing_keys = load_yml_keys(YML_PATH)

# 出力バッファ
newlive_all  = []
nextlive_all = []
yml_new      = []   # 新規追加分のみ
# calender_all = []
news_all     = []
# mainlive_all = []
#new_news_files = []  # 新規追加ライブ（newsファイル生成用）

for row_num, live in enumerate(lives, start=2):
    # CSVの列数が多い行では、DictReaderが余った値を None キーに入れる。
    # そのままだと Jinja2 側で「keywords must be strings」になるため除去する。
    extra_values = live.pop(None, None)
    if extra_values:
        print(f"⚠️ CSV {row_num}行目: ヘッダーより列が多いです。カンマ区切りが崩れている可能性があります。余った値: {extra_values}")

    live = {str(k).strip().lstrip("\ufeff"): (v if v else "") for k, v in live.items() if k is not None}

    # 必要な列が空でも落ちないようにする
    for field in [
        "title", "date", "time_open", "time_start", "time_end", "venue",
        "advance", "door", "performer", "url", "streaming_url",
        "streaming_price", "preSaleStart", "preSaleEnd", "general"
    ]:
        live.setdefault(field, "")

    # Google Calendar用日時整形
    start_cal = format_google_cal(live["date"], live["time_start"])
    live["google_start"] = start_cal
    live["google_end"] = format_google_cal(live["date"], live["time_end"]) if live["time_end"] else start_cal
    if live.get("preSaleStart"):
        live["google_pre_start"] = format_google_cal_for_ticket(live["preSaleStart"])
        live["google_pre_end"]   = format_google_cal_for_ticket(live["preSaleEnd"])
    if live.get("general"):
        live["google_general"] = format_google_cal_for_ticket(live["general"])

    # 日付整形
    live["date_formatted"]        = format_date(live["date"])
    live["preSaleStart_formatted"]= format_datetime(live.get("preSaleStart",""))
    live["preSaleEnd_formatted"]  = format_datetime(live.get("preSaleEnd",""))
    live["general_formatted"]     = format_datetime(live.get("general",""))

    # 重複チェック用キー
    key = (live["date"], live["title"], live["time_start"], live["url"])

    # 全出力
    newlive_all.append(Template(newlive_template).render(live))
    nextlive_all.append((live["date"], Template(nextlive_template).render(live)))
    # calender_all.append(Template(calender_template).render(live))
    # mainlive_all.append(Template(mainlive_template).render(live))

    # 新規のみ: YML追記 & news個別ファイル生成
    if key not in existing_keys:
        yml_new.append(Template(yml_template).render(live))
        news_all.append(Template(news_template.replace("%%TODAY%%", today)).render(live))
        #new_news_files.append(live)
        print(f"  ✅ 新規追加: {live['date']} 『{live['title']}』")
    else:
        print(f"  ─  スキップ: {live['date']} 『{live['title']}』（既存）")

# ── lives.yml に新規分を追記 ──
if yml_new:
    with open(YML_PATH, "a", encoding="utf-8") as f:
        f.write("\n" + "\n".join(yml_new))
    print(f"\n📝 lives.yml に {len(yml_new)} 件追記しました")
else:
    print("\n📝 lives.yml: 追記なし（全件既存）")

#── news個別ファイル生成（_news/{year}/YYMMDD_ライブ名.md）──
# for live in new_news_files:
#     # ライブ日付から年を取得してフォルダを決定
#     try:
#         live_year = str(datetime.strptime(live["date"], "%Y-%m-%d").year)
#     except Exception:
#         live_year = datetime.now().strftime("%Y")
#     year_dir = os.path.join(NEWS_BASE, live_year)
#     os.makedirs(year_dir, exist_ok=True)
#     fname = f"{today_file}_{safe_filename(live['title'])}.md"
#     fpath = os.path.join(year_dir, fname)
#     rendered = Template(news_template.replace("%%TODAY%%", today)).render(live)
#     with open(fpath, "w", encoding="utf-8") as f:
#         f.write(rendered)
#     print(f"  📄 _news/{live_year}/{fname}")

# ── 従来の一括出力ファイル ──
with open(os.path.join(OUTPUT_DIR, "newlive.txt"), "w", encoding="utf-8") as f:
    f.write("\n\n".join(newlive_all))

with open(os.path.join(OUTPUT_DIR, "nextlive.txt"), "w", encoding="utf-8") as f:
    sorted_nextlive = sorted(nextlive_all, key=lambda x: x[0])
    f.write("\n\n".join(text for _, text in sorted_nextlive))

# with open(os.path.join(OUTPUT_DIR, "all_lives.yml"), "w", encoding="utf-8") as f:
#     f.write("\n".join(yml_new) if yml_new else "# 新規なし\n")

# with open(os.path.join(OUTPUT_DIR, "calender.html"), "w", encoding="utf-8") as f:
#     f.write("\n".join(calender_all))

with open(os.path.join(OUTPUT_DIR, "news.html"), "w", encoding="utf-8") as f:
    f.write("\n".join(news_all) if news_all else "<!-- 新規なし -->")

# with open(os.path.join(OUTPUT_DIR, "mainlive.html"), "w", encoding="utf-8") as f:
#     f.write("\n".join(mainlive_all))


# ── TimeTree公開カレンダー用CSV出力 ──

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


TIMETREE_PATH = os.path.join(OUTPUT_DIR, "timetree.csv")

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


with open(TIMETREE_PATH, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=TIMETREE_FIELDS)
    writer.writeheader()

    for live in lives:

        date = (live.get("date") or "").strip()

        time_start = (live.get("time_start") or "").strip()
        time_end = (live.get("time_end") or "").strip()

        # 終了時刻が未設定の場合は、開始時刻の1時間後を仮の終了時刻にする
        if not time_end and time_start:
            start_dt = datetime.strptime(
                f"{date} {time_start}",
                "%Y-%m-%d %H:%M"
            )

            from datetime import timedelta
            end_dt = start_dt + timedelta(hours=1)

            time_end = end_dt.strftime("%H:%M")

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
                f"{date} {time_end}"
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


print(f"   TimeTree CSV    : {TIMETREE_PATH}")

print("\n✨ 完了！")
print(f"   lives.yml       : {YML_PATH}")
print(f"   news個別ファイル : {NEWS_BASE}/{{year}}/")
print(f"   その他出力      : {OUTPUT_DIR}/")
print("   カレンダー表示   : _includes/schedule_calendar.html が _data/lives.yml を読み込みます")
