const apiUrl = "http://127.0.0.1:5500/art_db.json";
const filterOptions = [];
const dropdownFilters = document.querySelectorAll(".dropdown-menu div");
const filterSpans = document.querySelectorAll(".filter-option span");
const catalog = document.getElementsByClassName("pictures")[0];

// Make a GET request using the Fetch API
fetch(apiUrl)
  .then((response) => {
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }
    return response.json();
  })
  .then((pictures) => {
    // Process the retrieved user data
    console.log("Pictures:", pictures);

    dropdownFilters.forEach((filter) => {
      let filterOption = filter.parentNode.parentNode; // Находим предыдущего сиблинга
      if (!filterOptions.includes(filterOption.firstElementChild.innerText)) {
        filterOptions.push(filterOption.firstElementChild.innerText);
      }
      filter.addEventListener("click", function (event) {
        if (filterOption) {
          filterSpans.forEach((filterSpan, i) => {
            filterSpans[i].innerText = filterOptions[i];
          });
          filterOption.querySelector("span").innerText = filter.innerText; // Устанавливаем текст сиблинга равным тексту кнопки
          const sortKey = event.target.getAttribute("data-sort");
          console.log(sortKey);
          switch (sortKey) {
            case "low-to-high":
              pictures.sort((a, b) => a.price - b.price);
              renderPictures();
              break;
            case "high-to-low":
              pictures.sort((a, b) => b.price - a.price);
              renderPictures();
              break;
            case "a-na":
              pictures.sort((a, b) => b.available - a.available);
              renderPictures();
              break;
            case "na-a":
              pictures.sort((a, b) => a.available - b.available);
              renderPictures();
              break;
            case "a-z":
              pictures.sort((a, b) => a.title.localeCompare(b.title));
              renderPictures();
              break;
            case "z-a":
              pictures.sort((a, b) => a.title.localeCompare(b.title)).reverse();
              renderPictures();
              break;

            default:
              return;
          }
        }
      });
    });

    function renderPictures() {
      catalog.innerHTML = "";
      pictures.forEach((picture) => {
        // Проверяем, продается ли картина
        const pictureDiv = document.createElement("div");
        pictureDiv.classList.add("picture");

        const img = document.createElement("img");
        img.src = picture.link;
        img.alt = picture.name;
        pictureDiv.appendChild(img);

        if (!picture.available) {
          img.classList.add("not_available");
        }

        const infoDiv = document.createElement("div");
        infoDiv.className = "infoPicture";
        pictureDiv.appendChild(infoDiv);

        const nameDiv = document.createElement("div");
        nameDiv.textContent = picture.title;
        infoDiv.appendChild(nameDiv);

        const priceDiv = document.createElement("div");
        priceDiv.textContent = `€${picture.price} EUR`;
        infoDiv.appendChild(priceDiv);

        catalog.appendChild(pictureDiv);
      });
    }
    renderPictures();
  })
  .catch((error) => {
    console.error("Ошибашка:", error);
    catalog.innerHTML = `
      <div class="error">
        <div class="error-image"></div>
        <br>
        <span>Es tut uns nicht leid, aber die Bilder konnten nicht geladen werden</span>
      </div>
    `;
  });
