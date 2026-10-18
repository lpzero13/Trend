"""Descriptive data audit. Warnings never silently adjust prices or become entry filters."""
from datetime import datetime, timedelta
from models import NY
from market_calendar import CALENDAR_VERSION, calendar, session_close


def audit(bars, *, feed="unknown", adjustment="unknown", market="XNYS"):
    daily = bars.get("1D",[])
    issues = []
    if adjustment == "raw":
        issues.append({"kind":"raw_corporate_actions","message":"Rohkurse: Splits/Dividenden sind nicht bereinigt; keine automatische Maßnahmenprüfung."})
    if feed == "iex":
        issues.append({"kind":"single_venue","message":"IEX ist ein einzelner Handelsplatz, kein vollständiger US-Marktfeed."})
    sessions = {datetime.fromtimestamp(b.time,NY).date().isoformat():b for b in daily}
    missing, non_sessions, conservative = [], [], []
    if daily and market == "XNYS":
        start, end = min(sessions), max(sessions)
        # Calendar windows are bounded per year; no dependence on today's default calendar span.
        for year in range(int(start[:4]), int(end[:4])+1):
            lo,hi=max(start,f"{year}-01-01"),min(end,f"{year}-12-31")
            expected=calendar(year).sessions_in_range(lo,hi)
            missing.extend(str(day.date()) for day in expected if str(day.date()) not in sessions)
        for day,bar in sessions.items():
            close=session_close(day)
            if close is None: non_sessions.append(day)
            elif bar.end != close: conservative.append({"day":day,"storedClose":bar.end,"calendarClose":close})
        if missing: issues.append({"kind":"missing_daily_sessions","count":len(missing),"examples":missing[:10],"message":"Fehlende Tageskerzen; Liquidität, Feed und Datenabdeckung prüfen. Keine Kerzen ergänzt."})
        if non_sessions: issues.append({"kind":"non_session_bars","count":len(non_sessions),"examples":non_sessions[:10]})
        if conservative: issues.append({"kind":"daily_close_model_difference","count":len(conservative),"examples":conservative[:5]})
    jumps=[]
    for previous,current in zip(daily,daily[1:]):
        change=current.open/previous.close-1
        if abs(change)>=.25:
            jumps.append({"time":current.time,"changePct":change*100})
    if jumps:
        issues.append({"kind":"large_price_discontinuities","count":len(jumps),"examples":jumps[:10],
                       "message":"Große Kurslücken: mögliche Kapitalmaßnahme, Nachricht oder Datenfehler; kein bestätigter Split."})
    return {"version":"tori-quality-1","calendar":CALENDAR_VERSION if market=="XNYS" else "not_checked",
            "feed":feed,"adjustment":adjustment,"issues":issues,"corporateActionsVerified":False,
            "universe":"present-day; delisted coverage not established","intradaySessions":"provider-native; extended hours possible"}
