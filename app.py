"""VN Apartment Intelligence v2 — Crimson Edition.
Streamlit BI/DSS dashboard cho ban giám đốc. Đọc dw.* qua DATABASE_URL (.streamlit/secrets.toml).
Thêm trang mới: viết hàm và gắn @page("khoá", "Tên") — menu tự cập nhật.
"""
import re
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine, text

st.set_page_config(page_title="VN Apartment | BI & DSS", page_icon="🏢", layout="wide", initial_sidebar_state="expanded")

# ------------------------------------------------------------ design tokens
RED, DEEP, ROSE, INK = "#B81E34", "#6E0F20", "#E8788A", "#2B1519"
SCALE = ["#FDECEE", "#F5B5BE", "#E0525F", "#B81E34", "#6E0F20"]
CAT = ["#B81E34", "#E8788A", "#6E0F20", "#E9A23B", "#4A4A55", "#C9A227", "#9C4A55", "#F5B5BE"]
# Chỉ dùng cho bốn biểu đồ được yêu cầu, không thay bảng màu toàn dashboard.
ACCENT_COLORS = ["#651728", "#B7283E", "#D66C7C", "#194C3A", "#39734F"]
DIV = ["#2F6F73", "#FFF7F8", "#B81E34"]
BED_ORDER = ["Studio", "1PN", "2PN", "3PN", "4PN+"]
AREA_ORDER = ["Dưới 45 m²", "45–60 m²", "60–80 m²", "80–100 m²", "Trên 100 m²"]

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
html {font-size:17px !important}
html,body,.stApp,[data-testid="stAppViewContainer"] {font-family:'Be Vietnam Pro',Arial,sans-serif !important;font-size:1rem !important;color:#2B1519 !important}
.stApp {background:#FBF6F6 !important}
/* Main dashboard fills the available viewport, including after sidebar collapse. */
[data-testid="stMain"] .block-container {width:100% !important;max-width:none !important;padding:2rem 2rem 3rem}
[data-testid="stAppViewBlockContainer"] {width:100% !important;max-width:none !important}
@media (max-width: 768px) {
  [data-testid="stMain"] .block-container {padding:1rem .85rem 2rem}
}
h1,h2,h3,p,label {font-family:'Be Vietnam Pro',Arial,sans-serif}
.brand {padding:10px 8px 22px;border-bottom:1px solid #EBCBD0;margin-bottom:20px}
.brand-title {font-size:1.4rem;font-weight:800;line-height:1.4;color:#FFFFFF !important}
.brand-sub {font-size:.85rem;color:#F5B5BE !important;letter-spacing:.12em;margin-top:5px;font-weight:700}
[data-testid="stSidebar"],[data-testid="stSidebar"] > div:first-child {background:linear-gradient(180deg,#6E0F20 0%,#3D0813 100%) !important}
/* Do not force sidebar width when Streamlit collapses it. */
[data-testid="stSidebarCollapsedControl"] {display:flex !important}
[data-testid="stSidebar"] .stRadio label p {color:#FBE4E6 !important;font-size:1.15rem !important;font-weight:600 !important}
[data-testid="stSidebar"] .stRadio label {border-radius:9px;padding:8px 12px;margin-bottom:4px}
[data-testid="stSidebar"] .stRadio label:has(input:checked) {background:#B81E34 !important}
[data-testid="stSidebar"] .stRadio label:has(input:checked) p {color:white !important;font-weight:700 !important}
[data-testid="stSidebar"] .stRadio > label {display:none}
[data-testid="stSidebar"] .stSelectbox label p,[data-testid="stSidebar"] .stMultiSelect label p,[data-testid="stSidebar"] .stToggle label p,[data-testid="stSidebar"] .stMarkdown p {color:#FBE4E6 !important;font-size:1.15rem !important;font-weight:700 !important}
[data-testid="stSidebar"] div[data-baseweb="select"] * {font-size:1.05rem !important}
[data-testid="stSidebar"] div[data-baseweb="select"] input {color:#2B1519 !important}
[data-testid="stSidebar"] .stButton button {border:1px solid #E8788A !important;background:#B81E34 !important;color:white !important;border-radius:9px !important;font-weight:700 !important;font-size:1.1rem !important;padding:10px 16px !important}
[data-testid="stSidebar"] hr {border-color:rgba(255,255,255,.2) !important}
/* Filter typography and consistent compact reset actions */
[data-testid="stSidebar"] .stMultiSelect label p,
[data-testid="stSidebar"] .stSelectbox label p,
[data-testid="stSidebar"] .stDateInput label p {font-size:.88rem !important;font-weight:600 !important;color:#FBE4E6 !important}
[data-testid="stSidebar"] [data-testid="stExpander"] {border:1px solid rgba(245,181,190,.35) !important;border-radius:10px !important;background:rgba(255,255,255,.045) !important}
[data-testid="stSidebar"] [data-testid="stExpander"] summary p {color:#FBE4E6 !important;font-size:.92rem !important;font-weight:700 !important}
[data-testid="stSidebar"] [data-testid="stDateInput"] input {font-size:.85rem !important}
[data-testid="stSidebar"] div[data-baseweb="tag"] {background:#F6DDE1 !important;color:#6E0F20 !important}
[data-testid="stSidebar"] div[data-baseweb="tag"] span {color:#6E0F20 !important}
[data-testid="stSidebar"] .stButton button[kind="secondary"] {font-size:.85rem !important;padding:5px 10px !important}
.filter-actions div[data-testid="stButton"] button {white-space:nowrap}

[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {color:#F5B5BE !important}
.hero {background:linear-gradient(120deg,#6E0F20,#B81E34 70%,#D9475A);color:white;border-radius:16px;padding:24px 30px;margin-bottom:18px;box-shadow:0 8px 24px rgba(184,30,52,.22)}
.hero h1 {color:white !important;font-size:2.1rem;font-weight:800;margin:0}
.hero p {color:#FBE4E6 !important;margin:8px 0 0;font-size:1.05rem}
.sec {font-size:1.35rem;font-weight:700;color:#6E0F20;margin:26px 0 12px;padding-left:14px;border-left:5px solid #B81E34}
.kpi {background:white;border-radius:12px;padding:22px 24px;border:1px solid #F0D9DC;border-top:5px solid #B81E34;min-height:145px;height:100%;box-shadow:0 6px 16px rgba(110,15,32,.06)}
.kpi .l {font-size:1.05rem;color:#8A5A62;font-weight:700}
.kpi .v {font-size:2.25rem;font-weight:800;color:#6E0F20;line-height:1.3;margin:6px 0}
.kpi .h {font-size:.82rem;color:#A98088}
.insight {background:white;border-left:5px solid #B81E34;border-radius:10px;padding:14px 18px;margin:10px 0 18px;font-size:1rem;color:#4A2A30}
.ct {font-weight:700;color:#6E0F20;font-size:1.08rem}
.cs {color:#A98088;font-size:.85rem;margin-bottom:5px}
[data-testid="stVerticalBlockBorderWrapper"] {background:white;border-radius:14px !important;border:1px solid #F0D9DC !important;padding:14px !important;box-shadow:0 3px 12px rgba(110,15,32,.04)}
[data-testid="stTextInput"] label p {font-size:1.1rem !important;font-weight:600 !important}
[data-testid="stDataFrame"] * {font-size:1rem !important}
button[data-baseweb="tab"] {font-weight:600}
button[data-baseweb="tab"][aria-selected="true"] {color:#B81E34 !important}
</style>""", unsafe_allow_html=True)


# ------------------------------------------------------------ data layer
@st.cache_resource
def db():
    url = st.secrets.get("DATABASE_URL", "")
    if not url:
        try:
            url = st.secrets["connections"]["postgres"]["url"]
        except (KeyError, TypeError):
            return None
    url = url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 10})


@st.cache_data(ttl=600, show_spinner=False)
def query(view):
    if not re.fullmatch(r"[a-z_0-9]+", view):
        raise ValueError("Tên view không hợp lệ")
    with db().connect() as con:
        return pd.read_sql_query(text(f"SELECT * FROM dw.{view}"), con)


def get(view, optional=False):
    try:
        return query(view)
    except Exception as e:
        if not optional:
            st.error(f"Không tải được dw.{view}")
            with st.expander("Chi tiết lỗi"):
                st.exception(e)
        return pd.DataFrame()


# ------------------------------------------------------------ helpers
def num(df, c):
    return pd.to_numeric(df[c], errors="coerce") if c in df else pd.Series(np.nan, index=df.index)


def priced(df):
    return df[num(df, "price_per_m2_vnd").gt(0)].copy()


def fmt(v):
    return "—" if pd.isna(v) else f"{v:,.0f}"


def ppm(v):
    return "—" if pd.isna(v) else f"{v / 1e6:,.1f} tr/m²"


def nun(df, c):
    return int(df[c].nunique()) if c in df else 0


def flag(s):
    return pd.to_numeric(s, errors="coerce").fillna(0).eq(1)


def apply_filters(df):
    """Bộ lọc chung; nguồn dữ liệu KPI được chọn trước khi gọi hàm."""
    f = st.session_state.get("flt", {})
    if df is None or df.empty:
        return df
    if f.get("src") and "source_name" in df:
        df = df[df.source_name.astype(str).isin(f["src"])]
    if f.get("year", "Theo KPI") not in ("Tất cả", "Theo KPI") and "year" in df:
        df = df[num(df, "year").eq(int(f["year"]))]
    actual_date_col = f.get("date_col") if f.get("date_col") in df else next(
        (c for c in ("full_date", "listing_date", "posted_date", "date_posted") if c in df), None)
    if f.get("dates") and actual_date_col:
        d = pd.to_datetime(df[actual_date_col], errors="coerce").dt.date
        lo, hi = f["dates"]
        df = df[d.between(lo, hi)]
    return df


def period_data():
    """Theo KPI đọc dw.v_kpi_base; các năm đọc dw.v_listing."""
    f = st.session_state.get("flt", {})
    view = "v_kpi_base" if f.get("year", "Theo KPI") == "Theo KPI" else "v_listing"
    return apply_filters(get(view))


def agg(df, cat, price=False, min_n=5):
    x = df.copy()
    x[cat] = x[cat].fillna("Chưa xác định").astype(str)
    if price:
        x = priced(x)
        z = x.groupby(cat).agg(val=("price_per_m2_vnd", "median"), n=("price_per_m2_vnd", "size")).reset_index()
        z = z[z.n >= min_n]
        z["val"] /= 1e6
    else:
        z = x.groupby(cat).size().reset_index(name="val")
        z["n"] = z["val"]
    return z


# ------------------------------------------------------------ UI blocks
def hero(t, sub):
    st.markdown(
        f'<div class="hero"><h1>{t}</h1><p>{sub}</p></div>',
        unsafe_allow_html=True
    )


def sec(t):
    st.markdown(f'<div class="sec">{t}</div>', unsafe_allow_html=True)


def insight(t):
    st.markdown(f'<div class="insight">{t}</div>', unsafe_allow_html=True)


def kpis(items):
    for col, (l, v, h) in zip(st.columns(len(items), gap="small"), items):
        col.markdown(f'<div class="kpi"><div class="l">{l}</div><div class="v">{v}</div>'
                     f'</div>', unsafe_allow_html=True)
    st.write("")


def card(title, fig=None, h=330, sub="", legend=False):
    """Khung biểu đồ chuẩn: tiêu đề + chú thích + biểu đồ."""
    with st.container(border=True):
        st.markdown(f'<div class="ct">{title}</div>', unsafe_allow_html=True)
        if fig is None:
            st.info("Chưa có dữ liệu phù hợp.")
            return
        fig.update_layout(font=dict(family="Be Vietnam Pro, Arial", size=12, color=INK), height=h,
                          paper_bgcolor="white", plot_bgcolor="white", colorway=CAT, showlegend=legend,
                          legend=dict(orientation="h", y=-0.2, title_text=""),
                          margin=dict(l=8, r=8, t=10, b=8), hoverlabel=dict(bgcolor="white"))
        fig.update_xaxes(gridcolor="#F6ECEE", zeroline=False)
        fig.update_yaxes(gridcolor="#F6ECEE", zeroline=False)
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "scrollZoom": any(getattr(trace, "type", "") in ("scattermap", "scattermapbox") for trace in fig.data)})


def sel(df, col, label, key, multi=True):
    if col not in df:
        return df
    vals = sorted(df[col].dropna().astype(str).unique())
    if multi:
        ch = st.multiselect(label, vals, key=key, placeholder="Tất cả")
        return df[df[col].astype(str).isin(ch)] if ch else df
    ch = st.selectbox(label, ["Tất cả"] + vals, key=key)
    return df if ch == "Tất cả" else df[df[col].astype(str) == ch]


# ------------------------------------------------------------ chart factory
def hbar(df, cat, price=False, top=12, min_n=5, order=None):
    if df.empty or cat not in df:
        return None
    z = agg(df, cat, price, min_n)
    if z.empty:
        return None
    z = z.sort_values("val", ascending=False).head(top).sort_values("val")
    if order:
        z[cat] = pd.Categorical(z[cat], [o for o in order if o in set(z[cat])], ordered=True)
        z = z.dropna(subset=[cat]).sort_values(cat, ascending=False)
    fig = px.bar(z, x="val", y=cat, orientation="h", color="val", color_continuous_scale=SCALE,
                 custom_data=["n"], text="val")
    fig.update_traces(texttemplate="%{x:,.1f}" if price else "%{x:,.0f}", textposition="outside", cliponaxis=False,
                      hovertemplate="%{y}<br>%{x:,.1f}<br>Cỡ mẫu: %{customdata[0]:,.0f}<extra></extra>")
    fig.update_layout(coloraxis_showscale=False, xaxis_title="Triệu đồng/m²" if price else "Số tin", yaxis_title=None)
    return fig


def donut(df, cat, top=7, colors=None):
    if df.empty or cat not in df:
        return None
    z = agg(df, cat).sort_values("val", ascending=False)
    if len(z) > top:
        z = pd.concat([z.head(top), pd.DataFrame({cat: ["Khác"], "val": [z.val[top:].sum()], "n": [0]})])
    fig = px.pie(z, names=cat, values="val", hole=0.58, color_discrete_sequence=colors or CAT)
    fig.update_traces(textinfo="percent", marker=dict(line=dict(color="white", width=2)),
                      hovertemplate="%{label}<br>%{value:,.0f} tin<br>Cỡ mẫu n = %{value:,.0f}<br>Tỷ trọng: %{percent}<extra></extra>")
    return fig


def map_fig(df, h=470):
    lat = next((c for c in ["latitude", "lat"] if c in df), None)
    lon = next((c for c in ["longitude", "lng", "lon"] if c in df), None)
    if not (lat and lon):
        return None
    m = df.copy()
    m[lat], m[lon] = num(m, lat), num(m, lon)
    m = m[m[lat].between(8, 24) & m[lon].between(102, 110)]
    if m.empty:
        return None
    m["tr_m2"] = num(m, "median_ppm") / 1e6
    m["n"] = num(m, "n_listings").fillna(1).clip(lower=1)
    name = "project_name" if "project_name" in m else "project_key"
    hd = {c: True for c in ["province_new", "district_label", "sale_status"] if c in m}
    fig = px.scatter_map(m, lat=lat, lon=lon, color="tr_m2", size="n", size_max=22, hover_name=name,
                         hover_data={**hd, lat: False, lon: False, "tr_m2": ":.1f", "n": True},
                         color_continuous_scale=SCALE, zoom=4.5, center={"lat": 16.1, "lon": 106.4},
                         map_style="carto-positron", labels={"tr_m2": "tr/m²", "n": "Số tin"})
    fig.update_layout(coloraxis_colorbar=dict(title="tr/m²", thickness=10, len=0.5))
    return fig


def heat(p, x, y, title_x, title_y, order_x=None, order_y=None):
    if not (x in p and y in p and len(p)):
        return None
    z = p.groupby([y, x], dropna=False).price_per_m2_vnd.agg(["median", "size"]).reset_index()
    z = z[z["size"] >= 3]
    if z.empty:
        return None
    z["median"] /= 1e6
    pv = z.pivot(index=y, columns=x, values="median")
    if order_x:
        pv = pv[[c for c in order_x if c in pv.columns] + [c for c in pv.columns if c not in order_x]]
    if order_y:
        pv = pv.loc[[r for r in order_y if r in pv.index] + [r for r in pv.index if r not in order_y]]
    fig = px.imshow(pv, color_continuous_scale=SCALE, aspect="auto", text_auto=".0f",
                    labels=dict(x=title_x, y=title_y, color="tr/m²"))
    return fig


# ------------------------------------------------------------ pages
PAGES = {}


def page(key, label, icon=""):
    def deco(fn):
        PAGES[key] = (label, fn)
        return fn
    return deco


@page("overview", "Tổng quan")
def overview():
    hero("Tổng quan thị trường chung cư Việt Nam", "Dữ liệu tin đăng từ năm 2022–2026")
    full = get("v_listing")
    base = period_data()
    if base.empty:
        st.info("Không có tin đăng phù hợp với bộ lọc đã chọn.")
        return
    chosen_year = st.session_state.get("flt", {}).get("year", "Theo KPI")
    period = "Theo KPI" if chosen_year == "Theo KPI" else ("Tất cả các năm" if chosen_year == "Tất cả" else f"Năm {chosen_year}")
    sec(f"Chỉ số · {period}")
    p = priced(base)
    # Năm KPI và nguồn tin đang chọn được áp dụng cho cả 5 chỉ số.
    province_counts = (base["province_new"].dropna().astype(str).value_counts()
                       if "province_new" in base else pd.Series(dtype="int64"))
    top_supply = (f"{province_counts.index[0]}" if not province_counts.empty else "—")
    top_supply_note = (f"{fmt(province_counts.iloc[0])} tin đăng" if not province_counts.empty else "Không có dữ liệu")
    price_rank = (p.groupby("province_new")["price_per_m2_vnd"].agg(["median", "size"])
                  if "province_new" in p and not p.empty else pd.DataFrame())
    if not price_rank.empty:
        price_rank = price_rank[price_rank["size"] >= 5].sort_values("median", ascending=False)
    top_price = str(price_rank.index[0]) if not price_rank.empty else "—"
    top_price_note = (ppm(price_rank.iloc[0]["median"]) if not price_rank.empty else "Không đủ mẫu giá")

    # Thẻ KPI gọn để 5 thẻ hiển thị cùng một hàng trên màn hình desktop.
    st.markdown("""<style>
    .overview-kpi {background:white;border:1px solid #F0D9DC;border-top:5px solid #B81E34;
        border-radius:12px;padding:16px 12px;min-height:135px;height:100%;
        box-shadow:0 6px 16px rgba(110,15,32,.06);overflow-wrap:anywhere}
    .overview-kpi .label {font-size:.85rem;color:#8A5A62;font-weight:700;line-height:1.35}
    .overview-kpi .value {font-size:clamp(1rem,1.65vw,1.75rem);font-weight:800;color:#6E0F20;
        line-height:1.25;margin:10px 0 6px}
    .overview-kpi .note {font-size:.76rem;color:#9A6971;line-height:1.4}
    </style>""", unsafe_allow_html=True)
    from html import escape as _escape
    overview_items = [
        ("Tin đăng", fmt(len(base)), "Trong phạm vi lọc"),
        ("Dự án", fmt(nun(base, "project_key")), "Dự án phân biệt"),
        ("Giá/m² trung vị", ppm(p.price_per_m2_vnd.median()) if len(p) else "—", "Giá chào bán"),
        ("Top 1 số tin", top_supply, top_supply_note),
        ("Top 1 giá/m² trung vị", top_price, top_price_note),
    ]
    for col, (label, value, note) in zip(st.columns(5, gap="small"), overview_items):
        with col:
            st.markdown(
                f'<div class="overview-kpi"><div class="label">{_escape(label)}</div>'
                f'<div class="value">{_escape(str(value))}</div>'
                f'<div class="note">{_escape(str(note))}</div></div>',
                unsafe_allow_html=True)


    sec("Bản đồ")
    proj = get("v_project_summary", True)
    if not proj.empty and "project_key" in proj and "project_key" in base:
        proj = proj[proj.project_key.isin(base.project_key.dropna())]
    card("Bản đồ dự án theo giá/m²", map_fig(proj) if len(proj) else None, 540)

    sec("Xu hướng & Cơ cấu")
    # Xu hướng năm luôn đọc toàn bộ v_listing, không giới hạn theo năm KPI.
    trend = full
    f = st.session_state.get("flt", {})
    if f.get("src") and "source_name" in trend:
        trend = trend[trend.source_name.astype(str).isin(f["src"])]
    if len(trend) and "year" in trend:
        trend = trend.copy()
        trend["year"] = num(trend, "year")
        trend = trend.dropna(subset=["year"])
        trend["year"] = trend["year"].astype(int)
        a, b = st.columns(2, gap="medium")
        with a:
            z = trend.groupby("year").size().reset_index(name="n")
            fig = px.bar(z, x="year", y="n", text="n", color="n", color_continuous_scale=SCALE) if len(z) else None
            if fig is not None:
                fig.update_traces(texttemplate="%{y:,.0f}", textposition="outside")
                fig.update_layout(coloraxis_showscale=False, xaxis=dict(type="category", title=None), yaxis_title="Số tin")
            card("Tin đăng theo năm", fig, 360)
        with b:
            z = priced(trend).groupby("year").price_per_m2_vnd.median().reset_index()
            if len(z):
                z["tr"] = z.price_per_m2_vnd / 1e6
                fig = px.line(z, x="year", y="tr", markers=True)
                fig.update_traces(line=dict(color=RED, width=3), marker=dict(size=10, color=DEEP), fill="tozeroy", fillcolor="rgba(184,30,52,.10)")
                fig.update_layout(xaxis=dict(type="category", title=None), yaxis_title="Triệu đồng/m²")
            else:
                fig = None
            card("Trung vị giá/m² theo năm", fig, 360)
    else:
        st.info("Chưa có dữ liệu xu hướng theo năm.")

    a, b = st.columns(2, gap="medium")
    with a:
        card("Cơ cấu tin theo vùng", donut(base, "region"), 380, "Tỷ trọng tin đăng theo vùng", legend=True)
    with b:
        card("Giá/m² trung vị vùng", hbar(base, "region", price=True, top=9), 380,
             "Triệu đồng/m² · tối thiểu 5 tin có giá")
    # Tổng quan tỉnh/thành: kết hợp quy mô nguồn cung và giá trên cùng biểu đồ.
    # Chỉ so sánh giá tại các tỉnh thuộc top 10 số tin; giá cần >=5 tin hợp lệ.
    a, b = st.columns(2, gap="medium")
    with a:
        if "province_new" in base:
            top_provinces = (base["province_new"].dropna().astype(str)
                             .value_counts().head(10))
            province_chart = None
            if not top_provinces.empty:
                province_names = top_provinces.index.tolist()
                province_prices = priced(base)
                price_by_province = (province_prices.groupby("province_new")["price_per_m2_vnd"]
                                     .agg(["median", "size"])) if "province_new" in province_prices else pd.DataFrame()
                province_chart = go.Figure()
                province_chart.add_trace(go.Bar(
                    x=province_names, y=top_provinces.values, name="Số tin đăng",
                    marker_color=RED, opacity=0.88,
                    hovertemplate="%{x}<br>Số tin: %{y:,.0f}<extra></extra>"))
                valid_prices = price_by_province.reindex(province_names) if not price_by_province.empty else pd.DataFrame()
                if not valid_prices.empty:
                    valid_prices = valid_prices[valid_prices["size"] >= 5]
                    if not valid_prices.empty:
                        province_chart.add_trace(go.Scatter(
                            x=valid_prices.index.tolist(), y=(valid_prices["median"] / 1e6).tolist(),
                            mode="lines+markers", name="Giá/m² trung vị",
                            yaxis="y2", line=dict(color=DEEP, width=3),
                            marker=dict(size=9, color="#FFFFFF", line=dict(color=DEEP, width=2.5)),
                            customdata=valid_prices["size"].to_numpy(),
                            hovertemplate="%{x}<br>Giá: %{y:,.1f} tr/m²<br>Tin có giá: %{customdata:,.0f}<extra></extra>"))
                province_chart.update_layout(
                    yaxis=dict(title="Số tin đăng", rangemode="tozero"),
                    yaxis2=dict(title="Triệu đồng/m²", overlaying="y", side="right", rangemode="tozero", showgrid=False),
                    xaxis=dict(title=None, tickangle=-35, categoryorder="array", categoryarray=province_names),
                    legend=dict(orientation="h", y=1.13, x=0),
                    margin=dict(l=8, r=8, t=35, b=70),
                    bargap=0.28)
            card("Top 10 tỉnh/thành · Số tin & giá/m²", province_chart, 430, legend=True)
        else:
            card("Top 10 tỉnh/thành · Số tin & giá/m²", None, 430)
    with b:
        card("Cơ cấu tin đăng theo phân khúc", donut(base, "segment_name", colors=ACCENT_COLORS) if "segment_name" in base else None,
             430, legend=True)


@page("geo", "Địa lý")
def geography():
    hero("Phân tích địa lý", "So sánh nguồn cung và giá căn hộ theo từng địa bàn")
    base = period_data()
    if base.empty:
        st.info("Không có dữ liệu phù hợp với bộ lọc chung.")
        return

    # Mọi selectbox dùng cùng một giá trị mặc định, kể cả sau khi bấm xóa.
    all_value = "Tất cả"
    geo_keys = ("g_region", "g_province_new", "g_district_label", "g_former_area")
    for key in geo_keys:
        st.session_state.setdefault(key, all_value)

    def clear_geo():
        for key in geo_keys:
            st.session_state[key] = all_value
        st.session_state["g_compare"] = None

    def region_changed():
        # Khi chọn vùng mới, bỏ lựa chọn tỉnh/quận không còn tương ứng.
        for key in ("g_province_new", "g_district_label", "g_former_area"):
            st.session_state[key] = all_value
        st.session_state["g_compare"] = None

    def province_changed():
        # Chọn tỉnh trực tiếp sẽ đồng bộ lại Vùng theo dữ liệu thực tế.
        province = st.session_state.get("g_province_new", all_value)
        if province != all_value and {"region", "province_new"} <= set(base.columns):
            regions = base.loc[base["province_new"].astype(str).eq(province), "region"].dropna().astype(str).unique()
            if len(regions) == 1:
                st.session_state["g_region"] = regions[0]
        for key in ("g_district_label", "g_former_area"):
            st.session_state[key] = all_value
        st.session_state["g_compare"] = None

    def former_changed():
        # Đổi khu vực cũ phải bỏ quận/huyện đã chọn để tránh lọc chéo.
        st.session_state["g_district_label"] = all_value
        st.session_state["g_compare"] = None

    def district_changed():
        st.session_state["g_compare"] = None

    def options(frame, column):
        if column not in frame:
            return []
        return sorted(frame[column].dropna().astype(str).unique().tolist())

    def select_geo(label, key, vals, on_change=None, disabled=False):
        opts = [all_value] + vals
        if st.session_state.get(key) not in opts:
            st.session_state[key] = all_value
        return st.selectbox(label, opts, key=key, on_change=on_change, disabled=disabled)

    with st.expander("Bộ lọc địa lý", expanded=True):
        left, right = st.columns([5, 1])
        with right:
            st.button("Xóa bộ lọc", key="g_clear", on_click=clear_geo, use_container_width=True)

        # Vùng và tỉnh được đồng bộ hai chiều; lựa chọn tỉnh không bị trộn với vùng khác.
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            region = select_geo("Vùng", "g_region", options(base, "region"), region_changed)
        province_frame = base
        if region != all_value and "region" in base:
            province_frame = base[base["region"].astype(str).eq(region)]
        with c2:
            province = select_geo("Tỉnh/thành", "g_province_new", options(province_frame, "province_new"), province_changed)

        df = province_frame
        if province != all_value and "province_new" in df:
            df = df[df["province_new"].astype(str).eq(province)]

        # Riêng TP.HCM: hiển thị khu vực cũ GIỮA tỉnh/thành và quận/huyện.
        # Không suy đoán danh sách quận: lấy trực tiếp từ các bản ghi trong view đang chọn.
        is_hcm = province != all_value and any(
            token in province.casefold() for token in ("hồ chí minh", "ho chi minh", "hcm")
        )
        if is_hcm and "former_area" in df.columns:
            former_values = options(df, "former_area")
            if former_values:
                former = select_geo("Khu vực cũ", "g_former_area", former_values, former_changed)
                if former != all_value:
                    df = df[df["former_area"].astype(str).eq(former)]
            else:
                st.session_state["g_former_area"] = all_value
        else:
            st.session_state["g_former_area"] = all_value

        # Quận/huyện luôn được giới hạn theo tỉnh đã chọn và khu vực cũ (nếu có).
        district_values = options(df, "district_label") if province != all_value else []
        district = select_geo("Quận/huyện", "g_district_label", district_values,
                              district_changed, disabled=province == all_value)
        if district != all_value and "district_label" in df:
            df = df[df["district_label"].astype(str).eq(district)]

    if df.empty:
        st.warning("Không có tin đăng trong phạm vi địa lý đã chọn.")
        return

    p = priced(df)
    kpis([("Tin đăng", fmt(len(df)), ""),
          ("Dự án", fmt(nun(df, "project_key")), ""),
          ("Giá/m² trung vị", ppm(p.price_per_m2_vnd.median()) if len(p) else "—", ""),
          ("Tin có giá", fmt(len(p)), "")])

    labels = {"region": "Vùng", "province_new": "Tỉnh/thành",
              "former_area": "Khu vực cũ", "district_label": "Quận/huyện"}
    if district != all_value:
        levels = []
    elif province != all_value:
        levels = ["district_label", "former_area"]
    elif region != all_value:
        levels = ["province_new"]
    else:
        levels = ["region", "province_new"]
    levels = [col for col in levels if col in df and nun(df, col) > 1]

    def geo_lollipop(frame, column, top=12):
        """So sánh giá trung vị bằng dot plot; chỉ dùng địa bàn có >=5 tin có giá."""
        if frame.empty or column not in frame:
            return None
        z = agg(frame, column, price=True, min_n=5)
        if z.empty:
            return None
        z = z.nlargest(top, "val").sort_values("val")
        fig = go.Figure()
        for _, r in z.iterrows():
            fig.add_trace(go.Scatter(x=[0, r["val"]], y=[str(r[column])] * 2,
                                     mode="lines", line=dict(color="#E9B2BC", width=3),
                                     hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=z["val"], y=z[column].astype(str), mode="markers+text",
                                 text=[f"{v:,.1f}" for v in z["val"]], textposition="middle right",
                                 marker=dict(size=13, color=RED, line=dict(color="white", width=1)),
                                 customdata=z[["n"]].to_numpy(),
                                 hovertemplate="%{y}<br>Giá trung vị: %{x:,.1f} tr/m²<br>Tin có giá: %{customdata[0]:,.0f}<extra></extra>",
                                 showlegend=False))
        fig.update_layout(xaxis_title="Triệu đồng/m²", yaxis_title=None,
                          margin=dict(l=8, r=55, t=10, b=20))
        fig.update_xaxes(rangemode="tozero")
        return fig

    def geo_share(frame, column, top=7):
        """Cơ cấu nguồn cung theo địa bàn; gộp các địa bàn còn lại thành Khác."""
        if frame.empty or column not in frame:
            return None
        z = frame[column].fillna("Chưa xác định").astype(str).value_counts()
        if z.empty:
            return None
        leading = z.head(top)
        labels_ = leading.index.tolist()
        values_ = leading.values.tolist()
        if len(z) > top:
            labels_.append("Khác")
            values_.append(int(z.iloc[top:].sum()))
        fig = px.pie(names=labels_, values=values_, hole=.60,
                     color_discrete_sequence=[DEEP, RED, "#D34B61", "#194C3A", ROSE, "#39734F", "#ECA6B1", "#9C4A55"])
        fig.update_traces(textinfo="percent", textposition="inside",
                          hovertemplate="%{label}<br>%{value:,.0f} tin (%{percent})<extra></extra>",
                          marker=dict(line=dict(color="white", width=2)))
        fig.update_layout(showlegend=True, legend=dict(orientation="v", x=1.02, y=.95))
        return fig

    def geo_category_bar(frame, column, price=False, top=10):
        if frame.empty or column not in frame:
            return None
        z = agg(frame, column, price=price, min_n=5)
        if z.empty:
            return None
        z = z.nlargest(top, "val").sort_values("val")
        fig = px.bar(z, x="val", y=column, orientation="h", text="val",
                     color="val", color_continuous_scale=SCALE, custom_data=["n"])
        fig.update_traces(texttemplate="%{x:,.1f}" if price else "%{x:,.0f}",
                          textposition="outside", cliponaxis=False,
                          hovertemplate="%{y}<br>%{x:,.1f}<br>Cỡ mẫu: %{customdata[0]:,.0f}<extra></extra>")
        fig.update_layout(coloraxis_showscale=False, yaxis_title=None,
                          xaxis_title="Triệu đồng/m²" if price else "Số tin",
                          margin=dict(l=8, r=55, t=10, b=20))
        return fig

    if levels:
        sec("So sánh địa bàn")
        if len(levels) > 1:
            if st.session_state.get("g_compare") not in levels:
                st.session_state["g_compare"] = "province_new" if "province_new" in levels else levels[0]
            lv = st.segmented_control("Cấp so sánh", levels, key="g_compare", format_func=labels.get) or levels[0]
        else:
            lv = levels[0]
        a, b = st.columns(2, gap="medium")
        with a:
            card(f"Nguồn cung theo {labels[lv].lower()}", geo_category_bar(df, lv), 430)
        with b:
            card(f"Mặt bằng giá/m² theo {labels[lv].lower()}", geo_lollipop(df, lv), 430)

        # Hai thước đo trên cùng biểu đồ giúp nhận ra địa bàn vừa nhiều tin vừa có giá cao.
        if not p.empty and "project_key" in df:
            supply = df.groupby(lv, dropna=False).size().rename("tin")
            prices = p.groupby(lv, dropna=False).agg(gia=("price_per_m2_vnd", "median"), n=("price_per_m2_vnd", "size"))
            joined = prices.join(supply, how="inner").reset_index()
            joined = joined[joined["n"] >= 5].copy()
            if len(joined) >= 3:
                joined["gia_tr"] = joined["gia"] / 1e6
                fig = px.scatter(joined, x="tin", y="gia_tr", hover_name=lv, text=lv,
                                 color="gia_tr", color_continuous_scale=SCALE,
                                 labels={"tin": "Số tin đăng", "gia_tr": "Giá trung vị (triệu đồng/m²)"})
                fig.update_traces(marker=dict(size=13, line=dict(width=1, color="white")),
                                  textposition="top center")
                fig.update_layout(coloraxis_showscale=False)
                card("Tương quan nguồn cung và mặt bằng giá giữa các địa bàn", fig, 390)

        # Cơ cấu nguồn cung giúp nhìn tỷ trọng, bổ sung góc nhìn khác biểu đồ xếp hạng.
        if nun(df, lv) >= 3:
            card(f"Tỷ trọng tin đăng theo {labels[lv].lower()}", geo_share(df, lv), 350, legend=True)

        sec("Bảng đối chiếu địa bàn")
        counts = df.groupby(lv, dropna=False).agg(
            tin=("project_key", "size"), du_an=("project_key", "nunique")).reset_index()
        if not p.empty:
            prices = p.groupby(lv, dropna=False).agg(
                gia=("price_per_m2_vnd", "median"), tin_co_gia=("price_per_m2_vnd", "size")).reset_index()
            counts = counts.merge(prices, on=lv, how="left")
        else:
            counts["gia"] = np.nan
            counts["tin_co_gia"] = 0
        counts["Giá trung vị (tr/m²)"] = (counts["gia"] / 1e6).round(1)
        out = counts[[lv, "tin", "du_an", "tin_co_gia", "Giá trung vị (tr/m²)"]].rename(columns={
            lv: labels[lv], "tin": "Số tin", "du_an": "Số dự án", "tin_co_gia": "Tin có giá"})
        out = out.sort_values("Số tin", ascending=False)
        st.dataframe(out, hide_index=True, use_container_width=True, height=420)
        st.download_button("Tải CSV", out.to_csv(index=False).encode("utf-8-sig"),
                           "dia_ly.csv", key="g_export")
    else:
        sec("Cơ cấu tin đăng tại địa bàn đã chọn")
        candidates = [("segment_name", "Phân khúc"), ("bedrooms_group", "Số phòng ngủ"),
                      ("area_group", "Nhóm diện tích")]
        valid = [(col, label) for col, label in candidates if col in df and nun(df, col) > 1]
        if valid:
            a, b = st.columns(2, gap="medium")
            with a:
                col, label = valid[0]
                card(f"Cơ cấu tin đăng theo {label.lower()}", geo_share(df, col), 380, legend=True)
            with b:
                col, label = valid[1] if len(valid) > 1 else valid[0]
                card(f"Số tin theo {label.lower()}", geo_category_bar(df, col, top=8), 380)
            if "area_group" in df and nun(df, "area_group") > 1:
                card("Giá/m² trung vị theo nhóm diện tích", geo_lollipop(df, "area_group", top=8), 350)
        else:
            st.info("Phạm vi hiện tại không có đủ nhóm dữ liệu để phân tích cơ cấu.")
        if "project_key" in df and nun(df, "project_key") > 1:
            sec("Dự án trong địa bàn")
            name_col = "project_name" if "project_name" in df else "project_key"
            g = df.groupby("project_key", dropna=False).size().reset_index(name="Số tin")
            if name_col != "project_key":
                names_df = df[["project_key", name_col]].drop_duplicates("project_key")
                g = g.merge(names_df, on="project_key", how="left")
            g = g.sort_values("Số tin", ascending=False).head(20)
            st.dataframe(g[[name_col, "Số tin"]].rename(columns={name_col: "Dự án"}),
                         hide_index=True, use_container_width=True)


@page("segment", "Phân khúc")
def segments():
    hero("Phân khúc thị trường", "Cơ cấu tin đăng, mặt bằng giá và đặc điểm căn hộ theo phân khúc")
    base = period_data()
    if base.empty:
        st.info("Không có tin đăng trong kỳ được chọn.")
        return

    from html import escape

    # Insight được trình bày nhất quán: nhãn, thông điệp chính và diễn giải ngắn.
    def segment_insight(heading, message, detail=""):
        st.markdown(
            '<div style="background:linear-gradient(110deg,#FFF8F9,#FFFFFF);'
            'border:1px solid #EBCBD0;border-left:4px solid #B81E34;'
            'border-radius:12px;padding:15px 18px;margin:9px 0 18px;'
            'box-shadow:0 3px 10px rgba(110,15,32,.04)">'
            f'<div style="color:#B81E34;font-size:.76rem;font-weight:800;'
            f'letter-spacing:.06em;text-transform:uppercase">{escape(heading)}</div>'
            f'<div style="color:#421D25;font-size:1.04rem;font-weight:700;'
            f'line-height:1.55;margin-top:5px">{escape(message)}</div>'
            + (f'<div style="color:#80616A;font-size:.88rem;line-height:1.5;'
               f'margin-top:5px">{escape(detail)}</div>' if detail else '')
            + '</div>', unsafe_allow_html=True)

    # Màu phân loại đủ khác biệt để phân biệt từng nhóm, không thay đổi tông giao diện.
    CONFIG_COLORS = ACCENT_COLORS

    def options(frame, field):
        return sorted(frame[field].dropna().astype(str).unique().tolist()) if field in frame else []

    # Bộ lọc phụ thuộc nhau, chỉ tác động trong trang này.
    def clear_segment_filters():
        # Reset the actual widget state, not merely the filtered dataframe.
        st.session_state["seg_province"] = "Tất cả"
        st.session_state["seg_district"] = "Tất cả"
        st.session_state["seg_segment"] = []
        st.session_state["seg_legal"] = []

    with st.expander("Bộ lọc phân khúc", expanded=True):
        _space, _action = st.columns([5, 1])
        with _action:
            st.button("Xóa bộ lọc", key="seg_clear", on_click=clear_segment_filters, use_container_width=True)
        a, b, c = st.columns(3)
        with a:
            province = st.selectbox("Tỉnh/thành", ["Tất cả"] + options(base, "province_new"), key="seg_province")
        df = base.loc[base["province_new"].astype(str).eq(province)].copy() if province != "Tất cả" and "province_new" in base else base.copy()
        with b:
            districts = options(df, "district_label") if province != "Tất cả" else []
            if st.session_state.get("seg_district", "Tất cả") not in ["Tất cả"] + districts:
                st.session_state["seg_district"] = "Tất cả"
            district = st.selectbox("Quận/huyện", ["Tất cả"] + districts, key="seg_district", disabled=province == "Tất cả")
        if district != "Tất cả" and "district_label" in df:
            df = df.loc[df["district_label"].astype(str).eq(district)].copy()
        with c:
            seg_options = options(df, "segment_name")
            if any(v not in seg_options for v in st.session_state.get("seg_segment", [])):
                st.session_state["seg_segment"] = []
            chosen_segments = st.multiselect("Phân khúc", seg_options, key="seg_segment", placeholder="Tất cả")
        if chosen_segments and "segment_name" in df:
            df = df.loc[df["segment_name"].astype(str).isin(chosen_segments)].copy()
        a, b = st.columns([1, 2])
        with a:
            legal_options = options(df, "legal_group")
            if any(v not in legal_options for v in st.session_state.get("seg_legal", [])):
                st.session_state["seg_legal"] = []
            legal = st.multiselect("Pháp lý", legal_options, key="seg_legal", placeholder="Tất cả")
        if legal and "legal_group" in df:
            df = df.loc[df["legal_group"].astype(str).isin(legal)].copy()


    if df.empty:
        st.warning("Không có tin đăng phù hợp với bộ lọc.")
        return
    p = priced(df)
    # KPI riêng cho trang Phân khúc: đo mức tập trung, chênh lệch giá và cấu hình nổi bật.
    seg_counts = df["segment_name"].dropna().astype(str).value_counts() if "segment_name" in df else pd.Series(dtype=int)
    leading_segment = str(seg_counts.index[0]) if len(seg_counts) else "—"
    leading_share = f"{seg_counts.iloc[0] / len(df):.0%}" if len(seg_counts) else "—"
    seg_prices = (p.groupby("segment_name").price_per_m2_vnd.agg(["median", "size"])
                  if "segment_name" in p else pd.DataFrame(columns=["median", "size"]))
    seg_prices = seg_prices[seg_prices["size"] >= 5]
    highest_price_segment = (str(seg_prices["median"].idxmax()) if len(seg_prices) else "—")
    def short_segment(value):
        return re.sub(r"^\s*\d+\s*[.\-]\s*", "", value).split(" (")[0].strip() if value != "—" else value
    bed_counts = df["bedrooms_group"].dropna().astype(str).value_counts() if "bedrooms_group" in df else pd.Series(dtype=int)
    main_bed = str(bed_counts.index[0]) if len(bed_counts) else "—"
    kpis([("Tin đăng", fmt(len(df)), ""),
          ("Phân khúc dẫn đầu", short_segment(leading_segment), ""),
          ("Phân khúc giá cao nhất", short_segment(highest_price_segment), ""),
          ("Cấu hình phòng ngủ phổ biến", main_bed, "")])

    sec("Cơ cấu nguồn cung & Mặt bằng giá")
    a, b = st.columns([.95, 1.05], gap="medium")
    with a:
        card("Tin đăng theo phân khúc", donut(df, "segment_name", colors=ACCENT_COLORS), 370, legend=True)
        if "segment_name" in df:
            counts = df["segment_name"].fillna("Chưa xác định").astype(str).value_counts()
            if len(counts):
                segment_insight("Phân khúc nổi bật",
                                f"{counts.index[0]} dẫn đầu với {counts.iloc[0] / len(df):.1%} số tin đăng.",
                                f"Tương ứng {fmt(counts.iloc[0])} trên tổng {fmt(len(df))} tin trong phạm vi lọc.")
    with b:
        fig = None
        if "segment_name" in p and len(p):
            z = p.groupby("segment_name", dropna=False).price_per_m2_vnd.agg(["median", "size"]).reset_index()
            z = z[z["size"] >= 5].sort_values("median")
            if len(z):
                z["tr"] = z["median"] / 1e6
                fig = px.bar(z, x="tr", y="segment_name", orientation="h", text="tr",
                             color="tr", color_continuous_scale=SCALE,
                             custom_data=["size"],
                             labels={"tr": "Triệu đồng/m²", "segment_name": ""})
                fig.update_traces(texttemplate="%{x:,.1f}", textposition="outside",
                                  hovertemplate="%{y}<br>Giá trung vị: %{x:,.1f} tr/m²<br>Tin có giá: %{customdata[0]:,.0f}<extra></extra>",
                                  cliponaxis=False)
                fig.update_layout(coloraxis_showscale=False, margin=dict(r=45))
        card("Giá/m² trung vị theo phân khúc", fig, 370,
             "Mỗi phân khúc cần ít nhất 5 tin có giá; không dùng giá trung bình.")
        if "segment_name" in p:
            z = p.groupby("segment_name").price_per_m2_vnd.agg(["median", "size"])
            z = z[z["size"] >= 5].sort_values("median", ascending=False)
            if len(z):
                segment_insight("Mặt bằng giá nổi bật",
                                f"{z.index[0]} có giá/m² trung vị cao nhất: {ppm(z.iloc[0]['median'])}.",
                                f"Tính từ {fmt(z.iloc[0]['size'])} tin có giá hợp lệ trong phân khúc này.")

    def config_card(title, fig):
        with st.container(border=True):
            st.markdown(f'<div class="ct">{title}</div>', unsafe_allow_html=True)
            if fig is None:
                st.info("Chưa có dữ liệu phù hợp.")
                return
            fig.update_layout(font=dict(family="Be Vietnam Pro, Arial", size=12, color=INK),
                              height=465, paper_bgcolor="white", plot_bgcolor="white",
                              hoverlabel=dict(bgcolor="white"), showlegend=True)
            fig.update_xaxes(gridcolor="#F6ECEE", zeroline=False)
            fig.update_yaxes(gridcolor="#F6ECEE", zeroline=False)
            st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

    sec("Cấu hình căn hộ theo phân khúc")
    a, b = st.columns(2, gap="medium")
    with a:
        fig = None
        if {"segment_name", "bedrooms_group"} <= set(df.columns):
            z = df.dropna(subset=["segment_name", "bedrooms_group"]).groupby(
                ["segment_name", "bedrooms_group"]).size().reset_index(name="n")
            if len(z):
                z["pct"] = z["n"] / z.groupby("segment_name")["n"].transform("sum") * 100
                fig = px.bar(z, x="segment_name", y="pct", color="bedrooms_group",
                             color_discrete_sequence=CONFIG_COLORS,
                             category_orders={"bedrooms_group": BED_ORDER},
                             custom_data=["n"],
                             labels={"segment_name": "", "pct": "Tỷ trọng (%)", "bedrooms_group": "Phòng ngủ"})
                fig.update_traces(hovertemplate="%{x}<br>%{fullData.name}: %{y:.1f}%<br>%{customdata[0]:,.0f} tin<extra></extra>")
                fig.update_layout(
                    barmode="stack", yaxis=dict(range=[0, 100], ticksuffix="%"),
                    legend_title_text="", height=430,
                    legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.48, yanchor="top", font=dict(size=11)),
                    margin=dict(l=8, r=8, t=10, b=125),
                    xaxis=dict(tickangle=-18, automargin=True))
        config_card("Tỷ trọng số phòng ngủ theo phân khúc", fig)
    with b:
        fig = None
        if {"segment_name", "area_group"} <= set(df.columns):
            z = df.dropna(subset=["segment_name", "area_group"]).groupby(
                ["segment_name", "area_group"]).size().reset_index(name="n")
            if len(z):
                z["pct"] = z["n"] / z.groupby("segment_name")["n"].transform("sum") * 100
                fig = px.bar(z, x="segment_name", y="pct", color="area_group",
                             color_discrete_sequence=CONFIG_COLORS,
                             category_orders={"area_group": AREA_ORDER}, custom_data=["n"],
                             labels={"segment_name": "", "pct": "Tỷ trọng (%)", "area_group": "Diện tích"})
                fig.update_traces(hovertemplate="%{x}<br>%{fullData.name}: %{y:.1f}%<br>%{customdata[0]:,.0f} tin<extra></extra>")
                fig.update_layout(
                    barmode="stack", yaxis=dict(range=[0, 100], ticksuffix="%"),
                    legend_title_text="", height=430,
                    legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.48, yanchor="top", font=dict(size=11)),
                    margin=dict(l=8, r=8, t=10, b=125),
                    xaxis=dict(tickangle=-18, automargin=True))
        config_card("Tỷ trọng nhóm diện tích theo phân khúc", fig)
    if {"segment_name", "bedrooms_group"} <= set(df.columns):
        pairs = df.groupby(["segment_name", "bedrooms_group"]).size().sort_values(ascending=False)
        if len(pairs):
            segment_name, bedroom = pairs.index[0]
            segment_insight("Cấu hình nổi bật",
                            f"{segment_name} – {bedroom} là tổ hợp có nhiều tin đăng nhất.",
                            f"Ghi nhận {fmt(pairs.iloc[0])} tin, chiếm {pairs.iloc[0] / len(df):.1%} tổng số tin trong phạm vi lọc.")

    sec("Phân bố địa lý & Mặt bằng giá")
    a, b = st.columns(2, gap="medium")
    with a:
        # Số tin theo tỉnh trong từng phân khúc; chỉ dùng tối đa 8 địa bàn để nhãn dễ đọc.
        fig = None
        if {"province_new", "segment_name"} <= set(df.columns):
            top = df["province_new"].value_counts().head(8).index
            z = df[df["province_new"].isin(top)].groupby(["province_new", "segment_name"]).size().reset_index(name="n")
            if len(z):
                fig = px.bar(z, x="n", y="province_new", color="segment_name",
                             orientation="h", color_discrete_sequence=CONFIG_COLORS,
                             labels={"n": "Số tin", "province_new": "", "segment_name": "Phân khúc"})
                fig.update_layout(barmode="stack", yaxis=dict(categoryorder="total ascending"))
        card("Phân khúc tập trung ở tỉnh/thành nào?", fig, 400, legend=True)
    with b:
        fig = None
        if {"province_new", "segment_name"} <= set(p.columns) and len(p):
            top = df["province_new"].value_counts().head(8).index
            q = p[p["province_new"].isin(top)]
            z = q.groupby(["province_new", "segment_name"]).price_per_m2_vnd.agg(["median", "size"]).reset_index()
            z = z[z["size"] >= 5]
            if len(z):
                z["tr"] = z["median"] / 1e6
                pv = z.pivot(index="province_new", columns="segment_name", values="tr")
                fig = px.imshow(pv, aspect="auto", color_continuous_scale=SCALE,
                                text_auto=".0f", labels={"x": "Phân khúc", "y": "", "color": "tr/m²"})
        card("Giá/m² trung vị theo tỉnh và phân khúc", fig, 400,
             "Ô trống = dưới 5 tin có giá; chỉ so sánh địa bàn có đủ mẫu.")
    if {"province_new", "segment_name"} <= set(df.columns):
        z_geo = df.dropna(subset=["province_new", "segment_name"]).groupby(
            ["province_new", "segment_name"]).size().sort_values(ascending=False)
        if len(z_geo):
            loc, seg_name = z_geo.index[0]
            segment_insight("Điểm tập trung tin đăng",
                            f"{loc} – {seg_name} là cặp địa bàn và phân khúc có nhiều tin nhất.",
                            f"Ghi nhận {fmt(z_geo.iloc[0])} tin trong phạm vi dữ liệu đang xem.")

    sec("Dự án nổi bật")
    if {"project_key", "project_name"} <= set(df.columns):
        # Gộp theo dự án để không nhân bản một dự án khi thuộc nhiều phân khúc.
        counts = df.groupby("project_key", dropna=True).agg(
            project_name=("project_name", "first"),
            province_new=("province_new", "first") if "province_new" in df else ("project_name", "first"),
            n=("project_key", "size")).reset_index()
        if "segment_name" in df:
            main_seg = df.dropna(subset=["segment_name"]).groupby(["project_key", "segment_name"]).size().reset_index(name="n_seg")
            if len(main_seg):
                main_seg = main_seg.sort_values(["n_seg", "segment_name"], ascending=[False, True]).drop_duplicates("project_key")
                counts = counts.merge(main_seg[["project_key", "segment_name"]], on="project_key", how="left")
        if len(p):
            med = p.groupby("project_key").price_per_m2_vnd.agg(["median", "size"]).reset_index()
            med["Giá trung vị (tr/m²)"] = (med["median"] / 1e6).round(1).where(med["size"] >= 5)
            counts = counts.merge(med[["project_key", "Giá trung vị (tr/m²)"]], on="project_key", how="left")
        counts = counts.sort_values("n", ascending=False).head(15)
        display = {"project_name": "Dự án", "province_new": "Tỉnh/thành",
                   "segment_name": "Phân khúc phổ biến", "n": "Số tin",
                   "Giá trung vị (tr/m²)": "Giá trung vị (tr/m²)"}
        cols = [x for x in display if x in counts]
        st.dataframe(counts[cols].rename(columns=display), hide_index=True, use_container_width=True, height=420)
        if len(counts):
            first = counts.iloc[0]
            segment_insight("Dự án được đăng nhiều",
                            f"{first['project_name']} dẫn đầu bảng với {fmt(first['n'])} tin đăng.",
                            "Bảng xếp theo số tin trong phạm vi lọc hiện tại.")
    else:
        st.info("Chưa có đủ tên và mã dự án trong dữ liệu đang lọc.")

@page("project", "Dự án")
def projects():
    hero("Danh mục & hiệu suất dự án",
         "Dự án nổi bật, phân bố danh mục, mặt bằng giá và những trường hợp cần theo dõi")
    raw = get("v_project_summary")
    if raw.empty:
        return

    from html import escape

    def project_insight(label, message, detail=""):
        st.markdown(
            '<div style="background:linear-gradient(110deg,#FFF8F9,#FFFFFF);'
            'border:1px solid #EBCBD0;border-left:4px solid #B81E34;'
            'border-radius:12px;padding:15px 18px;margin:9px 0 18px;'
            'box-shadow:0 3px 10px rgba(110,15,32,.04)">'
            f'<div style="color:#B81E34;font-size:.76rem;font-weight:800;'
            f'letter-spacing:.06em;text-transform:uppercase">{escape(str(label))}</div>'
            f'<div style="color:#421D25;font-size:1.04rem;font-weight:700;'
            f'line-height:1.55;margin-top:5px">{escape(str(message))}</div>'
            + (f'<div style="color:#80616A;font-size:.88rem;line-height:1.5;'
               f'margin-top:5px">{escape(str(detail))}</div>' if detail else '')
            + '</div>', unsafe_allow_html=True)

    def opts(frame, field):
        return sorted(frame[field].dropna().astype(str).unique().tolist()) if field in frame else []

    def clear_project_filters():
        for key in ("pr_province", "pr_investor", "pr_status", "pr_size"):
            st.session_state[key] = "Tất cả"
        st.session_state["pr_search"] = ""
        st.session_state["pr_reliable_only"] = False

    with st.expander("Bộ lọc dự án", expanded=False):
        _space, _action = st.columns([5, 1])
        with _action:
            st.button("Xóa bộ lọc", key="pr_clear", on_click=clear_project_filters, use_container_width=True)
        reliable_only = st.toggle("Chỉ dự án có tin ghép đáng tin cậy", value=False, key="pr_reliable_only",
                                  help="Giới hạn danh mục dự án theo tin có cờ is_reliable_match trong kỳ đang chọn.")
        a, b, c = st.columns(3)
        with a:
            province = st.selectbox("Tỉnh/thành", ["Tất cả"] + opts(raw, "province_new"),
                                    key="pr_province")
        scope = raw[raw["province_new"].astype(str).eq(province)].copy() if province != "Tất cả" and "province_new" in raw else raw.copy()
        with b:
            investors = opts(scope, "investor")
            if st.session_state.get("pr_investor", "Tất cả") not in ["Tất cả"] + investors:
                st.session_state["pr_investor"] = "Tất cả"
            investor = st.selectbox("Chủ đầu tư", ["Tất cả"] + investors, key="pr_investor")
        if investor != "Tất cả" and "investor" in scope:
            scope = scope[scope["investor"].astype(str).eq(investor)].copy()
        with c:
            statuses = opts(scope, "sale_status")
            if st.session_state.get("pr_status", "Tất cả") not in ["Tất cả"] + statuses:
                st.session_state["pr_status"] = "Tất cả"
            status = st.selectbox("Trạng thái", ["Tất cả"] + statuses, key="pr_status")
        if status != "Tất cả" and "sale_status" in scope:
            scope = scope[scope["sale_status"].astype(str).eq(status)].copy()
        a, b = st.columns([1, 2])
        with a:
            sizes = opts(scope, "size_group")
            if st.session_state.get("pr_size", "Tất cả") not in ["Tất cả"] + sizes:
                st.session_state["pr_size"] = "Tất cả"
            size = st.selectbox("Nhóm quy mô", ["Tất cả"] + sizes, key="pr_size")
        if size != "Tất cả" and "size_group" in scope:
            scope = scope[scope["size_group"].astype(str).eq(size)].copy()
        with b:
            search = st.text_input("Tìm dự án", key="pr_search", placeholder="Tên dự án hoặc chủ đầu tư")
    df = scope
    if reliable_only:
        listings = period_data()
        if {"project_key", "is_reliable_match"} <= set(listings.columns):
            keys = listings.loc[flag(listings["is_reliable_match"]), "project_key"].dropna().unique()
            df = df[df["project_key"].isin(keys)].copy()
        else:
            st.warning("View tin đăng thiếu cờ ghép dự án tin cậy; không áp dụng công tắc.")
    if search:
        mask = pd.Series(False, index=df.index)
        for col in ["project_name", "investor"]:
            if col in df:
                mask |= df[col].fillna("").astype(str).str.contains(search, case=False, regex=False)
        df = df[mask].copy()
    if df.empty:
        st.info("Không có dự án phù hợp với bộ lọc.")
        return

    df = df.copy()
    df["_n"] = num(df, "n_listings").fillna(0).clip(lower=0)
    df["_price"] = num(df, "median_ppm") / 1e6
    df.loc[~df["_price"].gt(0), "_price"] = np.nan
    name_col = "project_name" if "project_name" in df else "project_key"
    if name_col not in df:
        st.warning("Dữ liệu thiếu tên/mã dự án.")
        return
    df["_name"] = df[name_col].fillna("Chưa xác định").astype(str)
    active = df[df["_n"] > 0].copy()
    leader = active.sort_values("_n", ascending=False).iloc[0] if len(active) else None
    top_province = df["province_new"].dropna().value_counts() if "province_new" in df else pd.Series(dtype=int)
    with_price = df[df["_price"].notna()]
    coverage = len(with_price) / len(df) if len(df) else 0

    # KPI riêng của trang Dự án: mức độ tập trung tin ở nhóm dự án dẫn đầu.
    top10_share = (active.nlargest(10, "_n")["_n"].sum() / active["_n"].sum()
                   if len(active) and active["_n"].sum() > 0 else np.nan)
    kpi_items = [
        ("Dự án trong danh mục", fmt(len(df)), "Số dự án trong bộ lọc"),
        ("Dự án nổi bật", leader["_name"] if leader is not None else "—", "Dẫn đầu theo số tin"),
        ("Địa bàn tập trung", str(top_province.index[0]) if len(top_province) else "—", "Nhiều dự án nhất"),
        ("Tin tập trung ở Top 10", f"{top10_share:.1%}" if pd.notna(top10_share) else "—", "Tỷ trọng tin của 10 dự án dẫn đầu"),
    ]
    # Grid CSS riêng: không làm thay đổi KPI các trang Overview/Phân khúc.
    st.markdown("""<style>
    .project-kpi-grid {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:8px 0 22px}
    .project-kpi-card {box-sizing:border-box;min-width:0;min-height:166px;height:100%;
      background:white;border:1px solid #F0D9DC;border-top:5px solid #B81E34;
      border-radius:12px;padding:18px 15px;box-shadow:0 6px 16px rgba(110,15,32,.06);
      display:flex;flex-direction:column;justify-content:space-between;gap:8px}
    .project-kpi-label {font-size:.93rem;line-height:1.4;font-weight:700;color:#8A5A62}
    .project-kpi-value {font-size:clamp(1.15rem,1.55vw,1.72rem);font-weight:800;
      line-height:1.35;color:#6E0F20;overflow-wrap:anywhere;word-break:normal;
      display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
    .project-kpi-note {font-size:.78rem;line-height:1.35;color:#A98088}
    @media(max-width:1050px){.project-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
    @media(max-width:540px){.project-kpi-grid{grid-template-columns:1fr}}
    </style>""", unsafe_allow_html=True)
    st.markdown('<div class="project-kpi-grid">' + ''.join(
        '<div class="project-kpi-card">'
        f'<div class="project-kpi-label">{escape(label)}</div>'
        f'<div class="project-kpi-value" title="{escape(str(value), quote=True)}">{escape(str(value))}</div>'
        f'<div class="project-kpi-note">{escape(note)}</div></div>'
        for label, value, note in kpi_items
    ) + '</div>', unsafe_allow_html=True)

    sec("Dự án nổi bật")
    left, right = st.columns(2, gap="medium")
    with left:
        # Lollipop: rõ thứ hạng nhưng nhẹ mắt hơn biểu đồ cột.
        top = active.nlargest(10, "_n").sort_values("_n")
        fig = None
        if len(top):
            fig = go.Figure()
            for _, r in top.iterrows():
                fig.add_trace(go.Scatter(
                    x=[0, r["_n"]], y=[r["_name"], r["_name"]],
                    mode="lines", line=dict(color="#F1CDD3", width=4),
                    showlegend=False, hoverinfo="skip"))
            fig.add_trace(go.Scatter(
                x=top["_n"], y=top["_name"], mode="markers+text",
                marker=dict(size=13, color=RED, line=dict(color="white", width=1)),
                text=top["_n"].map(lambda v: fmt(v)), textposition="middle right",
                customdata=top[["_price"]].to_numpy(),
                hovertemplate="%{y}<br>%{x:,.0f} tin<extra></extra>",
                showlegend=False))
            fig.update_layout(xaxis_title="Số tin đăng", margin=dict(l=8, r=55, t=8, b=8))
        card("10 dự án hiện diện nhiều nhất", fig, 440)
    with right:
        # Dot plot so sánh giá giữa cùng 10 dự án, không giả định chuỗi thời gian.
        fig = None
        if len(top):
            z = top.dropna(subset=["_price"]).sort_values("_price")
            if len(z):
                fig = px.scatter(z, x="_price", y="_name", color="_price",
                                 color_continuous_scale=SCALE, text="_price",
                                 hover_data={"_n": True, "_price": ":.1f", "_name": False},
                                 labels={"_price": "Triệu đồng/m²", "_name": ""})
                fig.update_traces(marker=dict(size=13), texttemplate="%{x:.1f}",
                                  textposition="middle right")
                fig.update_layout(coloraxis_showscale=False, margin=dict(r=48))
        card("Giá/m² trung vị của các dự án nổi bật", fig, 440)
    if leader is not None:
        share = leader["_n"] / active["_n"].sum() if active["_n"].sum() else 0
        project_insight("Dự án nổi bật",
                        f"{leader['_name']} có {fmt(leader['_n'])} tin, chiếm {share:.1%} số tin trong danh mục đang lọc.",
                        "Dự án được xếp theo số tin đăng, không phải doanh số.")

    sec("Cơ cấu & phân bổ dự án")
    a, b = st.columns([0.9, 1.1], gap="medium")
    with a:
        card("Cơ cấu trạng thái dự án", donut(df, "sale_status"), 390, legend=True)
    with b:
        fig = None
        if "province_new" in df:
            z = df.groupby("province_new", dropna=True).size().reset_index(name="n")
            z = z.nlargest(10, "n")
            if len(z):
                # Treemap làm rõ mức độ tập trung địa bàn, tránh thêm một biểu đồ cột.
                fig = px.treemap(z, path=["province_new"], values="n",
                                 color="n", color_continuous_scale=SCALE,
                                 custom_data=["n"])
                fig.update_traces(textinfo="label+value",
                                  hovertemplate="%{label}: %{value:,.0f} dự án<extra></extra>")
                fig.update_layout(coloraxis_showscale=False)
        card("Địa bàn tập trung nhiều dự án", fig, 390)
    if len(top_province):
        project_insight("Địa bàn nổi bật",
                        f"{top_province.index[0]} dẫn đầu với {fmt(top_province.iloc[0])} dự án, chiếm {top_province.iloc[0]/len(df):.1%} danh mục đang lọc.")

    sec("Mặt bằng giá & các trường hợp cần theo dõi")
    a, b = st.columns(2, gap="medium")
    with a:
        fig = None
        if "province_new" in df and len(with_price):
            z = with_price.groupby("province_new").agg(
                n=("_price", "size"), median=("_price", "median")).reset_index()
            z = z[z["n"] >= 3].nlargest(9, "n").sort_values("median")
            if len(z):
                fig = go.Figure(go.Scatter(
                    x=z["median"], y=z["province_new"], mode="markers+text",
                    marker=dict(size=14, color=RED, line=dict(width=2, color="#F3D6DA")),
                    text=z["median"].map(lambda v: f"{v:.1f}"),
                    textposition="middle right",
                    customdata=z[["n"]].to_numpy(),
                    hovertemplate="%{y}<br>Trung vị giá dự án: %{x:.1f} tr/m²"
                                  "<br>%{customdata[0]} dự án có giá<extra></extra>"))
                fig.update_layout(xaxis_title="Triệu đồng/m²", margin=dict(r=45))
        card("Giá dự án theo địa bàn", fig, 370,
             "Trung vị các mức giá dự án; mỗi địa bàn cần từ 3 dự án có giá.")
    with b:
        # Tập trung vào 2 tín hiệu kiểm chứng được từ project summary.
        missing = df[df["_price"].isna()].copy()
        no_listings = df[df["_n"].eq(0)].copy()
        fig = go.Figure()
        fig.add_trace(go.Indicator(
            mode="number", value=len(missing),
            title={"text": "Dự án thiếu giá tham chiếu", "font": {"size": 14}},
            number={"font": {"color": DEEP, "size": 36}},
            domain={"x": [0, 0.46], "y": [0.18, 0.88]}))
        fig.add_trace(go.Indicator(
            mode="number", value=len(no_listings),
            title={"text": "Dự án chưa có tin trong view", "font": {"size": 14}},
            number={"font": {"color": RED, "size": 36}},
            domain={"x": [0.54, 1], "y": [0.18, 0.88]}))
        card("Chỉ báo cần kiểm tra", fig, 370)
    if len(missing) or len(no_listings):
        project_insight("Điểm cần theo dõi",
                        f"{fmt(len(missing))} dự án thiếu giá tham chiếu; {fmt(len(no_listings))} dự án không có tin trong bảng tổng hợp.",
                        "Đây là tín hiệu cần rà soát độ phủ dữ liệu, không phải kết luận về tình trạng kinh doanh.")

    sec("Danh mục chi tiết")
    display_cols = [c for c in ["project_name", "province_new", "district_label", "investor",
                                 "sale_status", "total_apartment", "n_listings",
                                 "n_sources", "median_ppm"] if c in df]
    out = df[display_cols].copy()
    if "median_ppm" in out:
        out["median_ppm"] = (num(out, "median_ppm") / 1e6).round(1)
    out = out.sort_values("n_listings", ascending=False) if "n_listings" in out else out
    st.dataframe(out, hide_index=True, use_container_width=True, height=440,
                 column_config={"project_name": "Dự án", "province_new": "Tỉnh/thành",
                                "district_label": "Quận/huyện", "investor": "Chủ đầu tư",
                                "sale_status": "Trạng thái", "total_apartment": "Quy mô (căn)",
                                "n_listings": "Số tin", "n_sources": "Số nguồn",
                                "median_ppm": st.column_config.NumberColumn(
                                    "Giá trung vị (tr/m²)", format="%.1f")})

@page("quality", "Nguồn & chất lượng")
def quality():
    hero("Nguồn tin & chất lượng dữ liệu",
         "Cơ cấu nguồn, độ phủ chéo dự án, độ đầy đủ dữ liệu và trạng thái giá")
    period = st.session_state.get("flt", {}).get("year", "Theo KPI")
    # Không dùng bộ lọc nguồn: trang này luôn so sánh tất cả nguồn trong cùng một kỳ.
    view = "v_kpi_base" if period == "Theo KPI" else "v_listing"
    df = get(view).copy()
    if period not in ("Theo KPI", "Tất cả") and "year" in df:
        df = df[num(df, "year").eq(int(period))].copy()
    if df.empty:
        st.info("Không có dữ liệu trong kỳ đã chọn.")
        return

    from html import escape
    def qins(label, message, detail=""):
        st.markdown(
            '<div style="background:linear-gradient(100deg,#FFF5F7,#FFFFFF);border:1px solid #E9C7CD;'
            'border-left:4px solid #B81E34;border-radius:12px;padding:15px 18px;margin:9px 0 18px">'
            f'<div style="color:#B81E34;font-size:.75rem;font-weight:800;letter-spacing:.05em">{escape(label.upper())}</div>'
            f'<div style="font-size:1.03rem;font-weight:700;color:#421D25;margin-top:5px">{escape(message)}</div>'
            + (f'<div style="font-size:.87rem;color:#77555D;margin-top:5px">{escape(detail)}</div>' if detail else '')
            + '</div>', unsafe_allow_html=True)

    # Chỉ lọc địa bàn; giữ nguyên cơ cấu nguồn và trạng thái giá để so sánh.
    def clear_quality_filters():
        st.session_state["q_province_v75"] = []

    with st.expander("Bộ lọc chất lượng", expanded=False):
        _space, _action = st.columns([5, 1])
        with _action:
            st.button("Xóa bộ lọc", key="q_reset_v75", on_click=clear_quality_filters, use_container_width=True)
        provinces = sorted(df["province_new"].dropna().astype(str).unique()) if "province_new" in df else []
        chosen = st.multiselect("Tỉnh/thành", provinces, key="q_province_v75", placeholder="Tất cả tỉnh/thành")
    if chosen and "province_new" in df:
        df = df[df["province_new"].astype(str).isin(chosen)].copy()
    if df.empty:
        st.info("Không có tin trong địa bàn đã chọn.")
        return

    # Tất cả chỉ số lấy từ đúng tập dữ liệu đang hiển thị.
    src = df["source_name"].fillna("Chưa xác định").astype(str) if "source_name" in df else pd.Series(dtype=str)
    vc = src.value_counts()
    valid_price = num(df, "price_per_m2_vnd").gt(0)
    price_col = next((c for c in ["price_status", "price_quality", "price_flag"] if c in df), None)
    project_scope = df.dropna(subset=["project_key"]).copy() if "project_key" in df else pd.DataFrame()
    if not project_scope.empty and "source_name" in project_scope:
        cross = project_scope.groupby("project_key")["source_name"].nunique()
    else:
        cross = pd.Series(dtype=int)
    multi = int(cross.ge(2).sum()) if len(cross) else 0
    kpis([
        ("Tin đăng", fmt(len(df)), ""),
        ("Nguồn tin", fmt(len(vc)), ""),
        ("Dự án đa nguồn", fmt(multi) if len(cross) else "—", ""),
        ("Tin có giá/m²", f"{valid_price.mean():.1%}", ""),
    ])
    st.caption("Phạm vi: " + ("Mẫu KPI" if period == "Theo KPI" else "Tất cả các năm" if period == "Tất cả" else f"Năm {period}"))

    sec("Cơ cấu nguồn tin")
    a, b = st.columns([.95, 1.05], gap="medium")
    with a:
        card("Tỷ trọng tin đăng theo nguồn", donut(df, "source_name", 8), 370, legend=True)
    with b:
        fig = None
        if len(vc):
            z = vc.rename_axis("Nguồn").reset_index(name="Số tin").sort_values("Số tin")
            fig = go.Figure(go.Scatter(
                x=z["Số tin"], y=z["Nguồn"], mode="markers+text",
                marker=dict(size=16, color=RED, line=dict(width=2, color="#F5B5BE")),
                text=z["Số tin"].map(fmt), textposition="middle right",
                hovertemplate="%{y}: %{x:,.0f} tin<extra></extra>"))
            fig.update_layout(xaxis_title="Số tin đăng", margin=dict(r=70))
        card("Quy mô đóng góp của từng nguồn", fig, 370)
    if len(vc):
        qins("Nguồn chi phối", f"{vc.index[0]} chiếm {vc.iloc[0]/len(df):.1%} tổng số tin đăng.",
             f"Tương ứng {fmt(vc.iloc[0])} / {fmt(len(df))} tin trong kỳ đang xem.")

    sec("Độ phủ dự án chéo nguồn")
    a, b = st.columns([1, 1], gap="medium")
    with a:
        fig = None
        if len(cross):
            z = cross.value_counts().sort_index().reset_index()
            z.columns = ["Số nguồn", "Số dự án"]
            fig = px.bar(z, x="Số nguồn", y="Số dự án", text="Số dự án",
                         color="Số nguồn", color_continuous_scale=SCALE)
            fig.update_traces(textposition="outside", cliponaxis=False)
            fig.update_layout(coloraxis_showscale=False,
                              xaxis=dict(dtick=1, title="Số nguồn xuất hiện"))
        card("Số dự án xuất hiện ở 1, 2, 3 nguồn", fig, 365,
             "Đếm nguồn khác nhau theo mã dự án trong kỳ và địa bàn đang chọn.")
    with b:
        fig = None
        if len(cross):
            z = cross.value_counts().sort_index()
            fig = px.pie(names=[f"{i} nguồn" for i in z.index], values=z.values,
                         hole=.6, color_discrete_sequence=[DEEP, RED, ROSE, "#F3C5CD"])
            fig.update_traces(textinfo="percent", marker=dict(line=dict(color="white", width=2)))
        card("Cơ cấu dự án theo mức độ hiện diện", fig, 365, legend=True)
    if len(cross):
        qins("Hiện diện đa nguồn",
             f"{fmt(multi)} / {fmt(len(cross))} dự án xuất hiện ở ít nhất 2 nguồn ({multi/len(cross):.1%}).",
             "Chỉ số phản ánh độ phủ chéo nguồn, không phải số lượng tin đăng của dự án.")
    else:
        st.info("Chưa có đủ mã dự án và nguồn tin để xác định độ phủ chéo.")

    sec("Độ đầy đủ dữ liệu")
    # Tỷ lệ thiếu theo từng trường, không cộng các trường với nhau vì một tin có thể thiếu nhiều trường.
    fields = [("Giá/m²", "price_per_m2_vnd"), ("Giá tổng", "price_total_vnd"),
              ("Diện tích", "area_m2"), ("Dự án", "project_key"),
              ("Phòng ngủ", "bedrooms_group"), ("Pháp lý", "legal_group")]
    records = []
    for label, field in fields:
        if field not in df:
            continue
        if field == "price_per_m2_vnd":
            missing = ~num(df, field).gt(0)
        elif field in ("price_total_vnd", "area_m2"):
            missing = ~num(df, field).gt(0)
        else:
            missing = df[field].isna() | df[field].astype(str).str.strip().isin(["", "Chưa xác định", "Không rõ"])
        records.append({"Trường": label, "Thiếu (%)": missing.mean()*100,
                        "Số tin thiếu": int(missing.sum())})
    a, b = st.columns([1.05, .95], gap="medium")
    with a:
        fig = None
        if records:
            z = pd.DataFrame(records).sort_values("Thiếu (%)", ascending=True)
            fig = px.bar(z, x="Thiếu (%)", y="Trường", orientation="h",
                         color="Thiếu (%)", color_continuous_scale=SCALE,
                         text="Thiếu (%)", custom_data=["Số tin thiếu"])
            fig.update_traces(texttemplate="%{x:.1f}%", textposition="outside",
                              hovertemplate="%{y}: %{x:.1f}%<br>%{customdata[0]:,.0f} tin<extra></extra>")
            fig.update_layout(coloraxis_showscale=False, xaxis_title="Tỷ lệ thiếu (%)",
                              margin=dict(r=50))
        card("Tỷ lệ thiếu theo trường dữ liệu", fig, 390)
    with b:
        fig = None
        if records and "source_name" in df:
            data = []
            for source, group in df.groupby("source_name"):
                for label, field in fields:
                    if field not in group:
                        continue
                    if field in ("price_per_m2_vnd", "price_total_vnd", "area_m2"):
                        rate = (~num(group, field).gt(0)).mean()*100
                    else:
                        rate = (group[field].isna() | group[field].astype(str).str.strip().isin(["", "Chưa xác định", "Không rõ"])).mean()*100
                    data.append({"Nguồn": str(source), "Trường": label, "Thiếu (%)": rate})
            if data:
                z = pd.DataFrame(data).pivot(index="Nguồn", columns="Trường", values="Thiếu (%)")
                fig = px.imshow(z, text_auto=".1f", aspect="auto",
                                color_continuous_scale=SCALE, zmin=0, zmax=100,
                                labels={"x":"", "y":"", "color":"Thiếu (%)"})
        card("Tỷ lệ thiếu theo nguồn (%)", fig, 390)
    if records:
        worst = max(records, key=lambda r:r["Thiếu (%)"])
        qins("Độ đầy đủ dữ liệu",
             f"{worst['Trường']} có tỷ lệ thiếu cao nhất: {worst['Thiếu (%)']:.1f}%.",
             f"Tương ứng {fmt(worst['Số tin thiếu'])} tin trong phạm vi lọc.")

    sec("Phân bố trạng thái giá")
    a, b = st.columns([1, 1], gap="medium")
    with a:
        fig = None
        if price_col:
            z = df[price_col].fillna("Chưa xác định").astype(str).value_counts().sort_values()
            fig = px.bar(x=z.values, y=z.index, orientation="h", text=z.values,
                         color=z.values, color_continuous_scale=SCALE,
                         labels={"x":"Số tin", "y":""})
            fig.update_traces(textposition="outside", cliponaxis=False)
            fig.update_layout(coloraxis_showscale=False, margin=dict(r=50))
        card("Số tin theo trạng thái giá", fig, 365,
             "Giữ nguyên tên trạng thái giá đã được phân loại trong Data Warehouse.")
    with b:
        fig = None
        if price_col and "source_name" in df:
            z = df.groupby(["source_name", price_col], dropna=False).size().reset_index(name="n")
            z[price_col] = z[price_col].fillna("Chưa xác định")
            fig = px.bar(z, x="source_name", y="n", color=price_col,
                         color_discrete_sequence=ACCENT_COLORS,
                         labels={"source_name":"", "n":"Số tin", price_col:"Trạng thái"})
            fig.update_layout(barnorm="percent", yaxis=dict(title="Tỷ trọng (%)", ticksuffix="%"))
        card("Cơ cấu trạng thái giá theo nguồn", fig, 365, legend=True)
    if price_col:
        statuses = df[price_col].fillna("Chưa xác định").astype(str).value_counts()
        if len(statuses):
            qins("Trạng thái giá phổ biến",
                 f"{statuses.index[0]} chiếm {statuses.iloc[0]/len(df):.1%} số tin.",
                 f"Tương ứng {fmt(statuses.iloc[0])} tin; các trạng thái giữ nguyên theo kết quả phân loại.")
    else:
        st.info("View hiện tại không có cột trạng thái giá; không suy diễn trạng thái từ giá trị giá/m².")

@page("dss", "DSS đầu tư")
def dss():
    hero("DSS · Ưu tiên thị trường đầu tư", "Xếp hạng thị trường, thử nghiệm trọng số và theo dõi cảnh báo")
    lv = st.segmented_control("Cấp đánh giá", ["Tỉnh/thành", "Quận/huyện"],
                              default="Tỉnh/thành", key="dss_level") or "Tỉnh/thành"
    df = get("v_dss_province" if lv == "Tỉnh/thành" else "v_dss_district", True)
    if df.empty:
        st.info("Chưa đọc được bảng DSS tương ứng.")
        return
    # v_dss_district tính đủ r_* trong SQL nội bộ nhưng không xuất sáu cột.
    # Khôi phục tại tầng hiển thị, không thay đổi view hay dữ liệu Supabase.
    # PostgreSQL percent_rank() = (rank() - 1) / (n - 1), với rank() kiểu min.
    # Cần tính trên TOÀN BỘ mỗi tier trước khi lọc nhóm xếp hạng đầy đủ.
    score_cols = ["r_depth", "r_price", "r_conc", "r_disp", "r_amen", "r_div"]
    if lv == "Quận/huyện" and "tier" in df and not all(c in df.columns for c in score_cols):
        specs = [
            ("r_depth", "n_priced", True, "bottom"),
            ("r_price", "median_ppm_trieu", True, "bottom"),
            ("r_conc", "top1_share", False, "top"),
            ("r_disp", "iqr_ratio", False, "top"),
            ("r_amen", "avg_amenity", True, "top"),
            ("r_div", "n_segments", True, "bottom"),
        ]
        # Các trường ppm/iqr/top1/amenity của view được làm tròn để hiển thị.
        # Vì thế percent_rank tái dựng có thể khác thứ hạng SQL gốc ở giá trị sát nhau.
        for output, source, ascending, na_option in specs:
            if output in df.columns or source not in df.columns:
                continue
            values = pd.to_numeric(df[source], errors="coerce")
            ranks = values.groupby(df["tier"], dropna=False).rank(
                method="min", ascending=ascending, na_option=na_option)
            sizes = df.groupby("tier", dropna=False)["tier"].transform("size")
            df[output] = ((ranks - 1) / (sizes - 1).replace(0, np.nan)).fillna(0.0)
    r = df[df.tier == "Xếp hạng đầy đủ"].copy() if "tier" in df else df.copy()
    r = r.sort_values("dss_score", ascending=False) if "dss_score" in r else r
    if lv == "Quận/huyện" and "district_label" in r:
        r["_n"] = (r.get("province_new", "").fillna("").astype(str) + " / " + r.district_label.fillna("").astype(str)).str.strip(" /")
    else:
        r["_n"] = r[next((c for c in ["province_new", "former_area"] if c in r), r.columns[0])].astype(str)
    crit = [("depth", "Độ sâu thị trường", 30), ("price", "Mặt bằng giá", 20), ("conc", "Rủi ro tập trung", 20),
            ("disp", "Phân tán giá", 15), ("amen", "Tiện ích", 10), ("div", "Đa dạng phân khúc", 5)]
    t1, t2, t3 = st.tabs(["Bảng xếp hạng", "What-if trọng số", "Tín hiệu & cảnh báo"])
    with t1:
        a, b = st.columns([1.2, 1], gap="medium")
        with a:
            z = r.head(12).sort_values("dss_score")
            card("Top 12 điểm ưu tiên", px.bar(z, x="dss_score", y="_n", orientation="h", color="dss_score",
                 color_continuous_scale=SCALE, text="dss_score").update_layout(coloraxis_showscale=False, yaxis_title=None,
                 xaxis_title="Điểm").update_traces(texttemplate="%{x:.1f}", cliponaxis=False) if "dss_score" in z else None, 420)
        with b:
            rc = ["r_" + c for c, _, _ in crit]
            if all(c in r for c in rc) and len(r):
                fig = go.Figure()
                for i, (_, row) in enumerate(r.head(3).iterrows()):
                    v = [float(row[c]) for c in rc]
                    fig.add_scatterpolar(r=v + v[:1], theta=[l for _, l, _ in crit] + [crit[0][1]], name=row["_n"],
                                         fill="toself", opacity=.42, line=dict(color=["#B7283E", "#194C3A", "#C69B50"][i], width=2.5),
                                         fillcolor=["rgba(183,40,62,0.12)", "rgba(25,76,58,0.12)", "rgba(198,155,80,0.12)"][i])
                card("Radar 6 tiêu chí — top 3", fig, 420, legend=True)
            else:
                card("Radar 6 tiêu chí", None, 420)
        ren = {"province_new": "Tỉnh/thành", "district_label": "Quận/huyện", "former_area": "Khu vực cũ", "rank": "Hạng",
               "dss_score": "Điểm", "n_listings": "Số tin", "n_projects": "Số dự án", "tier": "Nhóm"}
        out = df[[c for c in ren if c in df]].rename(columns=ren)
        # Có điểm hợp lệ trước, không đủ dữ liệu xuống cuối; điểm giảm dần.
        if "Điểm" in out.columns:
            out["Điểm"] = pd.to_numeric(out["Điểm"], errors="coerce")
            out["_has_score"] = out["Điểm"].notna() & np.isfinite(out["Điểm"])
            out = out.sort_values(["_has_score", "Điểm"], ascending=[False, False], na_position="last", kind="stable").drop(columns="_has_score")
        elif "Nhóm" in out.columns:
            out["_tier_order"] = out["Nhóm"].map({"Xếp hạng đầy đủ": 0, "Theo dõi": 1, "Không đủ dữ liệu": 2}).fillna(3)
            out = out.sort_values("_tier_order", kind="stable").drop(columns="_tier_order")
        st.dataframe(out, hide_index=True, use_container_width=True, height=320, column_config={
            "Điểm": st.column_config.ProgressColumn("Điểm", max_value=100, format="%.1f")})
    with t2:
        # Trọng số nháp độc lập: không tự ý thay đổi các thanh khác.
        # Chỉ áp dụng khi tổng bằng đúng 100% hoặc khi người dùng chủ động cân bằng.
        weight_keys = ["w_" + c for c, _, _ in crit]
        defaults = [d for _, _, d in crit]
        for wk, default in zip(weight_keys, defaults):
            if wk not in st.session_state:
                st.session_state[wk] = default
        if "dss_applied_weights" not in st.session_state:
            st.session_state["dss_applied_weights"] = defaults.copy()

        st.markdown("**Tùy chỉnh trọng số**")
        st.caption("Kéo từng thanh độc lập. Chỉ khi tổng đạt 100% mới có thể áp dụng; biểu đồ không đổi khi bạn đang chỉnh nháp.")
        cols = st.columns(3, gap="medium")
        for i, (c, label, default) in enumerate(crit):
            with cols[i % 3]:
                st.slider(label, 0, 100, key="w_" + c, step=1, format="%d%%")
        draft = [int(st.session_state[k]) for k in weight_keys]
        total_draft = sum(draft)
        diff = 100 - total_draft
        if diff == 0:
            st.success("Tổng trọng số: 100% · Sẵn sàng áp dụng")
        else:
            st.warning(f"Tổng hiện tại: {total_draft}% · {'Cần tăng' if diff > 0 else 'Cần giảm'} {abs(diff)}% để đạt 100%")

        def balance_dss_draft():
            values = [max(0, int(st.session_state[k])) for k in weight_keys]
            denom = sum(values)
            if denom == 0:
                values = defaults.copy()
                denom = 100
            raw = [100 * x / denom for x in values]
            rounded = [int(x) for x in raw]
            order = sorted(range(6), key=lambda i: raw[i] - rounded[i], reverse=True)
            for i in order[:100 - sum(rounded)]:
                rounded[i] += 1
            for k, val in zip(weight_keys, rounded):
                st.session_state[k] = val

        def apply_dss_draft():
            st.session_state["dss_applied_weights"] = [int(st.session_state[k]) for k in weight_keys]

        def reset_dss_whatif():
            # Chỉ đặt lại các trọng số What-if; không ảnh hưởng cấp đánh giá
            # hoặc bộ lọc toàn dashboard.
            for k, default in zip(weight_keys, defaults):
                st.session_state[k] = default
            st.session_state["dss_applied_weights"] = defaults.copy()

        c_apply, c_balance, c_reset, _ = st.columns([1.2, 1.5, 1.25, 1.75], gap="small")
        with c_apply:
            st.button("Áp dụng trọng số", key="dss_apply_weights", type="primary",
                      disabled=(total_draft != 100), on_click=apply_dss_draft,
                      use_container_width=True)
        with c_balance:
            st.button("Cân bằng về 100%", key="dss_balance_weights",
                      on_click=balance_dss_draft, use_container_width=True)
        with c_reset:
            st.button("Đặt lại mặc định", key="dss_reset_whatif",
                      on_click=reset_dss_whatif, use_container_width=True)
        applied = st.session_state["dss_applied_weights"]
        w = {c: applied[i] for i, (c, _, _) in enumerate(crit)}
        tot = sum(applied)
        rc = ["r_" + c for c, _, _ in crit]
        if not all(c in r for c in rc):
            st.info("Chưa đủ chỉ số đầu vào để hiển thị sáu tiêu chí.")
        elif tot:
            z = r.copy()
            z["sim"] = sum(num(z, "r_" + c) * w[c] / 100 for c, _, _ in crit) * 100
            z = z.sort_values("sim", ascending=False)
            z["new"] = np.arange(1, len(z) + 1)
            old = {i: k + 1 for k, i in enumerate(r.index)}
            z["delta"] = [old[i] - n for i, n in zip(z.index, z.new)]
            t = z.head(12).sort_values("sim")
            a, b = st.columns(2, gap="medium")
            with a:
                card("Xếp hạng sau điều chỉnh", px.bar(t, x="sim", y="_n", orientation="h", color="delta",
                     color_continuous_scale=["#6E0F20", "#FDF3F4", "#B81E34"], color_continuous_midpoint=0).update_layout(
                     yaxis_title=None, xaxis_title="Điểm mô phỏng", coloraxis_colorbar=dict(title="Δ hạng", thickness=10)), 420,
                     "Màu = thay đổi hạng so với mô hình gốc (đỏ = tăng)")
            with b:
                s = z.head(10)
                fig = go.Figure(go.Scatter(x=s.dss_score, y=s.sim, mode="markers+text", text=s._n, textposition="top center",
                                           marker=dict(size=13, color=RED)))
                mx = float(max(s.dss_score.max(), s.sim.max()))
                fig.add_shape(type="line", x0=0, y0=0, x1=mx, y1=mx, line=dict(dash="dot", color="#B9A0A5"))
                fig.update_layout(xaxis_title="Điểm gốc", yaxis_title="Điểm mô phỏng")
                card("Điểm gốc vs mô phỏng", fig, 420, "Trên đường chéo = được lợi khi đổi trọng số")
        else:
            st.warning("Cần ít nhất một trọng số lớn hơn 0.")
        insight("Mô hình chấm giá/m² cao là tốt hơn — đây là giả định của nhóm, không phải dự báo lợi nhuận.")
    with t3:
        gap, pipe, al = get("v_segment_gap", True), get("v_pipeline_province", True), get("v_alerts", True)
        a, b = st.columns(2, gap="medium")
        with a:
            if len(pipe) and {"n_sap_mo_ban", "province_new"} <= set(pipe.columns):
                z = pipe.sort_values("n_sap_mo_ban", ascending=False).head(10).sort_values("n_sap_mo_ban")
                card("Dự án sắp mở bán theo tỉnh", px.bar(z, x="n_sap_mo_ban", y="province_new", orientation="h",
                     color_discrete_sequence=[RED]).update_layout(yaxis_title=None, xaxis_title="Số dự án"), 340)
            else:
                card("Dự án sắp mở bán theo tỉnh", None, 340)
        with b:
            if len(gap) and {"province_new", "segment_name", "gap_pp"} <= set(gap.columns):
                pv = gap.assign(gap_pp=num(gap, "gap_pp")).pivot_table(index="province_new", columns="segment_name", values="gap_pp")
                card("Khoảng trống phân khúc theo tỉnh", px.imshow(pv, color_continuous_scale=[[0, "#194C3A"], [0.25, "#39734F"], [0.5, "#FFF7F8"], [0.75, "#D66C7C"], [1, "#B7283E"]], color_continuous_midpoint=0,
                     aspect="auto", labels=dict(color="điểm %")), 340, "Dương = tỷ trọng tin đăng thấp hơn mức tham chiếu toàn quốc; không kết luận thiếu nguồn cung")
            else:
                card("Khoảng trống phân khúc theo tỉnh", None, 340)
        # Đồng bộ tiêu đề bảng cảnh báo với các khung biểu đồ trong dashboard.
        with st.container(border=True):
            st.markdown('<div class="ct">Cảnh báo thị trường</div>', unsafe_allow_html=True)
            if len(al):
                alert_cols = [c for c in al if not c.startswith(("r_", "_"))]
                alert_labels = {
                    "alert_type": "Loại cảnh báo", "alert_name": "Cảnh báo",
                    "alert_level": "Mức cảnh báo", "severity": "Mức độ",
                    "province_new": "Tỉnh/thành", "district_label": "Quận/huyện",
                    "district_name": "Quận/huyện", "project_name": "Dự án",
                    "segment_name": "Phân khúc", "description": "Nội dung",
                    "message": "Nội dung", "details": "Chi tiết",
                    "metric_value": "Giá trị", "threshold_value": "Ngưỡng",
                    "threshold": "Ngưỡng", "n_listings": "Số tin đăng",
                    "n_projects": "Số dự án", "source_name": "Nguồn tin",
                    "alert_count": "Số cảnh báo", "created_at": "Ngày ghi nhận",
                }
                display_cols = {c: alert_labels.get(c, c.replace("_", " ").strip().capitalize()) for c in alert_cols}
                st.dataframe(al[alert_cols].rename(columns=display_cols), hide_index=True,
                             use_container_width=True)
            else:
                st.info("Chưa đọc được bản ghi cảnh báo từ dữ liệu hiện tại.")


# ------------------------------------------------------------ main
if db() is None:
    st.error("Chưa cấu hình DATABASE_URL trong `.streamlit/secrets.toml`.")
    st.stop()

with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-title">VN APARTMENT<br>INTELLIGENCE</div><div class="brand-sub">REAL ESTATE · BI &amp; DSS</div></div>', unsafe_allow_html=True)
    key = st.radio("Điều hướng", list(PAGES), format_func=lambda k: PAGES[k][0].strip(), label_visibility="collapsed")
    st.divider()
    st.markdown('<div style="font-weight:800;font-size:1.12rem;color:#FBE4E6;margin:10px 0 10px">Bộ lọc dữ liệu</div>', unsafe_allow_html=True)
    try:
        listing_options = query("v_listing")
        srcs = sorted(listing_options.source_name.dropna().astype(str).unique()) if "source_name" in listing_options else []
        years = sorted(num(listing_options, "year").dropna().astype(int).unique(), reverse=True) if "year" in listing_options else []
    except Exception:
        listing_options, srcs, years = pd.DataFrame(), [], []

    def clear_sidebar_filters():
        # Đặt lại cả giá trị widget (không chỉ điều kiện lọc) để giao diện
        # ngay sau khi nhấn Xóa bộ lọc hiển thị đúng trạng thái mặc định.
        st.session_state["sidebar_sources"] = []
        st.session_state["sidebar_year"] = "Theo KPI"
        st.session_state["sidebar_date_from"] = None
        st.session_state["sidebar_date_to"] = None
        st.session_state["sidebar_last_year"] = "Theo KPI"
        st.session_state["flt"] = {"src": [], "year": "Theo KPI", "dates": None, "date_col": None}

    # Nguồn tin đứng trước năm, dùng cùng kiểu nhãn và control của sidebar.
    if key == "quality":
        src = []  # Trang chất lượng cần hiển thị đồng thời tất cả nguồn.
    else:
        if "sidebar_sources" in st.session_state:
            st.session_state["sidebar_sources"] = [v for v in st.session_state["sidebar_sources"] if v in srcs]
        src = st.multiselect("Nguồn tin", srcs, key="sidebar_sources",
                             placeholder="Tất cả nguồn")
    year_choices = ["Theo KPI"] + [str(y) for y in years] + ["Tất cả"]
    if st.session_state.get("sidebar_year") not in year_choices:
        st.session_state["sidebar_year"] = "Theo KPI"
    year = st.selectbox("Năm", year_choices, key="sidebar_year")

    # Cùng font, cỡ chữ, viền và khoảng cách như ô Nguồn tin và Năm.
    st.markdown("""<style>
    [data-testid="stSidebar"] [data-testid="stDateInput"] label p,
    [data-testid="stSidebar"] [data-testid="stExpander"] summary p {
        font-family:'Be Vietnam Pro',Arial,sans-serif !important;
        font-size:1.15rem !important;font-weight:700 !important;color:#FBE4E6 !important;
    }
    [data-testid="stSidebar"] [data-testid="stDateInput"] input {
        font-family:'Be Vietnam Pro',Arial,sans-serif !important;
        font-size:1.05rem !important;color:#2B1519 !important;
    }
    [data-testid="stSidebar"] [data-testid="stDateInput"] [data-baseweb="input"] {
        border-radius:9px !important;
    }
    </style>""", unsafe_allow_html=True)
    date_col = next((c for c in ("full_date", "listing_date", "posted_date", "date_posted")
                     if c in listing_options.columns), None)
    dates = None
    if st.session_state.get("sidebar_last_year") != year:
        st.session_state.pop("sidebar_date_from", None)
        st.session_state.pop("sidebar_date_to", None)
        st.session_state["sidebar_last_year"] = year
    if date_col:
        from datetime import date as _date
        available = listing_options
        if year == "Theo KPI":
            available = get("v_kpi_base", optional=True)
        elif year != "Tất cả" and "year" in available:
            available = available[num(available, "year").eq(int(year))]
        valid_dates = (pd.to_datetime(available[date_col], errors="coerce").dropna()
                       if date_col in available else pd.Series(dtype="datetime64[ns]"))
        if year not in ("Theo KPI", "Tất cả"):
            # Cho phép chọn cả năm dù các bản ghi của năm chưa có ngày chi tiết.
            lo, hi = _date(int(year), 1, 1), _date(int(year), 12, 31)
        elif not valid_dates.empty:
            lo, hi = valid_dates.min().date(), valid_dates.max().date()
        else:
            lo = hi = None
        if lo is not None:
            for dk in ("sidebar_date_from", "sidebar_date_to"):
                old = st.session_state.get(dk)
                if old is not None and not lo <= old <= hi:
                    st.session_state[dk] = None
            # Giới hạn ngày ngay trong lịch: ngày bắt đầu không thể sau ngày kết thúc,
            # ngày kết thúc không thể trước ngày bắt đầu. Không đợi chọn sai rồi cảnh báo.
            old_start = st.session_state.get("sidebar_date_from")
            old_end = st.session_state.get("sidebar_date_to")
            if old_start is not None and old_end is not None and old_start > old_end:
                st.session_state["sidebar_date_to"] = None
                old_end = None
            with st.expander("Tùy chỉnh", expanded=False):
                start_date = st.date_input(
                    "Từ ngày", value=None, min_value=lo, max_value=old_end or hi,
                    key="sidebar_date_from", format="DD/MM/YYYY")
                end_date = st.date_input(
                    "Đến ngày", value=None, min_value=start_date or lo, max_value=hi,
                    key="sidebar_date_to", format="DD/MM/YYYY")
                if valid_dates.empty:
                    st.caption("Năm này chưa có ngày chi tiết để lọc chính xác.")
                elif start_date or end_date:
                    dates = (start_date or lo, end_date or hi)
    st.session_state["flt"] = {"src": src, "year": year, "dates": dates, "date_col": date_col}
    st.button("Xóa bộ lọc", on_click=clear_sidebar_filters, use_container_width=True)

try:
    PAGES[key][1]()
except Exception as e:
    st.error("Trang này gặp lỗi xử lý dữ liệu.")
    with st.expander("Chi tiết lỗi (cho người phát triển)"):
        st.exception(e)