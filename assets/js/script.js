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

// --- ライブ情報セクションのスクロールページ番号表示処理 ---

// ページ番号表示のセットアップを関数化する
function setupPaginationIndicator(scrollerId) {
  const scroller = document.getElementById(scrollerId);
  const paginationId = scrollerId.replace("-scroller", "-pagination");
  const paginationIndicator = document.getElementById(paginationId);

  if (!scroller || !paginationIndicator) {
    return;
  }

  const cards = scroller.querySelectorAll(".live-card");
  const totalPages = cards.length;

  // カードが1枚以下ならページ番号表示を隠す
  if (totalPages <= 1) {
    paginationIndicator.style.display = "none";
    scroller.classList.add("is-not-scrollable");
    return;
  }

  // ページ番号を更新する関数
  const updatePagination = () => {
    let currentPage = 1;
    let minDistance = Infinity;

    // 現在、最も中央に近いカードを探して、その番号を現在のページ番号とする
    const scrollerCenter =
      scroller.getBoundingClientRect().left + scroller.clientWidth / 2;
    cards.forEach((card, index) => {
      const cardCenter =
        card.getBoundingClientRect().left + card.clientWidth / 2;
      const distance = Math.abs(scrollerCenter - cardCenter);

      if (distance < minDistance) {
        minDistance = distance;
        currentPage = index + 1;
      }
    });

    // 見つけたページ番号を表示に反映させる
    paginationIndicator.textContent = `${currentPage} / ${totalPages}`;
  };

  // ユーザーが手動でスワイプした時もページ番号を更新する
  scroller.addEventListener("scroll", updatePagination, { passive: true });

  // 初期状態を設定
  setTimeout(updatePagination, 100);
}

// 作成した関数を、それぞれのスライダーIDで呼び出す
setupPaginationIndicator("todays-live-scroller");
setupPaginationIndicator("upcoming-lives-scroller");

/*
// --- トップページのスライダー設定 ---
if (document.querySelector(".swiper-container")) {
  const swiper = new Swiper(".swiper-container", {
    loop: true,
    autoplay: {
      delay: 4000,
      disableOnInteraction: false,
    },
    pagination: {
      el: ".swiper-pagination",
      clickable: true,
    },
  });
}*/

// --- 主なライブページの開閉機能 ---
const liveCardHeaders = document.querySelectorAll(".main-live-header");

// すべてのヘッダーにクリックイベントを設定
liveCardHeaders.forEach((header) => {
  header.addEventListener("click", () => {
    // クリックされたヘッダーの親要素である .main-live-card を取得
    const card = header.closest(".main-live-card");

    // is-open クラスを付けたり外したりする
    card.classList.toggle("is-open");

    // aria-expanded の状態を更新する
    const toggleButton = header.querySelector(".main-live-toggle");
    const isExpanded = card.classList.contains("is-open");
    toggleButton.setAttribute("aria-expanded", isExpanded);
  });
});

// 新しい「配信中」スライダーにも、同じセットアップ関数を呼び出す
setupPaginationIndicator("streaming-now-scroller");

// すべてのタブ要素とパネル要素を取得
const tabs = document.querySelectorAll(".tab-item");
const panels = document.querySelectorAll(".panel-item");

// 各タブにクリックイベントを設定
tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    // 1. すべてのタブからis-activeクラスを削除
    tabs.forEach((item) => item.classList.remove("is-active"));
    // 2. クリックされたタブにis-activeクラスを追加
    tab.classList.add("is-active");

    // 3. 表示するパネルのIDを取得
    const targetPanelId = tab.getAttribute("data-tab");

    // 4. すべてのパネルを非表示にし、対象のパネルだけを表示
    panels.forEach((panel) => {
      if (panel.id === targetPanelId) {
        panel.classList.add("is-visible");
      } else {
        panel.classList.remove("is-visible");
      }
    });
  });
});

// --- おすすめ動画スライダーの設定 ---
document.querySelectorAll(".pickup-swiper").forEach(function (container) {
  new Swiper(container, {
    loop: true,

    // 自動再生を無効化
    // autoplay: false,

    pagination: {
      el: container.querySelector(".swiper-pagination"),
      clickable: true,
    },
    navigation: {
      nextEl: container.querySelector(".swiper-button-next"),
      prevEl: container.querySelector(".swiper-button-prev"),
    },

    slidesPerView: 1,
    spaceBetween: 20,
    breakpoints: {
      768: {
        slidesPerView: 2,
      },
      1024: {
        slidesPerView: 3,
      },
    },
  });
});

// --- トップページのスライダー設定 ---
// (操作対象を ".banner-slider" に限定)
if (document.querySelector(".banner-slider")) {
  const swiper = new Swiper(".banner-slider", {
    loop: true,
    autoplay: {
      delay: 4000,
      disableOnInteraction: false,
    },
    pagination: {
      el: ".banner-pagination", // (これは前回修正済み)
      clickable: true,
    },
  });
}

/*
// --- おすすめ動画スライダーの設定 ---
// (操作対象を ".video-slider" に限定)
if (document.querySelector(".video-slider")) {
  const videoSwiper = new Swiper(".video-slider", {
    loop: true,

    // (ここには autoplay の設定は一切書かない)

    navigation: {
      nextEl: ".video-slider-button-next", // (これは前回修正済み)
      prevEl: ".video-slider-button-prev",
    },
  });
}*/
