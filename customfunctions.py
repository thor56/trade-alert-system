import pandas as pd
import numpy as np

import sqlite3
import os


def get_pivots(df, symbol):
    data = df
    data['swings'] = np.nan
    df_name = pd.read_excel('FinalList.xlsx', engine='openpyxl')
    data['SymbolDb'] = str(df_name.loc[df_name['symbol_id']
                                       == symbol, 'SymbolDb'].values[0]).replace(" ", "")

    pivot = data.iloc[0].price_open

    last_pivot_id = 0
    up_down = 0

    diff = 0

    for i in range(0, len(data)):
        row = data.iloc[i]

        # We don't have a trend yet
        if up_down == 0:
            if row.price_low < pivot - diff:
                data.loc[i, 'swings'] = row.price_low - pivot
                pivot, last_pivot_id = row.price_low, i
                data.loc[i, 'swing_price'] = row.price_low
                up_down = -1
            elif row.price_high > pivot + diff:
                data.loc[i, 'swings'] = row.price_high - pivot
                pivot, last_pivot_id = row.price_high, i
                data.loc[i, 'swing_price'] = row.price_high

                up_down = 1

        # Current trend is up
        elif up_down == 1:
            # If got price_higher than last pivot, update the swing
            if row.price_high > pivot:
                # Remove the last pivot, as it wasn't a real one
                data.loc[i, 'swings'] = data.loc[last_pivot_id, 'swings'] + \
                    (row.price_high - data.loc[last_pivot_id, 'price_high'])
                data.loc[i, 'swing_price'] = row.price_high
                data.loc[last_pivot_id, 'swing_price'] = np.nan
                data.loc[last_pivot_id, 'swings'] = np.nan
                pivot, last_pivot_id = row.price_high, i

            elif row.price_low < pivot - diff:
                data.loc[i, 'swings'] = row.price_low - pivot
                pivot, last_pivot_id = row.price_low, i
                data.loc[i, 'swing_price'] = row.price_low
                # Change the trend indicator
                up_down = -1

        # Current trend is down
        elif up_down == -1:
            # If got price_lower than last pivot, update the swing
            if row.price_low < pivot:
                # Remove the last pivot, as it wasn't a real one
                data.loc[i, 'swings'] = data.loc[last_pivot_id, 'swings'] + \
                    (row.price_low - data.loc[last_pivot_id, 'price_low'])
                data.loc[i, 'swing_price'] = row.price_low
                data.loc[last_pivot_id, 'swings'] = np.nan
                data.loc[last_pivot_id, 'swing_price'] = np.nan
                pivot, last_pivot_id = row.price_low, i

            elif row.price_high > pivot - diff:
                data.loc[i, 'swings'] = row.price_high - pivot
                pivot, last_pivot_id = row.price_high, i
                data.loc[i, 'swing_price'] = row.price_high
                # Change the trend indicator
                up_down = 1

    return data
    # print(data)
    # data.to_excel('FINAL.xlsx')


def getSymbolIds():
    df = pd.read_excel('FinalList.xlsx', engine='openpyxl')
    symbol_list = df['symbol_id']
    return symbol_list.tolist()


def getSwings(symbol: str):
    df = pd.read_excel('swings/'+symbol+".xlsx", engine='openpyxl')
    return df


def validateTrade(df_trade_1H):
    conn = sqlite3.connect('test.db')
    symbolDb = pd.read_excel("FinalList.xlsx", engine='openpyxl')
    c = conn.cursor()
    conn.execute("delete from  TradeCall;")
    conn.execute("delete from  SwingTable;")

    df_trade_1H.to_sql('TradeCall', conn, if_exists='append', index=False)
    # print(pd.read_sql("select * from TradeCall", conn))

    symbols = getSymbolIds()
    lis = []
    for symbol in symbols:
        for root, subdirectories, files in os.walk('swings/'):
            for subdirectory in subdirectories:
                folderName = os.path.join(root, subdirectory)
                try:
                    df = pd.read_excel(folderName + '/' +
                                       symbol + '.xlsx', engine='openpyxl')
                    lis.append(df)
                except IOError as e:
                    print(e)

    SwingDf = pd.concat(lis)
    SwingDf = SwingDf.iloc[:, 2:]
    # SwingDf.to_excel('Output.xlsx', index=False)
    print(SwingDf)
    SwingDf.to_sql('SwingTable', conn, if_exists='append', index=False)
    newDf = pd.read_sql("""    SELECT
        T1.*,
        DerivedTable.swings,DerivedTable.swing_price
    FROM TradeCall T1
    JOIN
    (
        SELECT 
            T2.*,
            ROW_NUMBER() OVER (PARTITION BY T2.SymbolDb ORDER BY T2.time_close DESC) AS RowNum
        FROM SwingTable T2, TradeCall T1
        WHERE datetime(T2.time_close) < datetime(T1.TimeStamp)
        AND T2.swings IS NOT NULL
    ) DerivedTable
    ON T1.Ticker = DerivedTable.SymbolDb
    WHERE DerivedTable.RowNum = 1""", conn)
    newDf.to_excel("CalculatedSwing.xlsx", index=False)
    print(newDf)
