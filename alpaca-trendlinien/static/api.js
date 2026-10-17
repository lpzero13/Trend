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
