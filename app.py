import datetime
import io
import os
import re
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# 1. 페이지 기본 설정 (와이드 레이아웃 적용)
st.set_page_config(
    page_title="BTX CS 월 별 대시보드",
    page_icon="20251218 PNG 축약형 로고_블루.png"
    if os.path.exists("20251218 PNG 축약형 로고_블루.png")
    else "🚖",
    layout="wide",
)

# 2. Pretendard 폰트 전면 적용 + [차트 전체화면 확대시에만] 글자 초대형 확대 CSS
st.markdown(
    """
    <style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css");

    /* Pretendard 폰트 전체 강제 적용 */
    html, body, [class*="css"], .stApp, * {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif !important;
    }

    .stApp {
        background-color: #F8FAFC;
    }
    
    /* 컴퓨터 모니터 해상도별 반응형 화면 폭 & 패딩 최적화 */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
        margin: 0 auto !important;
    }

    /* 메트릭 카드 (선명한 입체 그림자 + 테두리 라인) */
    div[data-testid="stMetric"], .stCard {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px !important;
        padding: 18px 22px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04) !important;
    }

    /* 차트 영역 카드화 */
    div[data-testid="stPlotlyChart"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px !important;
        padding: 12px !important;
        box-shadow: 0 8px 16px -2px rgba(0, 0, 0, 0.06), 0 4px 6px -2px rgba(0, 0, 0, 0.03) !important;
        overflow: hidden !important;
        width: 100% !important;
    }

    /* 🔥 [핵심] 차트 '전체화면(확대)' 상태일 때만 선택적으로 폰트 크기 초대형 강제 가공 🔥 */
    
    /* 1. 확대 시 X축 하단 항목명 (가맹, 기사앱 등) -> 38px */
    :fullscreen svg .xtick text,
    :fullscreen svg .xtick tspan,
    :-webkit-full-screen svg .xtick text,
    :-webkit-full-screen svg .xtick tspan {
        font-size: 38px !important;
        font-weight: 900 !important;
        fill: #0F172A !important;
    }

    /* 2. 확대 시 막대 상단 수치 (26건, 13건 등) -> 42px */
    :fullscreen svg .bartext,
    :fullscreen svg .bartext tspan,
    :fullscreen svg .textpoint text,
    :fullscreen svg .textpoint tspan,
    :-webkit-full-screen svg .bartext,
    :-webkit-full-screen svg .bartext tspan,
    :-webkit-full-screen svg .textpoint text,
    :-webkit-full-screen svg .textpoint tspan {
        font-size: 42px !important;
        font-weight: 900 !important;
        fill: #0F172A !important;
    }

    /* 3. 확대 시 Y축 세로 수치 (0, 5, 10...) -> 28px */
    :fullscreen svg .ytick text,
    :fullscreen svg .ytick tspan,
    :-webkit-full-screen svg .ytick text,
    :-webkit-full-screen svg .ytick tspan {
        font-size: 28px !important;
        font-weight: 800 !important;
        fill: #334155 !important;
    }

    /* 4. 확대 시 차트 제목 -> 42px */
    :fullscreen svg .gtitle,
    :fullscreen svg .gtitle tspan,
    :-webkit-full-screen svg .gtitle,
    :-webkit-full-screen svg .gtitle tspan {
        font-size: 42px !important;
        font-weight: 900 !important;
        fill: #003399 !important;
    }

    /* 5. 확대 시 범례 (Legend) -> 30px */
    :fullscreen svg .legendtext,
    :fullscreen svg .legendtext tspan,
    :-webkit-full-screen svg .legendtext,
    :-webkit-full-screen svg .legendtext tspan {
        font-size: 30px !important;
        font-weight: 800 !important;
        fill: #0F172A !important;
    }

    /* 탭(Tab) 메뉴 레이아웃 */
    div[data-testid="stTabs"] {
        background-color: #FFFFFF;
        padding: 8px 12px 0px 12px;
        border-radius: 12px;
        border: 1px solid #CBD5E1;
        box-shadow: 0 6px 12px -2px rgba(0, 0, 0, 0.06) !important;
        margin-bottom: 24px;
    }

    div[data-testid="stTabs"] button,
    button[data-baseweb="tab"] {
        padding: 10px 20px !important;
    }

    div[data-testid="stTabs"] button *,
    div[data-testid="stTabs"] button p,
    div[data-testid="stTabs"] button span,
    button[data-baseweb="tab"] *,
    button[data-baseweb="tab"] p,
    button[data-baseweb="tab"] span {
        font-size: 20px !important;
        font-weight: 800 !important;
        color: #003399 !important;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] *,
    div[data-testid="stTabs"] button[aria-selected="true"] p,
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #001A66 !important;
        font-weight: 900 !important;
    }

    div[data-baseweb="tab-highlight"] {
        background-color: #003399 !important;
        height: 3px !important;
    }

    /* 메트릭 라벨 (20px + 볼드체 + 찐파랑 #003399) */
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] *,
    div[data-testid="stMetricLabel"] p,
    [data-testid="stMetric"] label,
    [data-testid="stMetric"] label * {
        font-size: 19px !important;
        font-weight: 800 !important;
        color: #003399 !important;
    }
    
    div[data-testid="stMetricValue"] * {
        font-size: 26px !important;
        font-weight: 900 !important;
        color: #0F172A !important;
    }

    /* 모든 소제목 찐파랑(#003399) + 볼드체 */
    div[data-testid="stHeadingWithAnchor"] h1,
    div[data-testid="stHeadingWithAnchor"] h2,
    div[data-testid="stHeadingWithAnchor"] h3,
    div[data-testid="stHeadingWithAnchor"] h4,
    .stMarkdown h1,
    .stMarkdown h2,
    .stMarkdown h3,
    .stMarkdown h4 {
        color: #003399 !important;
        font-weight: 800 !important;
    }

    /* 구분선 및 알림 박스 */
    hr {
        border-top: 1px solid #CBD5E1 !important;
        margin: 1.8rem 0 !important;
    }

    div[data-testid="stNotification"] {
        border-radius: 10px !important;
        border: 1px solid #CBD5E1 !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.04) !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 3. 본문 상단 타이틀
st.title("🚖 BTX CS 월 별 대시보드")
st.caption(
    "구글 시트 및 엑셀 데이터를 실시간으로 자동 분석하여 월별·주차별·누적 CS"
    " 현황을 시각화합니다."
)

# 사이드바 데이터 연동 설정
st.sidebar.header("🔗 데이터 연동 설정")
gsheet_url = st.sidebar.text_input(
    "구글 시트 주소 (URL) 입력",
    value="https://docs.google.com/spreadsheets/d/1K_CnHTDs00TxDbdmIkpDmOmKdjgC6dDir5yV75GuKIs/edit?gid=1923992354#gid=1923992354",
    placeholder="https://docs.google.com/spreadsheets/d/...",
    help=(
        "구글 시트 [공유] 설정이 '링크가 있는 모든 사용자'로 되어있어야"
        " 합니다."
    ),
)

uploaded_file = st.sidebar.file_uploader(
    "또는 CS 관리 엑셀 파일 업로드 (.xlsx)", type=["xlsx"]
)

if st.sidebar.button("🔄 최신 데이터 새로고침"):
    st.cache_data.clear()
    st.rerun()

# 파란색 계열 전용 컬러 구성
BLUE_PIE_COLORS = [
    "#003399",
    "#1D4ED8",
    "#2563EB",
    "#3B82F6",
    "#60A5FA",
    "#0284C7",
    "#0369A1",
    "#0F172A",
]
BLUE_GROUP_COLORS = ["#003399", "#2563EB", "#3B82F6", "#60A5FA", "#93C5FD"]


# 차트 스타일링 (일반 화면 보기 모드용 깔끔한 기본 규격 원복)
def apply_chart_style(
    fig,
    x_series=None,
    max_val=None,
    text_size=18,    # 일반 화면 기본값 (18px)
    x_size=17,       # 일반 화면 기본값 (17px)
    y_size=15,       # 일반 화면 기본값 (15px)
    title_size=20,   # 일반 화면 기본값 (20px)
    is_group=False,
    force_bar_width=False,
):
    # 1. 막대 상단 수치 (기본 18px + 딥블랙 #0F172A + 볼드)
    fig.update_traces(
        texttemplate="<b>%{y:,.0f}건</b>",
        textposition="outside",
        textfont=dict(size=text_size, color="#0F172A", family="Pretendard"),
        cliponaxis=False,
    )

    if not is_group:
        fig.update_traces(marker_color="#003399")

    # 2. X축 (하단 문의 항목명) 17px
    if x_series is not None:
        unique_x = [str(x) for x in x_series.unique() if pd.notna(x)]
        n_cats = len(unique_x)

        if not is_group:
            if force_bar_width:
                fig.update_traces(width=0.45)
            else:
                bar_width = min(0.6, 0.15 * n_cats)
                fig.update_traces(width=bar_width)

        fig.update_xaxes(
            tickmode="array",
            tickvals=unique_x,
            ticktext=[f"<b style='color:#0F172A;'>{x}</b>" for x in unique_x],
            tickfont=dict(size=x_size, color="#0F172A", family="Pretendard"),
            title_text="",
            automargin=True,
        )
    else:
        fig.update_xaxes(
            tickfont=dict(size=x_size, color="#0F172A", family="Pretendard"),
            title_text="",
            automargin=True,
        )

    # 3. Y축 수치 설정 (15px)
    fig.update_yaxes(
        tickfont=dict(size=y_size, color="#334155", family="Pretendard"),
        title_font=dict(size=y_size, color="#334155", family="Pretendard"),
        automargin=True,
    )

    # 4. 레이아웃
    layout_args = dict(
        font=dict(family="Pretendard", color="#0F172A"),
        title_font=dict(size=title_size, color="#003399", family="Pretendard"),
        margin=dict(t=60, b=60, l=40, r=40),
        autosize=True,
        uniformtext_minsize=text_size,
        uniformtext_mode="show",
    )

    if not is_group:
        layout_args["showlegend"] = False
    else:
        layout_args["legend"] = dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
            font=dict(size=x_size, color="#0F172A", family="Pretendard"),
            title_text="",
        )

    if max_val is not None:
        layout_args["yaxis"] = dict(
            range=[0, max_val * 1.38],
            tickfont=dict(size=y_size, color="#334155", family="Pretendard"),
            title_font=dict(size=y_size, color="#334155", family="Pretendard"),
            automargin=True,
        )

    fig.update_layout(**layout_args)
    return fig


def clean_data_text(df):
    if df.empty:
        return df
    df.columns = [str(c).strip().replace("해제", "해지") for c in df.columns]
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.replace("해제", "해지")
    return df


@st.cache_data(ttl=60)
def load_all_workbook_data(gsheet_url, uploaded_file):
    excel_bytes = None
    if gsheet_url:
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", gsheet_url)
        if match:
            sheet_id = match.group(1)
            export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
            res = requests.get(export_url)
            if res.status_code == 200:
                excel_bytes = res.content
    elif uploaded_file:
        excel_bytes = uploaded_file.getvalue()

    if not excel_bytes:
        return {}, pd.DataFrame(), pd.DataFrame(), []

    xls_dict = pd.read_excel(
        io.BytesIO(excel_bytes), sheet_name=None, header=None
    )
    sheets = list(xls_dict.keys())

    cs_sheets = [s for s in sheets if "년" in s and "월" in s]

    def sort_key(s):
        m = re.search(r"(\d+)년\s*(\d+)월", s)
        if m:
            return int(m.group(1)) * 100 + int(m.group(2))
        return 0

    cs_sheets.sort(key=sort_key, reverse=True)

    cs_sheets_dict = {}
    for s in cs_sheets:
        raw = xls_dict[s]
        header_idx = 0
        for i in range(min(15, len(raw))):
            row_str = [str(x).strip() for x in raw.iloc[i].tolist()]
            if "상담일자" in row_str or "주차" in row_str or "분류" in row_str:
                header_idx = i
                break
        df_sheet = pd.read_excel(
            io.BytesIO(excel_bytes), sheet_name=s, header=header_idx
        )
        df_sheet.columns = [str(c).strip() for c in df_sheet.columns]
        df_sheet = clean_data_text(df_sheet)
        cs_sheets_dict[s] = df_sheet

    df_res_all = pd.DataFrame()
    if "CS예약(NEW)" in sheets:
        df_res_all = pd.read_excel(io.BytesIO(excel_bytes), sheet_name="CS예약(NEW)")
        df_res_all = clean_data_text(df_res_all)
        if "예약시간" in df_res_all.columns:
            df_res_all["예약시간_dt"] = pd.to_datetime(
                df_res_all["예약시간"], errors="coerce"
            )

    df_c_all = pd.DataFrame()
    for s_name in sheets:
        if ("해지" in s_name or "해제" in s_name) and "OB" in s_name:
            if (
                "2025" not in s_name
                and "2024" not in s_name
                and "2023" not in s_name
            ):
                raw_c = xls_dict[s_name]
                header_idx = 0
                for i in range(min(10, len(raw_c))):
                    row_str = [str(x).strip() for x in raw_c.iloc[i].tolist()]
                    if (
                        "OB일자" in row_str
                        or "해지사유" in row_str
                        or "인입날짜" in row_str
                    ):
                        header_idx = i
                        break
                df_c_all = pd.read_excel(
                    io.BytesIO(excel_bytes), sheet_name=s_name, header=header_idx
                )
                df_c_all.columns = [str(c).strip() for c in df_c_all.columns]
                df_c_all = clean_data_text(df_c_all)
                if "OB일자" in df_c_all.columns:
                    df_c_all["OB일자_dt"] = pd.to_datetime(
                        df_c_all["OB일자"], errors="coerce"
                    )
                break

    return cs_sheets_dict, df_res_all, df_c_all, cs_sheets


cs_sheets_dict, df_res_all, df_c_all, available_cs_sheets = (
    load_all_workbook_data(gsheet_url, uploaded_file)
)

if cs_sheets_dict:
    st.sidebar.markdown("---")
    st.sidebar.header("📅 분석 대상 월 선택")

    select_options = available_cs_sheets.copy()

    now = datetime.datetime.now()
    current_month_str = f"{now.year % 100}년{now.month}월"
    default_index = 0
    if current_month_str in select_options:
        default_index = select_options.index(current_month_str)

    selected_month_sheet = st.sidebar.selectbox(
        "조회할 월을 선택하세요", select_options, index=default_index
    )

    display_month_sheet = re.sub(r"년\s*", "년 ", selected_month_sheet).strip()

    m_match = re.search(r"(\d+)년\s*(\d+)월", selected_month_sheet)
    if m_match:
        target_year = 2000 + int(m_match.group(1))
        target_month = int(m_match.group(2))
    else:
        target_year, target_month = 2026, 7

    df = cs_sheets_dict.get(selected_month_sheet, pd.DataFrame())

    dynamic_week_ranges = []

    if not df.empty:
        week_col_main = "주차" if "주차" in df.columns else None
        date_col_main = None
        for c in df.columns:
            c_str = str(c).replace(" ", "")
            if any(kw in c_str for kw in ["상담일자", "일자", "날짜", "접수일", "시간"]):
                date_col_main = c
                break

        if week_col_main and date_col_main:
            temp_df = df.copy()
            temp_df["__dt__"] = pd.to_datetime(
                temp_df[date_col_main], errors="coerce"
            )
            temp_df = temp_df.dropna(subset=["__dt__", week_col_main])

            for w_name, grp in temp_df.groupby(week_col_main):
                w_str = str(w_name).strip()
                if "주" in w_str:
                    dynamic_week_ranges.append({
                        "min_d": grp["__dt__"].min().date(),
                        "max_d": grp["__dt__"].max().date(),
                        "week_name": w_str,
                    })
            dynamic_week_ranges.sort(key=lambda x: x["min_d"])

    df_res_7 = pd.DataFrame()
    if not df_res_all.empty:
        if (
            "CS비고" in df_res_all.columns
            and selected_month_sheet in df_res_all["CS비고"].values
        ):
            df_res_7 = df_res_all[df_res_all["CS비고"] == selected_month_sheet]
        elif "예약시간_dt" in df_res_all.columns:
            df_res_7 = df_res_all[
                (df_res_all["예약시간_dt"].dt.year == target_year)
                & (df_res_all["예약시간_dt"].dt.month == target_month)
            ]

    df_c_month_raw = pd.DataFrame()
    df_c_7 = pd.DataFrame()

    if not df_c_all.empty and "OB일자_dt" in df_c_all.columns:
        df_c_month_raw = df_c_all[
            (df_c_all["OB일자_dt"].dt.year == target_year)
            & (df_c_all["OB일자_dt"].dt.month == target_month)
        ].copy()

        def assign_dynamic_week(row):
            dt = row["OB일자_dt"]
            if pd.isna(dt):
                return "1주차"
            d_val = dt.date()

            if dynamic_week_ranges:
                for w_info in dynamic_week_ranges:
                    if w_info["min_d"] <= d_val <= w_info["max_d"]:
                        return w_info["week_name"]

                if d_val < dynamic_week_ranges[0]["min_d"]:
                    return dynamic_week_ranges[0]["week_name"]
                if d_val > dynamic_week_ranges[-1]["max_d"]:
                    return dynamic_week_ranges[-1]["week_name"]
                for i in range(len(dynamic_week_ranges) - 1):
                    if (
                        dynamic_week_ranges[i]["max_d"]
                        < d_val
                        < dynamic_week_ranges[i + 1]["min_d"]
                    ):
                        return dynamic_week_ranges[i]["week_name"]

            day_val = d_val.day
            w_num = (day_val - 1) // 7 + 1
            if w_num > 4:
                w_num = 4
            return f"{w_num}주차"

        df_c_month_raw["주차"] = df_c_month_raw.apply(
            assign_dynamic_week, axis=1
        )

        if "OB여부" in df_c_month_raw.columns:
            ob_status = df_c_month_raw["OB여부"].astype(str).str.strip()
            df_c_7 = df_c_month_raw[ob_status == "완료"].copy()
        else:
            df_c_7 = df_c_month_raw.copy()

    total_cancel_raw = len(df_c_month_raw) if not df_c_month_raw.empty else 0
    completed_cnt = len(df_c_7) if not df_c_7.empty else 0
    cancelled_cnt = 0
    if not df_c_month_raw.empty and "OB여부" in df_c_month_raw.columns:
        cancelled_cnt = len(
            df_c_month_raw[
                df_c_month_raw["OB여부"]
                .astype(str)
                .str.strip()
                .str.contains("해지 취소", na=False)
            ]
        )

    st.success(
        f"✅ [{display_month_sheet}] CS 인입({len(df):,}건) / CS예약({len(df_res_7):,}건) /"
        f" 실해지 완료({completed_cnt:,}건) 데이터 분석 완료!"
    )

    week_col = "주차" if "주차" in df.columns else None
    cat_col = (
        "분류"
        if "분류" in df.columns
        else ("대분류" if "대분류" in df.columns else None)
    )

    if cat_col:
        df = df.dropna(subset=[cat_col])

    tab1, tab2, tab3, tab4 = st.tabs([
        f"🍩 {display_month_sheet} CS 인입 비중 & CS 예약 현황",
        "📅 주차별 CS 인입 현황",
        f"🚨 {display_month_sheet} 해지OB 세부 분석",
        "🤖 AI 인사이트 리포트",
    ])

    # TAB 1: CS 인입 비중 & CS 예약 현황
    with tab1:
        st.subheader(f"📈 {display_month_sheet} CS 인입 비중 및 월간 현황")
        if cat_col:
            monthly_summary = df[cat_col].value_counts().reset_index()
            monthly_summary.columns = ["대분류", "건수"]
            total_calls = monthly_summary["건수"].sum()
            monthly_summary["비중(%)"] = (
                monthly_summary["건수"] / total_calls * 100
            ).round(1)
            monthly_summary["대분류_범례"] = (
                "<b>" + monthly_summary["대분류"].astype(str) + "</b>"
            )

            col1, col2 = st.columns(2)
            with col1:
                fig_pie = px.pie(
                    monthly_summary,
                    names="대분류_범례",
                    values="건수",
                    hole=0.4,
                    title=(
                        "<b><span style='color:#003399;'>"
                        f"{display_month_sheet} 문의별 비중 (총 {total_calls:,}건)</span></b>"
                    ),
                    color_discrete_sequence=BLUE_PIE_COLORS,
                )
                fig_pie.update_traces(
                    textinfo="percent+label",
                    textposition="inside",
                    textfont=dict(size=16, color="#FFFFFF", family="Pretendard"),
                )
                fig_pie.update_layout(
                    height=500,
                    font=dict(family="Pretendard", color="#0F172A"),
                    title_font=dict(size=20, color="#003399", family="Pretendard"),
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.08,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=18, color="#0F172A", family="Pretendard"),
                    ),
                    margin=dict(t=60, b=80, l=20, r=20),
                    autosize=True,
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                max_m_cnt = (
                    monthly_summary["건수"].max() if not monthly_summary.empty else 10
                )
                fig_m_bar = px.bar(
                    monthly_summary,
                    x="대분류",
                    y="건수",
                    text="건수",
                    title=(
                        "<b><span style='color:#003399;'>"
                        f"{display_month_sheet} 문의별 인입 건수</span></b>"
                    ),
                )
                fig_m_bar.update_layout(height=500, yaxis_title="<b>건수 (건)</b>")
                fig_m_bar = apply_chart_style(
                    fig_m_bar,
                    x_series=monthly_summary["대분류"],
                    max_val=max_m_cnt,
                    force_bar_width=True,
                )
                st.plotly_chart(fig_m_bar, use_container_width=True)

        st.markdown("---")
        st.subheader(f"📅 {display_month_sheet} CS 예약 & OB 현황")
        if not df_res_7.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("📄 CS 상담 예약 건수", f"{len(df_res_7):,} 건")
            top_res_region = (
                df_res_7["운행 지역"].mode()[0]
                if "운행 지역" in df_res_7.columns and not df_res_7["운행 지역"].empty
                else "부산"
            )
            m2.metric("📌 최다 접수 지역", f"{top_res_region}")

            ob_col = None
            for col_candidate in df.columns:
                if str(col_candidate).strip().upper() == "OB":
                    ob_col = col_candidate
                    break

            if ob_col:
                ob_series = df[ob_col].astype(str).str.extract(r"(\d+)")[0]
                ob_cnt = int(
                    pd.to_numeric(ob_series, errors="coerce").fillna(0).sum()
                )
            else:
                ob_cnt = 0

            m3.metric("📞 총 OB 진행 건수", f"{ob_cnt:,} 건")

            r_col1, r_col2 = st.columns(2)
            with r_col1:
                if "운행 지역" in df_res_7.columns:
                    res_reg_df = df_res_7["운행 지역"].value_counts().reset_index()
                    res_reg_df.columns = ["운행 지역", "예약건수"]
                    fig_res_reg = px.bar(
                        res_reg_df,
                        x="운행 지역",
                        y="예약건수",
                        text="예약건수",
                        title=(
                            "<b><span style='color:#003399;'>"
                            f"{display_month_sheet} 지역별 CS예약 건수</span></b>"
                        ),
                    )
                    fig_res_reg.update_layout(
                        height=480, yaxis_title="<b>예약건수 (건)</b>"
                    )
                    fig_res_reg = apply_chart_style(
                        fig_res_reg,
                        x_series=res_reg_df["운행 지역"],
                        max_val=res_reg_df["예약건수"].max(),
                        force_bar_width=True,
                    )
                    st.plotly_chart(fig_res_reg, use_container_width=True)
            with r_col2:
                if "문의 사항" in df_res_7.columns:
                    res_inq_df = df_res_7["문의 사항"].value_counts().reset_index()
                    res_inq_df.columns = ["문의 사항", "예약건수"]
                    fig_res_inq = px.bar(
                        res_inq_df,
                        x="문의 사항",
                        y="예약건수",
                        text="예약건수",
                        title=(
                            "<b><span style='color:#003399;'>"
                            f"{display_month_sheet} 문의별 CS예약 건수</span></b>"
                        ),
                    )
                    fig_res_inq.update_layout(
                        height=480, yaxis_title="<b>예약건수 (건)</b>"
                    )
                    fig_res_inq = apply_chart_style(
                        fig_res_inq,
                        x_series=res_inq_df["문의 사항"],
                        max_val=res_inq_df["예약건수"].max(),
                        force_bar_width=True,
                    )
                    st.plotly_chart(fig_res_inq, use_container_width=True)
        else:
            st.warning(
                f"CS예약(NEW) 시트에서 {display_month_sheet} 예약 데이터를 찾을 수"
                " 없습니다."
            )

    # TAB 2: 주차별 CS 인입 현황
    with tab2:
        st.subheader(f"📅 {display_month_sheet} 주차별 CS 인입 현황 (문의별)")

        if week_col and not df.empty:
            available_weeks = sorted([
                str(w).strip()
                for w in df[week_col].unique()
                if pd.notna(w) and "주" in str(w)
            ])
            if not available_weeks:
                available_weeks = ["1주차", "2주차", "3주차", "4주차"]
        else:
            available_weeks = ["1주차", "2주차", "3주차", "4주차"]

        col_left, col_right = st.columns(2)

        for idx, week_name in enumerate(available_weeks):
            target_col = col_left if idx % 2 == 0 else col_right
            with target_col:
                st.markdown(f"### 📌 {week_name}")
                df_week = (
                    df[df[week_col] == week_name] if week_col else pd.DataFrame()
                )

                if not df_week.empty and cat_col:
                    week_summary = df_week[cat_col].value_counts().reset_index()
                    week_summary.columns = ["분류", "건수"]
                    max_cnt = (
                        week_summary["건수"].max() if not week_summary.empty else 10
                    )

                    fig = px.bar(
                        week_summary,
                        x="분류",
                        y="건수",
                        text="건수",
                        title=(
                            "<b><span style='color:#003399;'>"
                            f"{week_name} 분류별 CS 건수 (총 {len(df_week):,}건)</span></b>"
                        ),
                    )
                    fig.update_layout(height=480, yaxis_title="<b>건수 (건)</b>")
                    fig = apply_chart_style(
                        fig,
                        x_series=week_summary["분류"],
                        max_val=max_cnt,
                        force_bar_width=True,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"{week_name} 데이터가 존재하지 않습니다.")

    # TAB 3: 해지 OB 세부 분석
    with tab3:
        st.subheader(
            f"🚨 {display_month_sheet} 해지OB 세부 분석 (실 해지 완료건만 반영)"
        )

        if not df_c_month_raw.empty:
            prod_counts = (
                df_c_7["가맹"].value_counts().to_dict()
                if "가맹" in df_c_7.columns
                else {}
            )

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("📌 전체 해지 접수 건수", f"{total_cancel_raw:,} 건")
            c2.metric("✅ 실 해지 완료 (차트반영)", f"{completed_cnt:,} 건")
            c3.metric("🔄 해지 취소(가맹유지)", f"{cancelled_cnt:,} 건")

            with c4:
                st.markdown(
                    """<div style="font-size: 19px; font-weight: 800; color: #003399; margin-bottom: 8px;">🏷️ 해지완료 가맹 상품</div>""",
                    unsafe_allow_html=True,
                )
                if prod_counts:
                    for k, v in prod_counts.items():
                        st.markdown(
                            f"""<div style="font-size: 1.4rem; font-weight: 600; line-height: 1.4; color: #0F172A;">• {k}: {v:,}건</div>""",
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown(
                        """<div style="font-size: 1.4rem; font-weight: 600; color: #0F172A;">-</div>""",
                        unsafe_allow_html=True,
                    )

            st.markdown("---")

            c_subtab1, c_subtab2 = st.tabs([
                "📋 주차별 해지 사유",
                f"📊 {display_month_sheet} 해지 종합 차트",
            ])

            with c_subtab1:
                st.subheader(
                    f"📋 주차별 해지 사유 (실 해지 완료 총 {completed_cnt:,}건 기준)"
                )

                if "주차" in df_c_7.columns and not df_c_7.empty:
                    c_weeks = sorted([
                        str(w).strip()
                        for w in df_c_7["주차"].unique()
                        if pd.notna(w) and "주" in str(w)
                    ])
                    if not c_weeks:
                        c_weeks = ["1주차", "2주차", "3주차", "4주차"]
                else:
                    c_weeks = ["1주차", "2주차", "3주차", "4주차"]

                c_col_l, c_col_r = st.columns(2)

                for idx, week_name in enumerate(c_weeks):
                    target_col = c_col_l if idx % 2 == 0 else c_col_r
                    with target_col:
                        st.markdown(f"### 📌 {week_name}")
                        df_cw = (
                            df_c_7[df_c_7["주차"] == week_name]
                            if "주차" in df_c_7.columns
                            else pd.DataFrame()
                        )
                        if not df_cw.empty and "해지사유" in df_cw.columns:
                            r_summary = df_cw["해지사유"].value_counts().reset_index()
                            r_summary.columns = ["해지사유", "건수"]
                            max_rc = r_summary["건수"].max()

                            fig_cw_reason = px.bar(
                                r_summary,
                                x="해지사유",
                                y="건수",
                                text="건수",
                                title=(
                                    "<b><span style='color:#003399;'>해지 OB"
                                    f" {week_name} 완료건 해지사유별 건수 (총"
                                    f" {len(df_cw):,}건)</span></b>"
                                ),
                            )
                            fig_cw_reason.update_layout(
                                height=450, yaxis_title="<b>건수 (건)</b>"
                            )
                            fig_cw_reason = apply_chart_style(
                                fig_cw_reason,
                                x_series=r_summary["해지사유"],
                                max_val=max_rc,
                                force_bar_width=True,
                            )
                            st.plotly_chart(fig_cw_reason, use_container_width=True)
                        else:
                            st.info(f"{week_name} 해지 완료 데이터가 없습니다.")

            with c_subtab2:
                st.subheader(
                    f"📊 {display_month_sheet} 해지사유 & 지역별 종합 차트 (실 해지"
                    " 완료 기준)"
                )
                ch_col1, ch_col2 = st.columns(2)
                with ch_col1:
                    if "해지사유" in df_c_7.columns:
                        reason_df = df_c_7["해지사유"].value_counts().reset_index()
                        reason_df.columns = ["해지사유", "건수"]
                        max_r_cnt = reason_df["건수"].max() if not reason_df.empty else 10

                        fig_reason = px.bar(
                            reason_df,
                            x="해지사유",
                            y="건수",
                            text="건수",
                            title=(
                                "<b><span style='color:#003399;'>"
                                f"{display_month_sheet} 해지사유별 건수 (총"
                                f" {completed_cnt:,}건)</span></b>"
                            ),
                        )
                        fig_reason.update_layout(
                            height=500, yaxis_title="<b>건수 (건)</b>"
                        )
                        fig_reason = apply_chart_style(
                            fig_reason,
                            x_series=reason_df["해지사유"],
                            max_val=max_r_cnt,
                            force_bar_width=True,
                        )
                        st.plotly_chart(fig_reason, use_container_width=True)

                with ch_col2:
                    if "지역" in df_c_7.columns and "해지사유" in df_c_7.columns:
                        reg_reason_pivot = (
                            pd.crosstab(df_c_7["지역"], df_c_7["해지사유"])
                            .reset_index()
                            .melt(id_vars="지역", var_name="해지사유", value_name="건수")
                        )
                        reg_reason_df = reg_reason_pivot[
                            reg_reason_pivot["건수"] > 0
                        ].copy()
                        reg_reason_df["지역_범례"] = (
                            "<b>" + reg_reason_df["지역"].astype(str) + "</b>"
                        )
                        max_rr_cnt = (
                            reg_reason_df["건수"].max() if not reg_reason_df.empty else 10
                        )

                        fig_reg_reason = px.bar(
                            reg_reason_df,
                            x="해지사유",
                            y="건수",
                            color="지역_범례",
                            barmode="group",
                            text="건수",
                            title=(
                                "<b><span style='color:#003399;'>"
                                f"{display_month_sheet} 지역별 & 해지 사유별 비교</span></b>"
                            ),
                            color_discrete_sequence=BLUE_GROUP_COLORS,
                        )
                        fig_reg_reason.update_layout(
                            height=500, yaxis_title="<b>건수 (건)</b>"
                        )
                        fig_reg_reason = apply_chart_style(
                            fig_reg_reason,
                            x_series=reg_reason_df["해지사유"],
                            max_val=max_rr_cnt,
                            is_group=True,
                        )
                        st.plotly_chart(fig_reg_reason, use_container_width=True)

        else:
            st.warning(
                f"해지OB 시트에서 {display_month_sheet} 해지 데이터를 찾을 수"
                " 없습니다."
            )

    # TAB 4: AI 인사이트 리포트
    with tab4:
        st.subheader(f"🤖 {display_month_sheet} AI 자동 생성 종합 분석 보고서")
        if cat_col and not df.empty:
            monthly_summary = df[cat_col].value_counts().reset_index()
            monthly_summary.columns = ["대분류", "건수"]
            total_calls = monthly_summary["건수"].sum()
            monthly_summary["비중(%)"] = (
                monthly_summary["건수"] / total_calls * 100
            ).round(1)

            top_cat = monthly_summary.iloc[0]["대분류"]
            top_val = monthly_summary.iloc[0]["건수"]
            top_pct = monthly_summary.iloc[0]["비중(%)"]

            st.markdown(f"""### 📌 {display_month_sheet} CS 종합 핵심 요약
1. **인입 콜 최다 문의**: **[{top_cat}]** 분야가 **{top_pct}% ({top_val:,}건 / 총 {total_calls:,}건)**으로 전체 1위를 기록했습니다.
2. **상담 예약 현황**: **{display_month_sheet} 총 {len(df_res_7):,}건**의 상담 예약이 인입되었습니다.
3. **해지 OB 현황**: **{display_month_sheet} 총 해지 접수 {total_cancel_raw:,}건** 중 **{completed_cnt:,}건 최종 실 해지 완료**, **{cancelled_cnt:,}건 해지 취소(가맹유지 방어)**를 달성했습니다.""")
else:
    st.info(
        "👈 왼쪽 사이드바에서 구글 시트 URL을 입력하시거나, 엑셀 파일(.xlsx)을"
        " 업로드해 주세요!"
    )
