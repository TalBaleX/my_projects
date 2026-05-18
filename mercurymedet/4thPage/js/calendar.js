class Calendar {
  constructor(root, options = {}) {
    this.root = root;

    this.daysEl = root.querySelector("[data-days]");
    this.titleEl = root.querySelector("[data-title]");
    this.prevBtn = root.querySelector("[data-prev]");
    this.nextBtn = root.querySelector("[data-next]");

    // 🔥 КРИТИЧНО: проверка структуры
    if (!this.daysEl || !this.titleEl || !this.prevBtn || !this.nextBtn) {
      console.warn("Calendar skipped: invalid markup", root);
      return;
    }

    this.onSelect = options.onSelect || null;
    this.currentDate = new Date();

    this.init();
  }

  init() {
    this.render();

    this.prevBtn.addEventListener("click", () => {
      this.currentDate.setMonth(this.currentDate.getMonth() - 1);
      this.render();
    });

    this.nextBtn.addEventListener("click", () => {
      this.currentDate.setMonth(this.currentDate.getMonth() + 1);
      this.render();
    });
  }

  render() {
    if (!this.titleEl || !this.daysEl) return;

    const year = this.currentDate.getFullYear();
    const month = this.currentDate.getMonth();

    this.titleEl.textContent = this.currentDate.toLocaleDateString("ru-RU", {
      month: "long",
      year: "numeric",
    });

    this.daysEl.innerHTML = "";

    const firstDay = new Date(year, month, 1).getDay() || 7;
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = new Date();

    // пустые ячейки
    for (let i = 1; i < firstDay; i++) {
      this.daysEl.appendChild(document.createElement("div"));
    }

    // дни месяца
    for (let day = 1; day <= daysInMonth; day++) {
      const cell = document.createElement("div");
      cell.textContent = day;

      if (
        day === today.getDate() &&
        month === today.getMonth() &&
        year === today.getFullYear()
      ) {
        cell.classList.add("day-selected");
      }

      cell.addEventListener("click", () => {
        this.selectDate(day);
      });

      this.daysEl.appendChild(cell);
    }
  }

  selectDate(day) {
    const selected = new Date(
      this.currentDate.getFullYear(),
      this.currentDate.getMonth(),
      day
    );

    if (this.onSelect) {
      this.onSelect(selected);
    }

    this.render();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const mediaQuery = window.matchMedia("(max-width: 992px)");

  const toggleBtn = document.getElementById("toggleBtn");
  const calendarPopup = toggleBtn?.nextElementSibling;
  const dateInput = document.getElementById("dateInput");

  function initCalendars(isMobile) {
    document.querySelectorAll("[data-calendar]").forEach((calendarEl) => {
      const type = calendarEl.dataset.type;

      // уничтожаем старые инстансы (на будущее)
      if (calendarEl._calendar) {
        calendarEl._calendar.destroy?.();
        calendarEl._calendar = null;
      }

      if (isMobile && type === "header") {
        calendarEl._calendar = new Calendar(calendarEl, {
          onSelect(date) {
            if (dateInput) {
              dateInput.textContent = date.toLocaleDateString("ru-RU");
              calendarPopup?.classList.add("hidden");
            }
          },
        });
      }

      if (!isMobile && type === "sidebar") {
        calendarEl._calendar = new Calendar(calendarEl, {
          onSelect(date) {
            console.log("Sidebar date:", date);
          },
        });
      }
    });

    initToggle(isMobile);
  }

  function positionCalendar(toggle, calendar) {
    const a = toggle.getBoundingClientRect();
    const c = calendar.getBoundingClientRect();
    const gap = 8;

    let left = a.right - c.width;
    let top = a.bottom + gap;

    // если не влезает справа
    if (left + c.width > window.innerWidth) {
      left = window.innerWidth - c.width - 8;
    }

    // если не влезает снизу — открываем вверх
    if (top + c.height > window.innerHeight) {
      top = a.top - c.height - gap;
    }

    calendar.style.left = `${left}px`;
    calendar.style.top = `${top}px`;
  }

  function initToggle(isMobile) {
    if (!toggleBtn || !calendarPopup) return;

    toggleBtn.onclick = null;
    document.onclick = null;

    if (!isMobile) {
      calendarPopup.classList.add("hidden");
      return;
    }

    toggleBtn.onclick = (e) => {
      e.stopPropagation();

      calendarPopup.classList.toggle("hidden");

      if (!calendarPopup.classList.contains("hidden")) {
        positionCalendar(toggleBtn, calendarPopup);
      }
    };

    document.onclick = (e) => {
      if (!calendarPopup.contains(e.target)) {
        calendarPopup.classList.add("hidden");
      }
    };
  }

  // первичная инициализация
  initCalendars(mediaQuery.matches);

  // реакция на resize
  mediaQuery.addEventListener("change", (e) => {
    initCalendars(e.matches);
  });
});
