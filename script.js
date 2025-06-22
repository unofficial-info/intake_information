// DOMが読み込まれたら実行
document.addEventListener("DOMContentLoaded", function () {
  // 必要な要素を取得
  const menuToggle = document.querySelector(".menu-toggle");
  const mainNav = document.querySelector(".main-nav");

  // メニューボタンがクリックされた時の処理
  menuToggle.addEventListener("click", function () {
    // 'is-active' というクラスを付けたり外したりする
    menuToggle.classList.toggle("is-active");
    mainNav.classList.toggle("is-active");
  });
});

// --- スクロールでふわっと表示させるアニメーション ---

// 監視対象の要素をすべて取得
const animatedSections = document.querySelectorAll(".content-section");

// Intersection Observerのオプション設定
const options = {
  root: null, // ビューポートを基準にする
  rootMargin: "0px",
  threshold: 0.1, // 要素が10%見えたらトリガー
};

// Intersection Observerのインスタンスを作成
const observer = new IntersectionObserver(handleIntersect, options);

// 各要素の監視を開始
animatedSections.forEach((section) => {
  observer.observe(section);
});

/**
 * 要素が画面に入ったり出たりしたときに実行される関数
 * @param {Array} entries - 監視対象の要素の情報の配列
 * @param {Object} observer - Observerのインスタンス
 */
function handleIntersect(entries, observer) {
  entries.forEach((entry) => {
    // isIntersectingプロパティがtrueなら、要素が画面に入ってきたということ
    if (entry.isIntersecting) {
      // is-visibleクラスを追加してアニメーションを発動
      entry.target.classList.add("is-visible");

      // 一度表示された要素は、もう監視する必要がないので監視を解除する
      observer.unobserve(entry.target);
    }
  });
}
