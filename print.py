import csv
import os
import re
import yaml
import webbrowser
import tempfile
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
⏰ 開場 {{ time_open }}｜開演 {{ time_start }}｜終演 {{ time_end }}
📍 {{ venue }}
🎫 {% if advance and door %}前売 ¥{{advance}}｜当日 ¥{{door}}{% elif advance %}前売 ¥{{advance}}{% elif door %}当日現金支払 ¥{{door}}{% endif %}
{% if streaming_price %}🎥 配信あり {{ streaming_url }}{% endif %}{% if preSaleStart %}
▼ {{ preSaleStart_formatted }}先行受付開始
{% elif general %}
▼ {{ general_formatted }}発売
{% else %}
▼ チケット販売中
{% endif %}{{ url }}
"""

nextlive_template = """
◤ {{date_formatted}}の予定 ◢

『{{ title }}』
⏰ 開場 {{ time_open }}｜開演 {{ time_start }}{% if time_end %}｜終演 {{ time_end }} {% endif %}
📍 {{ venue }}
🎫 {% if advance and door %}前売 ¥{{advance}}｜当日 ¥{{door}}{% elif advance %}前売 ¥{{advance}}{% elif door %}当日現金支払 ¥{{door}}{% endif %} {{url}}
{% if streaming_url %}🎥 配信 ¥{{streaming_price}} {{streaming_url}}{% endif %}
"""

yml_template = """
- date: "{{ date }}"
  title: "{{ title }}"
  venue: "{{ venue }}"
  time_open: "{{ time_open }}"
  time_start: "{{ time_start }}"
  {% if time_end %}time_end: "{{ time_end }}"{% endif %}
  {% if preSaleStart %}preSale_start: "{{ preSaleStart }}"
  preSale_end: "{{ preSaleEnd }}"{% endif %}
  {% if general %}general: "{{ general }}"{% endif %}
  url: "{{ url }}"
  {% if streaming_url %}streaming_url: "{{ streaming_url }}"{% endif %}
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
# カレンダーUI HTML生成
# ─────────────────────────────────────────────

def generate_calendar_html(lives_data):
    """lives.ymlのデータからカレンダーHTMLを生成"""

    # 月ごとにグループ化
    months = {}
    for live in lives_data:
        date_str = live.get("date", "")
        if not date_str:
            continue
        try:
            d = datetime.strptime(str(date_str), "%Y-%m-%d")
        except:
            continue
        key = (d.year, d.month)
        months.setdefault(key, []).append((d, live))

    # 月ソート
    sorted_months = sorted(months.keys())

    # 月ごとのカレンダーブロック
    month_blocks = []
    WEEKDAYS_JP = ["月", "火", "水", "木", "金", "土", "日"]

    for (year, month) in sorted_months:
        import calendar
        cal = calendar.monthcalendar(year, month)
        day_events = {}
        for d, live in months[(year, month)]:
            day_events.setdefault(d.day, []).append(live)

        rows = []
        for week in cal:
            cells = []
            for i, day in enumerate(week):
                is_sat = (i == 5)
                is_sun = (i == 6)
                if day == 0:
                    cells.append('<td class="empty"></td>')
                else:
                    day_class = "saturday" if is_sat else ("sunday" if is_sun else "")
                    events_html = ""
                    for live in day_events.get(day, []):
                        title = live.get("title", "")
                        url = live.get("url", "#")
                        time_start = live.get("time_start", "")
                        streaming = "🎥" if live.get("streaming_url") else ""
                        events_html += f'<a href="{url}" target="_blank" class="event-pill">{streaming}{time_start} {title}</a>'
                    cells.append(f'<td class="{day_class}"><span class="day-num">{day}</span>{events_html}</td>')
            rows.append("<tr>" + "".join(cells) + "</tr>")

        month_label = f"{year}年{month}月"
        month_blocks.append(f"""
<div class="month-block">
  <h2 class="month-title">{month_label}</h2>
  <table class="cal-table">
    <thead>
      <tr>
        {''.join(f'<th class="{"saturday" if i==5 else "sunday" if i==6 else ""}">{d}</th>' for i, d in enumerate(WEEKDAYS_JP))}
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</div>""")

    all_months_html = "\n".join(month_blocks)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ライブスケジュール</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@400;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #0e0e10;
    --surface: #17171b;
    --border: #2a2a32;
    --accent: #c8f060;
    --accent2: #60c8f0;
    --text: #e8e8ec;
    --muted: #6b6b80;
    --sat: #60aaff;
    --sun: #ff6b7a;
    --event-bg: #1e2a14;
    --event-border: #3a5a18;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'Shippori Mincho', serif;
    min-height: 100vh;
    padding: 2rem 1rem 4rem;
  }}

  /* ノイズテクスチャ */
  body::before {{
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 0;
    opacity: 0.5;
  }}

  header {{
    max-width: 1100px;
    margin: 0 auto 3rem;
    display: flex;
    align-items: baseline;
    gap: 1.5rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 1.5rem;
    position: relative;
    z-index: 1;
  }}

  header h1 {{
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    color: var(--accent);
  }}

  header .subtitle {{
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: var(--muted);
    letter-spacing: 0.1em;
  }}

  .calendar-wrapper {{
    max-width: 1100px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    gap: 3rem;
  }}

  .month-block {{
    animation: fadeUp 0.4s ease both;
  }}

  @keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(16px); }}
    to {{ opacity: 1; transform: translateY(0); }}
  }}

  .month-title {{
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--accent2);
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.12em;
    margin-bottom: 0.75rem;
    padding-left: 0.25rem;
    border-left: 3px solid var(--accent2);
    padding-left: 0.75rem;
  }}

  .cal-table {{
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
  }}

  .cal-table thead th {{
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    color: var(--muted);
    padding: 0.5rem 0.25rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
  }}

  .cal-table thead th.saturday {{ color: var(--sat); }}
  .cal-table thead th.sunday   {{ color: var(--sun); }}

  .cal-table tbody td {{
    vertical-align: top;
    border: 1px solid var(--border);
    padding: 0.4rem 0.4rem 0.6rem;
    min-height: 70px;
    background: var(--surface);
    transition: background 0.15s;
  }}

  .cal-table tbody td:hover {{
    background: #1c1c22;
  }}

  .cal-table tbody td.empty {{
    background: var(--bg);
    border-color: #1a1a1f;
  }}

  .cal-table tbody td.saturday .day-num {{ color: var(--sat); }}
  .cal-table tbody td.sunday .day-num   {{ color: var(--sun); }}

  .day-num {{
    display: block;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: var(--muted);
    margin-bottom: 0.3rem;
    font-weight: 500;
  }}

  .event-pill {{
    display: block;
    font-size: 0.65rem;
    line-height: 1.4;
    color: var(--accent);
    background: var(--event-bg);
    border: 1px solid var(--event-border);
    border-radius: 3px;
    padding: 0.15rem 0.35rem;
    margin-bottom: 0.25rem;
    text-decoration: none;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: background 0.15s, border-color 0.15s;
  }}

  .event-pill:hover {{
    background: #2a3d18;
    border-color: var(--accent);
    color: #d8ff70;
  }}

  footer {{
    max-width: 1100px;
    margin: 4rem auto 0;
    text-align: center;
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: var(--muted);
    letter-spacing: 0.1em;
    position: relative;
    z-index: 1;
  }}

  @media (max-width: 700px) {{
    .cal-table {{ font-size: 0.55rem; }}
    .event-pill {{ font-size: 0.55rem; }}
    header h1 {{ font-size: 1.4rem; }}
  }}
</style>
</head>
<body>
<header>
  <h1>ライブスケジュール</h1>
  <span class="subtitle">LIVE SCHEDULE — {datetime.now().strftime('%Y.%m.%d 更新')}</span>
</header>
<div class="calendar-wrapper">
{all_months_html}
</div>
<footer>generated by print.py · {datetime.now().strftime('%Y-%m-%d %H:%M')}</footer>
</body>
</html>"""
    return html


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

# ── Jekyllサイト用パス ──
YML_PATH   = os.path.join(SCRIPT_DIR, "_data", "lives.yml")   # _data/lives.yml
NEWS_BASE  = os.path.join(SCRIPT_DIR, "_news")                  # _news/{year}/YYMMDD_title.md
CSV_PATH   = os.path.join(SCRIPT_DIR, "lives.csv")

# ── ローカル確認用（ツイート原稿など） ──
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(SCRIPT_DIR, "_data"), exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")
today_file = datetime.now().strftime("%y%m%d")  # ファイル名用: 260528 形式

# CSV読み込み
with open(CSV_PATH, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    lives = list(reader)

# 既存YMLのキーを取得
existing_keys = load_yml_keys(YML_PATH)

# 出力バッファ
newlive_all  = []
nextlive_all = []
yml_new      = []   # 新規追加分のみ
calender_all = []
news_all     = []
mainlive_all = []
new_news_files = []  # 新規追加ライブ（newsファイル生成用）

for live in lives:
    live = {k: (v if v else "") for k, v in live.items()}

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
    calender_all.append(Template(calender_template).render(live))
    mainlive_all.append(Template(mainlive_template).render(live))

    # 新規のみ: YML追記 & news個別ファイル生成
    if key not in existing_keys:
        yml_new.append(Template(yml_template).render(live))
        news_all.append(Template(news_template.replace("%%TODAY%%", today)).render(live))
        new_news_files.append(live)
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

# ── news個別ファイル生成（_news/{year}/YYMMDD_ライブ名.md）──
for live in new_news_files:
    # ライブ日付から年を取得してフォルダを決定
    try:
        live_year = str(datetime.strptime(live["date"], "%Y-%m-%d").year)
    except Exception:
        live_year = datetime.now().strftime("%Y")
    year_dir = os.path.join(NEWS_BASE, live_year)
    os.makedirs(year_dir, exist_ok=True)
    fname = f"{today_file}_{safe_filename(live['title'])}.md"
    fpath = os.path.join(year_dir, fname)
    rendered = Template(news_template.replace("%%TODAY%%", today)).render(live)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(rendered)
    print(f"  📄 _news/{live_year}/{fname}")

# ── 従来の一括出力ファイル ──
with open(os.path.join(OUTPUT_DIR, "newlive.txt"), "w", encoding="utf-8") as f:
    f.write("\n\n".join(newlive_all))

with open(os.path.join(OUTPUT_DIR, "nextlive.txt"), "w", encoding="utf-8") as f:
    sorted_nextlive = sorted(nextlive_all, key=lambda x: x[0])
    f.write("\n\n".join(text for _, text in sorted_nextlive))

with open(os.path.join(OUTPUT_DIR, "all_lives.yml"), "w", encoding="utf-8") as f:
    f.write("\n".join(yml_new) if yml_new else "# 新規なし\n")

with open(os.path.join(OUTPUT_DIR, "calender.html"), "w", encoding="utf-8") as f:
    f.write("\n".join(calender_all))

with open(os.path.join(OUTPUT_DIR, "news.html"), "w", encoding="utf-8") as f:
    f.write("\n".join(news_all) if news_all else "<!-- 新規なし -->")

with open(os.path.join(OUTPUT_DIR, "mainlive.html"), "w", encoding="utf-8") as f:
    f.write("\n".join(mainlive_all))

# ── カレンダーUI生成 & ブラウザで自動表示 ──
with open(YML_PATH, encoding="utf-8") as f:
    all_lives_data = yaml.safe_load(f) or []

calendar_html = generate_calendar_html(all_lives_data)
cal_path = os.path.join(OUTPUT_DIR, "calendar_ui.html")
with open(cal_path, "w", encoding="utf-8") as f:
    f.write(calendar_html)

print(f"\n🗓️  カレンダーUIを表示します...")
webbrowser.open(f"file://{os.path.abspath(cal_path)}")

print("\n✨ 完了！")
print(f"   lives.yml     : {YML_PATH}")
print(f"   news個別ファイル: {NEWS_BASE}/{{year}}/") 
print(f"   カレンダーUI  : {cal_path}")
print(f"   その他出力    : {OUTPUT_DIR}/")
