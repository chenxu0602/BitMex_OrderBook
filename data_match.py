
import os, sys
import json
from datetime import datetime
import pandas as pd
import re
import matplotlib.pyplot as plt


def load_data_trade(cmp_name, dir_trade, start_dt, start_ti):
    dataframes = []
    files = os.listdir(dir_trade)
    print(f"N of files: {len(files)}")
    for fl in files:
        m = cmp_name.search(fl)
        if m:
            dt, ti = m.group(1), m.group(2)
            if dt >= start_dt and ti >= start_ti:
                filename = os.path.join(dir_trade, fl)
                print(f"Loading data {filename} ...")
                with open(filename, "r") as f:
                    df = pd.DataFrame(json.load(f))
                    dataframes.append(df)

    return pd.concat(dataframes)

def load_data_order(cmp_name, dir_trade, start_dt, start_ti):
    return load_data_trade(cmp_name, dir_trade, start_dt, start_ti)

cmp_trade= re.compile(r"bitmex_trade_(\d{8})_(\d{6}).json")
df_trade = load_data_trade(cmp_trade, "json", "20190706", "120000")

cmp_order= re.compile(r"bitmex_orderbook_(\d{8})_(\d{6}).json")
df_order = load_data_order(cmp_order, "json", "20190706", "120000")

df_order["datetime"] = pd.to_datetime(df_order["datetime"], unit="ms")
df_order.set_index("datetime", inplace=True)
df_order.sort_index(inplace=True)

df_trade["datetime"] = pd.to_datetime(df_trade["datetime"])
df_trade.set_index("datetime", inplace=True)
df_trade.sort_index(inplace=True)

df = pd.merge_asof(df_trade, df_order, left_index=True, right_index=True, direction="backward")

df2 = pd.DataFrame(index=df.index)

df2["mid"] = 0.5 *(df["a_1"] + df["b_1"])

df2["tot_vol"] = 0.0
for i in range(1, 11):
    for s in ['a', 'b']:
        df2[f"{s}{i}"] = (df[f"{s}_{i}"] - df2["mid"]) / 0.5
        df2["tot_vol"] = df2["tot_vol"] +  df[f"{s}_{i}_v"]

for i in range(1, 11):
    df2[f"v{i}"] = (df[f"a_{i}_v"] + df[f"b_{i}_v"]).div(df2["tot_vol"])
    df2[f"d{i}"] = (df[f"a_{i}_v"] - df[f"b_{i}_v"]).div(df2["tot_vol"])


df2["price"] = (df["price"] - df2["mid"]) / 0.5
df2["volume"] = df["volume"]

df2.dropna(subset=["mid", "a1", "b1", "a2", "b2"], how="all", inplace=True)

df3 = pd.DataFrame(index=df2.index)
df3["volume"] = df2["volume"]
df3["buy_vol"] = df3["sell_vol"] = df2["volume"]
df3.loc[df2.price <= 0.0, "buy_vol"] = 0.0
df3.loc[df2.price >= -0.0, "sell_vol"] = 0.0

df4 = df3.resample("1T", closed="right", label="right").sum()
df4["buy"] = df4["buy_vol"].div(df4["volume"])
df4["sell"] = df4["sell_vol"].div(df4["volume"])
df4["VPIN"] = (df4["buy_vol"] - df4["sell_vol"]).div(df4["volume"])

df4["mid"] = df2[["mid"]].resample("1T", label="right", closed="right").last()

                                                                                                                                          1,0-1         Top
