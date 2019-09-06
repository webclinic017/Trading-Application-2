from urllib.request import *
import json
import pandas as pd
import numpy as np

with urlopen("https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=NSE:SBIN&interval=1min&outputsize=full&apikey=08AXPZ0UQEVKUSD8") as response:
    source = response.read()

finalData={} # This should contain our final output and that is Renko OHLC data
renkoData={} # It contains information on the lastest bar of renko data for the number of stocks we are working on
finalRenko = {}

Position = ''
Symbol = 'SBIN'

n = 14
def ATR(df,n): #df is the DataFrame, n is the period 7,14 ,etc
    df['H-L']=abs(df['High'].astype(float)-df['Low'].astype(float))
    df['H-PC']=abs(df['High'].astype(float)-df['Close'].astype(float).shift(1))
    df['L-PC']=abs(df['Low'].astype(float)-df['Close'].astype(float).shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1)
    df['ATR']=np.nan
    df.ix[n-1,'ATR']=df['TR'][:n-1].mean() #.ix is deprecated from pandas version- 0.19
    for i in range(n,len(df)):
        df['ATR'][i]=(df['ATR'][i-1]*(n-1)+ df['TR'][i])/n
    return

data = json.loads(source)

#json.dumps(data, indent=2)
#print(data)
minute_data = data["Time Series (1min)"]
df = pd.DataFrame.from_dict(minute_data,orient='index')
df.drop(['5. volume'], axis=1, inplace = True)
df.rename(columns = {'1. open':'Open', '2. high':'High', '3. low':'Low', '4. close':'Close'}, inplace = True)

#print(json.dumps(minute_data, indent=2))
ATR(df,14)
df=df[['Open','High','Low','Close','ATR']]
print(df)

renkoData={'BrickSize': 0, 'Open':0.0,'Close':0.0,'Color':''}
renkoData['BrickSize']=round(df['ATR'][-1],2) #This can be set manually as well!
renkoData['Open']=renkoData['BrickSize']+renkoData['Close'] # This can be done the otherway round
renkoData['Color']='SELL'    # Should you choose to do the other way round, please change the color to 'BUY'

finalData=pd.DataFrame(index=None)
finalData['ReOpen']=0.0
finalData['ReHigh']=0.0
finalData['ReLow']=0.0
finalData['ReClose']=0.0
finalData['Color']=''

for index, row in df.iterrows():  # One may choose to use Pure python instead of Iterrows to loop though each n
    # every row to improve performace if datasets are large.
    if renkoData['Open'] > renkoData['Close']:
        while float(row['Close']) > (float(renkoData['Open']) + float(renkoData['BrickSize'])):
            renkoData['Open'] += renkoData['BrickSize']
            renkoData['Close'] += renkoData['BrickSize']
            finalData.loc[index] = row
            finalData['ReOpen'].loc[index] = renkoData['Close']
            finalData['ReHigh'].loc[index] = renkoData['Open']
            finalData['ReLow'].loc[index] = renkoData['Close']
            finalData['ReClose'].loc[index] = renkoData['Open']
            finalData['Color'].loc[index] = 'BUY'

        while float(row['Close']) < float((renkoData['Close']) - float(renkoData['BrickSize'])):
            renkoData['Open'] -= renkoData['BrickSize']
            renkoData['Close'] -= renkoData['BrickSize']
            finalData.loc[index] = row
            finalData['ReOpen'].loc[index] = renkoData['Open']
            finalData['ReHigh'].loc[index] = renkoData['Open']
            finalData['ReLow'].loc[index] = renkoData['Close']
            finalData['ReClose'].loc[index] = renkoData['Close']
            finalData['Color'].loc[index] = 'SELL'

    else:
        while float(row['Close']) < float((renkoData['Open']) - float(renkoData['BrickSize'])):
            renkoData['Open'] -= renkoData['BrickSize']
            renkoData['Close'] -= renkoData['BrickSize']
            finalData.loc[index] = row
            finalData['ReOpen'].loc[index] = renkoData['Close']
            finalData['ReHigh'].loc[index] = renkoData['Close']
            finalData['ReLow'].loc[index] = renkoData['Open']
            finalData['ReClose'].loc[index] = renkoData['Open']
            finalData['Color'].loc[index] = 'SELL'

        while float(row['Close']) > float((renkoData['Close']) + float(renkoData['BrickSize'])):
            renkoData['Open'] += renkoData['BrickSize']
            renkoData['Close'] += renkoData['BrickSize']
            finalData.loc[index] = row
            finalData['ReOpen'].loc[index] = renkoData['Open']
            finalData['ReHigh'].loc[index] = renkoData['Close']
            finalData['ReLow'].loc[index] = renkoData['Open']
            finalData['ReClose'].loc[index] = renkoData['Close']
            finalData['Color'].loc[index] = 'BUY'

print(finalData)
finalData['SMA'] = finalData.ReClose.rolling(10).mean()
finalData['TMA'] = finalData.SMA.rolling(10).mean()
print(finalData)

#"Symbol","Open", "Close", "Signal", "Position", "SMA", "TMA"

finalRenko = {'Symbol': '','Open':0, 'Close':0, 'Signal':'', 'Position':'', 'SMA':0, 'TMA':0}
finalRenko['Symbol'] = Symbol
finalRenko['Position'] = Position
finalRenko['Open'] = finalData['ReOpen']
finalRenko['Close'] = finalData['ReClose']
finalRenko['Signal'] = finalData['Color']
finalRenko['SMA'] = finalData['SMA']
finalRenko['TMA'] = finalData['TMA']
#finalRenko=finalRenko[['Symbol','Open','Close','Signal','Position','SMA','TMA']]
finalRenkodf = pd.DataFrame(finalRenko,index=None)
print(finalRenkodf)