// チケット情報のデータ
const ticketData = [
  {
    // ↓↓↓ 日付をYYYY-MM-DD形式に
    date: "2025-08-10",
    title: "夏のファンミーティング",
    datetime_str: "2025年8月10日(日) 18:00開演", // 表示用の日時はこちらに
    place: "東京国際フォーラム",
    // ↓↓↓ 絞り込み用の情報を追加
    prefecture: "東京都",
    artists: ["ゲストA", "ゲストB"],
    url: "#",
  },
  {
    date: "2025-09-20",
    title: "アコースティックライブ Vol.5",
    datetime_str: "2025年9月20日(土) 19:00開演",
    place: "大阪 なんばHatch",
    prefecture: "大阪府",
    artists: [], // 他の出演者がいない場合は空の配列
    url: "#",
  },
  {
    date: "2025-12-31",
    title: "カウントダウンライブ 2025-2026",
    datetime_str: "2025年12月31日(火) 23:00開演",
    place: "日本武道館",
    prefecture: "東京都",
    artists: ["スペシャルゲストX", "ゲストA"],
    url: "#",
  },
  {
    date: "2026-01-15",
    title: "新春ライブツアー in 福岡",
    datetime_str: "2026年1月15日(木) 19:00開演",
    place: "福岡サンパレス",
    prefecture: "福岡県",
    artists: [],
    url: "#",
  },
];
