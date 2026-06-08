"""
Black-Scholes Option Pricing Engine
=====================================
Pure-Python implementation of the Black-Scholes-Merton model.

Supports:
    - European call and put pricing
    - Full Greeks: Delta, Gamma, Vega, Theta, Rho
    - Continuous dividend yield (generalised BSM)
    - Implied Volatility via Brent's method

Author: Bhagyesh Soni
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from scipy.stats import norm
from scipy.optimize import brentq


# ──────────────────────────────────────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class OptionParams:
    """Immutable container for BSM input parameters.

    Attributes
    ----------
    S  : Current spot price of the underlying asset ($)
    K  : Strike price ($)
    T  : Time to expiry in years (e.g. 0.5 = 6 months)
    r  : Risk-free interest rate (annualised, decimal; e.g. 0.05 = 5%)
    sigma : Implied/historical volatility (annualised, decimal; e.g. 0.20 = 20%)
    q  : Continuous dividend yield (annualised, decimal; default 0.0)
    option_type : "call" or "put"
    """
    S: float
    K: float
    T: float
    r: float
    sigma: float
    q: float = 0.0
    option_type: Literal["call", "put"] = "call"

    def __post_init__(self) -> None:
        if self.S <= 0:
            raise ValueError("Spot price S must be positive.")
        if self.K <= 0:
            raise ValueError("Strike K must be positive.")
        if self.sigma < 0:
            raise ValueError("Volatility sigma must be non-negative.")
        if self.T < 0:
            raise ValueError("Time to expiry T must be non-negative.")
        if self.option_type not in ("call", "put"):
            raise ValueError("option_type must be 'call' or 'put'.")


# ──────────────────────────────────────────────────────────────────────────────
# Core BSM helpers
# ──────────────────────────────────────────────────────────────────────────────

def _d1_d2(p: OptionParams) -> tuple[float, float]:
    """Compute the BSM d1 and d2 terms."""
    if p.T == 0:
        return math.inf, math.inf
    d1 = (math.log(p.S / p.K) + (p.r - p.q + 0.5 * p.sigma ** 2) * p.T) / (
        p.sigma * math.sqrt(p.T)
    )
    d2 = d1 - p.sigma * math.sqrt(p.T)
    return d1, d2


# ──────────────────────────────────────────────────────────────────────────────
# Pricing
# ──────────────────────────────────────────────────────────────────────────────

def price(p: OptionParams) -> float:
    """Black-Scholes-Merton option price (with continuous dividend yield).

    Parameters
    ----------
    p : OptionParams

    Returns
    -------
    float : Option price in the same currency as S and K.
    """
    if p.T == 0:
        if p.option_type == "call":
            return max(p.S - p.K, 0.0)
        return max(p.K - p.S, 0.0)

    d1, d2 = _d1_d2(p)
    disc_r = math.exp(-p.r * p.T)
    disc_q = math.exp(-p.q * p.T)

    if p.option_type == "call":
        return p.S * disc_q * norm.cdf(d1) - p.K * disc_r * norm.cdf(d2)
    else:
        return p.K * disc_r * norm.cdf(-d2) - p.S * disc_q * norm.cdf(-d1)


# ──────────────────────────────────────────────────────────────────────────────
# Greeks
# ──────────────────────────────────────────────────────────────────────────────

def delta(p: OptionParams) -> float:
    """First derivative of option price w.r.t. spot (Δ).

    Range: [0, 1] for calls; [-1, 0] for puts.
    """
    if p.T == 0:
        if p.option_type == "call":
            return 1.0 if p.S > p.K else 0.0
        return -1.0 if p.S < p.K else 0.0

    d1, _ = _d1_d2(p)
    disc_q = math.exp(-p.q * p.T)
    if p.option_type == "call":
        return disc_q * norm.cdf(d1)
    return disc_q * (norm.cdf(d1) - 1)


def gamma(p: OptionParams) -> float:
    """Second derivative of option price w.r.t. spot (Γ).

    Same for calls and puts.
    """
    if p.T == 0 or p.sigma == 0:
        return 0.0
    d1, _ = _d1_d2(p)
    disc_q = math.exp(-p.q * p.T)
    return disc_q * norm.pdf(d1) / (p.S * p.sigma * math.sqrt(p.T))


def vega(p: OptionParams) -> float:
    """Sensitivity to a 1% change in volatility (ν).

    Returned as price change per 1% vol move (divide by 100 internally for
    the raw ∂V/∂σ expression).
    """
    if p.T == 0:
        return 0.0
    d1, _ = _d1_d2(p)
    disc_q = math.exp(-p.q * p.T)
    return p.S * disc_q * norm.pdf(d1) * math.sqrt(p.T) / 100.0


def theta(p: OptionParams) -> float:
    """Time decay: change in option price per calendar day (Θ).

    Negative for long options (time erodes value).
    """
    if p.T == 0:
        return 0.0
    d1, d2 = _d1_d2(p)
    disc_r = math.exp(-p.r * p.T)
    disc_q = math.exp(-p.q * p.T)

    term1 = -(p.S * disc_q * norm.pdf(d1) * p.sigma) / (2 * math.sqrt(p.T))

    if p.option_type == "call":
        term2 = -p.r * p.K * disc_r * norm.cdf(d2)
        term3 = p.q * p.S * disc_q * norm.cdf(d1)
    else:
        term2 = p.r * p.K * disc_r * norm.cdf(-d2)
        term3 = -p.q * p.S * disc_q * norm.cdf(-d1)

    # Return per-day theta
    return (term1 + term2 + term3) / 365.0


def rho(p: OptionParams) -> float:
    """Sensitivity to a 1% change in the risk-free rate (ρ).

    Returned as price change per 1% rate move.
    """
    if p.T == 0:
        return 0.0
    _, d2 = _d1_d2(p)
    disc_r = math.exp(-p.r * p.T)

    if p.option_type == "call":
        return p.K * p.T * disc_r * norm.cdf(d2) / 100.0
    return -p.K * p.T * disc_r * norm.cdf(-d2) / 100.0


def all_greeks(p: OptionParams) -> dict[str, float]:
    """Return all five Greeks as a dict."""
    return {
        "delta": delta(p),
        "gamma": gamma(p),
        "vega": vega(p),
        "theta": theta(p),
        "rho": rho(p),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Implied Volatility
# ──────────────────────────────────────────────────────────────────────────────

def implied_volatility(
    market_price: float,
    p: OptionParams,
    tol: float = 1e-8,
    max_iter: int = 200,
) -> float:
    """Compute implied volatility using Brent's root-finding method.

    Parameters
    ----------
    market_price : float
        Observed market price of the option.
    p : OptionParams
        Option parameters (sigma field is ignored; IV is what we solve for).
    tol : float
        Convergence tolerance on price.
    max_iter : int
        Maximum iterations for Brent's method.

    Returns
    -------
    float : Implied volatility (annualised decimal).

    Raises
    ------
    ValueError : If the market price is outside arbitrage bounds.
    RuntimeError : If the solver fails to converge.
    """
    # Arbitrage bounds
    disc_r = math.exp(-p.r * p.T)
    disc_q = math.exp(-p.q * p.T)

    if p.option_type == "call":
        lower_bound = max(p.S * disc_q - p.K * disc_r, 0.0)
    else:
        lower_bound = max(p.K * disc_r - p.S * disc_q, 0.0)

    upper_bound = p.S if p.option_type == "call" else p.K * disc_r

    if not (lower_bound - 1e-6 <= market_price <= upper_bound + 1e-6):
        raise ValueError(
            f"Market price {market_price:.4f} outside arbitrage bounds "
            f"[{lower_bound:.4f}, {upper_bound:.4f}]."
        )

    def objective(sigma: float) -> float:
        params = OptionParams(
            S=p.S, K=p.K, T=p.T, r=p.r, sigma=sigma, q=p.q,
            option_type=p.option_type,
        )
        return price(params) - market_price

    try:
        iv = brentq(objective, 1e-6, 10.0, xtol=tol, maxiter=max_iter)
    except ValueError as exc:
        raise RuntimeError(
            "Brent's method failed to bracket the root. "
            "Check inputs are reasonable."
        ) from exc

    return float(iv)


# ──────────────────────────────────────────────────────────────────────────────
# Convenience: P&L profile
# ──────────────────────────────────────────────────────────────────────────────

def pnl_at_expiry(p: OptionParams, premium_paid: float, spot_range: list[float]) -> list[float]:
    """Compute P&L of a long option position at expiry for a range of spot prices.

    Parameters
    ----------
    p : OptionParams (T field is irrelevant; uses intrinsic value)
    premium_paid : float  The original premium paid for the option.
    spot_range : list of floats  Spot prices to evaluate.

    Returns
    -------
    list of floats : P&L values corresponding to spot_range.
    """
    results = []
    for s in spot_range:
        if p.option_type == "call":
            intrinsic = max(s - p.K, 0.0)
        else:
            intrinsic = max(p.K - s, 0.0)
        results.append(intrinsic - premium_paid)
    return results
