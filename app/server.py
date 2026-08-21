# -*- coding: utf-8 -*-
"""CPRISK — ระบบบริหารความเสี่ยง รพ.ชุมแพ (MOCK/DEMO)
Flask local — โครงเดียวกับ SSCC (schema-driven form + SQLite JSON-per-row)
โหมดเดโม: ข้อมูลจำลองทั้งหมด และปุ่ม "ส่งเข้า NRLS" เป็นการจำลอง ไม่แตะเว็บจริง"""
import json
import re
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path

if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from flask import Flask, jsonify, redirect, render_template, request, url_for

import db

APP_DIR = Path(__file__).parent
CONFIG = json.loads((APP_DIR / "config.json").read_text(encoding="utf-8"))
CUSTOM_PATH = APP_DIR / "schema" / "custom_fields.json"
CF_TYPES = {"text", "number", "select", "checkbox-group", "date", "time", "textarea"}

app = Flask(__name__)


# ---------- schema ----------
def read_custom_raw():
    if CUSTOM_PATH.exists():
        return json.loads(CUSTOM_PATH.read_text(encoding="utf-8"))
    return {"fields": []}


def load_schema():
    schema = json.loads((APP_DIR / "schema" / "hrms_fields.json").read_text(encoding="utf-8"))
    custom = []
    for f in read_custom_raw().get("fields", []):
        if not f.get("enabled", True):
            continue
        f = dict(f)
        f["section"] = "CF"
        f["section_title"] = "ข้อมูลเพิ่มเติมของ รพ. (ตัวชี้วัดที่ รพ. เพิ่มเอง — ไม่ส่งเข้า NRLS)"
        custom.append(f)
    return schema["fields"] + custom


def field_key(f):
    return f["key"]


def show_if_map(fields):
    return {f["key"]: f["show_if"] for f in fields if f.get("show_if")}


def label_maps():
    """lookup สำหรับหน้าแสดงผล: key→field def และ (key,value)→ข้อความ"""
    fields = load_schema()
    fmap = {f["key"]: f for f in fields}
    vmap = {}
    for f in fields:
        for o in f.get("options", []):
            vmap[(f["key"], o["v"])] = o["t"]
    return fields, fmap, vmap


GROUP_TH = {"cps": "Patient Safety / Common Clinical Risk", "specific": "Specific Clinical Risk",
            "psg": "Personnel Safety Goals", "osg": "Organization Safety Goals"}


def sev_meta(sev):
    """สีทึบสำหรับกราฟ (Chart.js) — ไล่โทนตามความรุนแรง เขียว→ส้ม→แดง"""
    palette = {"A": "#7db8dc", "B": "#5aa87e", "C": "#8bc34a", "D": "#d4c122",
               "E": "#f0a030", "F": "#e87722", "G": "#bf360c", "H": "#9c1414", "I": "#660000",
               "1": "#8bc34a", "2": "#d4c122", "3": "#f0a030", "4": "#bf360c", "5": "#660000"}
    return palette.get(sev, "#999")


def sev_badge(sev):
    """สี badge ระดับความรุนแรง — ระดับต่ำใช้ตัวเข้มบนพื้นอ่อน ระดับสูงพื้นเข้มตัวขาว
    (แก้ตาม review: ชุดเดิม contrast ต่ำ และ E ที่เข้าเกณฑ์รุนแรงดันเป็นสีเขียว)"""
    palette = {
        "A": ("#e3f2fd", "#0d47a1"), "B": ("#e0f7f4", "#00695c"), "C": ("#e6f4e6", "#1b5e20"),
        "D": ("#fff9c4", "#795500"), "E": ("#ffe0b2", "#8a4500"), "F": ("#ffccbc", "#a03000"),
        "G": ("#bf360c", "#ffffff"), "H": ("#9c1414", "#ffffff"), "I": ("#660000", "#ffffff"),
        "1": ("#e6f4e6", "#1b5e20"), "2": ("#fff9c4", "#795500"), "3": ("#ffe0b2", "#8a4500"),
        "4": ("#bf360c", "#ffffff"), "5": ("#660000", "#ffffff"),
    }
    bg, fg = palette.get(sev, ("#eceff1", "#455a64"))
    return {"bg": bg, "fg": fg}


SEV_TH = {
    "A": "A — มีโอกาสเกิด (ยังไม่เกิด)", "B": "B — เกิดแล้วแต่ยังไม่ถึงผู้ป่วย",
    "C": "C — ถึงตัวแล้ว ไม่เป็นอันตราย", "D": "D — ถึงตัวแล้ว ต้องเฝ้าระวังเพิ่ม",
    "E": "E — อันตรายชั่วคราว ต้องบำบัดรักษา", "F": "F — ต้องนอน รพ./นอนนานขึ้น",
    "G": "G — อันตรายถาวร", "H": "H — ต้องช่วยชีวิต", "I": "I — เสียชีวิต",
    "1": "1 — น้อยมาก", "2": "2 — น้อย", "3": "3 — ปานกลาง", "4": "4 — สูง", "5": "5 — สูงมาก/วิกฤต",
}


@app.template_filter("thdt")
def thdt(iso):
    if not iso:
        return "—"
    try:
        d = datetime.fromisoformat(iso)
        return d.strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return iso


@app.template_filter("thd")
def thd(iso):
    if not iso:
        return "—"
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y")
    except ValueError:
        return iso


@app.context_processor
def inject_globals():
    return {"config": CONFIG, "GROUP_TH": GROUP_TH, "sev_meta": sev_meta,
            "sev_badge": sev_badge, "SEV_TH": SEV_TH, "STATUS_TH": db.STATUS_TH}


# ---------- หน้าแรก: เลือกบทบาท ----------
@app.route("/")
def home():
    counts = db.status_counts()
    return render_template("home.html", counts=counts)


# ---------- ผู้กรอก: ฟอร์มรายงานอุบัติการณ์ ----------
@app.route("/report")
def report_new():
    fields = load_schema()
    return render_template("form.html", fields=fields, values={},
                           field_key=field_key, show_if_map=show_if_map(fields),
                           today=datetime.now().strftime("%d/%m/%Y"),
                           today_iso=datetime.now().strftime("%Y-%m-%d"))


@app.route("/report/save", methods=["POST"])
def report_save():
    data = (request.get_json(force=True) or {}).get("data") or {}
    if not (data.get("detail") or "").strip():
        return jsonify(ok=False, error="กรุณากรอกรายละเอียดการเกิดเหตุ"), 400
    if not data.get("incident_group"):
        return jsonify(ok=False, error="กรุณาเลือกกลุ่มอุบัติการณ์"), 400
    # ลำดับวันที่ต้องสมเหตุผล: เกิดเหตุ ≤ ค้นพบ ≤ วันนี้ (กัน KPI เวลาตอบสนองเพี้ยน)
    today = datetime.now().strftime("%Y-%m-%d")
    od, fd = data.get("occur_date") or "", data.get("found_date") or ""
    if (od and od > today) or (fd and fd > today):
        return jsonify(ok=False, error="วันที่เกิดเหตุ/วันที่ค้นพบ เป็นวันในอนาคตไม่ได้"), 400
    if od and fd and fd < od:
        return jsonify(ok=False, error="วันที่ค้นพบ ต้องไม่มาก่อนวันที่เกิดอุบัติการณ์"), 400
    inc_id = db.add_incident(data, CONFIG["severe_clinical"], CONFIG["severe_general"])
    inc = db.get(inc_id)
    return jsonify(ok=True, id=inc_id, severe=bool(inc["severe"]), severity=inc["severity"])


# ---------- กรรมการ: หน้ารวม + เคส ----------
@app.route("/inbox")
def inbox():
    status_f = request.args.get("status", "").strip()
    severe_f = request.args.get("severe", "") == "1"
    q = request.args.get("q", "").strip()
    sort = request.args.get("sort", "new")  # new = ล่าสุดก่อน (default — กันเคสใหม่จมหาย) | severe = รุนแรงก่อน
    if sort not in ("new", "severe"):
        sort = "new"
    rows = db.list_incidents(status=status_f, severe_only=severe_f, q=q, sort=sort)
    counts = db.status_counts(q)
    counts["all"] = sum(v for k, v in counts.items() if k in db.STATUS_TH)
    _, fmap, vmap = label_maps()
    for r in rows:
        r["unit_t"] = vmap.get(("unit", r["unit"]), r["unit"] or "—")
        r["topic_t"] = vmap.get((f"topic_{r['group_key']}", r["topic"]), r["topic"] or "—")
    return render_template("inbox.html", rows=rows, counts=counts, status_f=status_f,
                           severe_f=severe_f, q=q, sort=sort)


@app.route("/case/<int:inc_id>")
def case_view(inc_id):
    inc = db.get(inc_id)
    if not inc:
        return redirect(url_for("inbox"))
    fields, fmap, vmap = label_maps()
    display = []
    for f in fields:
        v = inc["data"].get(f["key"])
        if v in (None, "", []):
            continue
        if isinstance(v, list):
            t = ", ".join(vmap.get((f["key"], x), x) for x in v)
        else:
            t = vmap.get((f["key"], v), v)
        display.append({"label": f["label"], "value": t, "section": f["section_title"]})
    return render_template("case.html", inc=inc, display=display)


@app.route("/case/<int:inc_id>/action", methods=["POST"])
def case_action(inc_id):
    inc = db.get(inc_id)
    if not inc:
        return jsonify(ok=False, error="ไม่พบเคส"), 404
    p = request.get_json(force=True) or {}
    action = p.get("action")
    text = str(p.get("text") or "").strip()
    # ต้องระบุชื่อผู้ดำเนินการเสมอ — ห้าม default เป็นชื่อคน (audit trail ต้องเชื่อถือได้)
    by = str(p.get("by") or "").strip()
    if not by:
        return jsonify(ok=False, error="กรุณาระบุชื่อผู้ดำเนินการ (ช่อง \"ดำเนินการในนาม\")"), 400

    if action == "ack":
        db.add_response(inc_id, "ack", text or "รับเรื่องแล้ว", by, new_status="ack")
    elif action == "progress":
        if not text:
            return jsonify(ok=False, error="กรุณาบันทึกความคืบหน้าการแก้ไข"), 400
        db.add_response(inc_id, "progress", text, by, new_status="resolving")
    elif action == "close":
        if not text:
            return jsonify(ok=False, error="กรุณาสรุปผลการแก้ไขก่อนปิดเคส"), 400
        db.add_response(inc_id, "close", text, by, new_status="resolved")
    elif action == "reopen":
        if inc["status"] != "resolved":
            return jsonify(ok=False, error="เคสนี้ยังไม่ได้ปิด"), 400
        db.add_response(inc_id, "reopen", text or "เปิดเคสใหม่เพื่อดำเนินการต่อ", by,
                        new_status="resolving")
    elif action == "nrls":
        # DEMO: จำลองการส่งเท่านั้น — ระบบจริงจะเข้าคิว Playwright เปิดเว็บ NRLS ให้ตรวจก่อนบันทึก (แบบ SSCC)
        db.mark_nrls_sim(inc_id)
        db.add_response(inc_id, "nrls", "ส่งข้อมูลเข้าระบบ NRLS (จำลอง — โหมดพัฒนา)", by)
    else:
        return jsonify(ok=False, error="ไม่รู้จักคำสั่งนี้"), 400
    return jsonify(ok=True)


# ---------- หน้าเว็บ NRLS จำลอง (โคลนโครงฟอร์มเว็บจริง — สาธิตการกรอกอัตโนมัติแบบ human-in-loop) ----------
@app.route("/nrls-sim/<int:inc_id>")
def nrls_sim(inc_id):
    inc = db.get(inc_id)
    if not inc:
        return redirect(url_for("inbox"))
    schema = json.loads((APP_DIR / "schema" / "hrms_fields.json").read_text(encoding="utf-8"))
    data = inc["data"]

    def visible(f):
        cond = f.get("show_if")
        if not cond:
            return True
        return all(data.get(k) in allowed for k, allowed in cond.items())

    # แสดงเฉพาะฟิลด์มาตรฐาน NRLS ที่เข้าเงื่อนไขของเคสนี้ (custom fields ของ รพ. ไม่ส่งเข้า NRLS)
    fields = [f for f in schema["fields"] if visible(f)]
    fill = []
    for f in fields:
        v = data.get(f["key"])
        if v in (None, "", []):
            continue
        if f["type"] == "date":
            try:
                v = datetime.fromisoformat(v).strftime("%d/%m/%Y")
            except ValueError:
                pass
        fill.append({"key": f["key"], "type": f["type"], "value": v})
    return render_template("nrls_sim.html", inc=inc, fields=fields, fill=fill)


# ---------- แจ้งเตือน (จำลอง in-app) ----------
@app.route("/api/alerts")
def api_alerts():
    rows = db.list_incidents(severe_only=True)
    new_severe = [r for r in rows if r["status"] == "new"]
    _, _, vmap = label_maps()
    items = [{"id": r["id"], "severity": r["severity"],
              "unit": vmap.get(("unit", r["unit"]), r["unit"]),
              "topic": vmap.get((f"topic_{r['group_key']}", r["topic"]), r["topic"]),
              "at": r["reported_at"]} for r in new_severe[:8]]
    return jsonify(n_new_severe=len(new_severe), items=items)


# ---------- dashboard ผู้บริหาร ----------
def _median(xs):
    return round(statistics.median(xs), 1) if xs else None


@app.route("/dashboard")
def dashboard():
    months = request.args.get("months", "12")
    incidents = db.all_full()
    if months != "all":
        cutoff = (datetime.now() - timedelta(days=int(months) * 30.5)).isoformat()
        incidents = [i for i in incidents if (i["reported_at"] or "") >= cutoff]

    now = datetime.now()
    total = len(incidents)
    severe = [i for i in incidents if i["severe"]]
    resolved = [i for i in incidents if i["status"] == "resolved"]

    ack_hours, resolve_days, ack24_ok, ack24_denom = [], [], 0, 0
    for i in incidents:
        rep = datetime.fromisoformat(i["reported_at"]) if i["reported_at"] else None
        if not rep:
            continue
        if i["ack_at"]:
            h = (datetime.fromisoformat(i["ack_at"]) - rep).total_seconds() / 3600
            ack_hours.append(h)
        # นับ %รับเรื่องใน 24 ชม. เฉพาะเคสที่อายุเกิน 24 ชม.แล้ว (เคสเพิ่งเข้าไม่ถูกนับว่าพลาด)
        if (now - rep).total_seconds() > 86400:
            ack24_denom += 1
            if i["ack_at"] and (datetime.fromisoformat(i["ack_at"]) - rep).total_seconds() <= 86400:
                ack24_ok += 1
        if i["resolved_at"]:
            resolve_days.append((datetime.fromisoformat(i["resolved_at"]) - rep).total_seconds() / 86400)

    sla_d = CONFIG["sla_resolve_days"]
    overdue = [i for i in incidents if i["status"] != "resolved" and i["reported_at"]
               and (now - datetime.fromisoformat(i["reported_at"])).days > sla_d]

    def count_by(key_fn, keys):
        c = {k: 0 for k in keys}
        for i in incidents:
            k = key_fn(i)
            if k in c:
                c[k] += 1
        return c

    sev_clin = count_by(lambda i: i["severity"] if i["group_key"] != "osg" else None, list("ABCDEFGHI"))
    sev_org = count_by(lambda i: i["severity"] if i["group_key"] == "osg" else None, ["1", "2", "3", "4", "5"])
    groups = count_by(lambda i: i["group_key"], list(GROUP_TH))

    _, fmap, vmap = label_maps()
    unit_stats = {}
    for i in incidents:
        u = i["unit"] or "?"
        s = unit_stats.setdefault(u, {"n": 0, "severe": 0, "open_over": 0, "ack_h": []})
        s["n"] += 1
        s["severe"] += i["severe"]
        if i in overdue:
            s["open_over"] += 1
        if i["ack_at"] and i["reported_at"]:
            s["ack_h"].append((datetime.fromisoformat(i["ack_at"])
                               - datetime.fromisoformat(i["reported_at"])).total_seconds() / 3600)
    unit_rows = sorted(
        [{"unit": vmap.get(("unit", u), u), "n": s["n"], "severe": s["severe"],
          "open_over": s["open_over"], "med_ack": _median(s["ack_h"])}
         for u, s in unit_stats.items()], key=lambda r: -r["n"])

    # แนวโน้มรายเดือน 12 เดือนล่าสุด (จากข้อมูลทั้งฐาน ไม่ตาม filter — ให้เห็นภาพยาวเสมอ)
    trend = {}
    for i in db.all_full():
        if not i["reported_at"]:
            continue
        m = i["reported_at"][:7]
        t = trend.setdefault(m, {"total": 0, "severe": 0})
        t["total"] += 1
        t["severe"] += i["severe"]
    months_sorted = sorted(trend)[-12:]
    # ป้ายเดือนล่าสุด: ถ้ายังไม่จบเดือน ต้องบอก — กันผู้บริหารอ่านแท่งที่ต่ำกว่าว่า "ดีขึ้น" ทั้งที่เดือนยังไม่ครบ
    trend_labels = list(months_sorted)
    if trend_labels and trend_labels[-1] == datetime.now().strftime("%Y-%m"):
        trend_labels[-1] += " *ยังไม่จบเดือน"

    top_topics = {}
    for i in incidents:
        t = vmap.get((f"topic_{i['group_key']}", i["topic"]), i["topic"])
        if t:
            top_topics[t] = top_topics.get(t, 0) + 1
    top_topics = sorted(top_topics.items(), key=lambda kv: -kv[1])[:8]

    stats = {
        "total": total, "n_severe": len(severe),
        "n_open_severe": sum(1 for i in severe if i["status"] != "resolved"),
        "pct_ack24": round(ack24_ok * 100 / ack24_denom) if ack24_denom else None,
        "med_ack_h": _median(ack_hours), "med_resolve_d": _median(resolve_days),
        "n_overdue": len(overdue), "n_resolved": len(resolved),
        "pct_resolved": round(len(resolved) * 100 / total) if total else 0,
        "n_nrls": sum(1 for i in incidents if i["nrls_status"]),
        "sla_resolve_days": sla_d,
    }
    charts = {
        "sev_clin": sev_clin, "sev_org": sev_org,
        "groups": {GROUP_TH[k]: v for k, v in groups.items()},
        "units": [[r["unit"], r["n"], r["severe"]] for r in unit_rows[:10]],
        "trend": {"labels": trend_labels,
                  "total": [trend[m]["total"] for m in months_sorted],
                  "severe": [trend[m]["severe"] for m in months_sorted]},
        "topics": top_topics,
        "sev_colors": {s: sev_meta(s) for s in list("ABCDEFGHI") + ["1", "2", "3", "4", "5"]},
    }
    return render_template("dashboard.html", stats=stats, charts=charts,
                           unit_rows=unit_rows, months=months)


# ---------- QR เข้า GitHub ของโปรเจกต์ (สำหรับแจกในที่ประชุม/เดโม) ----------
@app.route("/qr")
def qr_page():
    return render_template("qr.html", qr_url=CONFIG.get("qr_url", ""),
                           qr_label=CONFIG.get("qr_label", ""))


# ---------- หน้าเสนอช่องทางแจ้งเตือน ----------
@app.route("/channels")
def channels():
    return render_template("channels.html")


# ---------- ฟิลด์ รพ. (form builder — ยกมาจาก SSCC ตัด Excel ออก) ----------
@app.route("/fields")
def fields_page():
    return render_template("fields.html", fields=read_custom_raw().get("fields", []))


@app.route("/api/custom_fields", methods=["POST"])
def custom_fields_save():
    raw = read_custom_raw()
    incoming = (request.get_json(force=True) or {}).get("fields", [])
    next_id = int(raw.get("_next_id") or 1)
    for f in raw.get("fields", []):
        m = re.match(r"^cf_(\d+)$", f.get("key") or "")
        if m:
            next_id = max(next_id, int(m.group(1)) + 1)
    out = []
    for f in incoming:
        label = str(f.get("label") or "").strip()
        ftype = f.get("type")
        if not label:
            return jsonify(ok=False, error="มีหัวข้อที่ยังไม่ได้ตั้งชื่อ"), 400
        if ftype not in CF_TYPES:
            return jsonify(ok=False, error=f"รูปแบบการกรอกไม่ถูกต้อง: {ftype}"), 400
        g = {"key": str(f.get("key") or "").strip(), "label": label, "type": ftype,
             "enabled": f.get("enabled", True) is not False}
        if not g["key"]:
            g["key"] = f"cf_{next_id}"
            next_id += 1
        if ftype in ("select", "checkbox-group"):
            opts = [{"v": str(o.get("v", "")).strip(), "t": str(o.get("t", "")).strip()}
                    for o in (f.get("options") or [])]
            opts = [o for o in opts if o["t"]]
            if len(opts) < 2:
                return jsonify(ok=False, error=f"'{label}': ต้องมีตัวเลือกอย่างน้อย 2 ตัวเลือก"), 400
            g["options"] = opts
        cond = f.get("show_if")
        if isinstance(cond, dict) and all(isinstance(v, list) for v in cond.values()):
            g["show_if"] = cond
        if ftype == "number":
            for k in ("min", "max"):
                if f.get(k) not in (None, ""):
                    g[k] = f[k]
        if str(f.get("hint") or "").strip():
            g["hint"] = str(f["hint"]).strip()
        if f.get("required"):
            g["required"] = True
        out.append(g)
    keys = [g["key"] for g in out]
    if len(keys) != len(set(keys)):
        return jsonify(ok=False, error="มี key ซ้ำกัน — รีเฟรชหน้าแล้วลองใหม่"), 400
    raw["fields"] = out
    raw["_next_id"] = next_id
    CUSTOM_PATH.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    return jsonify(ok=True, fields=out)


if __name__ == "__main__":
    db.init()
    if CONFIG.get("demo_seed") and db.count_all() == 0:
        print("* ฐานว่าง — กำลัง seed ข้อมูลจำลองสำหรับเดโม...")
        import seed
        seed.run()
    port = CONFIG.get("port", 8548)
    print(f"* CPRISK เปิดใช้งานที่ http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False)
