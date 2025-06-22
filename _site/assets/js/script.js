// --- スクロールでふわっと表示させるアニメーション ---

// ↓↓↓ 監視対象を新しいクラス名に変更
const animatedTargets = document.querySelectorAll(".animate-on-scroll");

// Intersection Observerのオプション設定
const options = {
  root: null, // ビューポートを基準にする
  rootMargin: "0px",
  threshold: 0.1, // 要素が10%見えたらトリガー
};

/**
 * 要素が画面に入ったり出たりしたときに実行される関数
 * @param {Array} entries - 監視対象の要素の情報の配列
 * @param {Object} observer - Observerのインスタンス
 */

const observer = new IntersectionObserver(handleIntersect, options);

// ↓↓↓ 変数名を変更
animatedTargets.forEach((target) => {
  observer.observe(target);
});

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

// --- メニューのリンクをクリックしたら、メニューを閉じる処理 ---

// すべてのメニュー項目（<a>タグ）を取得
const navLinks = document.querySelectorAll(".nav_item a");

// メニューを開閉するためのチェックボックス（<input>タグ）を取得
const drawerInput = document.getElementById("drawer_input");

// 見つけてきた全てのメニューリンクに対して、処理を追加
navLinks.forEach(function (link) {
  // 各リンクがクリックされた時の動作を設定
  link.addEventListener("click", function () {
    // チェックボックスのチェックを強制的に外す
    drawerInput.checked = false;
  });
});
