# -*- coding: utf-8 -*-
"""seed ข้อมูลจำลองสำหรับเดโม — ~380 อุบัติการณ์ย้อนหลัง 12 เดือน
ข้อมูลทั้งหมดเป็นข้อมูลสมมติ ไม่มีข้อมูลผู้ป่วยจริง (ชื่อ/เหตุการณ์แต่งขึ้นทั้งหมด)"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

import db

APP_DIR = Path(__file__).parent
CONFIG = json.loads((APP_DIR / "config.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((APP_DIR / "schema" / "hrms_fields.json").read_text(encoding="utf-8"))

random.seed(4200)

_OPTS = {f["key"]: [o["v"] for o in f.get("options", [])] for f in SCHEMA["fields"] if f.get("options")}

# น้ำหนักการสุ่ม — เลียนสัดส่วนคร่าวๆ จากหน้า dashboard HRMS จริง
GROUP_W = [("cps", 55), ("specific", 8), ("psg", 22), ("osg", 15)]
SEV_CLIN_W = [("A", 5), ("B", 9), ("C", 34), ("D", 26), ("E", 16), ("F", 6), ("G", 2), ("H", 1), ("I", 1)]
SEV_ORG_W = [("1", 30), ("2", 32), ("3", 22), ("4", 12), ("5", 4)]
UNIT_W = [("ER", 14), ("MED_M", 10), ("MED_F", 10), ("OPD", 9), ("PHAR", 9), ("SURG", 8),
          ("ICU", 7), ("PED", 6), ("OBGYN", 5), ("LR", 4), ("OR", 4), ("LAB", 3), ("XRAY", 3),
          ("HD", 2), ("DENT", 2), ("REC", 1), ("FIN", 1), ("IT", 1), ("MAINT", 1)]

DETAIL = {
    "med_error": ["จ่ายยา {drug} ขนาด 500 mg แทน 250 mg ตามคำสั่งแพทย์ พบตอน double check ก่อนให้ยา",
                  "ให้ยา {drug} ผิดเวลา ห่างจากคำสั่งประมาณ 3 ชั่วโมง เนื่องจากรับเวรต่อกันไม่ครบถ้วน",
                  "ติดฉลากยา {drug} สลับกับผู้ป่วยเตียงข้างกัน พบก่อนให้ยา"],
    "med_adr": ["ผู้ป่วยมีผื่นแดงทั้งตัวหลังได้ {drug} เข็มแรก ประเมินเป็น mild allergic reaction",
                "หลังได้ {drug} 30 นาที ผู้ป่วยมีอาการแน่นหน้าอก บวมรอบตา รักษาตามแนวทาง anaphylaxis"],
    "patient_id": ["เรียกผู้ป่วยชื่อซ้ำกันเข้าห้องตรวจสลับคน พบเมื่อทวนสิทธิ์ก่อนทำหัตถการ",
                   "ติดสายรัดข้อมือผิดคนช่วงรับใหม่พร้อมกัน 2 ราย พบตอนตรวจสอบก่อนเจาะเลือด"],
    "infection": ["พบ CAUTI ในผู้ป่วยคาสายสวนปัสสาวะวันที่ 6", "พบ phlebitis ระดับ 2 ตำแหน่งให้สารน้ำแขนซ้าย"],
    "fall": ["ผู้ป่วยสูงอายุลุกเข้าห้องน้ำเองช่วงเวรดึกแล้วลื่นล้ม ศีรษะไม่กระแทก",
             "ผู้ป่วยตกเตียงขณะญาติเผลอหลับ ไม้กั้นเตียงยกไม่สุด มีแผลถลอกที่ศอก",
             "ญาติผู้ป่วยลื่นล้มหน้าห้องน้ำรวมที่พื้นเปียก"],
    "pressure": ["พบแผลกดทับระยะ 2 บริเวณก้นกบในผู้ป่วยติดเตียง รับ refer มาจาก รพ.สต."],
    "surgery": ["เครื่องมือผ่าตัดชุดสำรองไม่พร้อมใช้ ต้องเลื่อนเวลาผ่าตัด 40 นาที",
                "นับ gauze หลังผ่าตัดไม่ครบ ตรวจซ้ำพบครบภายในห้องผ่าตัด"],
    "blood": ["ส่ง specimen จองเลือดผิดหลอด ตรวจพบที่คลังเลือดก่อนเตรียมเลือด"],
    "diag": ["ผล film chest มี nodule แต่ไม่ได้ถูกตามต่อ พบจากการทบทวนเวชระเบียน"],
    "refer": ["ประสานรถ refer ล่าช้าจากรถติดภารกิจ ทำให้ออกตัวช้า 30 นาที"],
    "lab_report": ["รายงานผล K สูงวิกฤตทางโทรศัพท์แล้วไม่ได้ลงบันทึกรับทราบในระบบ"],
    "cpr": ["ผู้ป่วย sepsis ทรุดลงในตึกสามัญ ประเมิน early warning score ไม่ต่อเนื่องช่วงเปลี่ยนเวร"],
    "other_cps": ["สายน้ำเกลือหลุดระหว่างเคลื่อนย้ายผู้ป่วยไปตรวจพิเศษ"],
    "pph": ["ผู้คลอดตกเลือดหลังคลอดประมาณ 700 ml ได้รับการดูแลตาม protocol อาการคงที่"],
    "asphyxia": ["ทารกแรกเกิด Apgar 6 ที่ 1 นาที กระตุ้นแล้วดีขึ้นเป็น 9 ที่ 5 นาที"],
    "newborn": ["ทารกตัวเหลืองเกินเกณฑ์ต้องส่องไฟซ้ำหลังจำหน่าย"],
    "psych": ["ผู้ป่วยจิตเวชอาละวาดใน ER ทำลายอุปกรณ์ ควบคุมสถานการณ์ได้ ไม่มีผู้บาดเจ็บ"],
    "hd": ["ผู้ป่วยความดันตกระหว่างฟอกเลือด แก้ไขตามแนวทางแล้วฟอกต่อได้"],
    "stroke": ["ผู้ป่วย stroke มาถึงใน window แต่แจ้ง fast track ล่าช้า 15 นาทีจากการคัดกรอง"],
    "stemi": ["EKG ทำช้ากว่าเกณฑ์ 10 นาทีในผู้ป่วยเจ็บหน้าอก เนื่องจากผู้ป่วยหนาแน่น"],
    "sepsis": ["ให้ยาปฏิชีวนะ dose แรกช้ากว่าเกณฑ์ 1 ชั่วโมงในผู้ป่วยเข้าเกณฑ์ sepsis"],
    "other_sp": ["ผู้ป่วยเบาหวานน้ำตาลต่ำระหว่างงดน้ำงดอาหารรอตรวจพิเศษ"],
    "needle": ["พยาบาลถูกเข็มตำขณะ recap เข็มหลังฉีดยา ล้างแผลและเข้ากระบวนการตรวจเลือดตามแนวทาง",
               "ผู้ช่วยเหลือคนไข้ถูกของมีคมบาดขณะแยกขยะ พบเข็มปนอยู่ในถุงขยะทั่วไป"],
    "fluid": ["เลือดกระเด็นเข้าตาขณะช่วยทำหัตถการ ล้างตาทันทีและพบแพทย์ตามแนวทาง"],
    "assault": ["ญาติผู้ป่วยไม่พอใจการรอคอย ตะโกนด่าและขว้างเอกสารใส่เจ้าหน้าที่ห้องบัตร"],
    "ergo": ["เจ้าหน้าที่ปวดหลังเฉียบพลันหลังยกผู้ป่วยเปลี่ยนเตียงโดยไม่มีผู้ช่วย"],
    "occ_inf": ["บุคลากรสัมผัสผู้ป่วยวัณโรคก่อนทราบผล ตรวจคัดกรองผู้สัมผัสตามแนวทาง"],
    "chem": ["น้ำยาฆ่าเชื้อหกใส่มือขณะผสม ไม่ได้สวมถุงมือ ล้างด้วยน้ำสะอาดแล้วอาการปกติ"],
    "other_psg": ["เจ้าหน้าที่เวรดึกเวียนศีรษะจากพักผ่อนไม่พอ จัดเวรสำรองแทน"],
    "complaint": ["ญาติร้องเรียนการสื่อสารของเจ้าหน้าที่จุดคัดกรองว่าพูดจาไม่เหมาะสม",
                  "ผู้รับบริการร้องเรียนรอคิวรับยานานกว่า 2 ชั่วโมงในช่วงบ่าย"],
    "fire": ["เบรกเกอร์ตึกผู้ป่วยนอก trip ช่วงพายุฝน ไฟสำรองทำงานปกติ กู้คืนใน 20 นาที"],
    "it_down": ["ระบบ HIS ช้าผิดปกติช่วง 9:00-10:30 ทำให้คิวห้องตรวจสะสม ใช้แบบฟอร์มกระดาษสำรอง"],
    "data_leak": ["พบเอกสารสรุปเวชระเบียนวางค้างที่เครื่องถ่ายเอกสารส่วนกลาง เก็บคืนและทบทวนแนวทาง"],
    "property": ["ทรัพย์สินผู้ป่วยสูญหายระหว่างย้ายตึก ตรวจสอบกล้องวงจรปิดอยู่"],
    "env": ["ถังขยะติดเชื้อหน้าตึกล้นช่วงวันหยุดยาว จัดรอบเก็บเพิ่ม"],
    "security": ["บุคคลภายนอกเข้าหอผู้ป่วยนอกเวลาเยี่ยมโดยไม่แลกบัตร"],
    "other_osg": ["น้ำรั่วจากฝ้าเพดานห้องเก็บเวชภัณฑ์หลังฝนตกหนัก"],
}
DRUGS = ["Ceftriaxone", "Enalapril", "Metformin", "Warfarin", "Amlodipine", "Paracetamol", "Insulin RI"]
ACTIONS = ["ประเมินอาการ/ความเสียหายทันที รายงานหัวหน้าเวร และบันทึกเหตุการณ์",
           "แจ้งแพทย์เวรรับทราบ ให้การดูแลเบื้องต้น และเฝ้าระวังต่อเนื่อง",
           "แก้ไขหน้างานทันที ทบทวนกับทีมในเวร และแจ้งหน่วยงานที่เกี่ยวข้อง",
           "หยุดกระบวนการที่เป็นความเสี่ยง ตรวจสอบซ้ำ และรายงานตามลำดับชั้น"]
REPORTERS = ["พว.สายฝน", "พว.กมลชนก", "นพ.ธีรภัทร", "ภก.ศุภชัย", "พว.อรทัย", "จนท.วิชัย", "พว.นภาพร", ""]
COMMITTEE = ["พว.ปนัดดา (กรรมการความเสี่ยง)", "นพ.สมชาย (ประธาน RM)", "ภก.วรรณา (กรรมการความเสี่ยง)"]
RESP_ACK = ["รับเรื่องแล้ว มอบหมายหน่วยงานทบทวน", "รับเรื่องแล้ว ประสานหัวหน้าหน่วยงานที่เกี่ยวข้อง"]
RESP_FIX = ["หน่วยงานทบทวนสาเหตุร่วมกันในเวรประชุมเช้า กำหนดแนวทางป้องกันซ้ำ",
            "จัดทำ flow ใหม่และสื่อสารให้ทุกเวรรับทราบ", "เพิ่ม double check ในจุดที่เกิดเหตุ",
            "ทบทวน RCA ร่วมกับทีมสหวิชาชีพ"]
RESP_CLOSE = ["ดำเนินการแก้ไขครบถ้วน ติดตาม 1 เดือนไม่พบเหตุซ้ำ ปิดเคส",
              "ปรับแนวทางปฏิบัติและประกาศใช้แล้ว ปิดเคส", "สื่อสารผลการแก้ไขกลับหน่วยงานผู้รายงานแล้ว ปิดเคส"]


def _w(pairs):
    vals, weights = zip(*pairs)
    return random.choices(vals, weights=weights, k=1)[0]


def run(n=380):
    now = datetime.now()
    for _ in range(n):
        group = _w(GROUP_W)
        topic_key = f"topic_{group}"
        topic = random.choice(_OPTS[topic_key])
        unit = _w(UNIT_W)
        age_days = min(random.expovariate(1 / 130), 364)   # เอนไปทางเคสช่วงหลัง ให้เดือนล่าสุดคึกกว่า
        occurred = now - timedelta(days=age_days, hours=random.uniform(0, 24))
        found = occurred + timedelta(hours=random.choice([0, 0, 0, 4, 24, 48]))
        reported = found + timedelta(hours=random.uniform(0.5, 30))

        data = {
            "unit": unit,
            "place_type": random.choice(_OPTS["place_type"]),
            "incident_group": group,
            topic_key: topic,
            "affected": ("staff" if group == "psg" else "org" if group == "osg"
                         else _w([("ipd", 55), ("opd", 30), ("family", 5), ("none", 10)])),
            "occur_date": occurred.strftime("%Y-%m-%d"),
            "found_date": found.strftime("%Y-%m-%d"),
            "shift": _w([("morning", 45), ("evening", 33), ("night", 22)]),
            "source": _w([("self", 55), ("round", 12), ("chart", 10), ("complaint", 12),
                          ("other_unit", 7), ("committee", 4)]),
            "initial_action": random.choice(ACTIONS),
            "reporter_name": random.choice(REPORTERS),
            "detail": random.choice(DETAIL.get(topic, ["(รายละเอียดเหตุการณ์จำลอง)"])).format(
                drug=random.choice(DRUGS)),
        }
        if group == "osg":
            data["severity_org"] = _w(SEV_ORG_W)
        else:
            data["severity_clin"] = _w(SEV_CLIN_W)
        if random.random() < 0.5:
            data["cf_1"] = random.choice(["no", "yes", "na"])

        inc_id = db.add_incident(data, CONFIG["severe_clinical"], CONFIG["severe_general"],
                                 reported_at=reported.isoformat(timespec="seconds"))

        # เดินสถานะย้อนหลังให้สมจริง — เคสรุนแรงถูกรับเรื่องไวกว่า, เคสเก่าส่วนใหญ่ปิดแล้ว
        inc = db.get(inc_id)
        severe = inc["severe"]
        ack_delay_h = random.uniform(0.2, 6) if severe else random.uniform(1, 60)
        ack_at = reported + timedelta(hours=ack_delay_h)
        resolve_days = random.uniform(0.5, 6) if severe else random.uniform(1, 25)
        resolved_at = ack_at + timedelta(days=resolve_days)
        by = random.choice(COMMITTEE)

        if ack_at < now and random.random() < 0.95:
            db.add_response(inc_id, "ack", random.choice(RESP_ACK), by,
                            new_status="ack", at=ack_at.isoformat(timespec="seconds"))
            mid = ack_at + timedelta(days=resolve_days * 0.4)
            if mid < now and random.random() < 0.85:
                db.add_response(inc_id, "progress", random.choice(RESP_FIX), by,
                                new_status="resolving", at=mid.isoformat(timespec="seconds"))
                if resolved_at < now and random.random() < 0.88:
                    db.add_response(inc_id, "close", random.choice(RESP_CLOSE), by,
                                    new_status="resolved", at=resolved_at.isoformat(timespec="seconds"))
                    if random.random() < 0.8:
                        db.mark_nrls_sim(inc_id, at=(resolved_at + timedelta(days=1)).isoformat(timespec="seconds"))
    print(f"seeded {db.count_all()} incidents")


if __name__ == "__main__":
    db.init()
    run()
