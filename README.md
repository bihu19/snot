# SNOT-22 Dashboard

Interactive Streamlit dashboard for analyzing **SNOT-22 (Sino-Nasal Outcome Test)** patient data, synced in real-time with Google Sheets.

## Features

### Data Source & Refresh

- Data is pulled directly from a **Google Sheets** spreadsheet (published as CSV)
- Auto-refresh every **6 hours** (at 0:00, 6:00, 12:00, 18:00 Bangkok time)
- **Manual refresh** button available at the top of the page
- Live **countdown timer** shows time remaining until the next auto-refresh

### Tab 1: Overall Descriptive Analysis

Aggregate analysis across all patients with interactive filters.

**Filters (Slicers):**

| Filter | Type | Description |
|---|---|---|
| Year Range | Range slider | Select min-max year range |
| Gender | Dropdown | Filter by gender |
| Age Group | Multi-select | Choose one or more age groups: `<20`, `20-30`, `31-40`, `41-50`, `>=51` |

**Patient Count:**
- Displays the total number of unique patients matching the current filter conditions

**Monthly Mean Table:**
- Transposed table with **22 rows** (one per SNOT-22 symptom) and **12 columns** (Jan-Dec)
- Each row includes a Thai-language symptom description
- Shows the average score for each symptom per month

**Seasonal Trend Boxplots:**
- **22 boxplots** (one per symptom), each showing score distribution by month
- Y-axis standardized to `[0, 5]` for consistent comparison
- Data points plotted inside the box with jitter for visibility

### Tab 2: Patient Tracking (HN)

Individual patient trend analysis by Hospital Number (HN).

**HN Selection:**
- Text search input to filter HN numbers by typing
- Dropdown to select from filtered results

**Symptom Filter:**
- **Select All / Deselect All** buttons for quick toggling
- Multi-select widget to choose which of the 22 symptoms to display
- Selection persists across interactions via session state

**Trend Graph:**
- Line chart showing selected symptom scores over time for the chosen patient
- **Star markers** highlight data points where the symptom significantly affects the patient's quality of life (when the corresponding `_p` column is `TRUE` in the data)
- Legend labels use Thai symptom descriptions with numbering (e.g., `1. จำเป็นต้องสั่งน้ำมูก`)
- Legend title indicates: `★ = กระทบชีวิตผู้ป่วย` (affects patient's life)

## SNOT-22 Symptoms

| # | Column | Description (Thai) |
|---|---|---|
| 1 | one | จำเป็นต้องสั่งน้ำมูก |
| 2 | two | อาการคัดจมูก |
| 3 | three | จาม |
| 4 | four | น้ำมูกไหล |
| 5 | five | ไอ |
| 6 | six | น้ำมูกหรือเสมหะไหลลงคอ |
| 7 | seven | น้ำมูกเหนียว |
| 8 | eight | หูอื้อ |
| 9 | nine | มืนงง |
| 10 | ten | ปวดหู |
| 11 | eleven | ปวดหรือรู้สึกตื้อๆบริเวณหน้า |
| 12 | twelve | ประสาทการดมกลิ่นหรือรับรสลดประสิทธิภาพลง |
| 13 | thirteen | นอนหลับยาก |
| 14 | fourteen | ต้องตื่นขณะนอนกลางคืน |
| 15 | fifteen | นอนหลับไม่สนิท |
| 16 | sixteen | รู้สึกเหนื่อยตอนตื่นนอน |
| 17 | seventeen | อ่อนเพลีย |
| 18 | eighteen | ทำงานได้น้อยลง |
| 19 | nineteen | สมาธิลดลง |
| 20 | twenty | กลัดกลุ้ม กระสับกระส่าย หงุดหงิด |
| 21 | twenty_one | รู้สึกเศร้าใจ |
| 22 | twenty_two | รู้สึกอาย |

## Google Sheets Data Format

The Google Sheet must contain the following columns:

| Column | Type | Description |
|---|---|---|
| `HN` | Number | Hospital Number (patient ID) |
| `date_clean` | Date (`DD/MM/YYYY`) | Visit date |
| `age` | Number | Patient age |
| `gender` | Text | Patient gender |
| `one` - `twenty_two` | Number (0-5) | SNOT-22 symptom scores |
| `one_p` - `twenty_two_p` | Boolean (`TRUE`/`FALSE`) | Whether the symptom affects quality of life |

**Important:** The Google Sheet must be shared as **"Anyone with the link"** for the dashboard to read data.

## Setup & Deployment

### Prerequisites

- Python 3.8+
- Google Sheet shared with "Anyone with the link" access

### Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Deploy on Streamlit Cloud

1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **"New app"**
4. Select your repository, branch, and set main file to `app.py`
5. Click **Deploy**

## Tech Stack

- **Streamlit** — Web application framework
- **Pandas** — Data processing and analysis
- **Plotly** — Interactive charts (boxplots, line charts)
- **Google Sheets** — Data source (CSV export)
