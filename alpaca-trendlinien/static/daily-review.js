(() => {
  const byId = (id) => document.getElementById(id);
  const dateTime = new Intl.DateTimeFormat("de-DE", {
    dateStyle: "short", timeStyle: "short", timeZone: "Europe/Berlin",
  });
  const price = new Intl.NumberFormat("de-DE", { style: "currency", currency: "USD" });
  const changes = {
    first_report: "Erster Bericht", no_comparison: "Kein Vergleichsstand",
    new: "Neu auf der Liste", redrawn: "Neue rote Linie",
    closer: "Näher an Rot", farther: "Weiter von Rot entfernt", unchanged: "Kaum verändert",
  };
  const universes = {
    nasdaq100: "Nasdaq-100", sp500: "S&P 500", dow30: "Dow Jones", sp100: "S&P 100",
    russell1000: "Russell 1000", russell2000: "Russell 2000", dow_plus70: "Dow + 70",
  };

  function candleTime(value) {
    return value == null ? "fehlt" : dateTime.format(new Date(value * 1000));
  }

  function row(candidate) {
    const tr = document.createElement("tr");
    tr.insertCell().textContent = candidate.symbol;
    const dailyRed = candidate.dailyRed == null ? "" : " · Tagesrot " + price.format(candidate.dailyRed);
    tr.insertCell().textContent = candidate.reason + (candidate.qualified ? " Beide Linien qualifiziert." : " Aufbau vorläufig.")
      + " Rot " + price.format(candidate.red) + " · Grün " + price.format(candidate.green) + dailyRed;
    tr.insertCell().textContent = changes[candidate.change] || "—";
    const earlier = !candidate.complete4hClose || !candidate.completeDailyClose ? " · Teilstand" : "";
    tr.insertCell().textContent = "4h " + candleTime(candidate.closedAt) + " · 1D "
      + candleTime(candidate.dailyClosedAt) + earlier;
    const link = document.createElement("a");
    link.href = candidate.chartPath;
    link.textContent = candidate.symbol + " im Chart öffnen";
    tr.insertCell().append(link);
    return tr;
  }

  async function show() {
    const status = byId("daily-review-status");
    try {
      const response = await apiFetch("/api/workbench/daily-review");
      if (!response.ok) throw new Error("Die Abend-Watchlist lässt sich gerade nicht laden.");
      const { report } = await response.json();
      if (!report) {
        status.textContent = "Die erste Abend-Watchlist steht noch aus.";
        return;
      }
      const counts = report.coverage;
      const checked = (counts.candidate || 0) + (counts.no_candidate || 0);
      const previous = report.previousSession ? " · Vergleich mit " + report.previousSession : "";
      const scope = report.universes.map((key) => universes[key] || key).join(", ");
      const excluded = Object.values(counts).reduce((sum, count) => sum + count, 0) - checked;
      status.textContent = scope + " · Handelssitzung " + report.session + " · " + checked + " geprüft · "
        + report.candidates.length + " zur Sichtprüfung · " + excluded + " ausgelassen" + previous;
      byId("daily-review-table").hidden = !report.candidates.length;
      byId("daily-review-rows").replaceChildren(...report.candidates.map(row));
      const issues = Object.entries(report.issues);
      if (counts.no_local_history) issues.unshift(["Ohne lokale Kurshistorie", counts.no_local_history + " Symbole"]);
      byId("daily-review-issues").hidden = !issues.length;
      byId("daily-review-issues-list").replaceChildren(...issues.map(([symbol, reason]) => {
        const li = document.createElement("li");
        li.textContent = symbol + " · " + reason;
        return li;
      }));
    } catch (error) {
      status.textContent = error.message;
    }
  }

  show();
})();
