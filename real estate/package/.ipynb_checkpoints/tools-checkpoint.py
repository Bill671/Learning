# 爬取近五年資料
import pandas as pd
import requests
import zipfile
import os
import time
import random

# clean building material
def main_material(b):
    if str(b)=="nan":
        o = "鋼筋混凝土造" # mode
    else:
        o = b.replace("磚造、鋼筋混凝土","鋼筋混凝土加強磚造")
        o = o.replace("鋼骨ＲＣ造",'鋼骨鋼筋混凝土造')
        o = o.replace('鋼骨鋼筋混凝土造；鋼骨造','鋼骨鋼筋混凝土造')
        o = o.replace('見使用執照','見其他登記事項')
        o =o.replace('鋼骨造、鋼骨鋼筋混凝土造','鋼骨鋼筋混凝土造')
    return o

## clean 句號...
def city_clean(s):
    if s.find("(")!=-1:
        s = s[:s.find("(")]
    if s.find("【")!=-1:
        s = s[:s.find("【")]
    if s.find("﹝")!=-1:
        s = s[:s.find("﹝")]
    if s.find("（")!=-1:
        s = s[:s.find("（")] 
    return s.replace("。","")
import numpy as np
# 處理屋齡日期轉數值
def days2num(d):
    d = str(d)
    index = d.rfind("d")
    if index !=-1:
        d = d[: index-1]
    else :
        d = np.nan
    return d

# define func
def crawl_house(year,season): # year 為 西元年  
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

def organize():
   # 歷年資料夾
    fol = os.path.join('house_data')
    dirs = [d for d in os.listdir(fol) if d[:4] == 'real']
    dfs = []

    # 分析 台北市 的 房屋買賣交易 不包含新成屋與租房交易
    for d in dirs:
        print(d)
        df = pd.read_csv(os.path.join( fol ,d,'a_lvr_land_a.csv'), index_col=False)
        df['Q'] = d[-1]
        dfs.append(df.iloc[1:])
    
    df = pd.concat(dfs, sort=True)
    # 新增交易年份
    # df['year'] = df['交易年月日'].str[:-4].astype(int) + 1911

    # 不同名稱同項目資料合併
    df['單價元平方公尺'].fillna(df['單價元平方公尺'], inplace=True)
    df.drop(columns='單價元平方公尺')

    df['單價元平方公尺'] = df['單價元平方公尺'].astype(float)
    
    # 平方公尺換成坪
    # df['單價元坪'] = df['單價元平方公尺'] * 3.30579

    # 建物型態
    df['建物型態'] = df['建物型態'].str.split('(').str[0]

    # 刪除有備註之交易（多為親友交易、價格不正常之交易）
    df = df[df['備註'].isnull()]

    # 改成西元年
    df['交易年月日'] = pd.to_datetime((df['交易年月日'].str[:-4].astype(int) + 1911).astype(str) + df['交易年月日'].str[-4:] ,errors='coerce')
    df.set_index('交易年月日',inplace=True)

    # 只取2016年以後資料
    df = df.loc['2016-01-01':]

    # 移除非房屋資料
    df = df[(df.交易標的!="土地")&(df.交易標的 !="車位")] # set(df['交易標的'])

    # 匯出資料
    final_dir = os.path.join('house_data','new_data.pkl')
    df.to_pickle(final_dir)

# 處理 國字 轉數字
digit = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
def _trans(s):
    num = 0
    if s:
        idx_q, idx_b, idx_s, idx_負 = s.find('千'), s.find('百'), s.find('十'),s.find('地下')
        if idx_q != -1:
            num  += digit[s[idx_q - 1:idx_q]] * 1000
        if idx_b != -1:
            num  += digit[s[idx_b - 1:idx_b]] * 100
        if idx_s != -1:
        # 十前忽略一的處理
            num  += digit.get(s[idx_s - 1:idx_s], 1) * 10
        if s[-1] in digit:
            num  += digit[s[-1]]
        if idx_負 != -1:
            num = num*(-1)
    return num

def trans(chn):
    chn = chn.replace('零', '')
    idx_y, idx_w = chn.rfind('億'), chn.rfind('萬')
    if idx_w < idx_y:
        idx_w = -1
        num_y, num_w = 100000000, 10000
    if idx_y != -1 and idx_w != -1:
        return trans(chn[:idx_y]) * num_y+ _trans(chn[idx_y + 1:idx_w]) * num_w + _trans(chn[idx_w + 1:])
    elif idx_y != -1:
        return trans(chn[:idx_y]) * num_y + _trans(chn[idx_y+ 1:])
    elif idx_w != -1:
        return _trans(chn[:idx_w]) * num_w + _trans(chn[idx_w +1:])
    return _trans(chn)

# 只考慮移轉層次的高低， 不處理 附屬條件
def transform(item):
    item = str(item)
    
    import re
    p = re.compile('\S+層$')
    m = p.search(item)
    try:
        item = m.group()
    except:
        item = item.split(",")[0] 
    return item

def remove_comma(m):
    loop = m.split("，")
    tmp = []
    for k in loop:
        tmp.append(trans(k))
    tmp = list(filter(None, tmp))
    
    import numpy as np
    m = np.array(tmp).mean()
    tmp = []
    return m

def covert2date(s):
    s = str(s)
    if len(s)==7:
        y = str(int(s[:3])+1911)
        m = s[3:5]
        d = s[5:7]
        f = "-".join([y,m,d])
    elif len(s)==4:
        f = "-".join([str(s),"1","1"]) #未寫特定月份的一律假設其為1月1號製造
    else:
        f = s
    return f


def preprocessing(df):
    missing_col=df.isna().mean().sort_values(ascending=False)
    missing_columns= missing_col[missing_col!=0].to_frame().reset_index()

    # drop 大於 0.8
    drop_col = missing_col[missing_col>0.8].index.tolist()
    df = df.drop(columns= drop_col)
    df['主要用途'] = df['主要用途'].apply(lambda s : str(s).replace('見其他登記事項','其他').replace('見使用執照','其他'))

    # 要處理的欄位
    df['總樓層數'] = df['總樓層數'].apply(lambda s : str(s).replace('層',"")).apply(trans)
    df['移轉層次'] = df['移轉層次'].astype(str).apply(transform).apply(lambda s : str(s).replace('層',"")).apply(remove_comma)

    # 交易筆棟數 拆成 土地 建物 車位 三個欄位  # df.dtypes
    df['土地筆數']=df['交易筆棟數'].apply(lambda s : str(s)[:3].replace("土地","")).astype(float)
    df['建物筆數'] = df['交易筆棟數'].apply(lambda s : str(s)[3:6].replace("建物","")).astype(float)
    df['車位筆數']= df['交易筆棟數'].apply(lambda s : str(s)[6:].replace("車位","")).astype(float)
    df = df.drop(columns=['交易筆棟數','編號'])
    df['建築完成年月'] = df['建築完成年月'].apply(lambda s : pd.to_datetime(covert2date(s),errors='coerce'))
    return df

def missing_plot(df):
    missing_col= df.isna().mean().sort_values(ascending=False)
    missing_columns= missing_col[missing_col!=0].to_frame().reset_index()
    from matplotlib import pyplot as plt
    import seaborn as sns
    try:
        # 遺漏率繪圖
        plt.rcParams['font.family'] = 'SimSun' # 解決中文字問題，選擇能商用字體才安心
        plt.rcParams["figure.figsize"] = (20,10)

        fig,ax=plt.subplots(figsize=(7,7))
        sns.barplot(x=0,y='index',data=missing_columns)
    except:
        print("沒有缺失值")

def missing_preprocessing(df):
    df['電梯'] = df['電梯'].fillna("無") 
    df['車位類別'] = df['車位類別'].fillna("無車位") # df["車位總價元"][df['車位類別'].isna()]
    df['都市土地使用分區'] = df['都市土地使用分區'].fillna("未公告")
    df['都市土地使用分區']=df['都市土地使用分區'].apply(city_clean)
    df['主要建材'].fillna(df['主要建材'].mode(),inplace = True)
    df['單價元平方公尺']  = df['單價元平方公尺'].fillna(df['單價元平方公尺'].median() )
    df['主要建材'] = df['主要建材'].apply(main_material)
    df['移轉層次'] = df['移轉層次'].fillna(df['移轉層次'].median())
    return df

# add new variable項
def add_variable(df):
    if df.index[0] !=0:
        df = df.reset_index()
    df['屋齡byDay'] = pd.to_datetime(df['交易年月日'])-pd.to_datetime(df['建築完成年月'])
    df['屋齡byDay'] = df['屋齡byDay'].apply(days2num)
    df['屋齡byDay'] = df['屋齡byDay'].fillna(df['屋齡byDay'].median()).astype(int)
    df['屋齡byDat平方'] = df['屋齡byDay']*df['屋齡byDay']

    df['建物現況格局-房'] = df['建物現況格局-房'].astype(int)
    df['建物現況格局-廳'] = df['建物現況格局-廳'].astype(int)
    df['建物現況格局-衛'] = df['建物現況格局-衛'].astype(int)
    df['房廳衛multiple'] = df['建物現況格局-房']*df['建物現況格局-廳']*df['建物現況格局-衛'] #看房廳衛交互項
    df['總樓層數平方'] = df['總樓層數'].astype(int) * df['總樓層數'].astype(int)
    return df