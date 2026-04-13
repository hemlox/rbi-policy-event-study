# Quantitative Analysis of RBI Forward Guidance

## Project Overview
The goal of this project was to determine if it was possible to predict the impact of RBI's Monetary Policy Committee (MPC) resolutions and the governor's statements on various sectoral indices of the Indian Stock Exchange.

Instead of relying solely on official repo-rate changes, this project analyzes the sentiment of the forward guidance within the statements to see if it drives stock prices. The complete analysis, validation, and final results are detailed in `notebooks/Final_Report.ipynb`.

## Project Structure
```text
rbi-policy-analysis/
│
├── data/                          # gitignored
│   ├── final_sentiment_score.json
│   ├── raw_market_data.csv
│   ├── regression_results.csv
│   └── processed_merged.csv
│
├── artifacts/                     # gitignored
│   └── (extracted MPC and governor statements)
│
├── src/
│   ├── __init__.py
│   ├── scraper.py
│   ├── market_data.py
│   ├── nlp_engine.py
│   └── statistics.py
│
├── notebooks/
│   └── Final_Report.ipynb
│
├── requirements.txt
└── README.md
```

## Methodology

1. **Data Collection (`src/scraper.py`)**
   The RBI website uses legacy ASP.NET architecture with hidden JavaScript pagination. I built a headless Selenium scraper to bypass this and download 10 years of policy PDFs.

2. **Market Data (`src/market_data.py`)**
   Intraday data for 8 Nifty sectoral indices and the Nifty 50 benchmark was extracted using the `yfinance` library.

3. **Sentiment Analysis (`src/nlp_engine.py`)**
   Text was extracted from PDFs using `PyMuPDF` and split into sentence-level chunks. I used a zero-shot classification model (`facebook/bart-large-mnli`) to score the statements as hawkish, dovish, or neutral. Ambiguous chunks were filtered out using Shannon's Entropy, and a final document score was calculated using a neutral-penalized weighted mean.

4. **Statistical Testing (`src/statistics.py`)**
   This module handles the final analysis:
   - Aligning sentiment dates with trading days using forward-filling.
   - Calculating the Abnormal Rate of Return (ARR) using a 120-day rolling beta against the Nifty 50.
   - Running OLS regressions to find the correlation between sentiment and ARR.
   - Applying the Benjamini-Hochberg correction to adjust p-values for multiple comparisons.

## Future Work
- Implementing a `main.py` entry point to automate the entire pipeline from scraping to statistics.
- Fine-tuning a model specifically on the RBI corpus to improve sentiment accuracy.
- Using high-frequency tick data to isolate the immediate volatility shock following a release.

## Tech Stack
- **Languages:** Python
- **Libraries:** Selenium, Pandas, yfinance, PyMuPDF, PyTorch, HuggingFace Transformers, SciPy, statsmodels, Matplotlib, Seaborn