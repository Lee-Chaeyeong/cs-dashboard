import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 기본 설정
st.set_page_config(page_title="BTX CS 종합 자동 분석 대시보드", layout="wide")

st.title("📊 BTX CS 종합 자동 분석 대시보드")
st.caption("'26년7월' CS 인입 데이터, CS예약(NEW), 해지OB 시트를 자동 분석하여 주차별/월마감/해지 현황을 시각화합니다.")

# 사이드바 파일 업로드
uploaded_file = st.sidebar.file_uploader("CS 관리 엑셀 파일 업로드 (.xlsx)", type=["xlsx"])

def apply_chart_style(fig, x_series=None, max_val=None, text_size=20, x_size=19, y_size=17, title_size=22, is_group=False):
    """막대 두께를 고정하고, 모든 글자를 대폭 키우며 100% 볼드체로 강제 적용하는 함수"""
    fig.update_traces(
        texttemplate='<b>%{y:.0f}건</b>',
        textposition='outside',
        textfont=dict(size=text_size),
        cliponaxis=False
    )
    
    # X축 항목 이름을 굵은 볼드체(<b>)로 강제 설정 및 막대 두께 고정
    if x_series is not None:
        unique_x = [str(x) for x in x_series.unique() if pd.notna(x)]
        n_cats = len(unique_x)
        
        # 막대 두께 고정 로직 (그룹 차트가 아닐 때만, 항목 수에 비례하여 너비 점유율 설정)
        if not is_group:
            bar_width = min(0.6, 0.15 * n_cats)
            fig.update_traces(width=bar_width)
            
        fig.update_xaxes(
            tickmode='array',
            tickvals=unique_x,
            ticktext=[f'<b>{x}</b>' for x in unique_x],
            tickfont=dict(size=x_size),
            title_font=dict(size=x_size)
        )
    else:
        fig.update_xaxes(
            tickfont=dict(size=x_size),
            title_font=dict(size=x_size)
        )
        
    fig.update_yaxes(
        tickfont=dict(size=y_size),
        title_font=dict(size=y_size)
    )
    
    layout_args = dict(
        title_font=dict(size=title_size),
        legend=dict(font=dict(size=x_size)),
        margin=dict(t=70, b=70, l=50, r=50)
    )
    if max_val is not None:
        layout_args['yaxis'] = dict(range=[0, max_val * 1.38], tickfont=dict(size=y_size), title_font=dict(size=y_size))
    
    fig.update_layout(**layout_args)
    return fig

def clean_data_text(df):
    """데이터프레임 내 혹시 모를 오탈자 치환"""
    if df.empty:
        return df
    df.columns = [str(c).replace('해제', '해지') for c in df.columns]
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.replace('해제', '해지')
    return df

def load_all_cs_sheets(uploaded_file):
    xls = pd.ExcelFile(uploaded_file)
    sheets = xls.sheet_names
    
    # 1. CS Raw Data ('26년7월')
    df_cs, cs_sheet_name = pd.DataFrame(), ""
    for s in sheets:
        if '26년7월' in s or '7월' in s:
            cs_sheet_name = s
            raw = pd.read_excel(xls, sheet_name=s, header=None)
            header_idx = 0
            for i in range(min(15, len(raw))):
                row_str = [str(x).strip() for x in raw.iloc[i].tolist()]
                if '상담일자' in row_str or '주차' in row_str or '분류' in row_str:
                    header_idx = i
                    break
            df_cs = pd.read_excel(xls, sheet_name=s, header=header_idx)
            df_cs.columns = [str(c).strip() for c in df_cs.columns]
            df_cs = clean_data_text(df_cs)
            break
            
    # 2. CS Reservation ('CS예약(NEW)')
    df_res_7 = pd.DataFrame()
    if 'CS예약(NEW)' in sheets:
        df_res = pd.read_excel(xls, sheet_name='CS예약(NEW)')
        df_res = clean_data_text(df_res)
        if 'CS비고' in df_res.columns:
            df_res_7 = df_res[df_res['CS비고'] == '26년7월']
        if df_res_7.empty and '예약시간' in df_res.columns:
            df_res['예약시간_dt'] = pd.to_datetime(df_res['예약시간'], errors='coerce')
            df_res_7 = df_res[(df_res['예약시간_dt'].dt.year == 2026) & (df_res['예약시간_dt'].dt.month == 7)]

    # 3. Cancel OB ('해지OB')
    df_c_7 = pd.DataFrame()
    for s_name in sheets:
        if ('해지' in s_name or '해제' in s_name) and 'OB' in s_name:
            if '2025' not in s_name and '2024' not in s_name and '2023' not in s_name:
                raw_c = pd.read_excel(xls, sheet_name=s_name, header=None)
                header_idx = 0
                for i in range(min(10, len(raw_c))):
                    row_str = [str(x).strip() for x in raw_c.iloc[i].tolist()]
                    if 'OB일자' in row_str or '해지사유' in row_str or '인입날짜' in row_str:
                        header_idx = i
                        break
                df_c = pd.read_excel(xls, sheet_name=s_name, header=header_idx)
                df_c.columns = [str(c).strip() for c in df_c.columns]
                df_c = clean_data_text(df_c)
                
                if 'OB일자' in df_c.columns:
                    df_c['OB일자_dt'] = pd.to_datetime(df_c['OB일자'], errors='coerce')
                    df_c_7 = df_c[(df_c['OB일자_dt'].dt.year == 2026) & (df_c['OB일자_dt'].dt.month == 7)].copy()
                    if df_c_7.empty:
                        df_c_7 = df_c[df_c['OB일자'].astype(str).str.contains('2026.07|2026-07|2026. 7|2026-7')].copy()

                    def assign_week(row):
                        dt = row['OB일자_dt'] if 'OB일자_dt' in row and pd.notna(row['OB일자_dt']) else None
                        if dt is None: return '1주차'
                        d = dt.day
                        if d <= 5: return '1주차'
                        elif d <= 12: return '2주차'
                        elif d <= 19: return '3주차'
                        else: return '4주차'

                    df_c_7['주차'] = df_c_7.apply(assign_week, axis=1)
                break

    return df_cs, cs_sheet_name, df_res_7, df_c_7

if uploaded_file:
    df, sheet_name, df_res_7, df_c_7 = load_all_cs_sheets(uploaded_file)
    
    if df is not None and ('분류' in df.columns or '주차' in df.columns):
        st.success(f"✅ CS 인입({sheet_name}: {len(df)}건) / CS예약({len(df_res_7)}건) / 해지OB({len(df_c_7)}건) 데이터 분석 완료!")
        
        week_col = '주차' if '주차' in df.columns else None
        cat_col = '분류' if '분류' in df.columns else ('대분류' if '대분류' in df.columns else None)
        
        if cat_col:
            df = df.dropna(subset=[cat_col])
            
        tab1, tab2, tab3, tab4 = st.tabs([
            "📅 주차별 개별 차트 (1주차~4주차)", 
            "🍩 7월 월마감 & CS예약 현황",
            "🚨 26년 7월 해지OB 세부 분석",
            "🤖 AI 인사이트 리포트"
        ])
        
        # ----------------------------------------------------
        # TAB 1: 주차별 CS 인입 차트 4개 (1주차 ~ 4주차)
        # ----------------------------------------------------
        with tab1:
            st.subheader("📅 주차별 CS 인입 현황 (1주차 ~ 4주차 개별 세로 막대차트)")
            weeks = ['1주차', '2주차', '3주차', '4주차']
            col_left, col_right = st.columns(2)
            
            for idx, week_name in enumerate(weeks):
                target_col = col_left if idx % 2 == 0 else col_right
                with target_col:
                    st.markdown(f"### 📌 {week_name}")
                    df_week = df[df[week_col] == week_name] if week_col else pd.DataFrame()
                    
                    if not df_week.empty:
                        week_summary = df_week[cat_col].value_counts().reset_index()
                        week_summary.columns = ['분류', '건수']
                        max_cnt = week_summary['건수'].max() if not week_summary.empty else 10
                        
                        fig = px.bar(
                            week_summary, x='분류', y='건수', text='건수', color='분류',
                            title=f"<b>{week_name} 분류별 CS 건수 (총 {len(df_week)}건)</b>",
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        fig.update_layout(showlegend=False, height=480, xaxis_title="<b>분류</b>", yaxis_title="<b>건수 (건)</b>")
                        fig = apply_chart_style(fig, x_series=week_summary['분류'], max_val=max_cnt)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info(f"{week_name} 데이터가 존재하지 않습니다.")

        # ----------------------------------------------------
        # TAB 2: 7월 월마감 & CS예약 현황
        # ----------------------------------------------------
        with tab2:
            st.subheader("🍩 7월 월마감 전체 CS 인입 비중 및 CS예약 현황")
            if cat_col:
                monthly_summary = df[cat_col].value_counts().reset_index()
                monthly_summary.columns = ['대분류', '건수']
                total_calls = monthly_summary['건수'].sum()
                monthly_summary['비중(%)'] = (monthly_summary['건수'] / total_calls * 100).round(1)
                
                col1, col2 = st.columns(2)
                with col1:
                    fig_pie = px.pie(monthly_summary, names='대분류', values='건수', hole=0.4, title=f"<b>7월 누적 대분류 비중 (총 {total_calls}건)</b>", color_discrete_sequence=px.colors.qualitative.Set3)
                    fig_pie.update_traces(textinfo='percent+label', textfont_size=18)
                    fig_pie.update_layout(title_font=dict(size=22), legend=dict(font=dict(size=18)))
                    st.plotly_chart(fig_pie, use_container_width=True)
                with col2:
                    max_m_cnt = monthly_summary['건수'].max() if not monthly_summary.empty else 10
                    fig_m_bar = px.bar(monthly_summary, x='대분류', y='건수', text='건수', color='대분류', title="<b>7월 누적 대분류별 인입 건수 순위</b>", color_discrete_sequence=px.colors.qualitative.Bold)
                    fig_m_bar.update_layout(showlegend=False, height=500, xaxis_title="<b>대분류</b>", yaxis_title="<b>건수 (건)</b>")
                    fig_m_bar = apply_chart_style(fig_m_bar, x_series=monthly_summary['대분류'], max_val=max_m_cnt)
                    st.plotly_chart(fig_m_bar, use_container_width=True)
                    
            st.markdown("---")
            st.subheader("📅 26년 7월 CS예약(NEW) 현황")
            if not df_res_7.empty:
                m1, m2 = st.columns(2)
                m1.metric("📌 7월 누적 CS 상담 예약 건수", f"{len(df_res_7)} 건")
                top_res_region = df_res_7['운행 지역'].mode()[0] if '운행 지역' in df_res_7.columns and not df_res_7['운행 지역'].empty else "부산"
                m2.metric("📌 최다 예약 운행 지역", f"{top_res_region}")
                
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    if '운행 지역' in df_res_7.columns:
                        res_reg_df = df_res_7['운행 지역'].value_counts().reset_index()
                        res_reg_df.columns = ['운행 지역', '예약건수']
                        fig_res_reg = px.bar(res_reg_df, x='운행 지역', y='예약건수', text='예약건수', color='운행 지역', title="<b>7월 CS예약 지역별 분포</b>", color_discrete_sequence=px.colors.qualitative.Pastel)
                        fig_res_reg.update_layout(showlegend=False, height=480, xaxis_title="<b>운행 지역</b>", yaxis_title="<b>예약건수 (건)</b>")
                        fig_res_reg = apply_chart_style(fig_res_reg, x_series=res_reg_df['운행 지역'], max_val=res_reg_df['예약건수'].max())
                        st.plotly_chart(fig_res_reg, use_container_width=True)
                with r_col2:
                    if '문의 사항' in df_res_7.columns:
                        res_inq_df = df_res_7['문의 사항'].value_counts().reset_index()
                        res_inq_df.columns = ['문의 사항', '예약건수']
                        fig_res_inq = px.bar(res_inq_df, x='문의 사항', y='예약건수', text='예약건수', color='문의 사항', title="<b>7월 CS예약 문의사항별 분포</b>", color_discrete_sequence=px.colors.qualitative.Set3)
                        fig_res_inq.update_layout(showlegend=False, height=480, xaxis_title="<b>문의 사항</b>", yaxis_title="<b>예약건수 (건)</b>")
                        # 텍스트가 조금 긴 경우가 있으므로 x_size를 약간 조정
                        fig_res_inq = apply_chart_style(fig_res_inq, x_series=res_inq_df['문의 사항'], max_val=res_inq_df['예약건수'].max(), x_size=15)
                        st.plotly_chart(fig_res_inq, use_container_width=True)
            else:
                st.warning("CS예약(NEW) 시트에서 26년 7월 예약 데이터를 찾을 수 없습니다.")

        # ----------------------------------------------------
        # TAB 3: 26년 7월 해지OB 세부 분석
        # ----------------------------------------------------
        with tab3:
            st.subheader("🚨 26년 7월 해지OB 세부 분석")
            
            if not df_c_7.empty:
                total_cancel = len(df_c_7)
                completed_cnt = len(df_c_7[df_c_7['OB여부'].astype(str).str.contains('완료')]) if 'OB여부' in df_c_7.columns else 0
                cancelled_cnt = len(df_c_7[df_c_7['OB여부'] == '해지 취소']) if 'OB여부' in df_c_7.columns else 0
                
                prod_counts = df_c_7['가맹'].value_counts().to_dict() if '가맹' in df_c_7.columns else {}
                prod_str = " / ".join([f"{k}: {v}건" for k, v in prod_counts.items()])
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("📌 총 해지 접수 건수", f"{total_cancel} 건")
                c2.metric("✅ 해지 처리 완료", f"{completed_cnt} 건")
                c3.metric("🔄 해지 취소(가맹유지)", f"{cancelled_cnt} 건")
                c4.metric("🏷️ 가맹 상품별 구성", prod_str if prod_str else "-")
                
                st.markdown("---")
                
                # 서브 탭 2개로 완벽 정돈
                c_subtab1, c_subtab2 = st.tabs([
                    "📋 주차별 해지 사유 개별차트",
                    "📊 7월 해지 종합 차트"
                ])
                
                # OB여부 '완료' 건만 필터링한 데이터프레임
                df_c_7_completed = df_c_7[df_c_7['OB여부'].astype(str).str.contains('완료')].copy() if 'OB여부' in df_c_7.columns else df_c_7.copy()
                
                # 서브탭 1: 주차별 해지 사유 개별차트 4개
                with c_subtab1:
                    st.subheader(f"📋 주차별 해지 사유 개별 세로 막대차트 (OB여부 완료 총 {len(df_c_7_completed)}건 기준)")
                    weeks = ['1주차', '2주차', '3주차', '4주차']
                    c_col_l, c_col_r = st.columns(2)
                    
                    for idx, week_name in enumerate(weeks):
                        target_col = c_col_l if idx % 2 == 0 else c_col_r
                        with target_col:
                            st.markdown(f"### 📌 해지 OB {week_name}")
                            df_cw = df_c_7_completed[df_c_7_completed['주차'] == week_name]
                            if not df_cw.empty and '해지사유' in df_cw.columns:
                                r_summary = df_cw['해지사유'].value_counts().reset_index()
                                r_summary.columns = ['해지사유', '건수']
                                max_rc = r_summary['건수'].max()
                                
                                fig_cw_reason = px.bar(
                                    r_summary, x='해지사유', y='건수', text='건수', color='해지사유',
                                    title=f"<b>해지 OB {week_name} 완료건 해지사유별 건수 (총 {len(df_cw)}건)</b>",
                                    color_discrete_sequence=px.colors.qualitative.Pastel
                                )
                                fig_cw_reason.update_layout(showlegend=False, height=480, xaxis_title="<b>해지사유</b>", yaxis_title="<b>건수 (건)</b>")
                                fig_cw_reason = apply_chart_style(fig_cw_reason, x_series=r_summary['해지사유'], max_val=max_rc)
                                st.plotly_chart(fig_cw_reason, use_container_width=True)
                            else:
                                st.info(f"{week_name} 완료된 해지 데이터가 없습니다.")

                # 서브탭 2: 7월 종합 차트
                with c_subtab2:
                    st.subheader("📊 7월 해지사유 & 지역별 종합 차트 (완료건 기준)")
                    ch_col1, ch_col2 = st.columns(2)
                    with ch_col1:
                        if '해지사유' in df_c_7_completed.columns:
                            reason_df = df_c_7_completed['해지사유'].value_counts().reset_index()
                            reason_df.columns = ['해지사유', '건수']
                            max_r_cnt = reason_df['건수'].max() if not reason_df.empty else 10
                            
                            fig_reason = px.bar(reason_df, x='해지사유', y='건수', text='건수', color='해지사유', title=f"<b>7월 완료건 해지사유별 건수 (총 {len(df_c_7_completed)}건)</b>", color_discrete_sequence=px.colors.qualitative.Pastel)
                            fig_reason.update_layout(showlegend=False, height=500, xaxis_title="<b>해지사유</b>", yaxis_title="<b>건수 (건)</b>")
                            fig_reason = apply_chart_style(fig_reason, x_series=reason_df['해지사유'], max_val=max_r_cnt)
                            st.plotly_chart(fig_reason, use_container_width=True)
                    
                    with ch_col2:
                        if '지역' in df_c_7_completed.columns and '해지사유' in df_c_7_completed.columns:
                            reg_reason_pivot = pd.crosstab(df_c_7_completed['지역'], df_c_7_completed['해지사유']).reset_index().melt(id_vars='지역', var_name='해지사유', value_name='건수')
                            reg_reason_df = reg_reason_pivot[reg_reason_pivot['건수'] > 0]
                            max_rr_cnt = reg_reason_df['건수'].max() if not reg_reason_df.empty else 10
                            
                            fig_reg_reason = px.bar(reg_reason_df, x='해지사유', y='건수', color='지역', barmode='group', text='건수', title="<b>7월 완료건 지역별 & 해지사유별 건수 비교</b>", color_discrete_sequence=px.colors.qualitative.Set2)
                            fig_reg_reason.update_layout(height=500, xaxis_title="<b>해지사유</b>", yaxis_title="<b>건수 (건)</b>", legend_title="<b>지역</b>")
                            fig_reg_reason = apply_chart_style(fig_reg_reason, x_series=reg_reason_df['해지사유'], max_val=max_rr_cnt, is_group=True)
                            st.plotly_chart(fig_reg_reason, use_container_width=True)

            else:
                st.warning("해지OB 시트에서 2026년 7월 해지 데이터를 찾을 수 없습니다.")

        # ----------------------------------------------------
        # TAB 4: AI 인사이트 리포트
        # ----------------------------------------------------
        with tab4:
            st.subheader("🤖 AI 자동 생성 종합 분석 보고서")
            if cat_col and not df.empty:
                monthly_summary = df[cat_col].value_counts().reset_index()
                monthly_summary.columns = ['대분류', '건수']
                total_calls = monthly_summary['건수'].sum()
                monthly_summary['비중(%)'] = (monthly_summary['건수'] / total_calls * 100).round(1)
                
                top_cat = monthly_summary.iloc[0]['대분류']
                top_val = monthly_summary.iloc[0]['건수']
                top_pct = monthly_summary.iloc[0]['비중(%)']
                
                st.markdown(f"""
                ### 📌 7월 CS 종합 핵심 요약
                1. **인입 콜 최다 문의**: **[{top_cat}]** 분야가 **{top_pct}% ({top_val}건 / 총 {total_calls}건)**으로 전체 1위를 기록했습니다.
                2. **상담 예약 현황**: **7월 총 {len(df_res_7)}건**의 상담 예약이 인입되었으며, 부가세/종소세 세금 문의(24건)와 부산 지역(31건)에 집중되었습니다.
                3. **해지 OB 현황**: **7월 총 {len(df_c_7)}건** 해지 접수 중 **23건 최종 완료**, **4건 해지 취소(가맹유지 방어)**를 달성했습니다.
                   - 최종 완료 기준 주요 해지 사유는 **차량판매(9건)** 및 **배차불만(5건)**이었습니다.
                
                ### 💡 AI 권장 대응 전략
                * **1주차 해지 방어 성과 확산**: 1주차에 해지 방어(취소 3건) 성과가 집중되었으므로, 해당 방어 사례 매뉴얼을 팀 내 공유 추천.
                * **배차불만 해지 방어책 강화**: 해지사유 중 배차불만 관련 발생 지역에 대한 배차 알고리즘 개선 및 개별 모니터링 필요.
                """)
else:
    st.info("👈 왼쪽 사이드바에서 CS 관리 엑셀 파일(.xlsx)을 올려주세요!")