const burger = document.querySelector(".burger");
burger.addEventListener("click", burgerAppear);
function burgerAppear() {
  const overlay = document.createElement("div");
  const mobileMenu = document.createElement("div");

  overlay.className = "overlay";

  mobileMenu.innerHTML = `
  <div class="container-nav-mobile">
    <div><a href="/index.html">home</a></div>
    <div><a href="/available-art.html">available art</a></div>
    <div><a href="/about-me.html">about me</a></div>
    <div><a href="contacts.html">contacts</a></div>
  </div>
  `;
  mobileMenu.classList = "nav mobile";

  document.body.appendChild(overlay);
  document.body.appendChild(mobileMenu);
  overlay.addEventListener("click", burgerDisappear);
}
function burgerDisappear() {
  const overlay = document.querySelector(".overlay");
  const mobileMenu = document.querySelector(".nav.mobile");
  overlay.remove();
  mobileMenu.remove();
}
