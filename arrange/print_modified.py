import csv
import os
import re
import html as html_lib
from urllib.parse import urlencode, quote
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
# 公開用カレンダーUI HTML生成
# ─────────────────────────────────────────────

def build_google_calendar_url(live):
    """ライブ情報からGoogleカレンダー追加URLを作る（日本語もURLエンコード）"""
    start = format_google_cal(str(live.get("date", "")), str(live.get("time_start", "")))
    if not start:
        return ""
    end = format_google_cal(str(live.get("date", "")), str(live.get("time_end", ""))) if live.get("time_end") else start
    params = {
        "action": "TEMPLATE",
        "text": str(live.get("title", "")),
        "dates": f"{start}/{end}",
        "location": str(live.get("venue", "")),
    }
    if live.get("url"):
        params["details"] = str(live.get("url", ""))
    return "https://www.google.com/calendar/render?" + urlencode(params, quote_via=quote, safe="/:.")


def generate_calendar_html(lives_data):
    """_data/lives.ymlのデータから、JekyllにincludeできるカレンダーHTML断片を生成する"""
    import calendar
    import json

    def h(value):
        return html_lib.escape(str(value or ""), quote=True)

    now = datetime.now()
    this_month = (now.year, now.month)
    today_iso = now.strftime("%Y-%m-%d")

    # 月ごとにグループ化（今月以降のみ）
    months = {}
    for live in lives_data:
        date_str = str(live.get("date", ""))
        if not date_str:
            continue
        try:
            d = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            continue
        key = (d.year, d.month)
        if key < this_month:
            continue
        months.setdefault(key, []).append((d, live))

    sorted_months = sorted(months.keys())
    weekdays_jp = ["月", "火", "水", "木", "金", "土", "日"]

    # JS用ライブデータ（日付 → ライブ詳細リスト）
    event_map = {}
    for (_year, _month), day_lives in months.items():
        for d, live in day_lives:
            key_str = d.strftime("%Y-%m-%d")
            event_map.setdefault(key_str, []).append({
                "title": str(live.get("title", "")),
                "venue": str(live.get("venue", "")),
                "time_open": str(live.get("time_open", "")),
                "time_start": str(live.get("time_start", "")),
                "time_end": str(live.get("time_end", "")),
                "advance": str(live.get("advance", "")),
                "door": str(live.get("door", "")),
                "url": str(live.get("url", "#")),
                "streaming_url": str(live.get("streaming_url", "")),
                "streaming_price": str(live.get("streaming_price", "")),
                "google_calendar_url": build_google_calendar_url(live),
            })

    # time_startで昇順ソート（同時刻は追加順を維持）
    for key_str in event_map:
        event_map[key_str].sort(key=lambda x: x.get("time_start", "") or "")

    month_blocks = []
    for year, month in sorted_months:
        cal = calendar.monthcalendar(year, month)
        day_lives = {}
        for d, live in months[(year, month)]:
            day_lives.setdefault(d.day, []).append(live)

        rows_html = ""
        for week_idx, week in enumerate(cal):
            week_id = f"{year}-{month:02d}-w{week_idx}"
            cells = []

            for i, day in enumerate(week):
                if day == 0:
                    cells.append('<td class="schedule-day schedule-empty-day"></td>')
                    continue

                date_id = f"{year}-{month:02d}-{day:02d}"
                lives_today = sorted(day_lives.get(day, []), key=lambda x: str(x.get("time_start", "") or ""))
                class_names = ["schedule-day"]
                if i == 5:
                    class_names.append("is-saturday")
                if i == 6:
                    class_names.append("is-sunday")
                if date_id == today_iso:
                    class_names.append("is-today")
                if lives_today:
                    class_names.append("has-event")

                pills_html = ""
                for live in lives_today:
                    start = h(live.get("time_start", ""))
                    title = h(live.get("title", ""))
                    stream_icon = "🎥 " if live.get("streaming_url") else ""
                    pills_html += f'<span class="schedule-event-pill">{stream_icon}{start} {title}</span>'

                attrs = f'data-date-id="{date_id}" data-week-id="{week_id}"'
                if lives_today:
                    attrs += ' role="button" tabindex="0" aria-label="予定の詳細を開く"'
                cells.append(
                    f'<td class="{" ".join(class_names)}" {attrs}>'
                    f'<span class="schedule-day-num">{day}</span>'
                    f'{pills_html}'
                    f'</td>'
                )

            rows_html += "<tr>" + "".join(cells) + "</tr>\n"
            rows_html += (
                f'<tr class="schedule-detail-row" id="schedule-detail-{week_id}">'
                '<td colspan="7"><div class="schedule-detail-panel"><div class="schedule-detail-inner"></div></div></td>'
                '</tr>\n'
            )

        month_label = f"{year}年{month}月"
        th_html = "".join(
            f'<th class="{"is-saturday" if i == 5 else "is-sunday" if i == 6 else ""}">{day}</th>'
            for i, day in enumerate(weekdays_jp)
        )
        month_blocks.append(f"""
<section class="schedule-month-block">
  <h3 class="schedule-month-title">{month_label}</h3>
  <div class="schedule-table-scroll" aria-label="{month_label}のライブ予定">
    <table class="schedule-table">
      <thead><tr>{th_html}</tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>
</section>""")

    if month_blocks:
        all_months_html = "\n".join(month_blocks)
    else:
        all_months_html = '<p class="schedule-empty-message">現在表示できる予定はありません。</p>'

    event_map_json = json.dumps(event_map, ensure_ascii=False)
    updated = now.strftime("%Y.%m.%d %H:%M")

    fragment = """<style>
/* generated by arrange/print.py */
.intake-schedule {
  --schedule-text: #333333;
  --schedule-muted: #777777;
  --schedule-line: #dedbd3;
  --schedule-soft-line: #efede8;
  --schedule-card: rgba(255, 255, 255, 0.88);
  --schedule-accent: #cfe6da;
  --schedule-accent-deep: #60796c;
  --schedule-accent-pale: #f2f8f5;
  --schedule-sat: #5d7fa6;
  --schedule-sun: #b46a6a;
  --schedule-shadow: 0 14px 32px rgba(45, 45, 45, 0.08);
  color: var(--schedule-text);
  margin-top: 1.8rem;
}

.intake-schedule * {
  box-sizing: border-box;
}

.intake-schedule-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 1rem;
  margin-bottom: 1.2rem;
}

.intake-schedule-lead {
  margin: 0;
  color: var(--schedule-muted);
  font-size: 0.86rem;
  letter-spacing: 0.04em;
}

.intake-schedule-updated {
  color: var(--schedule-muted);
  font-size: 0.72rem;
  white-space: nowrap;
}

.schedule-month-block {
  margin: 0 0 2.4rem;
}

.schedule-month-title {
  position: relative;
  margin: 0 0 0.9rem;
  padding-left: 0.95rem;
  font-size: 1.15rem;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.schedule-month-title::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0.22em;
  width: 4px;
  height: 1.1em;
  border-radius: 999px;
  background: var(--schedule-accent);
}

.schedule-table-scroll {
  width: 100%;
  overflow-x: auto;
  padding-bottom: 0.3rem;
  -webkit-overflow-scrolling: touch;
}

.schedule-table {
  width: 100%;
  min-width: 680px;
  table-layout: fixed;
  border-collapse: separate;
  border-spacing: 0;
  background: var(--schedule-card);
  border: 1px solid var(--schedule-line);
  border-radius: 18px;
  overflow: hidden;
  box-shadow: var(--schedule-shadow);
}

.schedule-table th {
  padding: 0.72rem 0.55rem;
  border-bottom: 1px solid var(--schedule-line);
  background: #faf8f2;
  color: var(--schedule-muted);
  font-size: 0.72rem;
  font-weight: 500;
  text-align: left;
  letter-spacing: 0.14em;
}

.schedule-table th.is-saturday,
.schedule-day.is-saturday .schedule-day-num {
  color: var(--schedule-sat);
}

.schedule-table th.is-sunday,
.schedule-day.is-sunday .schedule-day-num {
  color: var(--schedule-sun);
}

.schedule-day {
  position: relative;
  height: 92px;
  padding: 0.55rem 0.5rem 0.65rem;
  vertical-align: top;
  border-right: 1px solid var(--schedule-soft-line);
  border-bottom: 1px solid var(--schedule-soft-line);
  background: rgba(255, 255, 255, 0.72);
  transition: background 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.schedule-day:nth-child(7) {
  border-right: none;
}

.schedule-empty-day {
  background: rgba(246, 244, 239, 0.48);
}

.schedule-day.has-event {
  cursor: pointer;
}

.schedule-day.has-event:hover,
.schedule-day.has-event:focus-visible {
  background: var(--schedule-accent-pale);
  outline: none;
  box-shadow: inset 0 0 0 2px var(--schedule-accent);
}

.schedule-day.is-active {
  background: var(--schedule-accent-pale);
  box-shadow: inset 0 0 0 2px var(--schedule-accent-deep);
}

.schedule-day.is-today .schedule-day-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.75em;
  height: 1.75em;
  border-radius: 999px;
  background: var(--schedule-accent);
  color: var(--schedule-text);
}

.schedule-day-num {
  display: block;
  margin-bottom: 0.42rem;
  color: var(--schedule-muted);
  font-size: 0.78rem;
  font-weight: 600;
}

.schedule-event-pill {
  display: block;
  width: 100%;
  margin: 0 0 0.24rem;
  padding: 0.18rem 0.36rem;
  border-left: 3px solid var(--schedule-accent-deep);
  border-radius: 6px;
  background: var(--schedule-accent);
  color: var(--schedule-text);
  font-size: 0.68rem;
  line-height: 1.45;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.schedule-detail-row td {
  padding: 0 !important;
  border: none !important;
  background: transparent !important;
}

.schedule-detail-panel {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.34s ease;
  background: #fffdf8;
  border-left: 1px solid var(--schedule-line);
  border-right: 1px solid var(--schedule-line);
  border-bottom: 1px solid var(--schedule-line);
}

.schedule-detail-inner {
  padding: 1.15rem 1.2rem 1.3rem;
}

.schedule-detail-date {
  margin-bottom: 0.85rem;
  color: var(--schedule-accent-deep);
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.schedule-detail-cards {
  display: grid;
  gap: 0.85rem;
}

.schedule-detail-card {
  padding: 1rem 1.05rem;
  border: 1px solid var(--schedule-line);
  border-radius: 14px;
  background: #ffffff;
}

.schedule-detail-title {
  margin-bottom: 0.55rem;
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.55;
}

.schedule-detail-row-item {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.35rem;
  color: var(--schedule-text);
  font-size: 0.82rem;
  line-height: 1.8;
}

.schedule-detail-label {
  flex: 0 0 3.2rem;
  color: var(--schedule-muted);
  font-size: 0.72rem;
  letter-spacing: 0.08em;
}

.schedule-detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 0.85rem;
}

.schedule-detail-link {
  display: inline-flex;
  align-items: center;
  gap: 0.22rem;
  padding: 0.36rem 0.72rem;
  border: 1px solid var(--schedule-accent-deep);
  border-radius: 999px;
  color: var(--schedule-accent-deep);
  background: #ffffff;
  font-size: 0.76rem;
  text-decoration: none;
  transition: background 0.18s ease, color 0.18s ease;
}

.schedule-detail-link:hover {
  color: #ffffff;
  background: var(--schedule-accent-deep);
}

.schedule-empty-message {
  color: var(--schedule-muted);
  text-align: center;
  padding: 2rem 1rem;
}

@media (max-width: 700px) {
  .intake-schedule-header {
    display: block;
  }
  .intake-schedule-updated {
    display: block;
    margin-top: 0.45rem;
  }
  .schedule-table {
    min-width: 620px;
  }
  .schedule-day {
    height: 82px;
    padding: 0.45rem 0.38rem 0.55rem;
  }
  .schedule-event-pill {
    font-size: 0.62rem;
  }
  .schedule-detail-row-item {
    display: block;
  }
  .schedule-detail-label {
    display: block;
    margin-bottom: 0.08rem;
  }
}
</style>

<div class="intake-schedule" data-intake-schedule>
  <div class="intake-schedule-header">
    <p class="intake-schedule-lead">日付をタップすると、開演時間・会場・チケット情報を確認できます。</p>
    <span class="intake-schedule-updated">generated: __UPDATED__</span>
  </div>
  __MONTHS_HTML__
</div>

<script>
(() => {
  const root = document.currentScript.previousElementSibling;
  if (!root) return;

  const EVENT_MAP = __EVENT_MAP_JSON__;
  let activeDate = null;
  let activeWeek = null;

  const esc = (value) => String(value || '').replace(/[&<>"]/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;'
  }[char]));

  const yen = (value) => value ? `¥${esc(value)}` : '';

  root.addEventListener('click', (event) => {
    const dayCell = event.target.closest('.schedule-day.has-event');
    if (!dayCell || !root.contains(dayCell)) return;
    toggleDetail(dayCell);
  });

  root.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    const dayCell = event.target.closest('.schedule-day.has-event');
    if (!dayCell || !root.contains(dayCell)) return;
    event.preventDefault();
    toggleDetail(dayCell);
  });

  function toggleDetail(dayCell) {
    const dateId = dayCell.dataset.dateId;
    const weekId = dayCell.dataset.weekId;
    const panelRow = root.querySelector(`#schedule-detail-${weekId}`);
    const panel = panelRow ? panelRow.querySelector('.schedule-detail-panel') : null;
    const inner = panel ? panel.querySelector('.schedule-detail-inner') : null;
    if (!dateId || !weekId || !panel || !inner) return;

    if (activeDate === dateId) {
      closePanel(panel);
      root.querySelectorAll('.schedule-day.is-active').forEach((td) => td.classList.remove('is-active'));
      activeDate = null;
      activeWeek = null;
      return;
    }

    if (activeWeek && activeWeek !== weekId) {
      const prevPanel = root.querySelector(`#schedule-detail-${activeWeek} .schedule-detail-panel`);
      if (prevPanel) closePanel(prevPanel);
    }

    root.querySelectorAll('.schedule-day.is-active').forEach((td) => td.classList.remove('is-active'));
    inner.innerHTML = buildDetailHtml(dateId, EVENT_MAP[dateId] || []);
    openPanel(panel);
    dayCell.classList.add('is-active');
    activeDate = dateId;
    activeWeek = weekId;
  }

  function buildDetailHtml(dateId, lives) {
    const [year, month, day] = dateId.split('-');
    const date = new Date(Number(year), Number(month) - 1, Number(day));
    const weekday = ['日', '月', '火', '水', '木', '金', '土'][date.getDay()];
    const dateLabel = `${Number(year)}/${Number(month)}/${Number(day)}(${weekday})`;

    const cards = lives.map((live) => {
      const time = live.time_open
        ? `開場 ${esc(live.time_open)} ｜ 開演 ${esc(live.time_start)}${live.time_end ? ' ｜ 終演 ' + esc(live.time_end) : ''}`
        : `開演 ${esc(live.time_start)}${live.time_end ? ' ｜ 終演 ' + esc(live.time_end) : ''}`;

      const price = live.advance && live.door
        ? `前売 ${yen(live.advance)} ｜ 当日 ${yen(live.door)}`
        : live.advance ? `前売 ${yen(live.advance)}`
        : live.door ? `当日 ${yen(live.door)}`
        : '';

      const ticketButton = live.url
        ? `<a class="schedule-detail-link" href="${esc(live.url)}" target="_blank" rel="noopener noreferrer">🎫 チケット</a>`
        : '';
      const streamButton = live.streaming_url
        ? `<a class="schedule-detail-link" href="${esc(live.streaming_url)}" target="_blank" rel="noopener noreferrer">🎥 配信${live.streaming_price ? ' ' + yen(live.streaming_price) : ''}</a>`
        : '';
      const calButton = live.google_calendar_url
        ? `<a class="schedule-detail-link" href="${esc(live.google_calendar_url)}" target="_blank" rel="noopener noreferrer">🗓️ Googleカレンダー</a>`
        : '';

      return `
        <article class="schedule-detail-card">
          <div class="schedule-detail-title">${esc(live.title)}</div>
          <div class="schedule-detail-row-item"><span class="schedule-detail-label">時間</span><span>${time}</span></div>
          ${live.venue ? `<div class="schedule-detail-row-item"><span class="schedule-detail-label">会場</span><span>${esc(live.venue)}</span></div>` : ''}
          ${price ? `<div class="schedule-detail-row-item"><span class="schedule-detail-label">料金</span><span>${price}</span></div>` : ''}
          <div class="schedule-detail-actions">${ticketButton}${streamButton}${calButton}</div>
        </article>`;
    }).join('');

    return `<div class="schedule-detail-date">${dateLabel}</div><div class="schedule-detail-cards">${cards}</div>`;
  }

  function openPanel(panel) {
    panel.style.maxHeight = panel.querySelector('.schedule-detail-inner').scrollHeight + 'px';
  }

  function closePanel(panel) {
    panel.style.maxHeight = '0';
  }
})();
</script>"""

    return (
        fragment
        .replace("__UPDATED__", h(updated))
        .replace("__MONTHS_HTML__", all_months_html)
        .replace("__EVENT_MAP_JSON__", event_map_json)
    )


def generate_calendar_preview_html(calendar_fragment, stylesheet_href="../assets/css/style.css"):
    """ローカル確認用のHTML。公開時は _includes/schedule_calendar.html と schedule.html を使う"""
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ライブスケジュール確認用</title>
  <link rel="stylesheet" href="{stylesheet_href}">
</head>
<body>
  <main class="content-section" style="max-width: 1100px; margin: 3rem auto; padding: 0 1rem;">
    <h1 class="section-title">SCHEDULE</h1>
    {calendar_fragment}
  </main>
</body>
</html>"""


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

# ── カレンダーUI生成（公開用include + 公開ページ + ローカル確認用）──
with open(YML_PATH, encoding="utf-8") as f:
    all_lives_data = yaml.safe_load(f) or []

# 既存のlives.ymlに料金系の項目がない場合でも、今回読み込んだCSVに同じライブがあれば補完する
csv_live_by_key = {
    (str(live.get("date", "")), str(live.get("title", "")), str(live.get("time_start", "")), str(live.get("url", ""))): live
    for live in lives
}
for item in all_lives_data:
    key = (str(item.get("date", "")), str(item.get("title", "")), str(item.get("time_start", "")), str(item.get("url", "")))
    csv_live = csv_live_by_key.get(key)
    if not csv_live:
        continue
    for field in ["advance", "door", "streaming_price", "streaming_url", "time_open", "time_end", "venue"]:
        if csv_live.get(field) and not item.get(field):
            item[field] = csv_live[field]

calendar_fragment = generate_calendar_html(all_lives_data)

# 1) トップページから読み込む公開用include
INCLUDES_DIR = os.path.join(PROJECT_DIR, "_includes")
os.makedirs(INCLUDES_DIR, exist_ok=True)
calendar_include_path = os.path.join(INCLUDES_DIR, "schedule_calendar.html")
with open(calendar_include_path, "w", encoding="utf-8") as f:
    f.write(calendar_fragment)

# 2) 直接アクセスできる公開用ページ /schedule/
schedule_page_path = os.path.join(PROJECT_DIR, "schedule.html")
schedule_page = """---
layout: default
title: SCHEDULE
permalink: /schedule/
---
<section class="content-section animate-on-scroll">
  <h1 class="section-title">SCHEDULE</h1>
  {% include schedule_calendar.html %}
</section>
"""
with open(schedule_page_path, "w", encoding="utf-8") as f:
    f.write(schedule_page)

# 3) 任意でブラウザ確認できるローカル確認用HTML（自動では開かない）
cal_path = os.path.join(OUTPUT_DIR, "calendar_ui.html")
preview_css = os.path.relpath(os.path.join(PROJECT_DIR, "assets", "css", "style.css"), OUTPUT_DIR).replace(os.sep, "/")
with open(cal_path, "w", encoding="utf-8") as f:
    f.write(generate_calendar_preview_html(calendar_fragment, preview_css))

print("\n✨ 完了！")
print(f"   lives.yml       : {YML_PATH}")
print(f"   news個別ファイル : {NEWS_BASE}/{{year}}/")
print(f"   公開用include   : {calendar_include_path}")
print(f"   公開用ページ     : {schedule_page_path}")
print(f"   ローカル確認用   : {cal_path}")
print(f"   その他出力      : {OUTPUT_DIR}/")