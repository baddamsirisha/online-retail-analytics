"""
Online Retail II - sales & customer analytics
Author: Shirisha Baddam

Pipeline:
  1. Load the raw UCI "Online Retail II" transactions into SQLite.
  2. Clean them with SQL (sql/01_clean.sql).
  3. Run the analysis queries in sql/ and save the results to outputs/tables.
  4. Score customers with RFM (Recency, Frequency, Monetary) and assign segments.
  5. Draw the charts used in the README (outputs/charts).

Run:  python src/analysis.py   (expects data/online_retail_II.csv)
"""
from pathlib import Path
import sqlite3

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "online_retail_II.csv"
SQL = ROOT / "sql"
TABLES = ROOT / "outputs" / "tables"
CHARTS = ROOT / "outputs" / "charts"
TABLES.mkdir(parents=True, exist_ok=True)
CHARTS.mkdir(parents=True, exist_ok=True)

# ---- chart style (one accent hue, recessive grid, text in ink colours) ----
BLUE, SURFACE, INK, INK2, GRID = "#2a78d6", "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
    "axes.titlesize": 13, "axes.axisbelow": True, "axes.titleweight": "bold", "axes.titlelocation": "left",
})
gbp_k = FuncFormatter(lambda v, _: f"£{v/1e3:,.0f}k")
gbp_m = FuncFormatter(lambda v, _: f"£{v/1e6:,.1f}M")


def run(con, name):
    return pd.read_sql_query((SQL / name).read_text(), con)


def main():
    # 1. load raw data
    raw = pd.read_csv(DATA, dtype={"Invoice": str, "StockCode": str})
    raw["InvoiceDate"] = pd.to_datetime(raw["InvoiceDate"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    con = sqlite3.connect(":memory:")
    raw.to_sql("raw", con, index=False)
    print(f"raw rows: {len(raw):,}")

    # 2. clean
    con.executescript((SQL / "01_clean.sql").read_text())
    n_clean = con.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    print(f"clean rows: {n_clean:,} ({n_clean/len(raw):.1%} of raw)")

    # 3. analysis queries
    results = {}
    for q in ["02_kpis", "03_monthly_revenue", "04_countries", "05_top_products",
              "06_rfm_base", "07_cohorts", "08_cancellations"]:
        results[q] = run(con, q + ".sql")
        results[q].to_csv(TABLES / f"{q}.csv", index=False)

    # 4. RFM scoring (quintiles, 5 = best)
    rfm = results["06_rfm_base"].copy()
    rfm["R"] = pd.qcut(rfm["recency_days"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M"] = pd.qcut(rfm["monetary_gbp"], 5, labels=[1, 2, 3, 4, 5]).astype(int)

    def segment(r):
        if r.R >= 4 and r.F >= 4:
            return "Champions"
        if r.R >= 3 and r.F >= 3:
            return "Loyal"
        if r.R >= 4 and r.F <= 2:
            return "New / promising"
        if r.R <= 2 and r.F >= 3:
            return "At risk"
        if r.R <= 2 and r.F <= 2:
            return "Lost / hibernating"
        return "Need attention"

    rfm["segment"] = rfm.apply(segment, axis=1)
    rfm.to_csv(TABLES / "rfm_customers.csv", index=False)
    seg = (rfm.groupby("segment")
              .agg(customers=("customer_id", "count"), revenue_gbp=("monetary_gbp", "sum"),
                   avg_recency_days=("recency_days", "mean"), avg_orders=("frequency", "mean"))
              .sort_values("revenue_gbp", ascending=False))
    seg["customer_share_pct"] = (100 * seg.customers / seg.customers.sum()).round(1)
    seg["revenue_share_pct"] = (100 * seg.revenue_gbp / seg.revenue_gbp.sum()).round(1)
    seg = seg.round(1)
    seg.to_csv(TABLES / "rfm_segments.csv")
    results["segments"] = seg

    # cohort retention matrix (% of each cohort active N months later)
    coh = results["07_cohorts"].pivot(index="cohort", columns="months_since_first", values="customers")
    retention = coh.div(coh[0], axis=0) * 100
    retention.round(1).to_csv(TABLES / "cohort_retention_pct.csv")

    # 5. charts
    charts(results, retention)
    print_summary(results, retention)


def charts(r, retention):
    # monthly revenue
    m = r["03_monthly_revenue"]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(m["month"], m["revenue_gbp"], color=BLUE, linewidth=2, marker="o", markersize=4)
    ax.yaxis.set_major_formatter(gbp_k)
    ax.set_xticks(range(0, len(m), 3), m["month"].iloc[::3], rotation=0)
    peak = m.loc[m.revenue_gbp.idxmax()]
    ax.annotate(f"Peak {peak.month}: £{peak.revenue_gbp/1e3:,.0f}k",
                (m.index[m.revenue_gbp.idxmax()], peak.revenue_gbp),
                textcoords="offset points", xytext=(-150, -5), color=INK2,
                arrowprops=dict(arrowstyle="-", color=INK2))
    ax.set_title("Monthly revenue, Dec 2009 – Nov 2011: strong Q4 seasonality")
    ax.set_ylabel("Revenue")
    fig.tight_layout(); fig.savefig(CHARTS / "monthly_revenue.png", dpi=150); plt.close(fig)

    # top countries excluding UK
    c = r["04_countries"]
    c = c[c.country != "United Kingdom"].head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(c["country"], c["revenue_gbp"], color=BLUE, height=0.6)
    ax.xaxis.set_major_formatter(gbp_k); ax.grid(axis="y", visible=False)
    for y, v in enumerate(c["revenue_gbp"]):
        ax.text(v, y, f"  £{v/1e3:,.0f}k", va="center", color=INK2, fontsize=9)
    ax.set_title("Top 10 export markets by revenue (UK excluded)")
    fig.tight_layout(); fig.savefig(CHARTS / "top_countries.png", dpi=150); plt.close(fig)

    # top products
    p = r["05_top_products"].iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(p["description"].str.title().str.slice(0, 38), p["revenue_gbp"], color=BLUE, height=0.6)
    ax.xaxis.set_major_formatter(gbp_k); ax.grid(axis="y", visible=False)
    ax.set_title("Top 10 products by revenue")
    fig.tight_layout(); fig.savefig(CHARTS / "top_products.png", dpi=150); plt.close(fig)

    # RFM segments: share of customers vs share of revenue (two charts side by side, same scale)
    s = r["segments"].sort_values("revenue_share_pct")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, col, title in [(axes[0], "customer_share_pct", "Share of customers"),
                           (axes[1], "revenue_share_pct", "Share of revenue")]:
        ax.barh(s.index, s[col], color=BLUE, height=0.6)
        ax.set_xlim(0, 100); ax.grid(axis="y", visible=False); ax.set_title(title, fontsize=11)
        for y, v in enumerate(s[col]):
            ax.text(v, y, f"  {v:.0f}%", va="center", color=INK2, fontsize=9)
    fig.suptitle("RFM customer segments", x=0.01, ha="left", fontweight="bold", fontsize=13)
    fig.tight_layout(); fig.savefig(CHARTS / "rfm_segments.png", dpi=150); plt.close(fig)

    # cohort retention heatmap (sequential single hue)
    ret = retention.loc[:, 1:12].iloc[:13]
    fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(ret.values, cmap="Blues", vmin=0, vmax=50, aspect="auto")
    ax.set_xticks(range(ret.shape[1]), ret.columns)
    ax.set_yticks(range(ret.shape[0]), ret.index)
    ax.grid(False)
    for i in range(ret.shape[0]):
        for j in range(ret.shape[1]):
            v = ret.values[i, j]
            if pd.notna(v):
                ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=8,
                        color="white" if v > 30 else INK)
    ax.set_xlabel("Months since first purchase"); ax.set_ylabel("Cohort (first purchase month)")
    ax.set_title("Customer retention by monthly cohort (% of cohort purchasing again)")
    fig.colorbar(im, ax=ax, label="% retained", shrink=0.8)
    fig.tight_layout(); fig.savefig(CHARTS / "cohort_retention.png", dpi=150); plt.close(fig)


def print_summary(r, retention):
    k = r["02_kpis"]; c = r["04_countries"]; s = r["segments"]
    print("\nKPIs by year:\n", k.to_string(index=False))
    print("\nUK share of revenue:", c.loc[c.country == "United Kingdom", "share_pct"].iloc[0], "%")
    print("\nSegments:\n", s.to_string())
    print("\nAvg month-1 retention: %.1f%%" % retention[1].mean())
    print("Avg month-3 retention: %.1f%%" % retention[3].mean())
    print("\nTop products:\n", r["05_top_products"][["description", "revenue_gbp"]].to_string(index=False))
    print("\nHighest cancellation rates:\n", r["08_cancellations"].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
