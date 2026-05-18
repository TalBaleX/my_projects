const monthTitle = document.getElementById("monthTitle");
const daysContainer = document.getElementById("days");

let currentDate = new Date();

function renderCalendar(date) {
  daysContainer.innerHTML = "";

  const month = date.getMonth();
  const year = date.getFullYear();

  monthTitle.textContent = date.toLocaleDateString("ru-RU", {
    month: "long",
    year: "numeric",
  });

  const firstDay = new Date(year, month, 1).getDay() || 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  for (let i = 1; i < firstDay; i++) {
    daysContainer.innerHTML += `<div></div>`;
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const isToday =
      d === date.getDate() &&
      month === new Date().getMonth() &&
      year === new Date().getFullYear();

    daysContainer.innerHTML += `
      <div class="${isToday ? "day-selected" : ""}">${d}</div>`;
  }
}

renderCalendar(currentDate);

// dropdown behavior
const toggleBtn = document.getElementById("toggleBtn");
const calendar = document.getElementById("calendar");

toggleBtn.onclick = () => {
  calendar.classList.toggle("hidden");
};

document.getElementById("prevBtn").onclick = () => {
  currentDate.setMonth(currentDate.getMonth() - 1);
  renderCalendar(currentDate);
};

document.getElementById("nextBtn").onclick = () => {
  currentDate.setMonth(currentDate.getMonth() + 1);
  renderCalendar(currentDate);
};
