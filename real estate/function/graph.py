import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

class Report():
    def __init__(self,df=None) :
        self.data = df
    def price_by_target(self,condition,groups="鄉鎮市區",target="單價元平方公尺",quantile=0.95,
                        starty=2014,select=None,tocsv=False,csvlabel='price'): # select= ['公寓','住宅大樓','套房','華廈']
        tmp_price_dict = {}
        for group in set(self.data[groups]):
            cond  = (
                condition 
                & (self.data[target] < self.data[target].quantile(quantile))
                & (self.data[target] > self.data[target].quantile(1-quantile))
                &  (self.data[groups]==group)
            )
            tmp_price_dict[group] = self.data[cond][target].groupby(self.data[cond]['year']).mean().loc[starty:]
        price = pd.DataFrame(tmp_price_dict).get(select) if select != None else pd.DataFrame(tmp_price_dict)
        price.plot()
        if tocsv:
            price.to_csv("graphic_data/{}_price.csv".format(csvlabel),encoding="big5")
        return price
    # 缺失值繪圖
    def missing_plot(self,df=None): 
        if df ==None:
            df = self.data
        missing_col= df.isna().mean().sort_values(ascending=False)
        missing_columns= missing_col[missing_col!=0].to_frame().reset_index()
        try:
            plt.rcParams['font.family'] = 'SimSun' 
            plt.rcParams["figure.figsize"] = (20,10)

            fig,ax=plt.subplots(figsize=(7,7))
            sns.barplot(x=0,y='index',data=missing_columns)
        except:
            print("沒有缺失值")