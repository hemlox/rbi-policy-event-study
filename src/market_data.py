import pandas as pd
import yfinance as fin
import os
def fetch_index_data(ticker_symbol, start_date, end_date):
    
       tick = fin.Ticker(ticker_symbol)
       df = tick.history(interval = '1d', start = start_date, end = end_date)
       df["Intraday_pct_change"] = ((df["Close"]-df["Open"])/df["Open"])*100
       df["Ticker"] = ticker_symbol
       return df
if __name__ == "__main__":   
    tickers =["^NSEBANK","^CNXAUTO","^CNXIT","^CNXFMCG","^CNXPHARMA","^CNXMETAL","^CNXREALTY","^CNXENERGY","^CNXMEDIA","^CNXPSUBANK","NIFTY_FIN_SERVICE.NS","NIFTY_PVT_BANK.NS"]
    frames=[]
    for ticker in tickers:
          df = fetch_index_data(ticker, "2016-09-01", "2026-03-16" )
          frames.append(df)
    df = pd.concat(frames)
    df.to_csv(path_or_buf = "data/raw_market_data.csv")
    
   