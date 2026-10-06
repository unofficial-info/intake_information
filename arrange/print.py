"""CSVを正本としてライブ一覧と、初回だけNEWSスナップショットを生成する。"""
import csv
import io
import os
from pathlib import Path
import re
import tempfile
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import uuid4

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from exports import write_exports

ROOT = Path(__file__).resolve().parent.parent
JST = timezone(timedelta(hours=9))
FIELDS = ['title', 'date', 'time_open', 'time_start', 'time_end', 'venue',
          'advance', 'door', 'performer', 'url', 'streaming_url', 'streaming_price',
          'preSaleStart', 'preSaleEnd', 'general', 'streaming_end_date', 'live_id', 'news_date']
RENAME = {'preSaleStart': 'preSale_start', 'preSaleEnd': 'preSale_end'}
WEEKDAYS = '月火水木金土日'


def date_label(value, with_time=False):
    if not value:
        return ''
    d = datetime.fromisoformat(value)
    date = f'{d.month}/{d.day}({WEEKDAYS[d.weekday()]})'
    return f'{date} {d:%H:%M}' if with_time else f'{d.year}/{date}'


def context(row):
    result = dict(row)
    result['date_formatted'] = date_label(row['date'])
    for field in ('preSaleStart', 'preSaleEnd', 'general'):
        result[field + '_formatted'] = date_label(row[field], True)
    def calendar(title, start, end, location):
        return 'https://www.google.com/calendar/render?' + urlencode({
            'action': 'TEMPLATE', 'text': title, 'dates': f'{start}/{end}', 'location': location})
    def stamp(value):
        return value.replace('-', '').replace(':', '')
    start = stamp(row['date'] + 'T' + row['time_start'] + ':00') if row['time_start'] else stamp(row['date'])
    end = stamp(row['date'] + 'T' + row['time_end'] + ':00') if row['time_end'] else start
    result['calendar_url'] = calendar(row['title'], start, end, row['venue'])
    result['presale_calendar_url'] = calendar('【先行】' + row['title'], stamp(row['preSaleStart']), stamp(row['preSaleEnd'] or row['preSaleStart']), row['url'])
    result['general_calendar_url'] = calendar('【チケ発】' + row['title'], stamp(row['general']), stamp(row['general']), row['url'])
    return result


def load_csv(path, today):
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)) or not {'title', 'date', 'venue'}.issubset(headers):
            raise ValueError('CSVヘッダーの重複、または必須列(title/date/venue)の不足')
        if set(headers) - set(FIELDS):
            raise ValueError(f'未対応のCSV列: {set(headers) - set(FIELDS)}')
        if not {'live_id', 'news_date'}.issubset(headers):
            raise ValueError('CSVが旧形式です。live_id・news_date列を含む最新版を使用してください。既存IDを失うため、列を空欄で追加せずバックアップから復元してください')
        rows = []
        ids, keys = set(), set()
        for line, raw in enumerate(reader, 2):
            if None in raw:
                raise ValueError(f'CSV {reader.line_num}行: 列数がヘッダーの{len(headers)}列より多いです。カンマを含む値は二重引用符で囲んでください')
            # 末尾の任意列は省略可能。途中の列の区切りは省略できません。
            row = {field: (raw.get(field) or '').strip() for field in FIELDS}
            for field in ('title', 'date', 'venue'):
                if not row[field]:
                    raise ValueError(f'CSV {line}行: {field} が空です')
            for field in ('date', 'news_date', 'streaming_end_date'):
                value = row[field]
                if value and not (field == 'news_date' and value == '-'):
                    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                        raise ValueError(f'CSV {line}行: {field} は YYYY-MM-DD 形式です')
                    datetime.strptime(value, '%Y-%m-%d')
            if row['news_date'] not in ('', '-') and row['news_date'] > today:
                raise ValueError(f'CSV {line}行: NEWSの未来日予約は未対応です。公開日に実行してください')
            for field in ('time_open', 'time_start', 'time_end'):
                if row[field]:
                    if not re.fullmatch(r'\d{2}:\d{2}', row[field]):
                        raise ValueError(f'CSV {line}行: {field} は HH:MM 形式です')
                    datetime.strptime(row[field], '%H:%M')
            for field in ('preSaleStart', 'preSaleEnd', 'general'):
                if row[field]:
                    row[field] = datetime.strptime(row[field], '%Y-%m-%dT%H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S')
            if '{%' in ''.join(row.values()) or '{{' in ''.join(row.values()):
                raise ValueError(f'CSV {line}行: Liquid構文は入力できません')
            row['live_id'] = row['live_id'] or uuid4().hex
            if not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}', row['live_id']):
                raise ValueError(f'CSV {line}行: live_id は英数字・ハイフン・アンダースコアのみです')
            key = tuple(row[k] for k in ('date', 'title', 'time_start', 'venue'))
            if row['live_id'] in ids or key in keys:
                raise ValueError(f'CSV {line}行: IDまたは同一公演の重複があります')
            ids.add(row['live_id'])
            keys.add(key)
            row['news_date'] = row['news_date'] or today
            rows.append(row)
    if not rows:
        raise ValueError('空のCSVで全ライブを削除することはできません')
    return rows


def news_index(root):
    index = {}
    for path in (root / '_news').rglob('*.md'):
        text = path.read_text(encoding='utf-8')
        if not text.startswith('---\n'):
            continue
        lines = text.splitlines()
        try:
            end = lines.index('---', 1)
        except ValueError:
            raise ValueError(f'NEWSのfront matterが閉じられていません: {path}')
        meta = yaml.safe_load('\n'.join(lines[1:end])) or {}
        live_id = meta.get('live_id')
        if live_id:
            if live_id in index:
                raise ValueError(f'NEWSのlive_id重複: {live_id}')
            index[live_id] = path
    return index


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == content:
        return
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(content)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def news_path(root, row, reserved):
    """公演名を使い、既存記事・今回生成する記事との衝突を避ける。"""
    title = re.sub(r'[\\/:*?"<>|#%\x00-\x1f\x7f]', '_', row['title'])
    title = title.strip(' .')[:60] or 'ライブ'
    directory = root / '_news' / row['news_date'][:4]
    stem = row['news_date'].replace('-', '')[2:] + '_' + title
    path = directory / (stem + '.md')
    if path.exists() or path in reserved:
        suffix = row['date'].replace('-', '') + '_' + (row['time_start'].replace(':', '') or '時刻未定')
        stem += '_' + suffix
        path = directory / (stem + '.md')
        number = 2
        while path.exists() or path in reserved:
            path = directory / (stem + f'_{number}.md')
            number += 1
    return path


def generate(root=ROOT, today=None):
    today = today or datetime.now(JST).strftime('%Y-%m-%d')
    rows = load_csv(root / 'arrange/lives.csv', today)
    yml_path = root / '_data/lives.yml'
    existing_lives = (yaml.safe_load(yml_path.read_text(encoding='utf-8')) or []) if yml_path.exists() else []
    existing_ids = {live.get('live_id') for live in existing_lives}
    new_lives = [row for row in rows if row['live_id'] not in existing_ids]
    known = news_index(root)
    env = Environment(loader=FileSystemLoader(Path(__file__).parent / 'templates'),
                      autoescape=True, undefined=StrictUndefined, keep_trailing_newline=True)
    template = env.get_template('live_news.html.j2')
    articles = {}
    for row in rows:
        if row['news_date'] == '-' or row['live_id'] in known:
            continue
        date = datetime.strptime(row['date'], '%Y-%m-%d')
        meta = {'layout': 'post', 'date': row['news_date'] + ' 00:00:00 +0900',
                'category': 'LIVE', 'title': f'【{date.month}/{date.day}】{row["title"]}【出演決定】',
                'live_id': row['live_id']}
        path = news_path(root, row, articles)
        articles[path] = '---\n' + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + '---\n\n' + template.render(context(row))
    data = [{RENAME.get(k, k): v for k, v in row.items() if (v or k in ('title', 'date', 'venue', 'time_open', 'time_start', 'url')) and k != 'news_date'} for row in rows]
    csv_buffer = io.StringIO(newline='')
    writer = csv.DictWriter(csv_buffer, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    # 全ての解析・レンダリングを完了してから書き込む。CSVのID/日付を最初に保存し、
    # 途中中断後も同じIDで再実行できるようにする。生成済み記事は常に変更しない。
    with tempfile.TemporaryDirectory() as temp:
        stage = Path(temp)
        write_exports([context(row) for row in rows], stage, new_lives=new_lives)
        atomic_write(root / 'arrange/lives.csv', csv_buffer.getvalue().encode('utf-8'))
        for path, text in articles.items():
            atomic_write(path, text.encode('utf-8'))
        atomic_write(root / '_data/lives.yml', yaml.safe_dump(data, allow_unicode=True, sort_keys=False).encode('utf-8'))
        for path in stage.iterdir():
            atomic_write(root / 'arrange/output' / path.name, path.read_bytes())
        preview = '\n'.join(articles.values()) if articles else '<!-- 新規なし -->'
        atomic_write(root / 'arrange/output/news.html', preview.encode('utf-8'))
    print(f'ライブ {len(rows)} 件を同期 / NEWS {len(articles)} 件を新規生成 / TimeTree {len(new_lives)} 件を出力')
    for path in articles:
        print(path.relative_to(root))


if __name__ == '__main__':
    try:
        generate()
    except (ValueError, OSError, yaml.YAMLError) as exc:
        raise SystemExit(f'生成を中止しました: {exc}')
