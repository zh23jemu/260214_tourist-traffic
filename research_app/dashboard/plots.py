import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _split_result_segments(result_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if result_df is None or result_df.empty:
        return pd.DataFrame(), pd.DataFrame()
    return (
        result_df[result_df["segment"] == "holdout"].copy(),
        result_df[result_df["segment"] == "forecast"].copy(),
    )


def build_actual_trend_figure(df: pd.DataFrame) -> go.Figure:
    valid = df[df["日期"].notna() & df["当日实际人数"].notna()].copy()
    if valid.empty:
        return go.Figure()
    fig = px.line(
        valid,
        x="日期",
        y="当日实际人数",
        title="实际客流趋势",
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return fig


def build_monthly_trend_figure(df: pd.DataFrame) -> go.Figure:
    valid = df[df["日期"].notna() & df["当日实际人数"].notna()].copy()
    if valid.empty:
        return go.Figure()
    valid["年月"] = valid["日期"].dt.to_period("M").astype(str)
    monthly = valid.groupby("年月", as_index=False)["当日实际人数"].mean()
    fig = px.bar(monthly, x="年月", y="当日实际人数", title="月均客流趋势")
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return fig


def build_day_type_box_figure(df: pd.DataFrame) -> go.Figure:
    if "日期类型" not in df.columns:
        return go.Figure()
    valid = df[df["当日实际人数"].notna()].copy()
    if valid.empty:
        return go.Figure()
    fig = px.box(
        valid,
        x="日期类型",
        y="当日实际人数",
        color="日期类型",
        title="不同日期类型的客流分布",
    )
    fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def build_day_type_avg_bar_figure(df: pd.DataFrame) -> go.Figure:
    valid = df[df["当日实际人数"].notna()].copy()
    if valid.empty or "日期类型" not in valid.columns:
        return go.Figure()
    summary = valid.groupby("日期类型", as_index=False)["当日实际人数"].mean().round(2)
    fig = px.bar(summary, x="日期类型", y="当日实际人数", color="日期类型", title="不同日期类型平均客流")
    fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def build_holiday_name_bar_figure(df: pd.DataFrame) -> go.Figure:
    valid = df[(df["当日实际人数"].notna()) & (df["节假日名称展示"] != "无")].copy()
    if valid.empty:
        return go.Figure()
    summary = valid.groupby("节假日名称展示", as_index=False)["当日实际人数"].mean().round(2)
    fig = px.bar(summary, x="节假日名称展示", y="当日实际人数", color="节假日名称展示", title="不同节假日平均客流")
    fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def build_arima_result_figure(result_df: pd.DataFrame) -> go.Figure:
    if result_df is None or result_df.empty:
        return go.Figure()

    fig = go.Figure()
    holdout_df, forecast_df = _split_result_segments(result_df)

    if not holdout_df.empty:
        fig.add_trace(
            go.Scatter(
                x=holdout_df["date"],
                y=holdout_df["actual"],
                mode="lines+markers",
                name="Holdout Actual",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=holdout_df["date"],
                y=holdout_df["predicted"],
                mode="lines+markers",
                name="Holdout Predicted",
            )
        )

    if not forecast_df.empty:
        fig.add_trace(
            go.Scatter(
                x=forecast_df["date"],
                y=forecast_df["predicted"],
                mode="lines+markers",
                name="Future Forecast",
                line=dict(dash="dash"),
            )
        )

    fig.update_layout(
        title="ARIMA 验证与未来预测",
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="Date",
        yaxis_title="Visitor Count",
    )
    return fig


def build_prophet_result_figure(result_df: pd.DataFrame) -> go.Figure:
    if result_df is None or result_df.empty:
        return go.Figure()

    fig = go.Figure()
    holdout_df, forecast_df = _split_result_segments(result_df)

    if not holdout_df.empty:
        fig.add_trace(
            go.Scatter(
                x=holdout_df["date"],
                y=holdout_df["actual"],
                mode="lines+markers",
                name="Holdout Actual",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=holdout_df["date"],
                y=holdout_df["predicted"],
                mode="lines+markers",
                name="Holdout Predicted",
            )
        )

    if not forecast_df.empty:
        fig.add_trace(
            go.Scatter(
                x=forecast_df["date"],
                y=forecast_df["predicted"],
                mode="lines+markers",
                name="Future Forecast",
                line=dict(dash="dash"),
            )
        )

    fig.update_layout(
        title="Prophet 验证与未来预测",
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="Date",
        yaxis_title="Visitor Count",
    )
    return fig


def build_xgboost_result_figure(result_df: pd.DataFrame) -> go.Figure:
    if result_df is None or result_df.empty:
        return go.Figure()

    fig = go.Figure()
    holdout_df, forecast_df = _split_result_segments(result_df)

    if not holdout_df.empty:
        fig.add_trace(
            go.Scatter(
                x=holdout_df["date"],
                y=holdout_df["actual"],
                mode="lines+markers",
                name="Holdout Actual",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=holdout_df["date"],
                y=holdout_df["predicted"],
                mode="lines+markers",
                name="Holdout Predicted",
            )
        )

    if not forecast_df.empty:
        fig.add_trace(
            go.Scatter(
                x=forecast_df["date"],
                y=forecast_df["predicted"],
                mode="lines+markers",
                name="Future Forecast",
                line=dict(dash="dash"),
            )
        )

    fig.update_layout(
        title="XGBoost 验证与未来预测",
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="Date",
        yaxis_title="Visitor Count",
    )
    return fig


def build_shap_summary_figure(summary_df: pd.DataFrame, top_n: int = 12) -> go.Figure:
    if summary_df is None or summary_df.empty:
        return go.Figure()

    plot_df = summary_df.head(top_n).sort_values("mean_abs_shap", ascending=True)
    fig = px.bar(
        plot_df,
        x="mean_abs_shap",
        y="feature",
        orientation="h",
        title="XGBoost SHAP 全局重要性",
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20), yaxis_title="Feature", xaxis_title="Mean |SHAP|")
    return fig


def build_shap_detail_figure(detail_df: pd.DataFrame, top_n: int = 12) -> go.Figure:
    if detail_df is None or detail_df.empty:
        return go.Figure()

    plot_df = detail_df.head(top_n).sort_values("shap_value", ascending=True)
    colors = ["#d94f4f" if value >= 0 else "#3b82f6" for value in plot_df["shap_value"]]
    fig = go.Figure(
        go.Bar(
            x=plot_df["shap_value"],
            y=plot_df["feature"],
            orientation="h",
            marker_color=colors,
        )
    )
    fig.update_layout(
        title="XGBoost 单样本 SHAP 贡献",
        margin=dict(l=20, r=20, t=50, b=20),
        yaxis_title="Feature",
        xaxis_title="SHAP Value",
    )
    return fig


def build_lstm_result_figure(result_df: pd.DataFrame) -> go.Figure:
    if result_df is None or result_df.empty:
        return go.Figure()

    fig = go.Figure()
    holdout_df, forecast_df = _split_result_segments(result_df)

    if not holdout_df.empty:
        fig.add_trace(
            go.Scatter(
                x=holdout_df["date"],
                y=holdout_df["actual"],
                mode="lines+markers",
                name="Holdout Actual",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=holdout_df["date"],
                y=holdout_df["predicted"],
                mode="lines+markers",
                name="Holdout Predicted",
            )
        )

    if not forecast_df.empty:
        fig.add_trace(
            go.Scatter(
                x=forecast_df["date"],
                y=forecast_df["predicted"],
                mode="lines+markers",
                name="Future Forecast",
                line=dict(dash="dash"),
            )
        )

    fig.update_layout(
        title="LSTM 验证与未来预测",
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="Date",
        yaxis_title="Visitor Count",
    )
    return fig


def build_tft_result_figure(result_df: pd.DataFrame) -> go.Figure:
    if result_df is None or result_df.empty:
        return go.Figure()

    fig = go.Figure()
    holdout_df, forecast_df = _split_result_segments(result_df)

    if not holdout_df.empty:
        fig.add_trace(
            go.Scatter(
                x=holdout_df["date"],
                y=holdout_df["actual"],
                mode="lines+markers",
                name="Holdout Actual",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=holdout_df["date"],
                y=holdout_df["predicted"],
                mode="lines+markers",
                name="Holdout Predicted",
            )
        )

    if not forecast_df.empty:
        fig.add_trace(
            go.Scatter(
                x=forecast_df["date"],
                y=forecast_df["predicted"],
                mode="lines+markers",
                name="Future Forecast",
                line=dict(dash="dash"),
            )
        )

    fig.update_layout(
        title="TFT 验证与未来预测",
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="Date",
        yaxis_title="Visitor Count",
    )
    return fig


def build_model_metric_comparison_figure(metrics_df: pd.DataFrame, metric_name: str = "rmse") -> go.Figure:
    if metrics_df is None or metrics_df.empty or metric_name not in metrics_df.columns:
        return go.Figure()

    plot_df = metrics_df.sort_values(metric_name, ascending=True).copy()
    fig = px.bar(
        plot_df,
        x="model_name",
        y=metric_name,
        color="model_name",
        title=f"模型 {metric_name.upper()} 对比",
    )
    fig.update_layout(showlegend=False, margin=dict(l=20, r=20, t=50, b=20), xaxis_title="Model")
    return fig


def build_model_forecast_comparison_figure(model_results: dict[str, object]) -> go.Figure:
    fig = go.Figure()
    added_actual = False

    for model_name, result in model_results.items():
        result_df = getattr(result, "forecast_df", None)
        holdout_df, forecast_df = _split_result_segments(result_df)

        if not added_actual and not holdout_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=holdout_df["date"],
                    y=holdout_df["actual"],
                    mode="lines+markers",
                    name="Holdout Actual",
                    line=dict(color="#111827", width=3),
                )
            )
            added_actual = True

        if not forecast_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=forecast_df["date"],
                    y=forecast_df["predicted"],
                    mode="lines+markers",
                    name=f"{model_name} Forecast",
                )
            )

    fig.update_layout(
        title="多模型未来预测对比",
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="Date",
        yaxis_title="Visitor Count",
        legend_title="Series",
    )
    return fig
