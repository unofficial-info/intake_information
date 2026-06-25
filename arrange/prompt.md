# 目的

以下のURLからそれぞれライブ情報を読み取り、csv形式で出力してください

# 出力形式

title,date,time_open,time_start,time_end,venue,advance,door,performer,url,streaming_url,streaming_price,preSaleStart,preSaleEnd,general

## 出力例

神保町Kakeru翔SPプラス+,2026-06-22,17:15,17:30,18:30,神保町よしもと漫才劇場,"1,500","1,800",マルセイユ／ミカボ／ピュート／インテイク／イワサキ／エグい速さ／ド天国／他,https://x.gd/ZcHrJ,https://x.gd/dDhoY,"1,300",2026-05-02T11:00:00,2026-05-07T11:00:00,2026-05-13T10:00:00
渋谷Kiwami極LIVE,2026-06-23,17:00,17:15,18:25,渋谷よしもと漫才劇場,"1,500","1,800",ダンビラムーチョ／ゆにばーす／ワラバランス／まちるだ／9番街レトロ／ソマオ・ミートボール／インテイク／他,https://x.gd/vJF5f,,,2026-05-02T11:00:00,2026-05-07T11:00:00,2026-05-13T10:00:00

# ルール

・ヘッダーは出力しないでください

・与えられたURLのページ内に情報がない項目についてはそれぞれ以下のように対処してください

1.venueの値を確認し、それぞれの劇場のURLを探索し、タイトル、日時が一致するものに関して情報を抜き出す
venue="渋谷よしもと漫才劇場"　：　https://shibuya-manzaigekijyo.yoshimoto.co.jp/schedule/
venue="神保町よしもと漫才劇場" ：　https://jimbocho-manzaigekijyo.yoshimoto.co.jp/schedule/
venue="大宮ラクーンよしもと劇場" :　https://omiya.yoshimoto.co.jp/schedule/
venue="よしもと幕張イオンモール劇場" : https://makuhari.yoshimoto.co.jp/schedule/
venue="ルミネtheよしもと" : https://lumine.yoshimoto.co.jp/schedule/

2.それでも情報がない場合は、推測はせずに空欄のまま出力する

・各URLを必ず個別に確認してください。
・前後のURLや同じ劇場・同じ月の公演情報を流用しないでください。
・劇場サイトで補完する場合は、タイトル・日付・開演時間がすべて一致した場合のみ補完してください。
・一致しない場合や確認できない場合は空欄にしてください。
・販売日時や終演時刻は、同じ劇場でも共通と判断しないでください。
・推測した値は入れないでください。
