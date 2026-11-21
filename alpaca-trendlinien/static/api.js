async function apiFetch(input, options) {
  try {
    return await fetch(input, options);
  } catch (error) {
    throw new Error(
      "Verbindung zum lokalen Tori-Server fehlgeschlagen. Bitte Start-Tori.ps1 starten und anschließend mit ↻ erneut laden.",
      { cause: error },
    );
  }
}
if (typeof document !== "undefined" && typeof document.addEventListener === "function") {
  document.addEventListener("click", (ev) => {
    document.querySelectorAll("details.nav-more[open]").forEach((el) => {
      if (!el.contains(ev.target)) el.removeAttribute("open");
    });
  });
}
