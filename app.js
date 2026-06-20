// Lightbox: open a lesson's real HTML in an iframe, lazy-loaded on open.
(function () {
  var lb = document.getElementById("lightbox");
  var frame = document.getElementById("lb-frame");
  var titleEl = document.getElementById("lb-title");
  var commonsEl = document.getElementById("lb-commons");
  var lastFocus = null;

  function open(btn) {
    lastFocus = btn;
    var slug = btn.getAttribute("data-slug");
    titleEl.textContent = btn.getAttribute("data-title") || "Lesson";
    var commons = btn.getAttribute("data-commons") || "#";
    commonsEl.setAttribute("href", commons);
    commonsEl.style.display = commons && commons !== "#" ? "" : "none";
    frame.src = "lessons/" + slug + ".html";   // lazy: only set on open
    lb.hidden = false;
    document.documentElement.style.overflow = "hidden";
    document.querySelector(".lightbox__close").focus();
  }

  function close() {
    lb.hidden = true;
    frame.src = "about:blank";
    document.documentElement.style.overflow = "";
    if (lastFocus) lastFocus.focus();
  }

  document.addEventListener("click", function (e) {
    var opener = e.target.closest(".card__open");
    if (opener) { open(opener); return; }
    if (e.target.closest("[data-close]")) close();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !lb.hidden) close();
  });

  // a lesson posts its title on load; keep the bar in sync when an in-lesson
  // cross-link (e.g. the Piskel hub nav bar) navigates the iframe to a sibling.
  window.addEventListener("message", function (e) {
    if (e.data && e.data.t === "lesson" && !lb.hidden && e.data.title) {
      titleEl.textContent = e.data.title;
    }
  });
})();
