"""Page 6 — Diner Simulator (live demo): type in a diner, see segment, reorder likelihood and recommendations."""
import plotly.graph_objects as go
import streamlit as st

from core import FEATURES, NICE, SEGMENTS, analyse_diner
from ui import SEG_COLORS, chips, get_artifacts, hero, insights, show, style

A = get_artifacts()
d = A["diners"].set_index("diner_id")
nice = lambda s: s.replace("_", " ")

hero("Diner Simulator", "Type in a diner and instantly see their segment, reorder likelihood and what to offer",
     "🔮", ("#7C4DFF", "#FF6B35"))

# ---- state: inputs live in session_state so presets / ID lookup can fill them -------------------------
DEFAULT = dict(age=28, orders_per_month=8, avg_order_value=90.0, avg_items_per_order=3,
               days_since_last_order=10, discount_rate=0.30, total_spend=800.0)
PRESETS = {
    "🎓 Frequent student": dict(age=21, orders_per_month=14, avg_order_value=40.0, avg_items_per_order=2,
                               days_since_last_order=4, discount_rate=0.60, total_spend=500.0),
    "👨‍👩‍👧 Lapsed family": dict(age=40, orders_per_month=3, avg_order_value=175.0, avg_items_per_order=6,
                              days_since_last_order=25, discount_rate=0.30, total_spend=600.0),
    "🍣 Premium regular": dict(age=33, orders_per_month=9, avg_order_value=100.0, avg_items_per_order=3,
                              days_since_last_order=8, discount_rate=0.10, total_spend=900.0),
}
for k, v in DEFAULT.items():
    st.session_state.setdefault(f"sim_{k}", v)
st.session_state.setdefault("sim_msg", "")


def apply_profile(profile: dict, msg: str = "") -> None:
    for k, v in profile.items():
        st.session_state[f"sim_{k}"] = v
    st.session_state["sim_msg"] = msg


def lookup_diner() -> None:
    diner_id = st.session_state.get("sim_lookup", "").strip().upper()
    if diner_id in d.index:
        row = d.loc[diner_id]
        profile = dict(age=int(row["age"]), orders_per_month=int(row["orders_per_month"]),
                       avg_order_value=float(row["avg_order_value"]), avg_items_per_order=int(row["avg_items_per_order"]),
                       days_since_last_order=int(row["days_since_last_order"]), discount_rate=float(row["discount_rate"]),
                       total_spend=float(row["total_spend"]))
        outcome = "reordered" if row["reordered"] == 1 else "did not reorder (churned)"
        apply_profile(profile, f"Loaded {diner_id} — in the data this diner {outcome}.")
    else:
        st.session_state["sim_msg"] = f"No diner with ID '{diner_id}'. Try one like D1293."


# ---- layout: inputs left, live result right ---------------------------------------------------------
left, right = st.columns([1, 1.25], gap="large")

with left:
    st.markdown("#### 1 · Enter a diner")
    pc = st.columns(3)
    for col, (label, prof) in zip(pc, PRESETS.items()):
        col.button(label, on_click=apply_profile, args=(prof, f"Loaded preset: {label}"))
    lc1, lc2 = st.columns([2, 1])
    lc1.text_input("Or look up a diner ID (e.g. D1293)", key="sim_lookup", placeholder="D1293")
    lc2.write("")
    lc2.write("")
    lc2.button("Load diner", on_click=lookup_diner)
    if st.session_state["sim_msg"]:
        st.caption(st.session_state["sim_msg"])

    st.slider("Age", 8, 70, key="sim_age")
    st.slider("Orders per month", 1, 25, key="sim_orders_per_month")
    st.slider("Average order value (AED)", 15.0, 250.0, step=1.0, key="sim_avg_order_value")
    st.slider("Average items per order", 1, 10, key="sim_avg_items_per_order")
    st.slider("Days since last order", 0, 60, key="sim_days_since_last_order")
    st.slider("Discount usage rate", 0.0, 1.0, step=0.01, key="sim_discount_rate")
    st.number_input("Total spend so far (AED)", min_value=0.0, max_value=20000.0, step=50.0, key="sim_total_spend")

profile = {k: st.session_state[f"sim_{k}"] for k in DEFAULT}
res = analyse_diner(A, profile)
seg, p = res["segment"], res["p_reorder"]
color = SEG_COLORS[seg]

if p < 0.40:
    band, band_color, action = "At risk of churning", "#EF476F", "Send a win-back offer now"
elif p < 0.60:
    band, band_color, action = "Watch closely", "#FFB703", "Nudge with a bundle before they drift"
else:
    band, band_color, action = "Likely to reorder", "#06D6A0", "Keep warm — suggest a bundle to grow basket size"

with right:
    st.markdown("#### 2 · Live result")
    st.markdown(f'<div class="segcard" style="background:{color}"><div class="l">Diner segment</div>'
                f'<div class="v">{seg}</div></div>', unsafe_allow_html=True)

    gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=p * 100, number=dict(suffix="%", font=dict(size=46)),
        title=dict(text=f"<b>Reorder likelihood — {band}</b>", font=dict(size=15)),
        gauge=dict(axis=dict(range=[0, 100], ticksuffix="%"), bar=dict(color="#1F2937", thickness=0.28),
                   steps=[dict(range=[0, 40], color="#FFC2D1"), dict(range=[40, 60], color="#FFE8A3"),
                          dict(range=[60, 100], color="#A8F0D8")],
                   threshold=dict(line=dict(color=band_color, width=5), thickness=0.85, value=p * 100))))
    gauge.update_layout(height=260, margin=dict(l=20, r=20, t=60, b=0), paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#1F2937"))
    show(gauge)
    st.caption("Risk bands: red under 40% · amber 40–60% · green 60% and above")

    st.markdown(f"**Recommended items for {seg}** — the segment's most-ordered items")
    chips([nice(i) for i in res["items"]], ["#FF6B35", "#7C4DFF", "#00B8A9", "#FFB703", "#118AB2"])
    if res["bundles"]:
        st.markdown("**Bundle to promote** — pairs ordered together far more than by chance")
        chips([f"{nice(b['antecedents'])} + {nice(b['consequents'])}  (lift {b['lift']:.1f})" for b in res["bundles"]],
              [color, color])
    else:
        st.markdown("**Bundle to promote** — no strong pairs in this segment; offer a fixed-price combo of the items above.")
    st.markdown(f'<div style="background:{band_color};color:#1F2937;border-radius:12px;padding:.6rem 1rem;'
                f'font-weight:700;margin-top:.6rem">➡ Suggested action: {action}</div>', unsafe_allow_html=True)

# ---- context charts -------------------------------------------------------------------------------------
c1, c2 = st.columns(2)
with c1:
    rng = A["feature_ranges"]
    S = A["segment_summary"]
    theta = [NICE[f] for f in FEATURES]
    norm = lambda f, v: min(max((v - rng.loc["min", f]) / (rng.loc["max", f] - rng.loc["min", f]), 0), 1)
    this = [norm(f, profile[f]) for f in FEATURES]
    avg = [norm(f, S.loc[seg, f]) for f in FEATURES]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=avg + avg[:1], theta=theta + theta[:1], name=f"{seg} average", fill="toself",
                                  opacity=0.45, line=dict(color=color, width=2)))
    fig.add_trace(go.Scatterpolar(r=this + this[:1], theta=theta + theta[:1], name="This diner",
                                  line=dict(color="#1F2937", width=3)))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 1], tickvals=[0, 0.5, 1])))
    show(style(fig, "This diner vs segment average (0 = lowest diner, 1 = highest diner)", height=400))
with c2:
    dd = A["diners"]
    fig = go.Figure()
    for s in SEGMENTS:
        sub = dd[dd["segment"] == s]
        fig.add_trace(go.Scatter(x=sub["orders_per_month"], y=sub["avg_order_value"], mode="markers", name=s,
                                 marker=dict(color=SEG_COLORS[s], size=7, opacity=0.55)))
    fig.add_trace(go.Scatter(x=[profile["orders_per_month"]], y=[profile["avg_order_value"]], mode="markers",
                             name="This diner", marker=dict(symbol="star", size=22, color="#FFD60A",
                                                            line=dict(width=2, color="#1F2937"))))
    show(style(fig, "Where this diner sits among all diners", "Orders per month", "Average order value (AED)", 400))

# ---- key insights ---------------------------------------------------------------------------------------
corr, imp = A["reorder_corr"], A["clf_importance"]
f1, f2 = imp.index[0], imp.index[1]
insights([
    f"<b>This diner:</b> {seg} · {p:.0%} reorder likelihood · {band.lower()} → {action.lower()}.",
    f"<b>What moves the score most:</b> {NICE[f1].lower()} and {NICE[f2].lower()} "
    f"(correlation with reordering {corr[f1]:+.2f} and {corr[f2]:+.2f}). Try changing them with the sliders.",
    "<b>Recommendations</b> are the segment's five most-ordered items; bundles appear only when a pair's lift is 1.5 or higher.",
    "<b>Best use:</b> check a diner before a campaign — treat red as win-back, amber as nudge, green as upsell.",
])
