# 舊名 tools
import pandas as pd
import requests
import zipfile
import time
import random
import os

# Main crawler
def crawl_house(starty=2015,endy=2022):
    for year in range(starty,endy):
        for season in range(1,5):
            print(year,season)
            _crawl(year, season)

def _crawl(year,season):
    try:
        year-=1911
        # scrape
        res = requests.get("https://plvr.land.moi.gov.tw//DownloadSeason?season="+str(year)+"S"+str(season)+"&type=zip&fileName=lvr_landcsv.zip")

        # save
        fname = str(year)+str(season)+'.zip'
        n = 'house_data'
        if not os.path.isdir(n):
            os.mkdir(n)
        fn = os.path.join('house_data',fname)
        open(fn, 'wb').write(res.content)

        # additional folder for files to extract
        folder = 'real_estate' + str(year) + str(season)
        fol = os.path.join('house_data',folder)
        if not os.path.isdir(fol):
            os.mkdir(fol)

        # extract files to the folder
        with zipfile.ZipFile(fn, 'r') as zip_ref:
            zip_ref.extractall(fol)

        time.sleep(8 + random.uniform(0,5))
    except:
        print('error from {},{}'.format(year,season)) 

# 台北市房屋買賣交易 不包含新成屋與租房交易
def data_select(select = "a_lvr_land_a.csv",droppthesh=0.8): 
    fol = os.path.join('house_data')
    dirs = [d for d in os.listdir(fol) if d[:4] == 'real']
    dfs = []
    for d in dirs:
        print(d)
        df = pd.read_csv(os.path.join( fol ,d,select), index_col=False)
        df['Q'] = d[-1]
        dfs.append(df.iloc[1:])
    df = pd.concat(dfs, sort=True)
    
    from function.preprocess import dirty_data_clean
    dirty_data_clean(df,droppthesh=droppthesh)