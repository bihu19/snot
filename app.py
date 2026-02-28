import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="SNOT-22 Dashboard")

# --- Google Sheets URL ---
# ต้องตั้งค่าแชร์เป็น "Anyone with the link" และใช้ /export?format=csv
SHEET_URL = "https://docs.google.com/spreadsheets/d/16tjUBGG0AUF7HWNiCCAlIjDUPxXOD1xPoJu0y2o7e4s/export?format=csv"

# --- เวลารีเฟรชอัตโนมัติ: 0:00, 6:00, 12:00, 18:00 ---
REFRESH_HOURS = [0, 6, 12, 18]
AUTO_REFRESH_TTL = 6 * 3600  # 6 ชั่วโมง (21600 วินาที)

SCORE_COLS = [
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
    'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
    'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty',
    'twenty_one', 'twenty_two',
]

SYMPTOM_DESCRIPTIONS = {
    'one': 'จำเป็นต้องสั่งน้ำมูก',
    'two': 'อาการคัดจมูก',
    'three': 'จาม',
    'four': 'น้ำมูกไหล',
    'five': 'ไอ',
    'six': 'น้ำมูกหรือเสมหะไหลลงคอ',
    'seven': 'น้ำมูกเหนียว',
    'eight': 'หูอื้อ',
    'nine': 'มืนงง',
    'ten': 'ปวดหู',
    'eleven': 'ปวดหรือรู้สึกตื้อๆบริเวณหน้า',
    'twelve': 'ประสาทการดมกลิ่นหรือรับรสลดประสิทธิภาพลง',
    'thirteen': 'นอนหลับยาก',
    'fourteen': 'ต้องตื่นขณะนอนกลางคืน',
    'fifteen': 'นอนหลับไม่สนิท',
    'sixteen': 'รู้สึกเหนื่อยตอนตื่นนอน',
    'seventeen': 'อ่อนเพลีย',
    'eighteen': 'ทำงานได้น้อยลง',
    'nineteen': 'สมาธิลดลง',
    'twenty': 'กลัดกลุ้ม กระสับกระส่าย หงุดหงิด',
    'twenty_one': 'รู้สึกเศร้าใจ',
    'twenty_two': 'รู้สึกอาย',
}

# คอลัมน์ _p ที่ระบุว่าอาการนั้นกระทบชีวิตผู้ป่วย (TRUE/FALSE)
SCORE_P_COLS = [f"{col}_p" for col in SCORE_COLS]

MONTH_ORDER = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


@st.cache_data(ttl=AUTO_REFRESH_TTL)  # แคชข้อมูล 6 ชั่วโมง
def load_data(url):
    try:
        df = pd.read_csv(url)
    except Exception:
        st.error("ไม่สามารถโหลดข้อมูลจาก Google Sheets ได้ กรุณาตรวจสอบ Link")
        return pd.DataFrame()

    # แปลงวันที่
    df['date_clean'] = pd.to_datetime(df['date_clean'], format='%d/%m/%Y', errors='coerce')
    df['Year'] = df['date_clean'].dt.year
    df['Month'] = df['date_clean'].dt.strftime('%b')  # "Jan", "Feb", ...
    df['Month_Num'] = df['date_clean'].dt.month

    # แปลงคอลัมน์คะแนนให้เป็นตัวเลข (แก้ปัญหากรณีข้อมูลเป็น string)
    for col in SCORE_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # แปลงคอลัมน์ _p (important flag) ให้เป็น boolean
    for col_p in SCORE_P_COLS:
        if col_p in df.columns:
            df[col_p] = df[col_p].astype(str).str.strip().str.upper().isin(['TRUE', '1', 'YES'])

    # สร้างช่วงอายุ: <20, 20-30, 31-40, 41-50, >=51
    df['age'] = pd.to_numeric(df['age'], errors='coerce')
    bins = [0, 19, 30, 40, 50, 120]
    labels = ['<20', '20-30', '31-40', '41-50', '>=51']
    df['Age_Group'] = pd.cut(df['age'], bins=bins, labels=labels).astype(str)
    df.loc[df['Age_Group'] == 'nan', 'Age_Group'] = None

    # แปลง HN เป็น string ที่สะอาด (แก้ปัญหา float เช่น 12345.0 → "12345")
    def clean_hn(x):
        if pd.isnull(x):
            return None
        try:
            return str(int(float(x)))
        except (ValueError, TypeError):
            return str(x).strip()

    df['HN_str'] = df['HN'].apply(clean_hn)

    return df


# --- ปุ่ม Refresh และนาฬิกานับถอยหลัง ---
refresh_col1, refresh_col2 = st.columns([1, 3])
with refresh_col1:
    if st.button("🔄 Refresh Data Now"):
        st.cache_data.clear()
        st.rerun()

with refresh_col2:
    # คำนวณเวลารีเฟรชถัดไป (0:00, 6:00, 12:00, 18:00) เป็น UTC+7
    tz_bkk = timezone(timedelta(hours=7))
    now_bkk = datetime.now(tz_bkk)
    next_refresh = None
    for h in REFRESH_HOURS:
        candidate = now_bkk.replace(hour=h, minute=0, second=0, microsecond=0)
        if candidate > now_bkk:
            next_refresh = candidate
            break
    if next_refresh is None:
        # ข้ามไปวันถัดไป เวลา 0:00
        next_refresh = (now_bkk + timedelta(days=1)).replace(
            hour=REFRESH_HOURS[0], minute=0, second=0, microsecond=0
        )

    next_refresh_utc_ms = int(next_refresh.astimezone(timezone.utc).timestamp() * 1000)

    # JavaScript countdown timer
    components.html(f"""
    <div id="countdown" style="font-size:14px; color:#555; padding:8px 0;">
        ⏱ รีเฟรชอัตโนมัติถัดไป: กำลังคำนวณ...
    </div>
    <script>
    var target = {next_refresh_utc_ms};
    function updateCountdown() {{
        var now = Date.now();
        var diff = target - now;
        if (diff <= 0) {{
            document.getElementById("countdown").innerHTML =
                "⏱ กำลังรีเฟรชข้อมูล...";
            return;
        }}
        var h = Math.floor(diff / 3600000);
        var m = Math.floor((diff % 3600000) / 60000);
        var s = Math.floor((diff % 60000) / 1000);
        document.getElementById("countdown").innerHTML =
            "⏱ รีเฟรชอัตโนมัติถัดไปใน: " + h + " ชม. " + m + " น. " + s + " วินาที" +
            " (รีเฟรชทุกวันเวลา 0:00, 6:00, 12:00, 18:00)";
    }}
    updateCountdown();
    setInterval(updateCountdown, 1000);
    </script>
    """, height=40)

df = load_data(SHEET_URL)

if not df.empty:
    st.title("SNOT-22 Dashboard")

    tab1, tab2 = st.tabs(["1. Overall Descriptive Analysis", "2. Patient Tracking (HN)"])

    # ==========================================
    # Tab 1: Overall Descriptive Analysis
    # ==========================================
    with tab1:
        st.header("Overall Pain Score Analysis")

        # Slicers (ตัวกรอง)
        col1, col2, col3 = st.columns(3)

        # Year: range slider (min-max)
        all_years = sorted(df['Year'].dropna().unique().astype(int).tolist())
        if len(all_years) >= 2:
            year_range = col1.slider(
                "เลือกช่วงปี (Year Range)",
                min_value=all_years[0], max_value=all_years[-1],
                value=(all_years[0], all_years[-1]),
            )
        elif len(all_years) == 1:
            col1.info(f"ปีที่มีข้อมูล: {all_years[0]}")
            year_range = (all_years[0], all_years[0])
        else:
            year_range = None

        # Gender: single select
        genders = ['All'] + df['gender'].dropna().unique().tolist()
        selected_gender = col2.selectbox("เลือกเพศ (Gender)", genders)

        # Age Group: multiselect
        age_options = sorted(df['Age_Group'].dropna().unique().tolist())
        selected_ages = col3.multiselect("เลือกช่วงอายุ (Age Group)", age_options, default=age_options)

        # การกรองข้อมูลตาม Slicer
        filtered_df = df.copy()
        if year_range:
            filtered_df = filtered_df[
                (filtered_df['Year'] >= year_range[0]) & (filtered_df['Year'] <= year_range[1])
            ]
        if selected_gender != 'All':
            filtered_df = filtered_df[filtered_df['gender'] == selected_gender]
        if selected_ages:
            filtered_df = filtered_df[filtered_df['Age_Group'].isin(selected_ages)]

        # แสดงจำนวนผู้ป่วยที่ตรงตามเงื่อนไข
        if 'HN_str' in filtered_df.columns:
            total_patients = filtered_df['HN_str'].nunique()
        else:
            total_patients = len(filtered_df)
        st.metric("จำนวนผู้ป่วยทั้งหมดที่ตรงตามเงื่อนไข", f"{total_patients} คน")

        # ============================================================
        # ตารางค่าเฉลี่ยแต่ละเดือน (Transposed: 22 rows x 12 months)
        # ============================================================
        st.subheader("ตารางค่าเฉลี่ยของแต่ละเดือน")

        monthly_mean = filtered_df.groupby('Month_Num')[SCORE_COLS].mean()

        # Transpose: rows = symptoms, columns = month numbers
        transposed = monthly_mean.T

        # Rename month-number columns to month abbreviations
        col_map = {}
        for m in transposed.columns:
            if pd.notnull(m):
                col_map[m] = MONTH_ORDER[int(m) - 1]
        transposed = transposed.rename(columns=col_map)

        # Add symptom description column
        transposed.insert(0, 'อาการ', [SYMPTOM_DESCRIPTIONS.get(s, '') for s in transposed.index])

        # Ensure all 12 months present (fill missing months with -)
        for m in MONTH_ORDER:
            if m not in transposed.columns:
                transposed[m] = None

        # Reorder: description first, then 12 months in order
        transposed = transposed[['อาการ'] + MONTH_ORDER]

        # Round numeric values for display
        display_df = transposed.copy()
        for m in MONTH_ORDER:
            display_df[m] = display_df[m].apply(lambda x: round(x, 2) if pd.notnull(x) else '-')

        st.dataframe(display_df, use_container_width=True)

        # ============================================================
        # กราฟ Time series Boxplot (หัวข้อ 1 ถึง 7)
        # ============================================================
        st.subheader("Seasonal Trend Boxplots (หัวข้อ 1 ถึง 7)")
        topics_to_plot = ['one', 'two', 'three', 'four', 'five', 'six', 'seven']
        plot_df = filtered_df.dropna(subset=['Month']).sort_values('Month_Num')

        # Get ordered month values that exist in the data
        existing_months = plot_df.drop_duplicates('Month_Num').sort_values('Month_Num')['Month'].tolist()

        for topic in topics_to_plot:
            fig = go.Figure()
            fig.add_trace(go.Box(
                x=plot_df['Month'],
                y=plot_df[topic],
                boxpoints='all',
                pointpos=0,       # จุดอยู่ตรงกลางกล่อง
                jitter=0.3,
                marker=dict(color='#1f77b4', size=4, opacity=0.6),
                line=dict(color='#1f77b4'),
                name=topic,
            ))
            fig.update_layout(
                title=f"Boxplot: {topic} — {SYMPTOM_DESCRIPTIONS.get(topic, '')}",
                xaxis=dict(categoryorder='array', categoryarray=existing_months),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # Tab 2: Individual Patient (HN) Analysis
    # ==========================================
    with tab2:
        st.header("Patient Trend Analysis")

        hn_list = sorted(df['HN_str'].dropna().unique().tolist())

        # ช่องค้นหา HN พร้อมพิมพ์กรองได้
        search_hn = st.text_input("พิมพ์เพื่อค้นหา HN", "")
        if search_hn:
            filtered_hn = [h for h in hn_list if search_hn in h]
        else:
            filtered_hn = hn_list

        if filtered_hn:
            selected_hn = st.selectbox("เลือก HN ของคนไข้เพื่อดูแนวโน้ม", filtered_hn)
        else:
            st.warning("ไม่พบ HN ที่ตรงกับคำค้นหา")
            selected_hn = None

        if selected_hn:
            patient_df = df[df['HN_str'] == selected_hn].sort_values('date_clean')

            if not patient_df.empty:
                fig2 = go.Figure()

                for i, col in enumerate(SCORE_COLS):
                    col_p = f"{col}_p"
                    label = f"{i+1}. {SYMPTOM_DESCRIPTIONS[col]}"
                    dates = patient_df['date_clean']
                    scores = patient_df[col]

                    # เส้นกราฟพร้อมจุดวงกลมปกติ
                    fig2.add_trace(go.Scatter(
                        x=dates, y=scores,
                        mode='lines+markers',
                        name=label,
                        marker=dict(symbol='circle', size=6),
                        legendgroup=label,
                    ))

                    # ซ้อนจุดดาว ★ บนจุดที่ _p = TRUE (อาการกระทบชีวิต)
                    if col_p in patient_df.columns:
                        important_mask = patient_df[col_p] == True
                        if important_mask.any():
                            fig2.add_trace(go.Scatter(
                                x=dates[important_mask],
                                y=scores[important_mask],
                                mode='markers',
                                name=f"{label} ★",
                                marker=dict(
                                    symbol='star',
                                    size=14,
                                    line=dict(width=1, color='black'),
                                ),
                                legendgroup=label,
                                showlegend=True,
                            ))

                fig2.update_layout(
                    title=f"แนวโน้มคะแนน SNOT-22 ทั้ง 22 หัวข้อ ตลอดการรักษาของ HN: {selected_hn}",
                    yaxis=dict(range=[0, 6]),
                    xaxis_title="วันที่",
                    yaxis_title="คะแนน",
                    legend_title="อาการ (★ = กระทบชีวิตผู้ป่วย)",
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("ไม่พบข้อมูลสำหรับ HN นี้")
