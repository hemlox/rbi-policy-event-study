import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
import json

sectoral_tickers =["^NSEBANK","^CNXAUTO","^CNXIT","^CNXFMCG","^CNXPHARMA","^CNXPSUBANK", "^CNXREALTY","^CNXENERGY"]
benchmark_ticker ="^NSEI"

def Z_value_of_sentiment_scores():
    with open ("data/final_sentiment_score_1.json", "r") as file:
        raw_sentiments = json.load(file)

    df_sentiment = pd.DataFrame(list(raw_sentiments.items()), columns =["filename", "raw_score"])
    types, date = [], []
    for filename in df_sentiment["filename"]:
        doc_type = filename[:3]
        types.append(doc_type)
        date_str = filename[-14:-4]
        date_obj = pd.to_datetime(date_str, format="%d-%m-%Y")
        date.append(date_obj)

    df_sentiment["types"] = types
    df_sentiment["date"] = date
    df_gov = df_sentiment[df_sentiment['types'] == 'gov'].copy()
    df_mpc = df_sentiment[df_sentiment['types'] == 'mpc'].copy()

    df_gov["Z_Score"] = (df_gov["raw_score"]-df_gov["raw_score"].mean())/df_gov["raw_score"].std()
    #the Z value of a give quantity is given by (value-mean)/standard deviation and is a measure of the number of standard variations the pint is from the meann
    df_mpc["Z_Score"] = (df_mpc["raw_score"]-df_mpc["raw_score"].mean())/df_mpc["raw_score"].std()

    df_sentiment = pd.concat([df_gov,df_mpc])
    df_daily = df_sentiment.groupby('date', as_index=False)['Z_Score'].mean()#if mpc and gov statement released on the same day
    df_daily = df_daily.sort_values(by="date")
    df_daily["delta_sentiment"] = df_daily["Z_Score"].diff()
    return df_daily

df_daily = Z_value_of_sentiment_scores()

#In a market model the actual rate of return is alpha(return independednt of market) +beta(sennsitivity of the stock wrt market)*return of market 
#                                                                                             +random error (ABNORMAL RATE OOF RETURN
#When considering intraday trading alpha for all intents and purposes is considered to be zero.
#beta is calculated by dividing the covariance of the stock and the benchmark/market with the variance of the market/benchmark itself
#return of the market we take as that  days intraday pct change and actual ror  is that days intradaypctchange for that stock
#so we finally get the ABNORMAL RATE OF RETURN using actual-expected se

def ARR_calc():
    df_stocks = pd.read_csv("data/raw_market_data.csv")
    df_stocks["Date"] = pd.to_datetime(df_stocks['Date']).dt.tz_localize(None)
    df_stocks = df_stocks.sort_values(by=["Ticker", "Date"])
    df_benchmark = df_stocks[df_stocks['Ticker'] == benchmark_ticker][['Date', 'Intraday_pct_change']].copy()
    df_benchmark = df_benchmark.rename(columns={'Intraday_pct_change': 'Market_Return'})
    df_sectors = pd.merge(df_stocks, df_benchmark, on='Date', how='inner')
    df_sectors = df_sectors.dropna(subset=['Market_Return', 'Intraday_pct_change'])
    # having a static data for a 10 year period was insanely rod didnt reallly work
    #ensure data is strictly sorted for rolling calcs
    df_sectors = df_sectors.sort_values(by=['Ticker', 'Date'])
    
    #calculating rolling 120-day beta to capture market regime shifts (bypassing .apply() to avoid Pandas KeyError)
    processed_groups =[]
    for ticker_name, group in df_sectors.groupby('Ticker'):
        group = group.copy()
        rolling_cov = group['Intraday_pct_change'].rolling(window=120, min_periods=30).cov(group['Market_Return'])
        rolling_var = group['Market_Return'].rolling(window=120, min_periods=30).var()
        group['Rolling_Beta'] = rolling_cov / rolling_var
        group['Expected Return'] = group['Market_Return'] * group['Rolling_Beta']
        processed_groups.append(group)

    #Reconstruct the dataframe safely
    df_sectors = pd.concat(processed_groups)
    
    df_sectors["ARR"] = df_sectors["Intraday_pct_change"] - df_sectors["Expected Return"]
    df_stocks = df_sectors
    return df_stocks, df_sectors

df_stocks, df_sectors = ARR_calc()

def date_cleaner(df_daily, df_stocks):
    # Precision fix to prevent MergeError
    df_daily['date'] = pd.to_datetime(df_daily['date']).astype('datetime64[ns]')
    df_stocks['Date'] = pd.to_datetime(df_stocks['Date']).astype('datetime64[ns]')
    
    df_daily = df_daily.sort_values('date')
    df_stocks = df_stocks.sort_values('Date')
    trading_days = pd.DataFrame({'Trading_Date': df_stocks['Date'].dropna().drop_duplicates().sort_values()})
# Mapping the RBI Event to the Market Calendar
    df_mapped_events = pd.merge_asof(left=df_daily,right=trading_days,left_on='date',right_on='Trading_Date',direction='forward')
    df_merged = pd.merge(left=df_stocks,right=df_mapped_events,left_on='Date',right_on='Trading_Date',how='inner')
# dropping first doc cuz of NaN
    df_merged = df_merged.dropna(subset=['delta_sentiment', 'ARR'])
    return df_merged

df_merged = date_cleaner(df_daily, df_stocks)
results = []
raw_p_values =[]

for ticker in sectoral_tickers:
    sector_data = df_merged[df_merged['Ticker'] == ticker]
    if not sector_data.empty:
        model = smf.ols('ARR ~ delta_sentiment', data=sector_data).fit()
        beta = model.params['delta_sentiment'] 
        p_val = model.pvalues['delta_sentiment'] 
        results.append({
            'Ticker': ticker,
            'Beta_Sensitivity': beta,
            'P-Value_Raw': p_val
        })
        raw_p_values.append(p_val)
results_df = pd.DataFrame(results)
#Benjamini-Hochberg False Discovery Rate correction
if not results_df.empty:
    reject_null, pvals_corrected, _, _ = multipletests(raw_p_values, alpha=0.05, method='fdr_bh')
    results_df['P-Value_Corrected'] = pvals_corrected
    results_df['Is_Significant'] = reject_null 

print(results_df.sort_values(by='P-Value_Corrected'))
