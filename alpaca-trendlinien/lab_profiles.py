"""Preregistered research profiles. Reference criteria are never rewritten."""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime
import math
import re

from datasets import digest
from models import DataError
from tori_entries import EntryScanner, atr, check
from trendlines import pair, rules_for, touch

VERSION = "tori-lab-1"
PROFILES = {
    "reference":{"label":"Tori-Referenz","description":"Unveränderte strenge Einstiegskriterien"},
    "baseline":{"label":"Grundausbruch / Grundbestätigung","description":"Technische Struktur und positives Risiko; Qualität nur messen"},
    "daily":{"label":"Grundsignal + Tageskontext","description":"Bestätigte Tagesstruktur zusätzlich verlangen"},
    "contacts3":{"label":"Grundsignal + drei Kontakte","description":"Mindestens drei eigenständige Kontakte beider Linien"},
    "momentum":{"label":"Grundsignal + Momentum","description":"Körper/ATR/Schlussposition zusätzlich verlangen"},
    "risk":{"label":"Grundsignal + enger Safety-Abstand","description":"Prozent- und ATR-Abstand zusätzlich begrenzen"},
    "room":{"label":"Grundsignal + Raum","description":"Bekannten Widerstand berücksichtigen; unbekannt bleibt unbekannt"},
    "retest_hold":{"label":"Tori mit eigener Retestbestätigung","description":"Beim Retest Halten statt Ausbruchskörper verlangen"},
    "atr_contacts":{"label":"Grundsignal mit ATR-Kontaktzone","description":"Explizite alternative Geometrie, kein Überschreiben der Referenz"},
    "zone_measure":{"label":"Feste Kontaktzone · Messung","description":"Identische Grundsignale und Anker; ATR-Zone nur als Zusatzmerkmal"},
    "zone_red3":{"label":"Feste Kontaktzone · Rot 3","description":"Grundsignal mit mindestens drei roten Kontaktepisoden"},
    "zone_green3":{"label":"Feste Kontaktzone · Grün 3","description":"Grundsignal mit mindestens drei grünen Kontaktepisoden"},
    "zone_both3":{"label":"Feste Kontaktzone · beide 3","description":"Grundsignal mit mindestens drei Kontaktepisoden je Linie"},
    "zone_reference":{"label":"Referenz mit fester Kontaktzone","description":"Nur Kontaktmessung ersetzen; übrige Referenzprüfungen unverändert"},
    "momentum_two":{"label":"Grundsignal + Momentum 2 aus 3","description":"Positiver Körper und zwei von drei Formmerkmalen; bestätigter Schluss bleibt Pflicht"},
    "room_15":{"label":"Grundsignal + bekannter Raum 1,5R","description":"Nur bekannte Raumgrenze von 2R auf 1,5R ändern; unbekannter Raum blockiert dieses Profil"},
    "risk_5":{"label":"Grundsignal + Safety bis 5 %","description":"Prozentgrenze 5 statt 3; ATR-Grenze und Safety unverändert; feste Kontaktzone nur messen"},
    "momentum_two_risk5":{"label":"Momentum 2 aus 3 + Safety 5 %","description":"Vorab definierte Kombination; Kontaktzahl und Raum als Diagnose, keine Drei-Kontakt-Pflicht"},
}
ZONE_REQUIREMENTS = {"zone_measure": set(), "zone_red3": {"zone_red_contacts", "zone_green_contacts"},
                     "zone_green3": {"zone_red_contacts", "zone_green_contacts"},
                     "zone_both3": {"zone_red_contacts", "zone_green_contacts"},
                     "zone_reference": {"zone_red_contacts", "zone_green_contacts"},
                     "risk_5":set(),"momentum_two_risk5":set()}
CORE = {"confirmed_anchors","ordered_safety","close_above_red","positive_risk","execution_above_trigger","interim_safety",
        "horizontal_confirmed","retest_held"}
MOMENTUM = {"positive_body","body_atr","body_fraction","close_location"}
ADDITIONS = {"daily":{"context"},"contacts3":{"red_contacts","green_contacts"},"momentum":MOMENTUM,
             "risk":{"safety_distance_pct","safety_distance_atr"},"room":{"room","execution_room"},
             "momentum_two":{"positive_body","momentum_two_of_three"},"room_15":{"room","execution_room"},
             "risk_5":{"safety_distance_pct","safety_distance_atr"},
             "momentum_two_risk5":{"positive_body","momentum_two_of_three","safety_distance_pct","safety_distance_atr"}}
DEFAULTS = {"experiment_id":"","hypothesis":"Trendlinien-Einstiege und der Zusatznutzen ihrer Qualitätsmerkmale werden auf getrennten Zeiträumen untersucht.",
    "primary_horizon":10,"primary_metric":"mean_excess_pct","primary_family":"breakout","stage":"development",
    "profiles":["reference","baseline","daily","contacts3","retest_hold","atr_contacts"],
    "variant_budget":8,"allow_native":False,"feed":"iex","adjustment":"split","benchmark_symbol":"SPY",
    "random_controls":3,"bootstrap_samples":200,"contact_tolerance_atr":.05,"line_lookback_days":365,
    "analysis_start":"","analysis_end":"","development_end":"","validation_end":"","development_fraction":.6,
    "walk_train_sessions":126,"walk_test_sessions":42,"min_train_events":20,"membership":[],
    "confirm_final_test":False,"execution":{"enabled":False,"capital":2000.,"risk_fraction":.01,
       "allocation_fraction":.25,"max_positions":5,"fractional":False,"fee_per_order":0.,"spread_bps":5.,
       "slippage_bps":5.,"exit":"stop_time","holding_days":20,"target_r":2.}}


def validate(value, horizons):
    if not isinstance(value,dict) or set(value)-set(DEFAULTS):
        raise DataError("Unbekannte Laborparameter.",400)
    result={**deepcopy(DEFAULTS),**value}
    for name in ("allow_native","confirm_final_test"):
        if type(result[name]) is not bool:raise DataError(f"{name}: ja/nein erforderlich.",400)
    if result["stage"] not in ("development","validation","holdout","walk_forward"):
        raise DataError("Unbekannte Forschungsphase.",400)
    if result["feed"] not in ("iex","sip") or result["adjustment"] not in ("raw","split","all"):
        raise DataError("Unbekannte Labordatenkonvention.",400)
    if result["primary_metric"] not in ("mean_excess_pct","median_return_pct") or type(result["primary_horizon"]) is not int or result["primary_horizon"] not in horizons:
        raise DataError("Primäre Kennzahl/Horizont muss vorab festgelegt sein.",400)
    if result["primary_family"] not in ("breakout","horizontal","retest"):raise DataError("Primäre Einstiegsfamilie vorab festlegen.",400)
    if not isinstance(result["hypothesis"],str) or not 10<=len(result["hypothesis"].strip())<=3000:
        raise DataError("Eine nachvollziehbare Forschungshypothese angeben (10–3000 Zeichen).",400)
    if not isinstance(result["profiles"],list) or not result["profiles"] or any(not isinstance(p,str) or p not in PROFILES for p in result["profiles"]) or len(set(result["profiles"]))!=len(result["profiles"]):
        raise DataError("Bekannte, verschiedene Regelprofile wählen.",400)
    for name,lo,hi in (("variant_budget",1,20),("random_controls",1,10),("bootstrap_samples",50,1000),
                       ("line_lookback_days",30,365),("walk_train_sessions",20,1260),("walk_test_sessions",5,252),("min_train_events",1,1000)):
        if type(result[name]) is not int or not lo<=result[name]<=hi:raise DataError(f"{name}: ungültiger Wertebereich.",400)
    if len(result["profiles"])>result["variant_budget"]:raise DataError("Vorregistriertes Variantenbudget überschritten.",400)
    for name,lo,hi in (("contact_tolerance_atr",0,.5),("development_fraction",.3,.8)):
        if type(result[name]) not in (int,float) or not math.isfinite(result[name]) or not lo<=result[name]<=hi:
            raise DataError(f"{name}: ungültiger Wertebereich.",400)
    for name in ("analysis_start","analysis_end","development_end","validation_end"):
        if not isinstance(result[name],str):raise DataError("Labordatum als JJJJ-MM-TT angeben.",400)
        if result[name]:
            try:
                if datetime.strptime(result[name],"%Y-%m-%d").strftime("%Y-%m-%d")!=result[name]:raise ValueError()
            except (ValueError,TypeError):raise DataError("Labordatum als JJJJ-MM-TT angeben.",400) from None
    if bool(result["development_end"])!=bool(result["validation_end"]):raise DataError("Beide Phasengrenzen gemeinsam angeben.",400)
    if not isinstance(result["experiment_id"],str) or result["experiment_id"] and not re.fullmatch("[a-f0-9]{32}",result["experiment_id"]):
        raise DataError("Ungültige Experiment-ID.",400)
    if not isinstance(result["benchmark_symbol"],str) or result["benchmark_symbol"] and not re.fullmatch(r"[A-Z][A-Z0-9./-]{0,29}",result["benchmark_symbol"]):
        raise DataError("Ungültiges Benchmark-Symbol.",400)
    membership=result["membership"]
    if not isinstance(membership,list) or len(membership)>20000:raise DataError("Ungültiger historischer Universumsbestand.",400)
    for row in membership:
        if not isinstance(row,dict) or set(row)!={"symbol","start","end","source"} or not all(isinstance(v,str) for v in row.values()):raise DataError("Mitgliedschaft benötigt Symbol, Start, Ende und Quellenangabe.",400)
        if not re.fullmatch(r"[A-Z][A-Z0-9./-]{0,29}",row["symbol"]):raise DataError("Ungültiges Mitgliedschaftssymbol.",400)
        try:
            for key in ("start","end"):
                if row[key] and datetime.strptime(row[key],"%Y-%m-%d").strftime("%Y-%m-%d")!=row[key]:raise ValueError()
        except ValueError:raise DataError("Ungültiges Datum im historischen Universum.",400) from None
        if not row["source"].strip() or row["end"] and row["start"]>row["end"]:raise DataError("Unvollständiger Universumsnachweis.",400)
    execution=value.get("execution",{})
    if not isinstance(execution,dict) or set(execution)-set(DEFAULTS["execution"]):raise DataError("Unbekannte Ausführungsparameter.",400)
    result["execution"]={**DEFAULTS["execution"],**execution}
    ex=result["execution"]
    if type(ex["enabled"]) is not bool or type(ex["fractional"]) is not bool or ex["exit"] not in ("time","stop_time","stop_target_time"):
        raise DataError("Ungültige Ausführungsvariante.",400)
    for name,lo,hi in (("capital",1,1e9),("risk_fraction",.0001,.25),("allocation_fraction",.001,1),
                       ("fee_per_order",0,1000),("spread_bps",0,500),("slippage_bps",0,500),("target_r",.1,20)):
        if type(ex[name]) not in (int,float) or not math.isfinite(ex[name]) or not lo<=ex[name]<=hi:raise DataError(f"Ausführung {name}: ungültiger Wert.",400)
    if type(ex["max_positions"]) is not int or not 1<=ex["max_positions"]<=1000 or type(ex["holding_days"]) is not int or not 1<=ex["holding_days"]<=250:
        raise DataError("Ungültige Positionszahl/Haltedauer.",400)
    return result


def profile_manifest(name, lab, tori):
    result = {"id":name,"version":"entry-flex-2" if name in ("risk_5","momentum_two_risk5") else "contact-zone-1" if name in ZONE_REQUIREMENTS else "entry-flex-1" if name in ("momentum_two","room_15") else VERSION,"definition":PROFILES[name],"tori":tori,
            "contactToleranceATR":lab["contact_tolerance_atr"] if name=="atr_contacts" or name in ZONE_REQUIREMENTS else 0,
            "lookbackDays":lab["line_lookback_days"] if name=="atr_contacts" else 365,
            "referenceUnchanged":name=="reference","hypothesis":lab["hypothesis"]}
    if name in ("momentum_two","momentum_two_risk5"):result["momentumRule"]={"positiveBodyRequired":True,"votes":2,"of":["body_atr","body_fraction","close_location"]}
    if name=="room_15":result["roomR"]=1.5
    if name in ("risk_5","momentum_two_risk5"):result["safetyLimits"]={"pct":5,"atr":tori["max_safety_atr"],"stopUnchanged":True}
    return result


class LabScanner(EntryScanner):
    def __init__(self, dataset, spec, plan, profile, emit=lambda item:None, shared=None):
        self.profile, self.lab, self.shared = profile, spec["lab"], shared if shared is not None else {}
        self.family=None
        super().__init__(dataset,spec,plan,emit)
        if profile=="room_15":
            self.options={**self.options,"min_room_r":1.5}
        if profile in ("risk_5","momentum_two_risk5"):
            self.options={**self.options,"max_safety_pct":5}
        self.context_cache=self.shared.setdefault("context",{})

    def source_data(self,dataset):
        if "sources" not in self.shared:
            from datasets import source_bars
            self.shared["sources"]=source_bars(dataset)
        return self.shared["sources"]

    def execution_source(self,sources):
        return (sources["5m"],"5m") if "5m" in sources else (sources["1h"],"1h")

    def source_rules(self,prefix):
        base=rules_for("4h")
        if self.profile!="atr_contacts":return base
        volatility=atr(prefix)
        return replace(base,lookback_days=self.lab["line_lookback_days"],tick=max(base.tick,(volatility or 0)*self.lab["contact_tolerance_atr"]))

    def lines(self,prefix):
        rules=self.source_rules(prefix)
        key=(len(prefix),rules.lookback_days,rules.tick)
        cache=self.shared.setdefault("lines",{})
        if key not in cache:cache[key]=pair(prefix,rules)
        return cache[key]

    def contacts(self,ray,prefix,upper):
        if self.profile!="atr_contacts":return super().contacts(ray,prefix,upper)
        rules=self.source_rules(prefix);last=-self.options["contact_gap_bars"];count=0
        from tori_entries import value
        for i in range(ray["a_index"],len(prefix)):
            if touch(prefix[i].high if upper else prefix[i].low,value(ray,i),rules):
                if i-last>=self.options["contact_gap_bars"]:count+=1
                last=i
        return count

    def arm(self,i):
        previous_count=len(self.cases)
        prefix=self.bars[:i];lines=self.lines(prefix)
        red,green=lines["red"],lines["green"]
        if red is None:self.coverage["withoutRed"]=self.coverage.get("withoutRed",0)+1
        if green is None:self.coverage["withoutGreen"]=self.coverage.get("withoutGreen",0)+1
        # Preserve red-break candidates even when no usable green line exists.
        # These remain rejected diagnostics, never synthetic accepted entries.
        if red is not None and red.valid and green is None:
            before,current=prefix[-1],self.bars[i]
            if before.close<=red.value(before.time,i-1) and current.close>red.value(current.time,i):
                from tori_entries import check
                old=red.output(before.time);signal_red={**old,"value":red.value(current.time,i)}
                identity=digest({"dataset":self.dataset["id"],"missingSafetyAt":current.end,"red":old,"version":VERSION})
                armed={"id":identity,"kind":"tori_setup","time":before.time,"closedAt":before.end,"close":before.close,
                       "red":old,"green":None,"features":deepcopy(self.context(before.end))}
                signal={**armed,"kind":"red_break","time":current.time,"closedAt":current.end,"close":current.close,
                        "red":signal_red,"features":deepcopy(self.context(current.end))}
                entry={"variant":"breakout","status":"rejected","phase":"breakout","reason":"missing_safety",
                       "entryMode":"tori","eventId":identity,"signalAt":current.end,"decidedAt":current.end,
                       "signal":signal,"armedSignal":armed,"quality":"provisional","group":"breakout_provisional",
                       "checks":[check("confirmed_red_anchor",True),check("green_available",False),
                                 check("close_above_red",True,current.close-signal_red["value"]),check("ordered_safety",None,required=False)]}
                case={"id":identity,"datasetId":self.dataset["id"],"symbol":self.dataset["material"]["symbol"],"mode":VERSION,
                      "startAt":before.end,"startIndex":i-1,"armedIndex":i-1,"breakIndex":i,"signal":signal,
                      "partition":"diagnostic","holdoutStart":self.plan["holdout_start"],"frozen":{"red":old,"green":None},"variants":[entry]}
                self.cases[identity]=case
                self.journal(case,"lab_rejected_missing_safety",current.end,reason="missing_safety")
                self.save(case)
        super().arm(i)
        if self.profile in ZONE_REQUIREMENTS:
            from contact_zones import freeze
            for case in list(self.cases.values())[previous_count:]:
                if case["frozen"].get("green"):
                    case["contactMeasurement"]=freeze(prefix,atr(prefix),self.lab["contact_tolerance_atr"])
                    self.save(case)

    def base_checks(self,case,i,prefix):
        checks,quality,volatility,context=super().base_checks(case,i,prefix)
        if self.profile in ZONE_REQUIREMENTS:
            from contact_zones import measure
            contacts=measure(case,prefix,self.options["contact_gap_bars"])
            checks.append(check("contact_zone_available",case["contactMeasurement"]["tolerance"] is not None))
            checks.append(check("contact_zone_definition",True,deepcopy(case["contactMeasurement"]),False))
            for side in ("red","green"):
                count=contacts[side]
                threshold=3 if self.profile in ("zone_measure","zone_both3","zone_"+side+"3") else 2
                if self.profile=="zone_reference" and side=="red":threshold=self.options["min_contacts"]
                checks.append(check("zone_"+side+"_contacts",None if count is None else count>=threshold,count))
        if self.profile in ("momentum_two","momentum_two_risk5"):
            votes=[c["state"] for c in checks if c["name"] in MOMENTUM-{"positive_body"}]
            passed,unknown=votes.count("pass"),votes.count("unknown")
            state=True if passed>=2 else None if passed+unknown>=2 else False
            checks.append(check("momentum_two_of_three",state,{"passed":passed,"unknown":unknown,"total":3}))
        if self.profile=="daily":
            state=context["structure"]["1D"]
            daily=next(c for c in checks if c["name"]=="context")
            daily.update(state="unknown" if state=="unknown" else "fail" if state=="down" else "pass",required=True)
        if self.profile=="contacts3":
            for c in checks:
                if c["name"] in ("red_contacts","green_contacts"):c["state"]="pass" if c["value"]>=3 else "fail"
        return checks,quality,volatility,context

    def risk_checks(self,price,safety,volatility):
        from tori_entries import check
        return super().risk_checks(price,safety,volatility)+[check("positive_risk",0<safety<price,price-safety)]

    def blocked(self,checks):
        for c in checks:
            original=c.setdefault("referenceRequired",c["required"])
            if self.profile=="reference":required=original
            elif self.profile=="zone_reference":
                required=(original and c["name"] not in ("red_contacts","green_contacts")) or c["name"] in ZONE_REQUIREMENTS[self.profile]|{"contact_zone_available"}
            elif self.profile in ZONE_REQUIREMENTS:
                required=c["name"] in CORE|ZONE_REQUIREMENTS[self.profile]|ADDITIONS.get(self.profile,set())|({"contact_zone_available"} if ZONE_REQUIREMENTS[self.profile] else set())
            elif self.profile=="retest_hold":required=original and not (self.family=="retest" and c["name"] in MOMENTUM)
            else:required=(original or self.profile in ("room","room_15") and c["name"] in ("room","execution_room")) and c["name"] in CORE|ADDITIONS.get(self.profile,set())
            c["required"]=required
        return super().blocked(checks)

    def confirm(self,case,variant,i,checks,volatility):
        self.family=variant["variant"]
        try:return super().confirm(case,variant,i,deepcopy(checks),volatility)
        finally:self.family=None
