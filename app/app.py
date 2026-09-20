# ============================================================
# ระบบแนะนำวิชาเสรี — Streamlit Edition
# Green Meridian Theme
# ============================================================

import re

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from course_data import (
    MANDATORY_COURSES,
    ELECTIVE_COURSES,
    enrollment,
    time_to_minutes,
    time_overlap,
    class_conflict,
    exam_conflict,
)
from feedback_database import initialize_database, get_feedback_summary, save_feedback

initialize_database()

# ============================================================
# Page config
# ============================================================
st.set_page_config(
    page_title="ระบบแนะนำวิชาเสรี",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Helper: render raw HTML safely
# ------------------------------------------------------------
# Streamlit's st.markdown() treats any line indented with 4+
# spaces as a Markdown code block, even with unsafe_allow_html
# =True. Since our HTML strings are built inside indented
# Python blocks (for-loops / with-blocks), the f-strings carry
# that indentation along with them.
#
# dedent() alone isn't enough: whenever an f-string conditional
# evaluates to '' (e.g. the "⭐ อันดับ 1" badge on non-top rows),
# that line becomes blank, and Markdown always treats a blank
# line as the end of an HTML block — regardless of indentation.
# The remaining lines then start a new block the parser doesn't
# trust as HTML, so it falls back to showing raw text.
#
# Collapsing every run of whitespace (including newlines) down
# to a single space removes blank lines and indentation at the
# same time, so this can't happen no matter how the f-string
# branches.
# ============================================================
def render_html(html: str):
    collapsed = re.sub(r"\s+", " ", html).strip()
    st.markdown(collapsed, unsafe_allow_html=True)


KEYWORD_SUGGESTIONS = [
   "",
   "เรียนง่าย",
   "A ง่าย",
   "ดาราศาสตร์",
   "สิ่งแวดล้อม",
   "มลพิษ",
   "พลังงาน",
   "เทคโนโลยี",
   "เทคโนโลยีสารสนเทศ",
   "คอมพิวเตอร์",
   "การเขียนโปรแกรม",
   "วิทยาการข้อมูล",
   "การวิเคราะห์ข้อมูล",
   "ภาษาอังกฤษ",
   "การสื่อสาร",
   "ศิลปะ",
   "การออกแบบวงจร",
   "ชีววิทยา",
   "จุลินทรีย์",
   "เคมี",
   "ฟิสิกส์",
   "แคลคูลัส",
   "คณิตศาสตร์",
   "สถิติ",
   "ความน่าจะเป็น",
   "ธุรกิจ",
   "เครื่องสำอาง",
   "อาหาร",
   "สุขภาพ",
   "ภาวะผู้นำ",
   "วัฒนธรรม",
   "กฎหมายและจริยธรรม",
   "สมบัติของจำนวนจริง",
   "ค่าสัมบูรณ์",
   "อัตราส่วน",
   "ร้อยละ",
   "การเทียบบัญญัติไตรยางศ์",
   "พหุนาม",
   "เศษส่วนของพหุนาม",
   "การแก้สมการและอสมการพหุนาม",
   "ระบบสมการเชิงเส้น",
   "ฟังก์ชัน",
   "ฟังก์ชันผกผัน",
   "ฟังก์ชันเชิงกำลัง",
   "ฟังก์ชันลอการิทึม",
   "กราฟของฟังก์ชันพื้นฐาน",
   "ทฤษฎีบทพีทาโกรัส",
   "ฟังก์ชันตรีโกณมิติ",
   "เมทริกซ์",
   "พีชคณิต",
   "เรขาคณิต",
   "เวกเตอร์",
   "ความสัมพันธ์",
   "อัตราการเปลี่ยนแปลง",
   "อนุพันธ์",
   "ปริพันธ์",
   "พื้นที่ระหว่างเส้นโค้ง",
   "อนุกรมเทย์เลอร์",
   "อนุกรมแมคคลอริน",
   "สมการเชิงอนุพันธ์",
   "ลำดับ",
   "อนุกรมอนันต์",
   "อนุกรมกำลัง",
   "ลิมิต",
   "ความต่อเนื่อง",
   "ค่าสุดขีด",
   "กฎของโลปิตาล",
   "พิกัดเชิงขั้ว",
   "เลขยกกำลัง",
   "ฟังก์ชันเอกซ์โพเนนเชียล",
   "ปริพันธ์หลายชั้น",
   "ตัวแปรเชิงซ้อน",
   "ระบบพิกัด",
   "ปรากฏการณ์ทางธรรมชาติบนโลก",
   "บรรยากาศโลก",
   "การพยากรณ์ทางอุตุนิยมวิทยา",
   "การเปลี่ยนแปลงสภาพภูมิอากาศ",
   "ปรากฏการณ์ทางดาราศาสตร์",
   "การสังเกตการณ์ทางดาราศาสตร์",
   "ระบบสุริยะ",
   "ดาวฤกษ์",
   "การประยุกต์ใช้ในชีวิตประจำวัน",
   "สหัสวรรษ",
   "ความรู้พื้นฐาน",
   "การประยุกต์",
   "ความคิดสร้างสรรค์",
   "การรักษาความมั่นคง",
   "กฎหมาย",
   "จริยธรรม",
   "เทคโนโลยีฐานข้อมูล",
   "การสื่อสารข้อมูล",
   "ระบบสารสนเทศ",
   "โดเมนแอปพลิเคชัน",
   "วิวัฒนาการของเทคโนโลยีสารสนเทศ",
   "แนวคิดการสร้างโปรแกรม",
   "การเขียนโปรแกรมเบื้องต้น",
   "ชนิดของข้อมูล",
   "ฟังก์ชันมาตรฐาน",
   "ไลบรารี่",
   "โปรแกรม",
   "โปรแกรมสำเร็จรูป",
   "ผังงาน",
   "ขั้นตอนการแก้ปัญหา",
   "ทฤษฎีความต้องการ",
   "มนุษย์",
   "ทักษะ",
   "ผู้นำ",
   "การพัฒนา",
   "ความแตกต่าง",
   "การสร้างทีม",
   "แรงจูงใจ",
   "มนุษยสัมพันธ์",
   "การแก้ปัญหา",
   "การตัดสินใจ",
   "การบริหารความขัดแย้ง",
   "การควบคุม",
   "การจัดการความเครียด",
   "ปรัชญา",
   "ความหมาย",
   "ศาสตร์พระราชา",
   "โครงการพระราชดำริ",
   "ดิน",
   "น้ำ",
   "ป่า",
   "อาชีพ",
   "วิศวกรรม",
   "เศรษฐกิจพอเพียง",
   "ทฤษฎีใหม่",
   "การพัฒนาตนเอง",
   "ชุมชน",
   "สังคม",
   "ประเทศชาติ",
   "ทรัพยากรธรรมชาติ",
   "ปัญหาสิ่งแวดล้อม",
   "ภัยคุกคาม",
   "กายภาพ",
   "ชีวภาพ",
   "ศิลปกรรม",
   "บริการระบบนิเวศ",
   "การท่องเที่ยวเชิงนิเวศ",
   "การอนุรักษ์",
   "ธรรมชาติ",
   "วิทยาศาสตร์",
   "มรดกโลก",
   "ระบบนิเวศ",
   "มลพิษทางน้ำ",
   "มลพิษทางอากาศ",
   "มลพิษทางดิน",
   "มูลฝอย",
   "ภาวะภูมิอากาศของโลก",
   "ความหลากหลายทางชีวภาพ",
   "สิ่งมีชีวิต",
   "คุณค่า",
   "ความงามของธรรมชาติ",
   "จิตสำนึก",
   "ความรับผิดชอบต่อสังคม",
   "อาหาร",
   "อุตสาหกรรมการเกษตร",
   "การแพทย์",
   "ความปลอดภัย",
   "ผู้บริโภค",
   "การจัดระบบสิ่งมีชีวิต",
   "เซลล์",
   "องค์ประกอบของเซลล์",
   "สารเคมีในสิ่งมีชีวิต",
   "โครงสร้าง",
   "ระบบอวัยวะ",
   "พฤติกรรม",
   "การปรับตัว",
   "นิเวศวิทยา",
   "พันธุศาสตร์",
   "การจัดจำแนกสิ่งมีชีวิต",
   "เมแทบอลิซึม",
   "อวัยวะ",
   "พันธุศาสตร์โมเลกุล",
   "พันธุศาสตร์ประชากร",
   "วิวัฒนาการ",
   "พืช",
   "สัตว์",
   "พฤติกรรมสัตว์",
   "ศาสตร์แขนงอื่น",
   "ปริมาณสัมพันธ์",
   "ทฤษฎีอะตอม",
   "โครงสร้างอะตอม",
   "ธาตุ",
   "ตารางธาตุ",
   "เคมีของธาตุ",
   "ธาตุกลุ่มหลัก",
   "อโลหะ",
   "โลหะทรานซิชัน",
   "พันธะเคมี",
   "แก๊ส",
   "ของเหลว",
   "ของแข็ง",
   "สารละลาย",
   "สมดุลเคมี",
   "สมดุลไอออน",
   "จลนพลศาสตร์เคมี",
   "จลนเคมี",
   "เทอร์โมไดนามิกส์",
   "กลศาสตร์ของอนุภาค",
   "วัตถุเกร็ง",
   "การสั่น",
   "คลื่น",
   "อุณหพลศาสตร์",
   "กลศาสตร์ของไหล",
   "เสียง",
   "สนามไฟฟ้า",
   "สนามแม่เหล็ก",
   "ทัศนศาสตร์",
   "ฟิสิกส์ยุคใหม่",
   "สมบัติของสสาร",
   "ทฤษฎีจลน์ของแก๊ส",
   "ควอนตัมฟิสิกส์",
   "วงจรไฟฟ้า",
   "แรง",
   "การเคลื่อนที่",
   "โมเมนตัม",
   "งาน",
   "แรงแม่เหล็ก",
   "ไฟฟ้า",
   "สัมพัทธภาพ",
   "โฟตอน",
   "กลศาสตร์ควอนตัม",
   "ปริมาณทางกายภาพ",
   "ระบบหน่วย",
   "ฟิสิกส์พื้นฐาน",
   "วิธีรวบรวมข้อมูล",
   "การแปลความหมายข้อมูล",
   "การนำเสนอ",
   "การจัดการข้อมูล",
   "การเก็บรวบรวมข้อมูล",
   "ระดับการวัด",
   "สถิติพรรณนา",
   "ตัวแปรสุ่ม",
   "การแจกแจงความน่าจะเป็น",
   "ทวินาม",
   "ปัวซอง",
   "ปกติ",
   "เลขชี้กำลัง",
   "การแจกแจงค่าตัวอย่าง",
   "การประมาณค่าพารามิเตอร์",
   "ช่วงความเชื่อมั่น",
   "การทดสอบสมมติฐาน",
   "สถิติไม่อิงพารามิเตอร์",
   "การถดถอย",
   "สหสัมพันธ์",
   "การวิเคราะห์ความแปรปรวน",
   "การประมวลผลข้อมูล",
   "การวิเคราะห์ทางสถิติ",
   "การแปลผล",
   "การเลือกตัวอย่าง",
   "การทดสอบไคกำลังสอง",
   "การตรวจสอบการแจกแจงปรกติ",
   "การแปลงข้อมูล",
   "การวิเคราะห์ความเกี่ยวพัน",
   "ตัวแปรจำแนกประเภท",
   "ความน่าจะเป็นแบบมีเงื่อนไข",
   "ความเป็นอิสระ",
   "ทฤษฎีบทของเบส์",
   "ค่าคาดหมาย",
   "การแจกแจงร่วม",
   "อสมการความน่าจะเป็น",
   "การลู่เข้า",
   "กฎจำนวนมาก",
   "การถดถอยเชิงเส้นพหุคูณ",
   "การถดถอยลอจิสติกทวิภาค",
   "การถดถอยหลายตัวแปร",
   "การประเมินตัวแบบ",
   "การคัดเลือกตัวแบบ",
   "เวกเตอร์ค่าเฉลี่ย",
   "เมทริกซ์ความแปรปรวนร่วม",
   "การจัดเตรียมข้อมูล",
   "ข้อมูลสูญหาย",
   "กราฟ",
   "แผนภาพ",
   "ตาราง",
   "สารสนเทศทางสถิติ",
   "การรายงาน",
   "สถิติพื้นฐาน",
   "การดูนก",
   "การจำแนกชนิด",
   "ถิ่นที่อยู่อาศัย",
   "พฤติกรรมการร้อง",
   "การหาอาหาร",
   "การสืบพันธุ์",
   "การสร้างรัง",
   "การอพยพ",
   "เทคโนโลยีการเพาะเห็ด",
   "การพัฒนาผลิตภัณฑ์อาหาร",
   "อาหารเสริมสุขภาพ",
   "เห็ด",
   "กฎระเบียบ",
   "มาตรฐานการเกษตร",
   "การผลิตอาหาร",
   "การทดลอง",
   "การประยุกต์ทางเคมี",
]


# ============================================================
# Green Meridian Theme — CSS
# ============================================================
render_html(
    """
    <style>
    :root{
        --meridian-950:#052e21;
        --meridian-900:#07402e;
        --meridian-800:#0a5c3f;
        --meridian-700:#0d7a52;
        --meridian-600:#129963;
        --meridian-500:#1cb578;
        --meridian-400:#3fd399;
        --meridian-300:#7ee6bb;
        --meridian-100:#e3faf0;
        --meridian-50:#f4fdf9;
        --gold:#d4af6a;
        --ink:#0e2a20;
        --card-radius:18px;
    }

    html, body, [class*="css"]{
        font-family: "Sarabun","Segoe UI",-apple-system,BlinkMacSystemFont,sans-serif;
    }

    /* ---------- App background ---------- */
    .stApp{
        background:
            radial-gradient(circle at 15% 0%, rgba(63,211,153,0.16), transparent 40%),
            radial-gradient(circle at 100% 20%, rgba(18,153,99,0.14), transparent 45%),
            linear-gradient(180deg, var(--meridian-50) 0%, #eef9f3 100%);
    }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"]{
        background: linear-gradient(195deg, var(--meridian-950) 0%, var(--meridian-800) 60%, var(--meridian-700) 100%);
    }
    section[data-testid="stSidebar"] *{
        color: var(--meridian-100) !important;
    }
    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea{
        background: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.35) !important;
        color: var(--ink) !important;
        border-radius: 12px !important;
    }
    /* placeholder text should stay readable but muted */
    section[data-testid="stSidebar"] input::placeholder,
    section[data-testid="stSidebar"] textarea::placeholder{
        color: #6b8f7f !important;
        opacity: 1 !important;
    }
    /* dropdown menu options (opens in a portal, not inside the sidebar) */
    div[data-baseweb="popover"] li,
    div[data-baseweb="popover"] div{
        color: var(--ink) !important;
    }
    section[data-testid="stSidebar"] label p{
        color: var(--meridian-300) !important;
        font-weight: 600;
    }

    /* ---------- Hero header ---------- */
    .hero{
        background: linear-gradient(120deg, var(--meridian-800) 0%, var(--meridian-600) 55%, var(--meridian-400) 130%);
        border-radius: 24px;
        padding: 2.1rem 2.4rem;
        color: white;
        box-shadow: 0 18px 40px -18px rgba(7,64,46,0.55);
        margin-bottom: 1.4rem;
        position: relative;
        overflow: hidden;
    }
    .hero::after{
        content:"";
        position:absolute; inset:0;
        background: radial-gradient(circle at 85% -10%, rgba(255,255,255,0.25), transparent 55%);
    }
    .hero h1{
        font-size: 2.1rem;
        margin: 0 0 .35rem 0;
        font-weight: 800;
        letter-spacing: .3px;
    }
    .hero p{
        margin:0;
        font-size: 1.02rem;
        opacity: .92;
        max-width: 640px;
    }
    .hero .badge{
        display:inline-block;
        background: rgba(255,255,255,0.18);
        border: 1px solid rgba(255,255,255,0.35);
        padding: .25rem .75rem;
        border-radius: 999px;
        font-size: .78rem;
        margin-bottom: .8rem;
        letter-spacing: .5px;
        backdrop-filter: blur(6px);
    }

    /* ---------- Section titles ---------- */
    .section-title{
        display:flex; align-items:center; gap:.55rem;
        color: var(--meridian-900);
        font-weight: 800;
        font-size: 1.25rem;
        margin: 1.6rem 0 .6rem 0;
    }
    .section-title .dot{
        width:10px; height:10px; border-radius:50%;
        background: linear-gradient(135deg, var(--meridian-400), var(--meridian-700));
        box-shadow: 0 0 0 4px rgba(28,181,120,0.18);
    }

    /* ---------- Generic card ---------- */
    .m-card{
        background: #ffffff;
        border: 1px solid rgba(10,92,63,0.10);
        border-radius: var(--card-radius);
        padding: 1.1rem 1.3rem;
        box-shadow: 0 10px 26px -18px rgba(10,92,63,0.35);
        margin-bottom: .9rem;
    }

    /* ---------- Result / rank card ---------- */
    .rank-card{
        background: linear-gradient(180deg, #ffffff 0%, var(--meridian-50) 100%);
        border: 1px solid rgba(10,92,63,0.12);
        border-left: 6px solid var(--meridian-500);
        border-radius: var(--card-radius);
        padding: 1.15rem 1.4rem;
        margin-bottom: 1rem;
        box-shadow: 0 14px 30px -20px rgba(7,64,46,0.4);
        transition: transform .15s ease, box-shadow .15s ease;
    }
    .rank-card:hover{
        transform: translateY(-2px);
        box-shadow: 0 18px 34px -18px rgba(7,64,46,0.45);
    }
    .rank-card.top1{ border-left-color: var(--gold); }

    .rank-pill{
        display:inline-flex; align-items:center; justify-content:center;
        min-width: 34px; height:34px; padding: 0 .5rem;
        border-radius: 999px;
        background: linear-gradient(135deg, var(--meridian-600), var(--meridian-800));
        color: white; font-weight: 800; font-size: .95rem;
        margin-right: .6rem;
    }
    .rank-card.top1 .rank-pill{
        background: linear-gradient(135deg, var(--gold), #b8863f);
    }

    .course-code{
        display:inline-block;
        background: var(--meridian-100);
        color: var(--meridian-800);
        font-weight: 700;
        font-size: .78rem;
        padding: .15rem .55rem;
        border-radius: 8px;
        letter-spacing: .3px;
    }

    .course-name{
        font-size: 1.12rem;
        font-weight: 800;
        color: var(--ink);
        margin: .35rem 0 .5rem 0;
    }

    .meta-row{
        display:flex; flex-wrap:wrap; gap: .45rem;
        font-size: .84rem; color:#2c4a3d;
        margin: .15rem 0;
    }
    .meta-chip{
        background: #f0fbf5;
        border: 1px solid rgba(10,92,63,0.14);
        border-radius: 8px;
        padding: .18rem .55rem;
    }

    .score-bar-wrap{
        background: #e7f6ee;
        border-radius: 999px;
        height: 9px;
        overflow: hidden;
        margin-top: .2rem;
    }
    .score-bar-fill{
        height: 100%;
        background: linear-gradient(90deg, var(--meridian-400), var(--meridian-700));
        border-radius: 999px;
    }

    .pass-tag{
        color: var(--meridian-700); font-weight:700; font-size:.85rem;
    }
    .fail-tag{
        color:#b3452c; font-weight:700; font-size:.85rem;
    }

    /* ---------- Buttons ---------- */
    .stButton>button, .stFormSubmitButton>button{
        background: linear-gradient(135deg, var(--meridian-600), var(--meridian-800));
        color: white;
        border: none;
        border-radius: 12px;
        padding: .6rem 1.4rem;
        font-weight: 700;
        letter-spacing: .3px;
        box-shadow: 0 10px 22px -12px rgba(10,92,63,0.55);
        transition: transform .12s ease;
        width: 100%;
    }
    .stButton>button:hover, .stFormSubmitButton>button:hover{
        transform: translateY(-1px);
        background: linear-gradient(135deg, var(--meridian-500), var(--meridian-700));
        color:white;
    }

    /* ---------- Metrics ---------- */
    div[data-testid="stMetric"]{
        background: #ffffff;
        border: 1px solid rgba(10,92,63,0.1);
        border-radius: 16px;
        padding: .8rem 1rem;
        box-shadow: 0 10px 24px -18px rgba(10,92,63,0.35);
    }
    div[data-testid="stMetricLabel"]{
        color: var(--meridian-700) !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }
    div[data-testid="stMetricLabel"] p{
        color: var(--meridian-700) !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricValue"]{
        color: var(--ink);
        font-weight: 800;
        white-space: normal;
        overflow-wrap: break-word;
        line-height: 1.2;
    }

    /* ---------- Tabs ---------- */
    button[data-baseweb="tab"]{
        font-weight: 700;
        color: var(--meridian-800);
    }
    div[data-baseweb="tab-highlight"]{
        background-color: var(--meridian-500) !important;
    }

    /* ---------- Expander ---------- */
    details{
        background: #ffffff !important;
        border: 1px solid rgba(10,92,63,0.12) !important;
        border-radius: 14px !important;
    }

    /* ---------- Responsive: tablet / mobile ---------- */
    @media (max-width: 900px){
        .hero{ padding: 1.5rem 1.3rem; border-radius: 18px; }
        .hero h1{ font-size: 1.5rem; }
        .hero p{ font-size: .92rem; }
        .rank-card{ padding: 1rem; }
        .course-name{ font-size: 1rem; }
    }
    @media (max-width: 480px){
        .hero h1{ font-size: 1.3rem; }
        .meta-row{ font-size: .78rem; }
        .rank-pill{ min-width: 28px; height:28px; font-size:.82rem; }

        /* 4 metric boxes: wrap into a 2x2 grid instead of squeezing
           into one row, and shrink text so it never gets cut off */
        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]){
            flex-wrap: wrap !important;
            gap: .6rem !important;
        }
        div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]) > div{
            flex: 1 1 45% !important;
            min-width: 45% !important;
        }
        div[data-testid="stMetric"]{
            padding: .7rem .8rem;
        }
        div[data-testid="stMetricLabel"] p{
            font-size: .78rem !important;
        }
        div[data-testid="stMetricValue"]{
            font-size: 1.25rem !important;
        }
    }
    </style>
    """
)

# ============================================================
# Session state
# ============================================================
if "results" not in st.session_state:
    st.session_state.results = None
if "mandatory_courses" not in st.session_state:
    st.session_state.mandatory_courses = None
if "filter_log" not in st.session_state:
    st.session_state.filter_log = None
if "valid_courses" not in st.session_state:
    st.session_state.valid_courses = None
if "search_meta" not in st.session_state:
    st.session_state.search_meta = None
if "satisfaction_rating" not in st.session_state:
    st.session_state.satisfaction_rating = None
if "satisfaction_comment" not in st.session_state:
    st.session_state.satisfaction_comment = ""

# ============================================================
# Hero header
# ============================================================
render_html(
    """
    <div class="hero">
        <span class="badge">🌿 SU FREE ELECTIVE ADVISOR</span>
        <h1>ระบบแนะนำคู่รายวิชาเลือกเสรี</h1>
        <p>ค้นหาวิชาเสรีที่เหมาะกับคุณ โดยไม่ชนตารางเรียน ไม่ชนสอบกลางภาค/ปลายภาค
        พร้อมจัดอันดับด้วย TF-IDF Cosine Similarity และ Item-Based Collaborative Filtering</p>
    </div>
    """
)

# ============================================================
# Sidebar — input form
# ============================================================
with st.sidebar:
    st.markdown("### 🔎 ค้นหาวิชาเสรี")
    st.caption("กรอกข้อมูลเพื่อรับคำแนะนำวิชาเสรีที่เหมาะกับคุณ")

    with st.form("search_form"):
        major = st.selectbox(
            "สาขา",
            options=list(MANDATORY_COURSES.keys()),
        )

        semester = st.radio(
            "ภาคการศึกษา",
            options=["1", "2"],
            horizontal=True,
            format_func=lambda s: f"ภาคการศึกษา {'ต้น' if s == '1' else 'ปลาย'}",
        )

        st.markdown("**คำค้นหาความสนใจ (3 คำ)**")
        keyword1 = st.selectbox(
            "คำค้นหาที่ 1",
            options=KEYWORD_SUGGESTIONS,
            format_func=lambda keyword: keyword or "พิมพ์เพื่อค้นหาคำแนะนำ...",
            help="คลิกช่องแล้วพิมพ์ เช่น ก, ง หรือ A เพื่อกรองคำแนะนำ จากนั้นเลือกคำที่ต้องการ",
        )
        keyword2 = st.selectbox(
            "คำค้นหาที่ 2",
            options=KEYWORD_SUGGESTIONS,
            format_func=lambda keyword: keyword or "พิมพ์เพื่อค้นหาคำแนะนำ...",
            help="คลิกช่องแล้วพิมพ์เพื่อกรองคำแนะนำ แล้วเลือกคำที่ต้องการ",
        )
        keyword3 = st.selectbox(
            "คำค้นหาที่ 3",
            options=KEYWORD_SUGGESTIONS,
            format_func=lambda keyword: keyword or "พิมพ์เพื่อค้นหาคำแนะนำ...",
            help="คลิกช่องแล้วพิมพ์เพื่อกรองคำแนะนำ แล้วเลือกคำที่ต้องการ",
        )

        submitted = st.form_submit_button("✨ ค้นหาวิชาเสรี")

    st.divider()
    st.caption("สร้างด้วย TF-IDF (char n-gram) + Cosine Similarity + Item-Based CF")

# ============================================================
# Core recommendation pipeline (mirrors original script)
# ============================================================
def run_recommendation(major, semester, keyword1, keyword2, keyword3):
    errors = []

    if major not in MANDATORY_COURSES:
        errors.append("ไม่พบข้อมูลสาขา")
        return None, errors

    if semester not in MANDATORY_COURSES[major]:
        errors.append("ไม่พบข้อมูลวิชาบังคับของเทอมนี้")
        return None, errors

    if semester not in ELECTIVE_COURSES:
        errors.append("ไม่พบข้อมูลวิชาเสรีของเทอมนี้")
        return None, errors

    mandatory_courses = MANDATORY_COURSES[major][semester]
    semester_electives = ELECTIVE_COURSES[semester]

    # ---------------- Filter electives against mandatory schedule ----------------
    valid_courses = {}
    filter_log = []

    for course_id, elective in semester_electives.items():
        conflict = False
        reasons = []

        for mandatory_id, mandatory in mandatory_courses.items():
            if class_conflict(elective, mandatory):
                conflict = True
                reasons.append(f"ชนเวลาเรียนกับ {mandatory_id}")

            if exam_conflict(elective["midterm"], mandatory["midterm"]):
                conflict = True
                reasons.append(f"ชนสอบกลางภาคกับ {mandatory_id}")

            if exam_conflict(elective["final"], mandatory["final"]):
                conflict = True
                reasons.append(f"ชนสอบปลายภาคกับ {mandatory_id}")

        if not conflict:
            valid_courses[course_id] = elective

        filter_log.append(
            {
                "course_id": course_id,
                "name": elective["name"],
                "passed": not conflict,
                "reasons": reasons,
            }
        )

    if len(valid_courses) == 0:
        errors.append("ไม่พบวิชาเสรีที่สามารถลงทะเบียนได้")
        return {
            "mandatory_courses": mandatory_courses,
            "filter_log": filter_log,
            "valid_courses": {},
        }, errors

    # ---------------- TF-IDF + Cosine similarity ----------------
    course_ids = list(valid_courses.keys())
    descriptions = [valid_courses[cid]["description"] for cid in course_ids]
    keywords = f"{keyword1} {keyword2} {keyword3}"
    documents = descriptions + [keywords]

    vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), lowercase=False)
    tfidf_matrix = vectorizer.fit_transform(documents)

    keyword_vector = tfidf_matrix[-1]
    course_vectors = tfidf_matrix[:-1]

    cosine_scores = cosine_similarity(course_vectors, keyword_vector).flatten()
    cosine_result = pd.DataFrame({"course_id": course_ids, "cosine_score": cosine_scores})

    # ---------------- Item-Based Collaborative Filtering ----------------
    interaction = enrollment.pivot_table(
        index="major", columns="course_id", values="student_count", aggfunc="sum", fill_value=0
    )

    all_cf_courses = list(
        dict.fromkeys(list(interaction.columns) + course_ids + list(mandatory_courses.keys()))
    )
    interaction = interaction.reindex(columns=all_cf_courses, fill_value=0)
    interaction_for_cf = interaction + 1

    if interaction.empty:
        cf_result = pd.DataFrame({"course_id": course_ids, "cf_score": np.zeros(len(course_ids))})
    else:
        item_similarity = cosine_similarity(interaction_for_cf.T)
        item_similarity_df = pd.DataFrame(
            item_similarity, index=interaction.columns, columns=interaction.columns
        )

        cf_scores = []
        for course_id in course_ids:
            similarities = []
            for mandatory_id in mandatory_courses.keys():
                if course_id in item_similarity_df.index and mandatory_id in item_similarity_df.columns:
                    similarities.append(item_similarity_df.loc[course_id, mandatory_id])
            cf_scores.append(np.mean(similarities) if similarities else 0)

        cf_result = pd.DataFrame({"course_id": course_ids, "cf_score": cf_scores})

    # ---------------- Merge + rank ----------------
    result = cosine_result.merge(cf_result, on="course_id")
    result["course_name"] = result["course_id"].apply(lambda x: valid_courses[x]["name"])
    result = result.sort_values(
        by=["cosine_score", "cf_score"], ascending=[False, False]
    ).reset_index(drop=True)

    return {
        "mandatory_courses": mandatory_courses,
        "filter_log": filter_log,
        "valid_courses": valid_courses,
        "result": result,
    }, errors


# ============================================================
# Run on submit
# ============================================================
if submitted:
    if not (keyword1 or keyword2 or keyword3):
        st.warning("⚠️ กรุณากรอกคำค้นหาความสนใจอย่างน้อย 1 คำ เพื่อผลลัพธ์ที่แม่นยำขึ้น")

    st.session_state.satisfaction_rating = None
    st.session_state.satisfaction_comment = ""

    with st.spinner("กำลังประมวลผล TF-IDF และ Collaborative Filtering..."):
        payload, errors = run_recommendation(major, semester, keyword1, keyword2, keyword3)

    st.session_state.search_meta = {
        "major": major,
        "semester": semester,
        "keywords": [keyword1, keyword2, keyword3],
    }

    if payload is None:
        st.session_state.results = None
        for e in errors:
            st.error(f"❌ {e}")
    else:
        st.session_state.mandatory_courses = payload["mandatory_courses"]
        st.session_state.filter_log = payload["filter_log"]
        st.session_state.valid_courses = payload["valid_courses"]
        st.session_state.results = payload.get("result")
        for e in errors:
            st.error(f"❌ {e}")

# ============================================================
# Display results
# ============================================================
meta = st.session_state.search_meta

if meta is None:
    render_html(
        """
        <div class="m-card">
            <b>👋 ยินดีต้อนรับ</b><br>
            เลือกสาขา ภาคการศึกษา และกรอกคำค้นหาความสนใจทางด้านซ้าย
            จากนั้นกดปุ่ม <b>"ค้นหาวิชาเสรี"</b> เพื่อรับคำแนะนำวิชาเสรีที่ไม่ชนตารางเรียนของคุณ
        </div>
        """
    )
    st.stop()


def render_satisfaction_survey(result, search_meta):
    st.divider()
    render_html(
        '<div class="section-title"><span class="dot"></span>สำรวจความพึงพอใจ</div>'
    )
    st.caption("ช่วยบอกเราหน่อยว่าผลการแนะนำวิชาครั้งนี้เป็นอย่างไร")

    with st.form("satisfaction_form"):
        rating = st.radio(
            "ให้คะแนนความพึงพอใจ",
            options=[1, 2, 3, 4, 5],
            format_func=lambda score: "★" * score,
            horizontal=True,
        )
        comment = st.text_area(
            "ข้อเสนอแนะเพิ่มเติม (ไม่บังคับ)",
            placeholder="บอกเราได้ว่าควรปรับปรุงอะไร",
        )
        feedback_submitted = st.form_submit_button("ส่งแบบประเมิน")

    if feedback_submitted:
        st.session_state.satisfaction_rating = rating
        st.session_state.satisfaction_comment = comment
        recommended_courses = ""
        if result is not None and len(result):
            recommended_courses = ", ".join(result["course_id"].astype(str))
        save_feedback(
            rating=rating,
            comment=comment,
            major=search_meta["major"],
            semester=search_meta["semester"],
            keywords=", ".join(keyword for keyword in search_meta["keywords"] if keyword),
            recommended_courses=recommended_courses,
        )
        st.success("ขอบคุณสำหรับความคิดเห็นของคุณ")
    elif st.session_state.satisfaction_rating is not None:
        st.info(
            f"คุณให้คะแนนความพึงพอใจ {'★' * st.session_state.satisfaction_rating} แล้ว"
        )

    average_rating, total_reviews = get_feedback_summary()
    if total_reviews:
        st.caption(
            f"คะแนนความพึงพอใจเฉลี่ย: {average_rating:.2f}/5 "
            f"จากผู้ประเมิน {total_reviews} คน"
        )
    else:
        st.caption("ยังไม่มีข้อมูลคะแนนความพึงพอใจ")


# --- Summary metrics ---
mandatory_courses = st.session_state.mandatory_courses
filter_log = st.session_state.filter_log
valid_courses = st.session_state.valid_courses
result = st.session_state.results

if mandatory_courses is not None:
    total_electives = len(filter_log) if filter_log else 0
    passed = sum(1 for f in filter_log if f["passed"]) if filter_log else 0
    top_score = f"{result.iloc[0]['cosine_score']:.2f}" if result is not None and len(result) else "—"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("สาขา", meta["major"])
    c2.metric("วิชาเสรีทั้งหมด", total_electives)
    c3.metric("ผ่านเงื่อนไข", passed)
    c4.metric("คะแนนสูงสุด (Cosine)", top_score)

    kw_display = ", ".join([k for k in meta["keywords"] if k]) or "—"
    st.caption(f"🏷️ Keyword: {kw_display}  ·  🗓️ เทอม {meta['semester']}")

tab_result, tab_mandatory, tab_filter = st.tabs(
    ["🏆 ผลการแนะนำ", "📚 วิชาบังคับ", "🧾 การตรวจสอบตารางเรียน"]
)

# ---------------- Tab: Recommendation results ----------------
with tab_result:
    if result is None or len(result) == 0:
        st.info("ไม่พบวิชาเสรีที่สามารถลงทะเบียนได้ตามเงื่อนไขที่กำหนด")
        render_satisfaction_survey(result, meta)
    else:
        render_html(
            '<div class="section-title"><span class="dot"></span>วิชาเสรีที่แนะนำ เรียงตามคะแนน</div>'
        )

        max_score = max(result["cosine_score"].max(), 1e-9)

        for idx, row in result.iterrows():
            course_id = row["course_id"]
            course = valid_courses[course_id]
            top1 = "top1" if idx == 0 else ""
            bar_pct = max(round((row["cosine_score"] / max_score) * 100), 2)

            classes_html = "".join(
                f'<span class="meta-chip">📅 {day} {start}–{end}</span>'
                for day, start, end in course["classes"]
            )

            if course["midterm"]:
                m_date, m_s, m_e = course["midterm"]
                midterm_html = f'<span class="meta-chip">📝 Midterm: {m_date} {m_s}–{m_e}</span>'
            else:
                midterm_html = '<span class="meta-chip">📝 Midterm: ไม่มีสอบ</span>'

            if course["final"]:
                f_date, f_s, f_e = course["final"]
                final_html = f'<span class="meta-chip">🧪 Final: {f_date} {f_s}–{f_e}</span>'
            else:
                final_html = '<span class="meta-chip">🧪 Final: ไม่มีสอบ</span>'

            render_html(
                f"""
                <div class="rank-card {top1}">
                    <div style="display:flex; align-items:center; flex-wrap:wrap; gap:.5rem;">
                        <span class="rank-pill">{idx+1}</span>
                        <span class="course-code">{course_id}</span>
                        {'<span class="course-code" style="background:#fff3da;color:#8a6416;">⭐ อันดับ 1</span>' if idx==0 else ''}
                    </div>
                    <div class="course-name">{row['course_name']}</div>
                    <div class="meta-row">{classes_html}</div>
                    <div class="meta-row">{midterm_html}{final_html}</div>
                    <div style="display:flex; justify-content:space-between; margin-top:.7rem; font-size:.82rem; color:#2c4a3d;">
                        <span>Cosine Similarity: <b>{row['cosine_score']:.4f}</b></span>
                        <span>Item-Based CF: <b>{row['cf_score']:.4f}</b></span>
                    </div>
                    <div class="score-bar-wrap"><div class="score-bar-fill" style="width:{bar_pct}%;"></div></div>
                </div>
                """
            )

        st.download_button(
            "⬇️ ดาวน์โหลดผลลัพธ์ (CSV)",
            data=result.to_csv(index=False).encode("utf-8-sig"),
            file_name="recommended_electives.csv",
            mime="text/csv",
        )

        render_satisfaction_survey(result, meta)

# ---------------- Tab: Mandatory courses ----------------
with tab_mandatory:
    render_html(
        '<div class="section-title"><span class="dot"></span>วิชาบังคับที่ใช้ตรวจสอบ</div>'
    )
    if mandatory_courses:
        rows = []
        for cid, c in mandatory_courses.items():
            schedule = ", ".join(f"{d} {s}-{e}" for d, s, e in c["classes"])
            rows.append({"รหัสวิชา": cid, "ชื่อวิชา": c["name"], "ตารางเรียน": schedule})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ---------------- Tab: Filter log ----------------
with tab_filter:
    render_html(
        '<div class="section-title"><span class="dot"></span>ตรวจสอบตารางเรียน / Midterm / Final</div>'
    )
    if filter_log:
        for f in filter_log:
            status = '<span class="pass-tag">✅ ผ่าน</span>' if f["passed"] else '<span class="fail-tag">❌ ไม่ผ่าน</span>'
            reasons_html = ""
            if f["reasons"]:
                reasons_html = "<ul style='margin:.3rem 0 0 1.1rem;'>" + "".join(
                    f"<li style='font-size:.85rem;color:#7a4633;'>{r}</li>" for r in f["reasons"]
                ) + "</ul>"
            render_html(
                f"""
                <div class="m-card">
                    <span class="course-code">{f['course_id']}</span>
                    <b>{f['name']}</b> — {status}
                    {reasons_html}
                </div>
                """
            )