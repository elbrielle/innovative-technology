(function () {
  var query = "";
  var search = document.getElementById("course-search");
  var status = document.getElementById("search-status");

  function matches(module) {
    var text = (module.getAttribute("data-search") || module.textContent || "").toLowerCase();
    return !query || text.indexOf(query) !== -1;
  }

  function updateCourseMap() {
    var visible = 0;
    document.querySelectorAll("[data-module]").forEach(function (module) {
      module.hidden = !matches(module);
      if (!module.hidden) visible += 1;
    });
    document.querySelectorAll("[data-course-section]").forEach(function (section) {
      section.hidden = !Array.prototype.some.call(section.querySelectorAll("[data-module]"), function (module) {
        return !module.hidden;
      });
    });
    if (status) {
      status.textContent = query
        ? (visible === 1 ? "1 module matches your search." : visible + " modules match your search.")
        : "Showing all " + visible + " modules.";
    }
  }

  if (search) {
    search.addEventListener("input", function () { query = search.value.trim().toLowerCase(); updateCourseMap(); });
  }

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
