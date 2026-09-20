# ตั้งค่าฐานข้อมูล Supabase

## 1. สร้างโปรเจกต์

1. เข้า https://supabase.com และสร้างโปรเจกต์ใหม่
2. เปิดเมนู **SQL Editor**
3. เปิดไฟล์ `supabase_schema.sql` ใน repository นี้
4. คัดลอก SQL ทั้งหมดไปวาง แล้วกด **Run**

## 2. คัดลอกค่าการเชื่อมต่อ

ใน Supabase ไปที่ **Project Settings > API** แล้วคัดลอก:

- **Project URL**
- **Publishable key** (หรือ anon key ในหน้าตาแบบเก่า)

ห้ามใช้ `service_role` key ในหน้าเว็บหรือ commit ลง GitHub

## 3. ตั้งค่าใน Streamlit Cloud

ไปที่ **App settings > Secrets** แล้วเพิ่ม:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-publishable-or-anon-key"
```

จากนั้นกด **Reboot app**

## 4. ตั้งค่าในเครื่อง

Linux/macOS:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-publishable-or-anon-key"
streamlit run app/app.py
```

Windows PowerShell:

```powershell
$env:SUPABASE_URL="https://your-project.supabase.co"
$env:SUPABASE_KEY="your-publishable-or-anon-key"
streamlit run app/app.py
```

เมื่อมีตัวแปรทั้งสองค่า ระบบจะบันทึกรีวิวไปที่ Supabase และคำนวณค่าเฉลี่ยจากข้อมูลออนไลน์ ทุกคนจึงเห็นข้อมูลชุดเดียวกัน

ถ้าไม่ตั้งค่าตัวแปร ระบบจะ fallback ไปใช้ `app/feedback.db` สำหรับการทดลองในเครื่อง
