document.addEventListener("DOMContentLoaded", () => {
  const nextBtn = document.querySelector(".page-btn.next");

  nextBtn.addEventListener("click", (e) => {
    e.preventDefault();

    const pages = Array.from(document.querySelectorAll(".page-btn:not(.next)"));
    const activePage = document.querySelector(".page-btn.active");

    const currentIndex = pages.indexOf(activePage);
    const nextPage = pages[currentIndex + 1];

    if (nextPage) {
      window.location.href = nextPage.href;
    }
  });
});
