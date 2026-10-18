"""
Multi-Asset Portfolio Valuation & Visual Analytics Engine
Description: Downloads historical market data, calculates daily position values
and aggregate portfolio equity, and generates an institutional dual-panel tear-sheet.
"""

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# 1. PORTFOLIO CONFIGURATION (Holdings & Allocation)
PORTFOLIO_HOLDINGS = {
    "MAR": 50,    # Marriott International
    "EXPE": 75,   # Expedia Group
    "AAPL": 40,   # Apple
    "MSFT": 30,   # Microsoft
    "AMZN": 60    # Amazon
}

START_DATE = "2025-01-01"
tickers = list(PORTFOLIO_HOLDINGS.keys())

print(f"📡 Downloading market data for: {tickers} from {START_DATE}...")
raw_data = yf.download(tickers, start=START_DATE, progress=False)
close_prices = raw_data["Close"]

# 2. CALCULATE DAILY VALUE OF EACH POSITION ($ USD)
position_values = pd.DataFrame()
for ticker_sym, shares in PORTFOLIO_HOLDINGS.items():
    position_values[ticker_sym] = close_prices[ticker_sym] * shares

position_values["Total_Portfolio_Value"] = position_values.sum(axis=1)

# 3. EXECUTIVE PERFORMANCE METRICS
initial_val = position_values["Total_Portfolio_Value"].iloc[0]
current_val = position_values["Total_Portfolio_Value"].iloc[-1]
net_gain = current_val - initial_val
total_return_pct = (net_gain / initial_val) * 100

print(f"Initial Investment: ${initial_val:,.2f} USD")
print(f"Current Valuation:  ${current_val:,.2f} USD")
print(f"Total Cumulative Return: {total_return_pct:+.2f}%")

# 4. INSTITUTIONAL VISUAL TEAR-SHEET
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
fig.suptitle("EXECUTIVE PORTFOLIO PERFORMANCE DASHBOARD", fontsize=15, fontweight="bold", y=0.95)

# Panel 1: Aggregate Equity Curve
dates = position_values.index
total_equity = position_values["Total_Portfolio_Value"]
ax1.plot(dates, total_equity, color="#0f4c81", linewidth=2.5, label="Total Equity")
ax1.fill_between(dates, total_equity, total_equity.min() * 0.95, color="#0f4c81", alpha=0.15)
ax1.set_title("Total Portfolio Equity ($ USD)", fontsize=12, fontweight="bold")
ax1.yaxis.set_major_formatter(ticker.StrMethodFormatter("${x:,.0f}"))
ax1.grid(True, linestyle="--", alpha=0.6)
ax1.legend(loc="upper left")

# Panel 2: Normalized Relative Performance (Base = 100)
normalized_prices = (close_prices / close_prices.iloc[0]) * 100
colors = ["#2b5c8f", "#d95f02", "#7570b3", "#e7298a", "#1b9e77"]

for i, ticker_sym in enumerate(tickers):
    ax2.plot(normalized_prices.index, normalized_prices[ticker_sym], label=ticker_sym, linewidth=1.8, color=colors[i % len(colors)])

ax2.axhline(100, color="gray", linestyle=":", linewidth=1.2, label="Baseline (Jan 2025 = 100)")
ax2.set_title("Relative Asset Trajectories (Base = 100)", fontsize=12, fontweight="bold")
ax2.set_xlabel("Date", fontsize=11, fontweight="bold")
ax2.set_ylabel("Growth Index", fontsize=11, fontweight="bold")
ax2.grid(True, linestyle="--", alpha=0.6)
ax2.legend(loc="upper left", ncol=3)

plt.tight_layout(rect=[0, 0.03, 1, 0.93])
plt.show()
