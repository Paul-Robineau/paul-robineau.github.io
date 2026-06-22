/* Light / Dark / Auto theme switch.
   The only script on the site. First-party, no network, no tracking:
   it just records your preference in localStorage and sets a data-theme
   attribute that the stylesheet reacts to. "Auto" follows the OS setting. */
(function () {
  "use strict";
  var root = document.documentElement;
  var KEY = "theme"; // stored value: "light" | "dark" | (absent = auto)

  function apply(mode) {
    if (mode === "light" || mode === "dark") {
      root.setAttribute("data-theme", mode);
    } else {
      root.removeAttribute("data-theme");
    }
  }

  function saved() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }

  // Run immediately (script is in <head>) so there is no flash of the
  // wrong theme before the page paints.
  apply(saved());

  function wire() {
    var btn = document.getElementById("theme-toggle");
    if (!btn) return;
    var order = ["auto", "light", "dark"];
    var labels = { auto: "Auto", light: "Light", dark: "Dark" };

    function current() { return saved() || "auto"; }

    function render() {
      var m = current();
      btn.setAttribute("data-mode", m);
      btn.setAttribute("aria-label", "Colour theme: " + labels[m] + " (click to change)");
      btn.title = "Theme: " + labels[m];
    }

    btn.addEventListener("click", function () {
      var next = order[(order.indexOf(current()) + 1) % order.length];
      try {
        if (next === "auto") localStorage.removeItem(KEY);
        else localStorage.setItem(KEY, next);
      } catch (e) {}
      apply(next === "auto" ? null : next);
      render();
    });

    btn.hidden = false; // reveal only now that it actually works
    render();
  }

  // Reading time: count the words in a post body and fill its meta slot.
  // ~200 words/minute, rounded up, minimum 1. Progressive enhancement: if JS
  // is off the slot just stays empty.
  function readingTime() {
    var body = document.querySelector(".post__body");
    var slot = document.querySelector("[data-reading-time]");
    if (!body || !slot) return;
    var words = (body.textContent.trim().match(/\S+/g) || []).length;
    slot.textContent = " · " + Math.max(1, Math.round(words / 200)) + " min read";
  }

  function init() { wire(); readingTime(); }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
