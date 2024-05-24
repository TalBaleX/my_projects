let imagesBox = document.getElementsByClassName("images")[0];
let imagesBottom = imagesBox.offsetTop + imagesBox.offsetHeight;
let bottomY;
window.onscroll = function () {
  bottomY = window.scrollY + window.innerHeight;
  if (
    bottomY > imagesBox.offsetTop &&
    window.scrollY < imagesBottom &&
    imagesBox.classList.contains("transition") == false
  ) {
    console.log("box is riched");
    imagesBox.classList.add("transition");
  }
};
