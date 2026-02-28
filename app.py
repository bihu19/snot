import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="SNOT-22 Dashboard")

# --- Google Sheets URL ---
# ต้องตั้งค่าแชร์เป็น "Anyone with the link" และใช้ /export?format=csv
SHEET_URL = "https://docs.google.com/spreadsheets/d/16tjUBGG0AUF7HWNiCCAlIjDUPxXOD1xPoJu0y2o7e4s/export?format=csv"


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
    df['Month'] = df['date_clean'].dt.strftime('%m-%b')
    df['Month_Num'] = df['date_clean'].dt.month

    # สร้างช่วงอายุ: <20, 20-30, 31-40, 41-50, >=51
    bins = [0, 19, 30, 40, 50, 120]
    labels = ['<20', '20-30', '31-40', '41-50', '>=51']
    df['Age_Group'] = pd.cut(df['age'], bins=bins, labels=labels)

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

        ages = ['All'] + df['Age_Group'].dropna().unique().tolist()
        selected_age = col3.selectbox("เลือกช่วงอายุ (Age Group)", ages)

        # การกรองข้อมูลตาม Slicer
        filtered_df = df.copy()
        if selected_year != 'All':
            filtered_df = filtered_df[filtered_df['Year'] == selected_year]
        if selected_gender != 'All':
            filtered_df = filtered_df[filtered_df['gender'] == selected_gender]
        if selected_age != 'All':
            filtered_df = filtered_df[filtered_df['Age_Group'] == selected_age]

        # ตารางค่าเฉลี่ยแต่ละเดือน (หัวข้อ 1-22)
        st.subheader("ตารางค่าเฉลี่ยของแต่ละเดือน")
        mean_cols = [
            'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
            'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
            'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty',
            'twenty_one', 'twenty_two',
        ]

        monthly_mean = filtered_df.groupby(['Month_Num', 'Month'])[mean_cols].mean().reset_index()
        monthly_mean = monthly_mean.drop(columns=['Month_Num'])
        st.dataframe(monthly_mean.set_index('Month'), use_container_width=True)

        # กราฟ Time series Boxplot (หัวข้อ 1 ถึง 7)
        st.subheader("Seasonal Trend Boxplots (หัวข้อ 1 ถึง 7)")
        topics_to_plot = ['one', 'two', 'three', 'four', 'five', 'six', 'seven']
        plot_df = filtered_df.sort_values('Month_Num')

        for topic in topics_to_plot:
            fig = px.box(
                plot_df, x='Month', y=topic,
                title=f"Boxplot การกระจายตัวคะแนนหัวข้อ: {topic} ในแต่ละเดือน",
                points="all", color_discrete_sequence=['#1f77b4'],
            )
            st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # Tab 2: Individual Patient (HN) Analysis
    # ==========================================
    with tab2:
        st.header("Patient Trend Analysis")

        hn_list = df['HN'].dropna().unique().astype(int).astype(str).tolist()
        selected_hn = st.selectbox("เลือก HN ของคนไข้เพื่อดูแนวโน้ม", hn_list)

        patient_df = df[df['HN'].astype(str) == selected_hn].sort_values('date_clean')

        if not patient_df.empty:
            melted_df = patient_df.melt(
                id_vars=['date_clean'],
                value_vars=mean_cols,
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
