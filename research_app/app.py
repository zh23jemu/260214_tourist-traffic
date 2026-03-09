import streamlit as st

from research_app.analysis.descriptive import (
    build_day_type_summary,
    build_holiday_summary,
    build_overview_metrics,
)
from research_app.analysis.explainability import (
    build_xgboost_shap_analysis,
    explainability_status,
)
from research_app.data_pipeline.dataset import (
    filter_dashboard_dataset,
    load_source_dataset,
    prepare_dashboard_dataset,
)
from research_app.dashboard.plots import (
    build_actual_trend_figure,
    build_arima_result_figure,
    build_day_type_avg_bar_figure,
    build_day_type_box_figure,
    build_holiday_name_bar_figure,
    build_lstm_result_figure,
    build_monthly_trend_figure,
    build_prophet_result_figure,
    build_shap_detail_figure,
    build_shap_summary_figure,
    build_tft_result_figure,
    build_xgboost_result_figure,
)
from research_app.models.arima_model import train_arima
from research_app.models.lstm_model import train_lstm
from research_app.models.prophet_model import train_prophet
from research_app.models.registry import MODEL_REGISTRY
from research_app.models.tft_model import train_tft
from research_app.models.xgboost_model import train_xgboost


@st.cache_data(show_spinner=False)
def run_cached_arima(df, county: str | None):
    return train_arima(df=df, county=county if county != "全部" else None)


@st.cache_data(show_spinner=False)
def run_cached_prophet(df, county: str | None):
    return train_prophet(df=df, county=county if county != "全部" else None)


@st.cache_data(show_spinner=False)
def run_cached_xgboost(df, county: str | None):
    return train_xgboost(df=df, county=county if county != "全部" else None)


@st.cache_data(show_spinner=False)
def run_cached_xgboost_shap(df, county: str | None):
    return build_xgboost_shap_analysis(df=df, county=county if county != "全部" else None)


@st.cache_data(show_spinner=False)
def run_cached_lstm(df, county: str | None):
    return train_lstm(df=df, county=county if county != "全部" else None)


@st.cache_data(show_spinner=False)
def run_cached_tft(df, county: str | None):
    return train_tft(df=df, county=county if county != "全部" else None)


def main() -> None:
    st.set_page_config(
        page_title="荔波县旅游客流研究系统",
        page_icon="📊",
        layout="wide",
    )

    st.title("荔波县旅游客流研究系统")
    st.caption("面向论文研究路线的 Streamlit + Plotly 多模型实验与分析入口")

    raw_df = load_source_dataset()
    df = prepare_dashboard_dataset(raw_df)

    with st.sidebar:
        st.header("筛选条件")
        county_options = ["全部"]
        if "区县" in df.columns:
            county_options.extend(sorted(df["区县"].dropna().astype(str).str.strip().unique().tolist()))
        selected_county = st.selectbox("区县", county_options, index=0)

        day_type_options = []
        if "日期类型" in df.columns:
            day_type_options = [v for v in sorted(df["日期类型"].dropna().unique().tolist()) if v]
        selected_day_types = st.multiselect("日期类型", day_type_options, default=day_type_options)

        min_date = df["日期"].min().date() if "日期" in df.columns and df["日期"].notna().any() else None
        max_date = df["日期"].max().date() if "日期" in df.columns and df["日期"].notna().any() else None
        selected_range = st.date_input(
            "日期范围",
            value=(min_date, max_date) if min_date and max_date else (),
            min_value=min_date,
            max_value=max_date,
        )

    start_date = selected_range[0] if isinstance(selected_range, tuple) and len(selected_range) == 2 else None
    end_date = selected_range[1] if isinstance(selected_range, tuple) and len(selected_range) == 2 else None
    filtered_df = filter_dashboard_dataset(
        df,
        county=None if selected_county == "全部" else selected_county,
        day_types=selected_day_types,
        start_date=start_date,
        end_date=end_date,
    )
    metrics = build_overview_metrics(filtered_df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("有效日期数", metrics["valid_dates"])
    col2.metric("有效客流样本", metrics["valid_actual_rows"])
    col3.metric("日期范围", metrics["date_range"])
    col4.metric("节假日类型数", metrics["holiday_type_count"])

    st.subheader("研究路线概览")
    st.markdown(
        """
        - 数据导入与时空对齐
        - 描述性统计与分布分析
        - SHAP 可解释性分析
        - 多模型训练：ARIMA / Prophet / XGBoost / LightGBM / LSTM / TFT
        - Plotly 研究仪表盘展示
        """
    )

    overview_tab, calendar_tab, models_tab, data_tab = st.tabs(
        ["概览看板", "日期类型分析", "模型路线", "样本数据"]
    )

    with overview_tab:
        left, right = st.columns(2)
        with left:
            st.subheader("实际客流趋势")
            st.plotly_chart(build_actual_trend_figure(filtered_df), use_container_width=True)
        with right:
            st.subheader("月均客流趋势")
            st.plotly_chart(build_monthly_trend_figure(filtered_df), use_container_width=True)

        bottom_left, bottom_right = st.columns(2)
        with bottom_left:
            st.subheader("不同日期类型平均客流")
            st.plotly_chart(build_day_type_avg_bar_figure(filtered_df), use_container_width=True)
        with bottom_right:
            st.subheader("不同节假日平均客流")
            st.plotly_chart(build_holiday_name_bar_figure(filtered_df), use_container_width=True)

    with calendar_tab:
        left, right = st.columns(2)
        with left:
            st.subheader("日期类型客流分布")
            st.plotly_chart(build_day_type_box_figure(filtered_df), use_container_width=True)
        with right:
            st.subheader("日期类型统计表")
            st.dataframe(build_day_type_summary(filtered_df), use_container_width=True, hide_index=True)

        st.subheader("节假日分组统计")
        holiday_summary = build_holiday_summary(filtered_df)
        if holiday_summary.empty:
            st.warning("当前筛选条件下没有节假日样本。")
        else:
            st.dataframe(holiday_summary, use_container_width=True, hide_index=True)

    with models_tab:
        st.subheader("模型实验规划")
        model_rows = [{"model_name": name, **meta} for name, meta in MODEL_REGISTRY.items()]
        st.dataframe(model_rows, use_container_width=True, hide_index=True)

        st.subheader("ARIMA 实验结果")
        arima_result = run_cached_arima(df, selected_county)
        st.write(arima_result.notes)
        if arima_result.status == "trained":
            m1, m2, m3 = st.columns(3)
            m1.metric("ARIMA MAE", f"{arima_result.metrics['mae']:.2f}")
            m2.metric("ARIMA RMSE", f"{arima_result.metrics['rmse']:.2f}")
            m3.metric("ARIMA MAPE", f"{arima_result.metrics['mape']:.4f}")
            st.plotly_chart(build_arima_result_figure(arima_result.forecast_df), use_container_width=True)
            st.dataframe(arima_result.forecast_df, use_container_width=True, hide_index=True)
        else:
            st.warning("ARIMA 当前未能完成训练，请检查样本量或筛选条件。")

        st.subheader("Prophet 实验结果")
        prophet_result = run_cached_prophet(df, selected_county)
        st.write(prophet_result.notes)
        if prophet_result.status == "trained":
            m1, m2, m3 = st.columns(3)
            m1.metric("Prophet MAE", f"{prophet_result.metrics['mae']:.2f}")
            m2.metric("Prophet RMSE", f"{prophet_result.metrics['rmse']:.2f}")
            m3.metric("Prophet MAPE", f"{prophet_result.metrics['mape']:.4f}")
            st.plotly_chart(build_prophet_result_figure(prophet_result.forecast_df), use_container_width=True)
            st.dataframe(prophet_result.forecast_df, use_container_width=True, hide_index=True)
        else:
            st.warning("Prophet 当前未能完成训练，请检查样本量或筛选条件。")

        st.subheader("XGBoost 实验结果")
        xgboost_result = run_cached_xgboost(df, selected_county)
        st.write(xgboost_result.notes)
        if xgboost_result.status == "trained":
            m1, m2, m3 = st.columns(3)
            m1.metric("XGBoost MAE", f"{xgboost_result.metrics['mae']:.2f}")
            m2.metric("XGBoost RMSE", f"{xgboost_result.metrics['rmse']:.2f}")
            m3.metric("XGBoost MAPE", f"{xgboost_result.metrics['mape']:.4f}")
            st.plotly_chart(build_xgboost_result_figure(xgboost_result.forecast_df), use_container_width=True)
            st.dataframe(xgboost_result.forecast_df, use_container_width=True, hide_index=True)
        else:
            st.warning("XGBoost 当前未能完成训练，请检查样本量或筛选条件。")

        st.subheader("LSTM 实验结果")
        lstm_result = run_cached_lstm(df, selected_county)
        st.write(lstm_result.notes)
        if lstm_result.status == "trained":
            m1, m2, m3 = st.columns(3)
            m1.metric("LSTM MAE", f"{lstm_result.metrics['mae']:.2f}")
            m2.metric("LSTM RMSE", f"{lstm_result.metrics['rmse']:.2f}")
            m3.metric("LSTM MAPE", f"{lstm_result.metrics['mape']:.4f}")
            st.plotly_chart(build_lstm_result_figure(lstm_result.forecast_df), use_container_width=True)
            st.dataframe(lstm_result.forecast_df, use_container_width=True, hide_index=True)
        else:
            st.warning("LSTM 当前未能完成训练，请检查样本量或筛选条件。")

        st.subheader("TFT 实验结果")
        tft_result = run_cached_tft(df, selected_county)
        st.write(tft_result.notes)
        if tft_result.status == "trained":
            m1, m2, m3 = st.columns(3)
            m1.metric("TFT MAE", f"{tft_result.metrics['mae']:.2f}")
            m2.metric("TFT RMSE", f"{tft_result.metrics['rmse']:.2f}")
            m3.metric("TFT MAPE", f"{tft_result.metrics['mape']:.4f}")
            st.plotly_chart(build_tft_result_figure(tft_result.forecast_df), use_container_width=True)
            st.dataframe(tft_result.forecast_df, use_container_width=True, hide_index=True)
        else:
            st.warning("TFT 当前未能完成训练，请检查样本量或筛选条件。")

        st.subheader("可解释性分析状态")
        st.info(explainability_status())
        shap_result = run_cached_xgboost_shap(df, selected_county)
        st.write(shap_result.notes)
        if shap_result.status == "ready":
            left, right = st.columns(2)
            with left:
                st.plotly_chart(build_shap_summary_figure(shap_result.summary_df), use_container_width=True)
            with right:
                sample_label = shap_result.sample_date.date() if shap_result.sample_date is not None else "-"
                st.caption(f"解释样本日期: {sample_label}")
                st.plotly_chart(build_shap_detail_figure(shap_result.detail_df), use_container_width=True)

            summary_col, detail_col = st.columns(2)
            with summary_col:
                st.subheader("SHAP 全局重要性表")
                st.dataframe(shap_result.summary_df, use_container_width=True, hide_index=True)
            with detail_col:
                st.subheader("SHAP 单样本贡献表")
                st.dataframe(shap_result.detail_df, use_container_width=True, hide_index=True)
        else:
            st.warning("当前筛选条件下无法生成 SHAP 分析。")

    with data_tab:
        st.subheader("当前筛选后的样本数据")
        show_cols = [c for c in ["日期", "区县", "当日实际人数", "当日预测人数", "当日天气", "日期属性", "日期属性编码", "节假日名称"] if c in filtered_df.columns]
        if filtered_df.empty:
            st.warning("当前筛选条件下没有数据。")
        else:
            st.dataframe(filtered_df[show_cols].sort_values("日期", ascending=False), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
