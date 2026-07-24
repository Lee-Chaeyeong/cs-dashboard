# TAB 2: 월마감 & CS예약 현황
    with tab2:
        st.subheader(f"🍩 {selected_month_sheet} 월마감 전체 CS 인입 비중 및 CS예약 현황")
        if cat_col:
            monthly_summary = df[cat_col].value_counts().reset_index()
            monthly_summary.columns = ['대분류', '건수']
            total_calls = monthly_summary['건수'].sum()
            monthly_summary['비중(%)'] = (monthly_summary['건수'] / total_calls * 100).round(1)
            
            col1, col2 = st.columns(2)
            with col1:
                fig_pie = px.pie(monthly_summary, names='대분류', values='건수', hole=0.4, title=f"<b>{selected_month_sheet} 누적 대분류 비중 (총 {total_calls}건)</b>", color_discrete_sequence=px.colors.qualitative.Set3)
                fig_pie.update_traces(textinfo='percent+label', textposition='inside', textfont=dict(size=16))
                fig_pie.update_layout(
                    title_font=dict(size=22),
                    legend=dict(font=dict(size=18)),
                    margin=dict(t=80, b=50, l=40, r=40)
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                max_m_cnt = monthly_summary['건수'].max() if not monthly_summary.empty else 10
                fig_m_bar = px.bar(monthly_summary, x='대분류', y='건수', text='건수', color='대분류', title=f"<b>{selected_month_sheet} 누적 대분류별 인입 건수 순위</b>", color_discrete_sequence=px.colors.qualitative.Bold)
                fig_m_bar.update_layout(showlegend=False, height=500, xaxis_title="<b>대분류</b>", yaxis_title="<b>건수 (건)</b>")
                fig_m_bar = apply_chart_style(fig_m_bar, x_series=monthly_summary['대분류'], max_val=max_m_cnt, force_bar_width=True)
                st.plotly_chart(fig_m_bar, use_container_width=True)
                
        st.markdown("---")
        st.subheader(f"📅 {selected_month_sheet} CS예약(NEW) 및 OB 현황")
        if not df_res_7.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric(f"📌 {selected_month_sheet} 누적 CS 상담 예약 건수", f"{len(df_res_7)} 건")
            top_res_region = df_res_7['운행 지역'].mode()[0] if '운행 지역' in df_res_7.columns and not df_res_7['운행 지역'].empty else "부산"
            m2.metric("📌 최다 예약 운행 지역", f"{top_res_region}")
            
            # O열 (OB) 데이터가 있으면 빈칸을 제외하고 건수 계산
            ob_cnt = len(df[df['OB'].notna() & (df['OB'].astype(str).str.strip() != '')]) if 'OB' in df.columns else 0
            m3.metric(f"📞 {selected_month_sheet} OB 건수", f"{ob_cnt} 건")
            
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                if '운행 지역' in df_res_7.columns:
                    res_reg_df = df_res_7['운행 지역'].value_counts().reset_index()
                    res_reg_df.columns = ['운행 지역', '예약건수']
                    fig_res_reg = px.bar(res_reg_df, x='운행 지역', y='예약건수', text='예약건수', color='운행 지역', title=f"<b>{selected_month_sheet} CS예약 지역별 분포</b>", color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig_res_reg.update_layout(showlegend=False, height=480, xaxis_title="<b>운행 지역</b>", yaxis_title="<b>예약건수 (건)</b>")
                    fig_res_reg = apply_chart_style(fig_res_reg, x_series=res_reg_df['운행 지역'], max_val=res_reg_df['예약건수'].max(), force_bar_width=True)
                    st.plotly_chart(fig_res_reg, use_container_width=True)
            with r_col2:
                if '문의 사항' in df_res_7.columns:
                    res_inq_df = df_res_7['문의 사항'].value_counts().reset_index()
                    res_inq_df.columns = ['문의 사항', '예약건수']
                    fig_res_inq = px.bar(res_inq_df, x='문의 사항', y='예약건수', text='예약건수', color='문의 사항', title=f"<b>{selected_month_sheet} CS예약 문의사항별 분포</b>", color_discrete_sequence=px.colors.qualitative.Set3)
                    fig_res_inq.update_layout(showlegend=False, height=480, xaxis_title="<b>문의 사항</b>", yaxis_title="<b>예약건수 (건)</b>")
                    fig_res_inq = apply_chart_style(fig_res_inq, x_series=res_inq_df['문의 사항'], max_val=res_inq_df['예약건수'].max(), force_bar_width=True)
                    st.plotly_chart(fig_res_inq, use_container_width=True)
        else:
            st.warning(f"CS예약(NEW) 시트에서 {selected_month_sheet} 예약 데이터를 찾을 수 없습니다.")
