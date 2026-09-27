/* TEAM YUKIES — preview UI light/dark theme */
(() => {
  const STORAGE_KEY = "team-yukies-ui-theme";
  const THEMES = new Set(["light", "dark"]);

  function storedTheme() {
    try {
      const value = localStorage.getItem(STORAGE_KEY);
      return THEMES.has(value) ? value : "light";
    } catch {
      return "light";
    }
  }

  function updateButton(theme) {
    const button = document.querySelector("#theme-toggle");
    if (!button) return;

    const dark = theme === "dark";
    button.textContent = dark ? "LIGHT" : "DARK";
    button.setAttribute("aria-pressed", String(dark));
    button.setAttribute("aria-label", dark ? "Switch preview UI to light mode" : "Switch preview UI to dark mode");
    button.title = dark ? "라이트 모드로 전환" : "다크 모드로 전환";
  }

  function applyTheme(theme, persist = false) {
    const next = THEMES.has(theme) ? theme : "light";
    document.documentElement.dataset.uiTheme = next;
    updateButton(next);

    if (persist) {
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch {}
    }
  }

  // Apply before the page paints so a saved dark theme does not flash light first.
  applyTheme(storedTheme());

  document.addEventListener("DOMContentLoaded", () => {
    updateButton(document.documentElement.dataset.uiTheme || "light");

    const button = document.querySelector("#theme-toggle");
    if (!button) return;

    button.addEventListener("click", () => {
      const current = document.documentElement.dataset.uiTheme || "light";
      applyTheme(current === "dark" ? "light" : "dark", true);
    });
  });
})();
