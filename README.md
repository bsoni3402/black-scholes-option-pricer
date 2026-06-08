# Black-Scholes Option Pricer

An interactive web dashboard for pricing European options using the **Black-Scholes-Merton (BSM)** model, featuring all five Greeks, 2D price/Greek heatmaps, P&L profiles, and an Implied Volatility solver.

Built with Python, Streamlit, and Plotly.

---

## Live Demo

Deploy to [Streamlit Cloud](https://share.streamlit.io) for a free public URL — push the repo, connect it, and the app is live in under a minute.

---

## Features

**Greeks Dashboard**
- All five option Greeks (Delta, Gamma, Vega, Theta, Rho) with a dollar-impact table
- Delta & Gamma vs Spot chart with dual y-axis
- Theta decay curve across the option's remaining life

**Price Heatmap**
- 2D heatmap of option price across Spot × Volatility space
- Configurable axis ranges; full price table exportable as CSV

**P&L Profile**
- Long option P&L at three time horizons: today, midway, and expiry
- Profit and loss zones shaded; break-even and max loss displayed automatically

**Greeks Heatmaps**
- Spatial view of any Greek (Δ, Γ, ν, Θ, ρ) across a 25×25 Spot × Volatility grid

**Implied Volatility Calculator**
- Back out IV from any observed market price using Brent's root-finding method
- IV vs Market Price curve and a volatility smile chart across strike space

---

## Project Structure

```
black_scholes_option_pricer/
├── app.py                   # Streamlit dashboard (5 tabs)
├── black_scholes_engine.py  # Standalone BSM pricing engine
├── requirements.txt
└── README.md
```

The engine (`black_scholes_engine.py`) is fully decoupled from the UI and can be imported directly into any Python script or Jupyter notebook.

---

## Tech Stack

| Library | Purpose |
|---------|---------|
| Python 3.11+ | Core language |
| Streamlit | Interactive web UI |
| Plotly | Charts and heatmaps |
| SciPy | Brent's method for IV solving |
| NumPy / Pandas | Numerical computing and tabular display |

---

## Installation

```bash
# Clone the repository
git clone https://github.com/bhagyeshsoni03/black-scholes-option-pricer.git
cd black-scholes-option-pricer

# Install dependencies
pip install -r requirements.txt

# Run
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Model

This implementation uses the generalised Black-Scholes-Merton formula supporting a continuous dividend yield `q`.

**Call:**  C = S·e^(−qT)·N(d₁) − K·e^(−rT)·N(d₂)

**Put:**   P = K·e^(−rT)·N(−d₂) − S·e^(−qT)·N(−d₁)

Where:

d₁ = [ln(S/K) + (r − q + σ²/2)·T] / (σ√T),  d₂ = d₁ − σ√T

**Greeks:**

| Greek | Definition | Interpretation |
|-------|-----------|----------------|
| Delta (Δ) | ∂V/∂S | Price change per $1 move in spot |
| Gamma (Γ) | ∂²V/∂S² | Rate of change of Delta |
| Vega (ν) | ∂V/∂σ ÷ 100 | Price change per 1% move in volatility |
| Theta (Θ) | −∂V/∂T ÷ 365 | Price decay per calendar day |
| Rho (ρ) | ∂V/∂r ÷ 100 | Price change per 1% move in the risk-free rate |

---

## Validation

The engine is validated against known analytical results:

- Put-call parity holds to machine precision across all inputs
- IV round-trip accuracy: `IV(BSM_price) == σ` to 1×10⁻⁸ tolerance
- Correct intrinsic values at expiry (T = 0)

---

## Using the App

### Overview

The sidebar controls all inputs. Every chart and metric updates live as you adjust parameters — there is no submit button. The five tabs are independent views into the same priced option.

### Input Parameters

| Parameter | What it represents | Typical range |
|-----------|-------------------|---------------|
| Option type | Call (right to buy) or Put (right to sell) | — |
| Spot price (S) | Current market price of the underlying | e.g. $100 |
| Strike price (K) | Price at which the option can be exercised | e.g. $100 |
| Time to expiry (T) | Remaining life in years | 0.01 – 2.0 |
| Risk-free rate (r) | Annualised risk-free rate (e.g. US T-bill) | 0–10% |
| Volatility (σ) | Annualised implied or historical vol | 5–100% |
| Dividend yield (q) | Continuous dividend yield of the underlying | 0–10% |

### Tab-by-Tab Guide

**Tab 1 — Greeks Dashboard**

Start here. The metric cards at the top show the live option price and all five Greeks. The dollar-impact table translates each Greek into a concrete dollar move — for example, a Delta of 0.55 means the option gains roughly $0.55 for every $1 rise in spot. The dual-axis chart shows how Delta and Gamma evolve across the spot range, illustrating the convexity of the position. The Theta decay chart shows how the option bleeds value over time — notice it accelerates sharply near expiry for ATM options.

**Tab 2 — Price Heatmap**

The heatmap shows option price as a function of spot and volatility simultaneously. Darker regions (higher price) move diagonally — a useful way to visualise how both the underlying and vol surface affect value. Adjust the axis ranges with the sliders to zoom into the region of interest, then download the full grid as CSV for further analysis.

**Tab 3 — P&L Profile**

This tab prices the option at three points in time: now, halfway to expiry, and at expiry. The expiry line is the familiar hockey-stick payoff. The earlier lines show time value — the premium above intrinsic value that decays as the option approaches expiry. The shaded zones make profit and loss regions immediately clear. Break-even is marked automatically.

**Tab 4 — Greeks Heatmaps**

Select any Greek from the dropdown and view it across the full Spot × Volatility grid. Gamma, for example, peaks sharply at-the-money when volatility is low — this is the region of maximum convexity risk, important for delta-hedging strategies. Vega is highest for ATM options with more time remaining and diminishes as the option moves deep in- or out-of-the-money.

**Tab 5 — Implied Volatility Calculator**

Enter an observed market price to back out the implied volatility. This is the vol the market is "pricing in" — distinct from realised historical vol. The IV vs Price curve shows the relationship across a price range. The volatility smile chart plots IV across strikes for a fixed spot and expiry, illustrating how market-implied vol is not flat (as BSM assumes) but typically higher for deep ITM and OTM options.

### Worked Example: Pricing an ATM Call

Use these parameters to replicate a standard textbook result:

- Spot = 100, Strike = 100 (at-the-money)
- T = 0.5 (6 months), r = 5%, σ = 20%, q = 0%

Expected output: call price ≈ $6.89, Delta ≈ 0.56, Gamma ≈ 0.019, Theta ≈ −$0.026/day.

Switching to a put with the same parameters gives ≈ $4.42. The difference (6.89 − 4.42 = 2.47) equals S − K·e^(−rT) = 100 − 100·e^(−0.025) ≈ 2.47, confirming put-call parity.

---

## Deployment

1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in
3. Select the repository and set `app.py` as the entry point
4. Click Deploy — a public URL is generated automatically

---

## License

MIT License — free to use, modify, and distribute.

---

Bhagyesh Soni — [github.com/bhagyeshsoni03](https://github.com/bhagyeshsoni03)
