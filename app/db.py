# -*- coding: utf-8 -*-
"""ชั้นข้อมูล SQLite ของ CPRISK — เก็บอุบัติการณ์เป็น JSON ต่อแถว (แนวเดียวกับ SSCC)
คอลัมน์ที่ใช้ค้น/สรุปบ่อย แยกออกมาเป็นคอลัมน์จริง เพื่อให้ dashboard คิวรีเร็ว"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "cprisk.db"

STATUS_TH = {
    "new": "🆕 รายงานใหม่",
    "ack": "👀 รับเรื่องแล้ว",
    "resolving": "🔧 กำลังแก้ไข",
    "resolved": "✅ ปิดเคสแล้ว",
}


def _conn():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL DEFAULT 'new',      -- new | ack | resolving | resolved
                severe INTEGER NOT NULL DEFAULT 0,       -- 1 = เข้าเกณฑ์รุนแรง (ตาม config)
                severity TEXT DEFAULT '',                -- A-I หรือ 1-5
                group_key TEXT DEFAULT '',               -- cps | specific | psg | osg
                topic TEXT DEFAULT '',                   -- รหัสเรื่อง (ต่อกลุ่ม)
                unit TEXT DEFAULT '',
                occur_date TEXT DEFAULT '',
                reported_at TEXT, ack_at TEXT, resolved_at TEXT,
                nrls_status TEXT DEFAULT '',             -- '' | sim  (mock: จำลองการส่ง NRLS)
                nrls_at TEXT,
                data TEXT NOT NULL DEFAULT '{}',
                responses TEXT NOT NULL DEFAULT '[]'     -- [{at, by, action, text}]
            )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_inc_status ON incidents(status)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_inc_reported ON incidents(reported_at)")


def _row_to_dict(r):
    d = dict(r)
    d["data"] = json.loads(d.get("data") or "{}")
    d["responses"] = json.loads(d.get("responses") or "[]")
    return d


def derive_columns(data, severe_clin, severe_gen):
    """ดึงค่าที่ใช้สรุปบ่อยออกจาก data ของฟอร์ม"""
    group = data.get("incident_group") or ""
    topic = data.get("topic_%s" % group) or ""
    if group == "osg":
        sev = data.get("severity_org") or ""
        severe = 1 if sev in severe_gen else 0
    else:
        sev = data.get("severity_clin") or ""
        severe = 1 if sev in severe_clin else 0
    return {"group_key": group, "topic": topic, "severity": sev, "severe": severe,
            "unit": data.get("unit") or "", "occur_date": data.get("occur_date") or ""}


def add_incident(data, severe_clin, severe_gen, reported_at=None):
    cols = derive_columns(data, severe_clin, severe_gen)
    now = reported_at or datetime.now().isoformat(timespec="seconds")
    with _conn() as c:
        cur = c.execute(
            """INSERT INTO incidents (status, severe, severity, group_key, topic, unit,
                                      occur_date, reported_at, data)
               VALUES ('new', ?, ?, ?, ?, ?, ?, ?, ?)""",
            (cols["severe"], cols["severity"], cols["group_key"], cols["topic"],
             cols["unit"], cols["occur_date"], now, json.dumps(data, ensure_ascii=False)))
        return cur.lastrowid


def get(inc_id):
    with _conn() as c:
        r = c.execute("SELECT * FROM incidents WHERE id = ?", (inc_id,)).fetchone()
        return _row_to_dict(r) if r else None


def list_incidents(status="", severe_only=False, q="", sort="severe"):
    sql = "SELECT * FROM incidents WHERE 1=1"
    args = []
    if status:
        sql += " AND status = ?"
        args.append(status)
    if severe_only:
        sql += " AND severe = 1 AND status != 'resolved'"
    if q:
        sql += " AND (data LIKE ? OR CAST(id AS TEXT) = ?)"
        args += [f"%{q}%", q]
    # sort="new" = ล่าสุดก่อน (กันเคสใหม่ระดับเบาจมใต้เคสรุนแรงเก่า) | "severe" = รุนแรงก่อน
    if sort == "new":
        sql += " ORDER BY reported_at DESC"
    else:
        sql += " ORDER BY severe DESC, reported_at DESC"
    with _conn() as c:
        return [_row_to_dict(r) for r in c.execute(sql, args).fetchall()]


def status_counts(q=""):
    sql = "SELECT status, COUNT(*) n FROM incidents"
    args = []
    if q:
        sql += " WHERE (data LIKE ? OR CAST(id AS TEXT) = ?)"
        args += [f"%{q}%", q]
    sql += " GROUP BY status"
    with _conn() as c:
        counts = {r["status"]: r["n"] for r in c.execute(sql, args).fetchall()}
    with _conn() as c:
        counts["severe_open"] = c.execute(
            "SELECT COUNT(*) FROM incidents WHERE severe = 1 AND status != 'resolved'").fetchone()[0]
    return counts


def add_response(inc_id, action, text, by, new_status=None, at=None):
    inc = get(inc_id)
    if not inc:
        return None
    now = at or datetime.now().isoformat(timespec="seconds")
    inc["responses"].append({"at": now, "by": by, "action": action, "text": text})
    sets = ["responses = ?"]
    args = [json.dumps(inc["responses"], ensure_ascii=False)]
    if new_status:
        sets.append("status = ?")
        args.append(new_status)
        if new_status == "ack" and not inc.get("ack_at"):
            sets.append("ack_at = ?")
            args.append(now)
        if new_status == "resolved":
            sets.append("resolved_at = ?")
            args.append(now)
        else:
            # กลับสู่สถานะยังไม่ปิด (เช่น reopen) — เวลาปิดเคสเดิมต้องถูกล้าง ไม่งั้น KPI นับผิด
            sets.append("resolved_at = NULL")
    args.append(inc_id)
    with _conn() as c:
        c.execute(f"UPDATE incidents SET {', '.join(sets)} WHERE id = ?", args)
    return get(inc_id)


def mark_nrls_sim(inc_id, at=None):
    now = at or datetime.now().isoformat(timespec="seconds")
    with _conn() as c:
        c.execute("UPDATE incidents SET nrls_status = 'sim', nrls_at = ? WHERE id = ?", (now, inc_id))
    return get(inc_id)


def update_data(inc_id, data, severe_clin, severe_gen):
    cols = derive_columns(data, severe_clin, severe_gen)
    with _conn() as c:
        c.execute(
            """UPDATE incidents SET severe=?, severity=?, group_key=?, topic=?, unit=?,
                                    occur_date=?, data=? WHERE id=?""",
            (cols["severe"], cols["severity"], cols["group_key"], cols["topic"], cols["unit"],
             cols["occur_date"], json.dumps(data, ensure_ascii=False), inc_id))
    return get(inc_id)


def all_full():
    with _conn() as c:
        return [_row_to_dict(r) for r in c.execute(
            "SELECT * FROM incidents ORDER BY reported_at").fetchall()]


def count_all():
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
