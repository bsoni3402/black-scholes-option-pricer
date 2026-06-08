"""
Black-Scholes Option Pricer — Streamlit Dashboard
===================================================
Interactive dashboard for pricing European options and visualising
option Greeks, P&L profiles, and Implied Volatility.

Run:
    streamlit run app.py

Author: Bhagyesh Soni
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from black_scholes_engine import (
    OptionParams,
    price,
    delta,
    gamma,
    vega,
    theta,
    rho,
    all_greeks,
    implied_volatility,
    pnl_at_expiry,
)

# ──────────────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Black-Scholes Option Pricer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar — global inputs
# ──────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("📈 BSM Option Pricer")
    st.caption("Black-Scholes-Merton with continuous dividend yield")

    st.header("Option Parameters")

    option_type = st.radio("Option Type", ["call", "put"], horizontal=True)

    S = st.number_input("Spot Price (S)", min_value=1.0, max_value=10_000.0, value=100.0, step=1.0)
    K = st.number_input("Strike Price (K)", min_value=1.0, max_value=10_000.0, value=100.0, step=1.0)
    T = st.slider("Time to Expiry (years)", min_value=0.01, max_value=5.0, value=1.0, step=0.01)
    r = st.slider("Risk-Free Rate (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.1) / 100
    sigma = st.slider("Volatility (%)", min_value=1.0, max_value=200.0, value=20.0, step=0.5) / 100
    q = st.slider("Dividend Yield (%)", min_value=0.0, max_value=20.0, value=0.0, step=0.1) / 100

    params = OptionParams(S=S, K=K, T=T, r=r, sigma=sigma, q=q, option_type=option_type)
    option_price = price(params)
    greeks = all_greeks(params)

    st.divider()
    st.metric("Option Price", f"${option_price:.4f}")
    st.caption(f"Δ {greeks['delta']:.4f}  |  Γ {greeks['gamma']:.4f}")
    st.caption(f"ν {greeks['vega']:.4f}  |  Θ {greeks['theta']:.4f}/day  |  ρ {greeks['rho']:.4f}")


# ──────────────────────────────────────────────────────────────────────────────
# Main tabs
# ──────────────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏛️ Greeks Dashboard",
    "🗺️ Price Heatmap",
    "💰 P&L Profile",
    "🔬 Greeks Heatmaps",
    "🔍 IV Calculator",
])


# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 — Greeks Dashboard
# ──────────────────────────────────────────────────────────────────────────────

with tab1:
    st.header("Greeks Dashboard")

    # ── Greek cards ──────────────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    greek_colors = ["#4CAF50", "#2196F3", "#FF9800", "#F44336", "#9C27B0"]
    greek_descriptions = {
        "delta": ("Δ Delta", "Price sensitivity to $1 spot move"),
        "gamma": ("Γ Gamma", "Rate of change of Delta"),
        "vega":  ("ν Vega",  "Price sensitivity to 1% vol move"),
        "theta": ("Θ Theta", "Time decay ($/day)"),
        "rho":   ("ρ Rho",   "Sensitivity to 1% rate move"),
    }

    for col, (gk, (label, desc)) in zip([col1, col2, col3, col4, col5], greek_descriptions.items()):
        with col:
            st.metric(label, f"{greeks[gk]:.4f}", help=desc)

    st.divider()

    # ── Dollar impact table ──────────────────────────────────────────────────
    st.subheader("Dollar Impact per Unit Move")
    impact_df = pd.DataFrame({
        "Greek": ["Delta", "Gamma", "Vega", "Theta", "Rho"],
        "Value": [greeks["delta"], greeks["gamma"], greeks["vega"], greeks["theta"], greeks["rho"]],
        "Per": ["+$1 spot", "+$1 spot (2nd order)", "+1% vol", "1 day", "+1% rate"],
        "$ Impact": [
            f"${greeks['delta'] * S:.4f}",
            f"${greeks['gamma'] * S**2 * 0.01:.4f}",
            f"${greeks['vega']:.4f}",
            f"${greeks['theta']:.4f}",
            f"${greeks['rho']:.4f}",
        ],
    })
    st.dataframe(impact_df, use_container_width=True, hide_index=True)

    st.divider()

    # ── Delta & Gamma vs Spot ────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    spot_range = np.linspace(S * 0.5, S * 1.5, 200)

    with col_left:
        st.subheader("Delta & Gamma vs Spot")
        deltas, gammas = [], []
        for s in spot_range:
            p_tmp = OptionParams(S=float(s), K=K, T=T, r=r, sigma=sigma, q=q, option_type=option_type)
            deltas.append(delta(p_tmp))
            gammas.append(gamma(p_tmp))

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=spot_range, y=deltas, name="Delta", line=dict(color="#4CAF50", width=2)))
        fig.add_trace(go.Scatter(x=spot_range, y=gammas, name="Gamma", line=dict(color="#2196F3", width=2), yaxis="y2"))
        fig.add_vline(x=S, line_dash="dash", line_color="gray", annotation_text="Current S")
        fig.add_vline(x=K, line_dash="dot", line_color="orange", annotation_text="Strike K")
        fig.update_layout(
            xaxis_title="Spot Price ($)",
            yaxis_title="Delta",
            yaxis2=dict(title="Gamma", overlaying="y", side="right"),
            legend=dict(orientation="h"),
            height=350,
            margin=dict(t=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Theta Decay vs Time")
        time_range = np.linspace(0.01, T, 200)
        thetas = []
        for t_val in time_range:
            p_tmp = OptionParams(S=S, K=K, T=float(t_val), r=r, sigma=sigma, q=q, option_type=option_type)
            thetas.append(theta(p_tmp))

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=time_range[::-1], y=thetas[::-1],
            name="Theta ($/day)", line=dict(color="#F44336", width=2),
            fill="tozeroy", fillcolor="rgba(244,67,54,0.1)",
        ))
        fig2.update_layout(
            xaxis_title="Time to Expiry (years)",
            yaxis_title="Theta ($/day)",
            height=350,
            margin=dict(t=20),
        )
        st.plotly_chart(fig2, use_container_width=True)


# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — Price Heatmap
# ──────────────────────────────────────────────────────────────────────────────

with tab2:
    st.header("Option Price Heatmap — Spot × Volatility")
    st.caption("Each cell shows the BSM price for that (Spot, Volatility) combination.")

    h_col1, h_col2 = st.columns(2)
    with h_col1:
        spot_min_pct = st.slider("Spot Range — Min (%)", 50, 99, 70, key="hm_spot_min")
        spot_max_pct = st.slider("Spot Range — Max (%)", 101, 200, 130, key="hm_spot_max")
    with h_col2:
        vol_min = st.slider("Vol Range — Min (%)", 1, 50, 5, key="hm_vol_min")
        vol_max = st.slider("Vol Range — Max (%)", 10, 200, 60, key="hm_vol_max")

    n_grid = 20
    spots = np.linspace(S * spot_min_pct / 100, S * spot_max_pct / 100, n_grid)
    vols = np.linspace(vol_min / 100, vol_max / 100, n_grid)

    price_grid = np.zeros((len(vols), len(spots)))
    for i, vol in enumerate(vols):
        for j, spot in enumerate(spots):
            p_tmp = OptionParams(S=float(spot), K=K, T=T, r=r, sigma=float(vol), q=q, option_type=option_type)
            price_grid[i, j] = price(p_tmp)

    fig_hm = go.Figure(data=go.Heatmap(
        z=price_grid,
        x=[f"${s:.1f}" for s in spots],
        y=[f"{v*100:.0f}%" for v in vols],
        colorscale="Viridis",
        colorbar=dict(title="Price ($)"),
        hovertemplate="Spot: %{x}<br>Vol: %{y}<br>Price: $%{z:.4f}<extra></extra>",
    ))
    # Mark current parameters
    current_spot_label = f"${S:.1f}"
    current_vol_label = f"{sigma*100:.0f}%"
    fig_hm.update_layout(
        xaxis_title="Spot Price",
        yaxis_title="Volatility",
        height=500,
        margin=dict(t=10),
    )
    st.plotly_chart(fig_hm, use_container_width=True)

    # Downloadable table
    with st.expander("📥 Download Price Table"):
        df_hm = pd.DataFrame(
            price_grid,
            index=[f"{v*100:.1f}%" for v in vols],
            columns=[f"${s:.2f}" for s in spots],
        )
        st.dataframe(df_hm.round(4), use_container_width=True)
        csv = df_hm.to_csv().encode()
        st.download_button("Download CSV", csv, "bsm_price_heatmap.csv", "text/csv")


# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 — P&L Profile
# ──────────────────────────────────────────────────────────────────────────────

with tab3:
    st.header("P&L Profile — Long Option Position")

    pnl_spots = np.linspace(S * 0.5, S * 1.5, 300)

    # Three time horizons
    t_now = T
    t_mid = T / 2
    t_expiry = 0.0

    fig_pnl = go.Figure()

    for t_horizon, label, color in [
        (t_now, f"Today (T={T:.2f}y)", "#2196F3"),
        (t_mid, f"Midway (T={T/2:.2f}y)", "#FF9800"),
        (t_expiry, "At Expiry (T=0)", "#F44336"),
    ]:
        pnl_vals = []
        for s in pnl_spots:
            if t_horizon == 0:
                # Use intrinsic value
                if option_type == "call":
                    val = max(s - K, 0.0)
                else:
                    val = max(K - s, 0.0)
            else:
                p_tmp = OptionParams(S=float(s), K=K, T=t_horizon, r=r, sigma=sigma, q=q, option_type=option_type)
                val = price(p_tmp)
            pnl_vals.append(val - option_price)

        fig_pnl.add_trace(go.Scatter(
            x=pnl_spots, y=pnl_vals,
            name=label,
            line=dict(color=color, width=2),
        ))

    # Break-even line
    fig_pnl.add_hline(y=0, line_dash="dash", line_color="white", line_width=1)
    fig_pnl.add_vline(x=S, line_dash="dot", line_color="gray", annotation_text="Current S")
    fig_pnl.add_vline(x=K, line_dash="dot", line_color="orange", annotation_text="Strike K")

    # Shade profit / loss regions at expiry
    pnl_expiry = [max(s - K, 0) - option_price if option_type == "call" else max(K - s, 0) - option_price
                  for s in pnl_spots]
    fig_pnl.add_trace(go.Scatter(
        x=pnl_spots, y=[max(v, 0) for v in pnl_expiry],
        fill="tozeroy", fillcolor="rgba(76,175,80,0.15)", line=dict(width=0), name="Profit zone", showlegend=True,
    ))
    fig_pnl.add_trace(go.Scatter(
        x=pnl_spots, y=[min(v, 0) for v in pnl_expiry],
        fill="tozeroy", fillcolor="rgba(244,67,54,0.15)", line=dict(width=0), name="Loss zone", showlegend=True,
    ))

    fig_pnl.update_layout(
        xaxis_title="Spot Price at Horizon ($)",
        yaxis_title="P&L ($)",
        legend=dict(orientation="h"),
        height=450,
        margin=dict(t=10),
    )
    st.plotly_chart(fig_pnl, use_container_width=True)

    # Stats
    if option_type == "call":
        breakeven = K + option_price
    else:
        breakeven = K - option_price
    max_loss = -option_price
    max_profit = "Unlimited (call)" if option_type == "call" else f"${K - option_price:.2f} (put)"

    c1, c2, c3 = st.columns(3)
    c1.metric("Premium Paid", f"${option_price:.4f}")
    c2.metric("Break-Even at Expiry", f"${breakeven:.2f}")
    c3.metric("Max Loss", f"${max_loss:.4f}")


# ──────────────────────────────────────────────────────────────────────────────
# TAB 4 — Greeks Heatmaps
# ──────────────────────────────────────────────────────────────────────────────

with tab4:
    st.header("Greeks Heatmaps — Spot × Volatility")

    greek_choice = st.selectbox(
        "Select Greek",
        ["delta", "gamma", "vega", "theta", "rho"],
        format_func=lambda x: {"delta": "Δ Delta", "gamma": "Γ Gamma", "vega": "ν Vega",
                                "theta": "Θ Theta", "rho": "ρ Rho"}[x],
    )

    greek_fn = {"delta": delta, "gamma": gamma, "vega": vega, "theta": theta, "rho": rho}[greek_choice]

    g_spots = np.linspace(S * 0.6, S * 1.4, 25)
    g_vols = np.linspace(0.05, 0.80, 25)

    greek_grid = np.zeros((len(g_vols), len(g_spots)))
    for i, vol in enumerate(g_vols):
        for j, spot in enumerate(g_spots):
            p_tmp = OptionParams(S=float(spot), K=K, T=T, r=r, sigma=float(vol), q=q, option_type=option_type)
            greek_grid[i, j] = greek_fn(p_tmp)

    fig_gh = go.Figure(data=go.Heatmap(
        z=greek_grid,
        x=[f"${s:.1f}" for s in g_spots],
        y=[f"{v*100:.0f}%" for v in g_vols],
        colorscale="RdBu" if greek_choice in ("delta", "rho") else "Plasma",
        colorbar=dict(title=greek_choice.capitalize()),
        hovertemplate=f"Spot: %{{x}}<br>Vol: %{{y}}<br>{greek_choice.capitalize()}: %{{z:.5f}}<extra></extra>",
        zmid=0 if greek_choice in ("theta", "rho") else None,
    ))
    fig_gh.update_layout(
        xaxis_title="Spot Price",
        yaxis_title="Volatility",
        height=500,
        margin=dict(t=10),
    )
    st.plotly_chart(fig_gh, use_container_width=True)

    st.caption(f"**{greek_choice.capitalize()}** spatial behaviour for a {option_type} with K=${K}, T={T:.2f}y, r={r*100:.1f}%")


# ──────────────────────────────────────────────────────────────────────────────
# TAB 5 — Implied Volatility Calculator
# ──────────────────────────────────────────────────────────────────────────────

with tab5:
    st.header("Implied Volatility Calculator")

    iv_col1, iv_col2 = st.columns([1, 1])

    with iv_col1:
        st.subheader("Solve for IV")
        market_price_input = st.number_input(
            "Observed Market Price ($)",
            min_value=0.01,
            max_value=float(S),
            value=round(option_price, 2),
            step=0.01,
            help="Enter the market price of the option to back out implied volatility.",
        )

        if st.button("Calculate IV", type="primary"):
            try:
                iv_result = implied_volatility(
                    market_price=market_price_input,
                    p=OptionParams(S=S, K=K, T=T, r=r, sigma=0.25, q=q, option_type=option_type),
                )
                st.success(f"**Implied Volatility: {iv_result * 100:.4f}%**")

                # Verify round-trip
                verification = price(OptionParams(S=S, K=K, T=T, r=r, sigma=iv_result, q=q, option_type=option_type))
                st.caption(f"Verification: BSM price at IV = ${verification:.6f} (input was ${market_price_input:.6f})")
            except (ValueError, RuntimeError) as e:
                st.error(f"IV calculation failed: {e}")

    with iv_col2:
        st.subheader("IV vs Market Price")
        price_range = np.linspace(option_price * 0.3, option_price * 2.5, 100)
        iv_vals = []
        for mp in price_range:
            try:
                iv_v = implied_volatility(
                    market_price=float(mp),
                    p=OptionParams(S=S, K=K, T=T, r=r, sigma=0.25, q=q, option_type=option_type),
                )
                iv_vals.append(iv_v * 100)
            except Exception:
                iv_vals.append(np.nan)

        fig_iv = go.Figure()
        fig_iv.add_trace(go.Scatter(
            x=price_range, y=iv_vals,
            name="Implied Vol",
            line=dict(color="#9C27B0", width=2),
        ))
        fig_iv.add_vline(x=option_price, line_dash="dash", line_color="gray", annotation_text="BSM price")
        fig_iv.update_layout(
            xaxis_title="Market Price ($)",
            yaxis_title="Implied Volatility (%)",
            height=300,
            margin=dict(t=10),
        )
        st.plotly_chart(fig_iv, use_container_width=True)

    # Volatility smile
    st.subheader("Volatility Smile")
    st.caption("IV for different strikes at current market price (assumes flat market price curve — illustrative).")

    smile_strikes = np.linspace(S * 0.7, S * 1.3, 25)
    smile_ivs = []
    for k_val in smile_strikes:
        try:
            p_atm = OptionParams(S=S, K=float(k_val), T=T, r=r, sigma=sigma, q=q, option_type=option_type)
            theoretical_mp = price(p_atm)
            # Add a small vol skew to make the smile realistic
            skew = 0.02 * ((S - float(k_val)) / S)
            p_skewed = OptionParams(S=S, K=float(k_val), T=T, r=r, sigma=sigma + skew, q=q, option_type=option_type)
            smile_mp = price(p_skewed)
            iv_s = implied_volatility(
                market_price=smile_mp,
                p=OptionParams(S=S, K=float(k_val), T=T, r=r, sigma=0.25, q=q, option_type=option_type),
            )
            smile_ivs.append(iv_s * 100)
        except Exception:
            smile_ivs.append(np.nan)

    fig_smile = go.Figure()
    fig_smile.add_trace(go.Scatter(
        x=smile_strikes, y=smile_ivs,
        name="Vol Smile",
        line=dict(color="#FF6B35", width=2),
        mode="lines+markers",
        marker=dict(size=5),
    ))
    fig_smile.add_vline(x=S, line_dash="dash", line_color="gray", annotation_text="ATM (S)")
    fig_smile.update_layout(
        xaxis_title="Strike ($)",
        yaxis_title="Implied Volatility (%)",
        height=300,
        margin=dict(t=10),
    )
    st.plotly_chart(fig_smile, use_container_width=True)
