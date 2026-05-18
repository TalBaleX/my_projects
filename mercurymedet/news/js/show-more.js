document.addEventListener("DOMContentLoaded", () => {
  const cards = document.querySelectorAll(".news-card");
  const showMoreBtn = document.getElementById("showMore");

  const STEP = 9;
  let visibleCount = STEP;

  // Скрываем все карточки
  cards.forEach((card) => (card.style.display = "none"));

  // Функция показа карточек
  function showCards() {
    for (let i = 0; i < visibleCount && i < cards.length; i++) {
      cards[i].style.display = "flex";
    }

    // Если все карточки показаны — скрываем кнопку
    if (visibleCount >= cards.length) {
      showMoreBtn.style.display = "none";
    }
  }

  // Первый показ
  showCards();

  // Кнопка "Показать ещё"
  showMoreBtn.addEventListener("click", () => {
    visibleCount += STEP;
    showCards();
  });
});
