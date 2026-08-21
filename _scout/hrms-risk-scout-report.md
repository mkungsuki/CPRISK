# Scout Report: hrms-risk

**Date:** 2026-08-21
**Spec source:** _intake/hrms-risk-spec.md
**Mode:** light scout (ตาม handoff — เน้น local reuse, external เท่าที่จำเป็น)

## Verdict: 🔧 FORK & EXTEND — ใช้โค้ดเบส SSCC (C:\SSCC\app) เป็นแกน + Chart.js (vendored) สำหรับกราฟ

Fit ของ SSCC ต่อ P0 mock: **~75%** (feature fit 7/10 ×40% + maintenance 10/10 ×20% [โค้ดเราเอง ผ่าน E2E จริง] + license 10/10 ×15% [ของเราเอง] + stack 10/10 ×15% + docs 6/10 ×10%)

## Local Assets ที่ Reuse ได้ (verified โดยอ่านโค้ดจริง — Tier 1)

| Asset | ที่อยู่ | สภาพ | ใช้กับ hrms-risk |
|---|---|---|---|
| Schema-driven form engine | `app/schema/sscc_fields.json` (136 fields, types: text/number/date/time/select/textarea/checkbox-group, มี show_if/required/pattern/section) + `templates/form.html` | ✅ ใช้จริงอยู่ | เขียน `hrms_fields.json` ใหม่ตามฟอร์ม HRMS → ได้ฟอร์มทันทีโดยไม่แก้ engine |
| DB layer | `app/db.py` (SQLite, JSON-per-row, status draft/submitted) | ✅ | ขยาย status เป็น workflow (reported→ack→resolving→resolved→submitted) + เพิ่มตาราง responses |
| Custom fields (form builder) | `app/schema/custom_fields.json` + route `/fields` + `/api/custom_fields` | ✅ | จุดขาย "เพิ่มตัวชี้วัดเองได้" — ยกไปทั้งชุด |
| Queue ส่งเข้าเว็บกลาง | `server.py` `/queue/*` + `fill_sscc.py` (Playwright+Edge, session profile ใน `data/edge_profile`) | ✅ ผ่าน E2E เว็บจริง | **P1 เท่านั้น** — mock ไม่แตะ; ตอน P1 เขียน `fill_hrms.py` ตาม pattern เดิม |
| Mock target site + tests | `app/mock/mock_sscc.py`, `test_e2e.py`, `test_queue.py` | ✅ | pattern สำหรับ `mock_hrms` ตอน P1 |
| Templates/UI ไทย | `templates/base.html`, `list.html`, `dq.html` | ✅ | โครง layout + ภาษา UI |
| Deploy scripts | `setup.bat`, `start.bat`, `update.bat`, `tools/make_deploy_zip.py` | ✅ | ใช้ท่าเดียวกัน |

**Stack เดิม:** Flask + SQLite + Playwright + openpyxl (`requirements.txt`) — ตรง spec "แนวเดียวกับ SSCC"

## Gap Analysis (ของที่ต้องสร้างใหม่สำหรับ mock)

### Gap 1: Multi-role views (ผู้กรอก / กรรมการ / ผู้บริหาร)
- Status: CONFIRMED MISSING — SSCC เป็น single-role (grep server.py: ไม่มี user/role/login)
- Mock: ทำเป็น role switcher ง่ายๆ (เลือกบทบาทตอนเข้า ไม่ต้อง auth จริง) / ระบบจริง = P1
- Effort mock: ~ครึ่งวัน

### Gap 2: Workflow ตอบกลับ + แจ้งเตือน 2 ระดับ
- Status: CONFIRMED MISSING — SSCC มีแค่ draft/submitted, ไม่มี response loop
- Mock: เพิ่ม status chain + ตาราง response + หน้ารวมเรียงตามความแรง
- Effort mock: ~ครึ่งวัน

### Gap 3: Dashboard กราฟ
- Status: CONFIRMED MISSING — SSCC ไม่มี chart เลย (templates ไม่มี canvas/svg chart)
- แก้ด้วย external: **Chart.js** (donut ตรงหน้าตา HRMS, vendored ไฟล์เดียว ใช้ offline ใน intranet ได้)
- Effort mock: ~ครึ่งวัน (รวม metric queries)

### Gap 4: หน้าเปรียบเทียบช่องทางแจ้งเตือน
- Status: CONFIRMED MISSING — หน้า static content ใหม่
- Effort mock: ~1-2 ชม.

### Gap 5: ฟอร์ม HRMS schema + seed ข้อมูลปลอม
- Status: ต้องเขียนใหม่ (มี screenshot ฟอร์มจริงเป็นต้นแบบ; dropdown ครบชุดเก็บจากเว็บจริงตอน P1)
- Effort mock: ~ครึ่งวัน

## External Candidate (ตัวเดียว)

### Chart.js
- URL: https://github.com/chartjs/Chart.js
- Verified 2026-08-21:
  - License: **MIT** via raw-fetch `raw.githubusercontent.com/chartjs/Chart.js/master/LICENSE.md` (Tier 2) ✅
  - Health: 67,652 ⭐, pushed 2026-05-27 via github-api (Tier 3) ✅
- ใช้แบบ vendored ไฟล์ UMD เดียว (ไม่พึ่ง CDN — intranet ต้อง offline ได้)
- Fallback ถ้าไม่อยากมี dependency: donut ด้วย SVG stroke-dasharray เขียนเองได้ (~50 บรรทัด) — เก็บเป็นทางหนีไว้

## Verification Audit
| Claim | Source | Tier | Verified |
|---|---|---|---|
| SSCC form engine schema-driven, 7 field types, show_if | อ่าน `app/schema/sscc_fields.json` + form.html จริง | 1 | ✅ |
| SSCC ไม่มี role/chart/response-loop | grep `server.py`, templates | 1 | ✅ |
| Chart.js MIT | raw LICENSE.md | 2 | ✅ |
| Chart.js active (2026-05) | GitHub API | 3 | ✅ |

## Next Step
- Handoff → architect/build: ตั้งโปรเจกต์ใหม่ (แนะนำ `C:\CPRISK` หรือโฟลเดอร์แยกใน C:\SSCC) โดย copy โครง app ของ SSCC มาเป็นฐาน แล้วปิด 5 gaps ตามลำดับ: schema ฟอร์ม → workflow/status → role views → dashboard → หน้าช่องทางแจ้งเตือน + seed data
- Architecture decisions ใน spec ยังคุมทุกข้อ (ไม่ auto-fire, mock ไม่แตะเว็บรัฐจริง ฯลฯ)
