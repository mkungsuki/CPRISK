# CPRISK — ระบบบริหารความเสี่ยง รพ.ชุมแพ

ระบบกรอกอุบัติการณ์ "กรอกครั้งเดียวที่ รพ." เก็บลงฐานของ รพ. ก่อน → กรรมการความเสี่ยงรับเรื่อง-ตอบกลับ
→ ตรวจทานแล้วค่อยส่งเข้าเว็บกลาง HRMS/NRLS (cphos.thai-nrls.org, HRMS v6.3)
พี่น้องกับโปรเจกต์ **SSCC Stroke** (`C:\SSCC`) — ยกโครง/แนวคิดมาจากที่นั่น

## สถานะ (2026-08-21)

- **Mock เสร็จแล้ว ผ่าน E2E ในเบราว์เซอร์แล้ว** (ฟอร์ม→คิวกรรมการ→ปิดเคส→NRLS จำลอง→dashboard→custom fields)
- **มีเว็บ NRLS จำลองแล้ว** (`/nrls-sim/<id>` + `templates/nrls_sim.html`) — โคลนโครงฟอร์ม HRMS v6.3 สไตล์เว็บราชการ
  กดจากหน้าเคส → ระบบกรอกอัตโนมัติทีละช่อง (animation) → กรรมการตรวจทานแล้วกดบันทึกเอง → mark ส่ง NRLS
  แสดงเฉพาะฟิลด์ที่เข้าเงื่อนไข show_if ของเคส, custom fields ไม่โผล่ (ไม่ส่งเข้า NRLS), ผ่าน E2E แล้ว
- **ผ่าน blind review 2 ทีม + แก้ชุดก่อนเดโม HA แล้ว** (2026-08-21) — รายงานเต็มใน `_review/`
  ที่แก้ไป: สี badge severity ใหม่ (ไล่โทน+contrast ผ่าน, tooltip คำอธิบาย), ชื่อผู้ดำเนินการบังคับกรอก+จำใน
  localStorage (เลิก default ชื่อบุคคล), ฟอร์ม validate ค้าง+ลำดับวันที่ (client+server), inbox เรียง
  "ล่าสุดก่อน" เป็น default+สลับได้+sticky header+แถวปิดแล้วจางลง+ทั้งแถวคลิกได้, มือถือไม่ล้นจอแล้ว
  (inbox/case), ปิดเคสมี confirm+เปิดเคสใหม่ได้ (action `reopen`), กระดิ่งชี้ /inbox?severe=1&status=new,
  กราฟแนวโน้มติดป้ายเดือนยังไม่จบ, line-height 1.6
- **มีหน้า `/qr`** — QR ชี้ https://github.com/mkungsuki/CPRISK (แก้ได้ที่ `config.json` ค่า `qr_url`)
  ใช้ `static/qrcode.min.js` (qrcodejs, MIT, vendored — offline ได้)
- ยังไม่แก้ (รอ P1/ตัดสินใจ): login/สิทธิ์, หน้าติดตามเคสของผู้รายงาน (ทั้งสอง review ชี้ตรงกัน — เพิ่มเข้า P1),
  export dashboard, pagination inbox, ผูก label for/id (a11y), ศัพท์กลุ่มอุบัติการณ์อังกฤษล้วน
- เส้นตาย: มีของโชว์ "กำลังพัฒนา" ภายใน 2 วัน (ผ่านแล้ว) → **เดโมให้ HA ดูได้อาทิตย์หน้า** → ระบบจริงไม่รีบ
- โหมดงาน: ช่วยงาน รพ. (ไม่คิดเงิน ไม่มี quote) — คนสั่งงานคือฝ่ายบริหาร/กรรมการความเสี่ยง

## เอกสารกำกับ (อยู่ในโปรเจกต์นี้แล้ว)

- `_intake/hrms-risk-spec.md` — spec ที่ผู้ใช้ยืนยันแล้ว (requirement, priority, เกณฑ์สำเร็จ)
- `_scout/hrms-risk-scout-report.md` — ผล scout ว่ายกอะไรจาก SSCC มาได้บ้าง
- `README.md` — วิธีเปิดเดโม + ท่าเดโมแนะนำ + แผน P1

## การตัดสินใจที่ล็อกแล้ว (ห้าม re-debate เว้นแต่ผู้ใช้สั่งเปลี่ยน)

1. **ไม่ยิงเข้า NRLS อัตโนมัติ** — เก็บเป็นคิว/draft ให้กรรมการตรวจก่อนกดส่ง (human-in-loop)
2. **Mock ห้ามแตะเว็บรัฐจริง** — ปุ่มส่ง NRLS เป็นจำลองจนกว่าจะเข้าเฟส P1 และมี account จริงทดสอบ
3. **ช่องทางแจ้งเตือนไม่ตัดสินใจแทน** — หน้า `/channels` เสนอตัวเลือกให้บริหารเลือก (กันผู้พัฒนากลายเป็นผู้ดูแลถาวร)
4. **ฟอร์มยึดฟิลด์ตามเว็บ HRMS จริง** เพื่อ map 1:1 ตอนส่งจริง — ชุด dropdown ปัจจุบันเป็นชุดย่อจาก screenshot
   ชุดเต็มต้องเก็บจากเว็บจริงตอน P1
5. เกณฑ์เคสรุนแรง: clinical E–I / ทั่วไป 3–5 — ตั้งค่าได้ใน `app/config.json`

## โครงทางเทคนิค

- **Flask + SQLite** (JSON ต่อแถวใน `incidents.data` + คอลัมน์สรุปแยกไว้ให้ dashboard คิวรีเร็ว) — `app/db.py`
- **ฟอร์ม schema-driven**: `app/schema/hrms_fields.json` ขับ `templates/form.html` — แก้ฟอร์ม = แก้ JSON ไม่แตะโค้ด
  (engine เดียวกับ SSCC: type text/number/date/time/select/textarea/checkbox-group + `show_if` + select ≤4 ตัวเลือกเป็นปุ่มกด)
- **Custom fields**: `app/schema/custom_fields.json` + หน้า `/fields` — รพ. เพิ่มตัวชี้วัดเอง โผล่ท้ายฟอร์มทันที
- **Chart.js ฝังไฟล์** `app/static/chart.umd.js` (MIT, vendored) — ต้องใช้งานได้ offline ใน intranet ห้ามพึ่ง CDN
- **Seed เดโม**: ฐานว่าง + `demo_seed: true` → seed 380 เคสจำลองอัตโนมัติ (`app/seed.py`, deterministic)
  ล้างเดโม: ลบ `app/data/cprisk.db` แล้วเปิดใหม่
- Port 8548 (`app/config.json`) — เปิดด้วย `app/start.bat` หรือ `python app/server.py`
- ภาษา UI ไทยทั้งหมด กลุ่มเป้าหมายคือคนหน้างาน ไม่ใช่คนไอที — ทุกข้อความต้องอ่านรู้เรื่องโดยไม่ต้องอธิบาย

## แผน P1 (ระบบจริง — เรียงตามลำดับ)

1. **ยิงเข้า NRLS จริง**: เขียน `fill_hrms.py` ตาม pattern `C:\SSCC\app\fill_sscc.py`
   (Playwright + Edge profile จำ session, spawn subprocess + runlock, คิวหลายเคส, ผู้ใช้ login เอง
   โปรแกรมกรอกให้ แล้ว**คนตรวจก่อนกดบันทึกบนเว็บเสมอ**) + เก็บ dropdown/รหัสอุบัติการณ์ชุดเต็มจากเว็บจริง
2. **Multi-user จริง**: ย้ายขึ้นเครื่อง intranet (บริหารคุยกับ IT รพ. — ไม่ใช่งานเรา) + login/สิทธิ์ 3 บทบาท
   (ผู้กรอก/กรรมการ/ผู้บริหาร) + **หน้าติดตามเคสของผู้รายงาน** (เลขเคส+รหัสลับ เห็นสถานะ/คำตอบกลับ —
   blind review ทั้งสองทีมชี้ตรงกันว่าจำเป็นต่อแรงจูงใจการรายงาน)
3. **ช่องทางแจ้งเตือน** ตามที่บริหารเลือกจาก `/channels` (แนวโน้ม: LINE OA เฉพาะเคสรุนแรง ส่งแค่เลขเคส+ระดับ ไม่ส่งข้อมูลผู้ป่วย)
4. **Export Excel รายงาน HA** — ยก pattern `C:\SSCC\app\excel_export.py`

## กติกาที่สืบทอดจาก SSCC (บทเรียนที่จ่ายมาแล้ว)

- ข้อมูลผู้ป่วยอยู่ในเครื่อง/intranet เท่านั้น — ห้ามขึ้น cloud, เตือนผู้ใช้เรื่อง OneDrive/ไดรฟ์แชร์ (PDPA)
- update script ห้ามทับ `custom_fields.json` ที่ รพ. แก้เอง (ใช้กลไก defaults + `_defaults_seen` แบบ SSCC ถ้าทำ update.bat)
- ระวังบั๊ก .bat กับ CRLF (เคยล้าง .bat เป็น 0 byte ทั้งชุดที่ SSCC)
- ก่อนส่งจริงทุกเวอร์ชัน ต้องผ่าน E2E กับ mock ของเว็บเป้าหมาย (SSCC มี `app/mock/mock_sscc.py` + tests เป็นตัวอย่าง)
