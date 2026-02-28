import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="SNOT-22 Dashboard")

# --- Google Sheets URL ---
# ต้องตั้งค่าแชร์เป็น "Anyone with the link" และใช้ /export?format=csv
SHEET_URL = "https://docs.google.com/spreadsheets/d/16tjUBGG0AUF7HWNiCCAlIjDUPxXOD1xPoJu0y2o7e4s/export?format=csv"

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

MONTH_ORDER = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


@st.cache_data(ttl=300)  # แคชข้อมูล 5 นาที แล้วโหลดใหม่
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
        years = ['All'] + sorted(df['Year'].dropna().unique().astype(int).tolist())
        selected_year = col1.selectbox("เลือกปี (Year)", years)

        genders = ['All'] + df['gender'].dropna().unique().tolist()
        selected_gender = col2.selectbox("เลือกเพศ (Gender)", genders)

        ages = ['All'] + sorted(df['Age_Group'].dropna().unique().tolist())
        selected_age = col3.selectbox("เลือกช่วงอายุ (Age Group)", ages)

        # การกรองข้อมูลตาม Slicer
        filtered_df = df.copy()
        if selected_year != 'All':
            filtered_df = filtered_df[filtered_df['Year'] == selected_year]
        if selected_gender != 'All':
            filtered_df = filtered_df[filtered_df['gender'] == selected_gender]
        if selected_age != 'All':
            filtered_df = filtered_df[filtered_df['Age_Group'] == selected_age]

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
            fig = px.box(
                plot_df, x='Month', y=topic,
                title=f"Boxplot: {topic} — {SYMPTOM_DESCRIPTIONS.get(topic, '')}",
                points="all", color_discrete_sequence=['#1f77b4'],
                category_orders={'Month': existing_months},
            )
            st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # Tab 2: Individual Patient (HN) Analysis
    # ==========================================
    with tab2:
        st.header("Patient Trend Analysis")

        hn_list = sorted(df['HN_str'].dropna().unique().tolist())
        selected_hn = st.selectbox("เลือก HN ของคนไข้เพื่อดูแนวโน้ม", hn_list)

        # ใช้ HN_str ที่แปลงแล้วเพื่อเปรียบเทียบ (แก้ปัญหา float mismatch)
        patient_df = df[df['HN_str'] == selected_hn].sort_values('date_clean')

        if not patient_df.empty:
            melted_df = patient_df.melt(
                id_vars=['date_clean'],
                value_vars=SCORE_COLS,
                var_name='Symptom_Topic',
                value_name='Score',
            )

            fig2 = px.line(
                melted_df, x='date_clean', y='Score', color='Symptom_Topic',
                markers=True,
                title=f"แนวโน้มคะแนน SNOT-22 ทั้ง 22 หัวข้อ ตลอดการรักษาของ HN: {selected_hn}",
            )
            fig2.update_layout(yaxis=dict(range=[0, 6]))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("ไม่พบข้อมูลสำหรับ HN นี้")
