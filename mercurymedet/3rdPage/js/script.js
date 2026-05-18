// CASES CAROUSEL
(() => {
  const slider = document.getElementById("casesCarousel");
  if (!slider) return;

  const track = slider.querySelector(".cases-track");
  const slides = Array.from(track.children);
  const prev = slider.querySelector(".carousel-control-prev");
  const next = slider.querySelector(".carousel-control-next");

  if (!track || !prev || !next || slides.length === 0) return;

  const BREAKPOINT_TABLET = 1140;
  const BREAKPOINT_MOBILE = 768;
  let index = 0;
  let perView = 3;
  let maxIndex = 0;

  function calcPerView() {
    if (window.innerWidth < BREAKPOINT_MOBILE) return 1;
    if (window.innerWidth < BREAKPOINT_TABLET) return 2;
    return 3;
  }

  function recalc() {
    perView = calcPerView();
    index = 0;
    maxIndex = Math.max(0, slides.length - perView);
    update();
  }

  function update() {
    const slideWidth = slides[0].offsetWidth + 24; // gap
    track.style.transform = `translateX(-${index * slideWidth}px)`;

    // LEFT
    if (index === 0) {
      prev.classList.add("disabled");
    } else {
      prev.classList.remove("disabled");
    }

    // RIGHT
    if (index >= maxIndex) {
      next.classList.add("disabled");
    } else {
      next.classList.remove("disabled");
    }
  }

  prev.addEventListener("click", () => {
    if (index > 0) {
      index--;
      update();
    }
  });

  next.addEventListener("click", () => {
    if (index < maxIndex) {
      index++;
      update();
    }
  });

  window.addEventListener("resize", recalc);
  recalc();
})();

// REVIEWS CAROUSEL
(() => {
  const slider = document.getElementById("reviewsCarousel");
  if (!slider) return;

  const track = slider.querySelector(".reviews-track");
  const cards = Array.from(track.children);
  const prev = slider.querySelector(".carousel-control-prev");
  const next = slider.querySelector(".carousel-control-next");

  const GAP = 24;
  let index = 0;
  let perView = 4;
  let step = 4;
  let maxIndex = 0;

  function calc() {
    if (window.innerWidth < 768) {
      perView = 1;
      step = 1;
    } else if (window.innerWidth < 1140) {
      perView = 2;
      step = 2;
    } else {
      perView = 6; // 2x2 на ПК
      step = 2;
    }

    index = 0;
    maxIndex = Math.max(0, cards.length - perView);
    update();
  }

  function update() {
    const cardWidth = cards[0].offsetWidth + GAP;
    track.style.transform = `translateX(-${index * cardWidth}px)`;

    prev.classList.toggle("disabled", index === 0);
    next.classList.toggle("disabled", index >= maxIndex);
  }

  prev.addEventListener("click", () => {
    if (index > 0) {
      index = Math.max(0, index - step);
      update();
    }
  });

  next.addEventListener("click", () => {
    if (index < maxIndex) {
      index = Math.min(maxIndex, index + step);
      update();
    }
  });

  window.addEventListener("resize", calc);
  calc();
})();

// CLIENTS
(() => {
  const grid = document.getElementById("clientsGrid");
  const prev = document.getElementById("clientsPrev");
  const next = document.getElementById("clientsNext");

  if (!grid || !prev || !next) return;

  const BREAKPOINT_MOBILE = 768;
  const allCards = Array.from(grid.children);
  let mobileIndex = 0;

  function isMobile() {
    return window.innerWidth <= BREAKPOINT_MOBILE;
  }

  // ===== ПК + планшет =====
  function rotateDesktop(direction) {
    const columns = [];

    // Создаем колонки по 2 карточки
    for (let i = 0; i < allCards.length; i += 2) {
      columns.push([allCards[i], allCards[i + 1]]);
    }

    // Вращаем колонки
    if (direction === "next") {
      columns.push(columns.shift());
    } else {
      columns.unshift(columns.pop());
    }

    // Перестраиваем массив и DOM
    const reordered = columns.flat();
    grid.innerHTML = "";
    reordered.forEach((card) => grid.appendChild(card));
    allCards.splice(0, allCards.length, ...reordered);
  }

  function renderMobile() {
    grid.innerHTML = "";
    const start = mobileIndex * 4;
    const visible = allCards.slice(start, start + 4);
    visible.forEach((card) => grid.appendChild(card));
  }

  function slideMobile(direction) {
    const totalSlides = Math.ceil(allCards.length / 4);

    if (direction === "next") {
      mobileIndex = (mobileIndex + 1) % totalSlides;
    } else {
      mobileIndex = (mobileIndex - 1 + totalSlides) % totalSlides;
    }

    renderMobile();
  }

  function handle(direction) {
    if (isMobile()) {
      slideMobile(direction);
    } else {
      rotateDesktop(direction);
    }
  }

  // События
  next.addEventListener("click", () => handle("next"));
  prev.addEventListener("click", () => handle("prev"));

  window.addEventListener("resize", () => {
    mobileIndex = 0;
    grid.innerHTML = "";

    if (isMobile()) {
      renderMobile();
    } else {
      allCards.forEach((card) => grid.appendChild(card));
    }
  });

  // Инициализация
  if (isMobile()) {
    renderMobile();
  }
})();
