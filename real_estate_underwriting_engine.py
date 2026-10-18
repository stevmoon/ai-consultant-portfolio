# ==============================================================================
# MULTI-ASSET PORTFOLIO TRACKER ENGINE
# ==============================================================================

import yfinance as yf
import pandas as pd

# 1. PORTFOLIO CONFIGURATION (Share Holdings)
portfolio_holdings = {
    "MAR": 50,    # Marriott International
    "EXPE": 75,   # Expedia Group
    "AAPL": 40,   # Apple
    "MSFT": 30,   # Microsoft
    "AMZN": 60    # Amazon
}

tickers = list(portfolio_holdings.keys())
start_date = "2025-01-01"

print(f"📡 Downloading historical market data for: {tickers} from {start_date}...")

# 2. DOWNLOAD HISTORICAL CLOSING PRICES IN A SINGLE CALL
# yfinance downloads all 5 tickers at once into a multi-column DataFrame:
raw_data = yf.download(tickers, start=start_date, progress=False)

# Extract only the 'Close' prices
close_prices = raw_data["Close"]

# 3. CALCULATE DAILY VALUE OF EACH POSITION ($)
# Position Value = Closing Price * Number of Shares Held
position_values = pd.DataFrame()

for ticker, shares in portfolio_holdings.items():
    position_values[ticker] = close_prices[ticker] * shares

# 4. CALCULATE AGGREGATE TOTAL PORTFOLIO VALUE OVER TIME
# Sum across columns (axis=1) for each day:
position_values["Total_Portfolio_Value"] = position_values.sum(axis=1)

# 5. CALCULATE DAILY PORTFOLIO RETURNS (%)
position_values["Daily_Return_Pct"] = position_values["Total_Portfolio_Value"].pct_change() * 100

# ==============================================================================
# 6. EXECUTIVE SUMMARY & PERFORMANCE REPORT
# ==============================================================================
initial_portfolio_value = position_values["Total_Portfolio_Value"].iloc[0]
current_portfolio_value = position_values["Total_Portfolio_Value"].iloc[-1]
total_dollar_gain = current_portfolio_value - initial_portfolio_value
total_return_pct = (total_dollar_gain / initial_portfolio_value) * 100

print("\n======================= PORTFOLIO VALUATION REPORT =======================")
print(f"Period:                     {start_date} to Present")
print(f"Initial Investment Capital: ${initial_portfolio_value:,.2f} USD")
print(f"Current Portfolio Value:    ${current_portfolio_value:,.2f} USD")
print(f"Total Net P&L:              ${total_dollar_gain:+,.2f} USD")
print(f"Cumulative Return:          {total_return_pct:+.2f}%")
print("==========================================================================")

# 7. PER-ASSET PERFORMANCE BREAKDOWN
print("\n--- INDIVIDUAL ASSET BREAKDOWN (LATEST POSITION VALUES) ---")
latest_prices = close_prices.iloc[-1]
asset_summary = []

for ticker, shares in portfolio_holdings.items():
    current_price = latest_prices[ticker]
    current_val = current_price * shares
    weight_pct = (current_val / current_portfolio_value) * 100
    
    asset_summary.append({
        "Ticker": ticker,
        "Shares": shares,
        "Current Price": f"${current_price:,.2f}",
        "Position Value": f"${current_val:,.2f}",
        "Portfolio Weight": f"{weight_pct:.1f}%"
    })

breakdown_df = pd.DataFrame(asset_summary)
print(breakdown_df.to_string(index=False))

# ==============================================================================
EXECUTIVE PORTFOLIO VISUAL TEAR-SHEET
# ==============================================================================

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Set an institutional, clean aesthetic
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

# Create a 2-Panel Figure (Top: Total Portfolio Equity | Bottom: Individual Stock Trajectories)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
fig.suptitle("EXECUTIVE PORTFOLIO PERFORMANCE DASHBOARD (2025 – PRESENT)", fontsize=16, fontweight="bold", y=0.95)

# ------------------------------------------------------------------------------
# PANEL 1: AGGREGATE TOTAL PORTFOLIO VALUE OVER TIME
# ------------------------------------------------------------------------------
dates = position_values.index
total_val = position_values["Total_Portfolio_Value"]

ax1.plot(dates, total_val, color="#0f4c81", linewidth=2.5, label="Total Portfolio Equity")
ax1.fill_between(dates, total_val, total_val.min() * 0.95, color="#0f4c81", alpha=0.15)

# Formatting Panel 1
ax1.set_title("Total Portfolio Equity ($ USD)", fontsize=13, fontweight="bold", pad=10)
ax1.set_ylabel("Portfolio Value ($ USD)", fontsize=11, fontweight="bold")
ax1.yaxis.set_major_formatter(ticker.StrMethodFormatter("${x:,.0f}"))
ax1.grid(True, linestyle="--", alpha=0.6)
ax1.legend(loc="upper left", frameon=True)

# Highlight Initial vs Current Value with Annotations
initial_pt = (dates[0], total_val.iloc[0])
current_pt = (dates[-1], total_val.iloc[-1])
ax1.scatter([initial_pt[0], current_pt[0]], [initial_pt[1], current_pt[1]], color="#d9534f", s=50, zorder=5)
ax1.annotate(f"Start: ${initial_pt[1]:,.0f}", xy=initial_pt, xytext=(15, -10), textcoords="offset points", fontweight="bold")
ax1.annotate(f"Current: ${current_pt[1]:,.0f}\n(+{total_return_pct:.1f}%)", xy=current_pt, xytext=(-100, 15), textcoords="offset points", fontweight="bold", color="#1b7837")

# ------------------------------------------------------------------------------
# PANEL 2: NORMALIZED ASSET GROWTH (Starting at 100 for apples-to-apples comparison)
# ------------------------------------------------------------------------------
# Normalizing: (Price / Initial_Price) * 100 allows comparing a $300 stock with a $150 stock directly
normalized_prices = (close_prices / close_prices.iloc[0]) * 100

colors = ["#2b5c8f", "#d95f02", "#7570b3", "#e7298a", "#1b9e77"]

for i, ticker_sym in enumerate(tickers):
    ax2.plot(normalized_prices.index, normalized_prices[ticker_sym], label=ticker_sym, linewidth=1.8, color=colors[i % len(colors)])

# Baseline 100 horizontal line (Breakeven)
ax2.axhline(100, color="gray", linestyle=":", linewidth=1.2, label="Baseline (Jan 2025 = 100)")

# Formatting Panel 2
ax2.set_title("Relative Asset Growth (Normalized to 100 at Jan 2025)", fontsize=13, fontweight="bold", pad=10)
ax2.set_xlabel("Date", fontsize=11, fontweight="bold")
ax2.set_ylabel("Growth Index (Base = 100)", fontsize=11, fontweight="bold")
ax2.grid(True, linestyle="--", alpha=0.6)
ax2.legend(loc="upper left", frameon=True, ncol=3)

# Layout adjustment
plt.tight_layout(rect=[0, 0.03, 1, 0.93])
plt.show()
