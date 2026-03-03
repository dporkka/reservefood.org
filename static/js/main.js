document.addEventListener("DOMContentLoaded", function () {
  var nav = document.getElementById("main-nav");
  var toggle = nav ? nav.querySelector(".nav-toggle") : null;

  if (!nav || !toggle) return;

  toggle.addEventListener("click", function () {
    var expanded = toggle.getAttribute("aria-expanded") === "true";
    toggle.setAttribute("aria-expanded", String(!expanded));
    nav.classList.toggle("nav-open", !expanded);
  });
});
