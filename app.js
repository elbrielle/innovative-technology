(function () {
  var query = "";
  var filter = "all";
  var search = document.getElementById("course-search");
  var buttons = Array.prototype.slice.call(document.querySelectorAll("[data-filter]"));

  function matches(card) {
    var text = (card.getAttribute("data-search") || card.textContent || "").toLowerCase();
    var role = card.getAttribute("data-role");
    var state = card.getAttribute("data-state");
    var filtered = filter === "all" || role === filter || (filter === "optional" && (state === "optional" || state === "parked"));
    return filtered && (!query || text.indexOf(query) !== -1);
  }

  function updateCourseMap() {
    document.querySelectorAll("[data-module]").forEach(function (module) {
      var cards = Array.prototype.slice.call(module.querySelectorAll(".item-card"));
      cards.forEach(function (card) { card.hidden = !matches(card); });
      var moduleText = (module.getAttribute("data-search") || "").toLowerCase();
      var moduleMatch = filter === "all" && query && moduleText.indexOf(query) !== -1;
      module.hidden = !moduleMatch && cards.length > 0 && !cards.some(function (card) { return !card.hidden; });
    });
  }

  if (search) {
    search.addEventListener("input", function () { query = search.value.trim().toLowerCase(); updateCourseMap(); });
  }
  buttons.forEach(function (button) {
    button.addEventListener("click", function () {
      filter = button.getAttribute("data-filter") || "all";
      buttons.forEach(function (candidate) { candidate.classList.toggle("is-active", candidate === button); });
      updateCourseMap();
    });
  });

  document.querySelectorAll(".enhanceable_content.tabs").forEach(function (tabs, groupIndex) {
    var links = Array.prototype.slice.call(tabs.querySelectorAll(":scope > ul:first-child a[href^='#']"));
    if (!links.length) return;
    var panels = links.map(function (link) { return document.getElementById(link.getAttribute("href").slice(1)); }).filter(Boolean);
    if (!panels.length) return;
    function show(index) {
      panels.forEach(function (panel, panelIndex) { panel.hidden = panelIndex !== index; });
      links.forEach(function (link, linkIndex) {
        link.setAttribute("role", "tab");
        link.setAttribute("aria-selected", linkIndex === index ? "true" : "false");
        link.setAttribute("tabindex", linkIndex === index ? "0" : "-1");
      });
    }
    links.forEach(function (link, index) {
      link.addEventListener("click", function (event) { event.preventDefault(); show(index); });
      link.addEventListener("keydown", function (event) {
        if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
        event.preventDefault();
        var next = (index + (event.key === "ArrowRight" ? 1 : links.length - 1)) % links.length;
        show(next); links[next].focus();
      });
    });
    tabs.querySelector(":scope > ul:first-child").setAttribute("role", "tablist");
    tabs.setAttribute("data-tab-group", String(groupIndex));
    show(0);
  });
})();
