# インテイク非公式 information

お笑いコンビ「インテイク」のライブ・チケット・配信・ニュースをまとめる非公式情報サイトです。Jekyll で静的ページを生成し、GitHub Actions から GitHub Pages に公開しています。

[公開サイト](https://unofficial-info.github.io/intake_information/)

## ローカルで確認する

Ruby と Bundler が必要です。GitHub Actions では Ruby 3.1 を使用しています。依存 gem のバージョンは `Gemfile.lock` で管理しています。

```sh
bundle install
bundle exec jekyll serve
```

ブラウザで <http://127.0.0.1:4000/intake_information/> を開きます。終了は `Ctrl + C` です。

公開用ファイルの生成だけを行う場合：

```sh
bundle exec jekyll build
```

生成先は `_site/` です。直接編集せず、元の HTML・Markdown・YAML・SCSS を修正してください。`_config.yml` の変更後はサーバーを再起動します。今日のライブやチケット発売情報などはビルド時刻を使うため、日付や時刻が変わった状態を確認する場合も再ビルドしてください。タイムゾーンは `Asia/Tokyo` です。

## 更新したい内容と編集先

| 内容 | 編集先 |
| --- | --- |
| ライブ日程・会場・料金・チケット・配信 | `arrange/lives.csv`（変換で `_data/lives.yml` を生成） |
| ニュース記事 | `_news/年/` 内の Markdown |
| 「主なライブ」の紹介・開催情報 | `_main_lives/` 内の Markdown |
| コンビ・メンバーのプロフィール | `_data/profiles.yml` |
| カレンダーのライブ以外の予定 | `_data/events.yml` |
| おすすめ動画 | `_data/videos.yml` |
| バナー画像とリンク | `_data/banners.yml`、`assets/images/` |
| トップページのラジオ・最終手動更新日 | `index.html` |
| 動画タブの埋め込み | `_includes/video_section.html` |

バナー部品は `_includes/banner_slider.html` にありますが、現在のトップページでは読み込まれていません。データだけ変更してもトップページには表示されません。

### ライブを追加する

`arrange/lives.csv` に行を追加し、次のコマンドを1回実行します。

```sh
.venv/bin/python arrange/print.py
```

新規行の `live_id`・`news_date` は空欄で構いません。初回実行時にIDと日本時間の当日が補完され、`_data/lives.yml` と個別NEWSが生成されます。既存行の修正では `live_id` を変更しないでください。生成済みNEWSは当時の記録として保持されます。NEWSを作らない場合は `news_date` に `-` を入力します。

初回セットアップと詳しい運用は [IMPLEMENTATION_NOTES.md](IMPLEMENTATION_NOTES.md) を参照してください。

### NEWS を追加する

`_news/2026/261001_記事名.md` のように年別フォルダへ作成します。表示順はファイル名ではなく、冒頭の `date` が基準です。

```markdown
---
layout: post
date: 2026-10-01 12:00:00 +0900
category: "LIVE"
title: "【10/20】ライブ名【出演決定】"
---

ここに本文を記入します。
```

既存のカテゴリは `LIVE`・`TICKET`・`MEDIA`・`CONTEST` です。新規ライブの出演告知はCSVから自動生成します。上記の手動作成は、それ以外のお知らせや訂正記事で使用します。

### 主なライブを編集する

`_main_lives/` の Markdown に紹介文と `summary` を記入します。ファイル名の先頭の番号で一覧順を管理します。現在は `output: false` のため、個別ページは生成せず `main-lives.html` の開閉式カードに表示します。

## ファイル構成

| ファイル・フォルダ | 役割 |
| --- | --- |
| `index.html` | トップページ |
| `live.html` | ライブ一覧・絞り込み・並び替え |
| `news.html`、`news/` | NEWS 一覧、手動カテゴリページ |
| `profile.html`、`main-lives.html`、`schedule.html` | プロフィール、主なライブ、カレンダー |
| `_config.yml` | URL・タイムゾーン・コレクション・ページ送りの設定 |
| `_data/` | 各ページで共有する YAML データ |
| `_includes/` | ヘッダー、各セクション、記事表示、`pagination.html` などの部品 |
| `_layouts/` | 共通の骨格、記事・カテゴリ一覧などのレイアウト |
| `assets/css/style.scss` | SCSS の入口。Jekyll が `style.css` に変換 |
| `assets/css/partials/` | 基本・共通部品・ページ別・スマートフォン向けのスタイル |
| `assets/js/script.js` | メニュー、表示アニメーション、開閉、動画タブ、Swiper の制御 |
| `assets/images/` | 写真・バナー・アイコン |
| `arrange/` | CSV から更新用データや告知原稿を作る補助ツール |
| `.github/workflows/jekyll.yml` | ビルド・動画更新・公開のワークフロー |

CSS は `style.scss` に記載した順番で読み込み、最後の `_responsive.scss` で幅 767px 以下の表示を調整します。同じセレクタやプロパティを整理する際は、後勝ちの上書きや詳細度を確認してください。カレンダーや LIVE 一覧など、一部のスタイル・スクリプトは各 HTML 内にもあります。

## 自動更新と公開

- `main` ブランチへの push、毎日 **日本時間 0:10**（UTC 15:10）、Actions の手動実行が契機です。定期実行は遅れる場合があります。
- YouTube API から最新動画 ID を取得し、ビルド用の `_includes/video_section.html` を更新します。リポジトリの Secret `YOUTUBE_API_KEY` が必要です。この変更は元ファイルへコミットされません。
- Jekyll で `_site/` を生成し、GitHub Pages に公開します。
- フォント、Font Awesome、Swiper、埋め込み動画などは外部サービスから読み込みます。

## CSV 補助ツール

`arrange/print.py` はCSVからライブ一覧を同期し、新規ライブのNEWSを自動作成します。SNS原稿・確認用HTML・TimeTree CSVも `arrange/output/` に出力します。TimeTree CSVはその回の新規追加分のみで、新規なしの再実行時はヘッダーだけになります。Python 3.9以上が必要です。

```sh
python3 -m venv .venv
.venv/bin/pip install -r arrange/requirements.txt
.venv/bin/python arrange/print.py
```

CSV・YAML・新規NEWS・補助出力の差分を確認し、まとめてコミットしてください。GitHub Actionsは生成済みデータをビルドする既存の流れを維持しています。CSV変換はpush前にローカルで実行します。

## 現在の確認事項

ビルドは完了しますが、既存のページ生成設定には以下の警告があります。

- 自動生成用の `autopage_collection` レイアウトが存在しません。
- `news/` の手動カテゴリページと AutoPages が一部の同じ URL に出力しています。

生成ページやページ送りの仕様に関わるため、整理時は公開ページへの影響を確認してから変更してください。
