# 舊名 tools
import pandas as pd
import os
import numpy as np

# Main
def dirty_data_clean(df,droppthesh=0.8):
    df['單價元平方公尺'] = df['單價元平方公尺'].astype(float)
    df['建物型態'] = df['建物型態'].str.split('(').str[0] 
    df = df[df['備註'].isnull()] # 刪除有備註之交易（多為親友交易、價格不正常之交易）
    
    # 民國改西元年
    df['交易年月日'] = pd.to_datetime((df['交易年月日'].str[:-4].astype(int) + 1911).astype(str) + df['交易年月日'].str[-4:] ,errors='coerce')
    df.set_index('交易年月日',inplace=True)
    df = df.loc['2016-01-01':]
    
    # 移除非房屋資料
    df = df[(df.交易標的!="土地")&(df.交易標的 !="車位")]
    df['屋齡byDay'] = pd.to_datetime(df['交易年月日'])-pd.to_datetime(df['建築完成年月'])        

    # Sub function
    ## clean building material
    def main_material(b):
        if str(b)=="nan":
            o = "鋼筋混凝土造" # mode
        else:
            o = b.replace("磚造、鋼筋混凝土","鋼筋混凝土加強磚造")
            o = o.replace("鋼骨ＲＣ造",'鋼骨鋼筋混凝土造')
            o = o.replace('鋼骨鋼筋混凝土造；鋼骨造','鋼骨鋼筋混凝土造')
            o = o.replace('見使用執照','見其他登記事項')
            o = o.replace('鋼骨造、鋼骨鋼筋混凝土造','鋼骨鋼筋混凝土造')
        return o
    ## 處理屋齡日期轉數值
    def days2num(d):
        d = str(d)
        index = d.rfind("d")
        if index !=-1:
            d = d[: index-1]
        else :
            d = np.nan
        return d
    
    ## clean 句號...
    def bracket_removal(s):
        if s.find("(")!=-1:
            s = s[:s.find("(")]
        if s.find("【")!=-1:
            s = s[:s.find("【")]
        if s.find("﹝")!=-1:
            s = s[:s.find("﹝")]
        if s.find("（")!=-1:
            s = s[:s.find("（")] 
        return s.replace("。","")
    
    df['屋齡byDay'] = pd.to_datetime(df['交易年月日'])-pd.to_datetime(df['建築完成年月'])
    df['屋齡byDay'] = df['屋齡byDay'].apply(days2num)
    # Imputer
    Imputer = {
            "電梯": "無",
            "車位類別":"無車位",
            "都市土地使用分區":"未公告",
            "主要建材": df['主要建材'].mode()[0],
            "單價元平方公尺": df['單價元平方公尺'].median(),
            "屋齡byDay": df['屋齡byDay'].median()        
            
    }  
    df.fillna(Imputer,inplace=True) 
    int_columns= ['建物現況格局-房', '建物現況格局-廳', '建物現況格局-衛','屋齡byDay']
    df[int_columns] = df[int_columns].apply(lambda x: x.astype(int))
    
    df['屋齡byDat平方'] = df['屋齡byDay'] ** 2
    df['房廳衛multiple'] = df['建物現況格局-房']*df['建物現況格局-廳']*df['建物現況格局-衛'] #看房廳衛交互項
    df['總樓層數平方'] = df['總樓層數'].astype(int) * df['總樓層數'].astype(int)
    
    df['都市土地使用分區']=df['都市土地使用分區'].apply(bracket_removal)
    df['主要建材'] = df['主要建材'].apply(main_material)
    df['主要用途'] = df['主要用途'].apply(lambda s : str(s).replace('見其他登記事項','其他').replace('見使用執照','其他'))

    # 交易筆棟數 拆成 土地 建物 車位 三個欄位  # df.dtypes
    df['土地筆數']=df['交易筆棟數'].apply(lambda s : str(s)[:3].replace("土地","")).astype(float)
    df['建物筆數'] = df['交易筆棟數'].apply(lambda s : str(s)[3:6].replace("建物","")).astype(float)
    df['車位筆數']= df['交易筆棟數'].apply(lambda s : str(s)[6:].replace("車位","")).astype(float)
    
    # 刪除欄位
    missing_col=df.isna().mean().sort_values(ascending=False)
    missing_columns= missing_col[missing_col!=0].to_frame().reset_index()
    drop_col = missing_col[missing_col>droppthesh].index.tolist()
    df = df.drop(columns= drop_col.extend(['交易筆棟數','編號']))
    
    # 欄位拆解
    tran = Trans_digit()
    df['總樓層數'] = df['總樓層數'].apply(lambda s : str(s).replace('層',"")).apply(tran.trans)
    df['移轉層次'] = df['移轉層次'].astype(str).apply(tran.transform).apply(lambda s : str(s).replace('層',"")).apply(tran.remove_comma)
    df['移轉層次'] = df['移轉層次'].fillna(df['移轉層次'].median())
    df['建築完成年月'] = df['建築完成年月'].apply(lambda s : pd.to_datetime(tran.covert2date(s),errors='coerce')) 
    
    
    # 匯出資料
    final_dir = os.path.join('house_data','new_data.csv')
    df.to_csv(final_dir)
    
class Trans_digit():
    def __init__(self,digit={'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}):
        self.digit = digit
    def _trans(self,s):
        num = 0
        if s:
            idx_q, idx_b, idx_s, idx_負 = s.find('千'), s.find('百'), s.find('十'),s.find('地下')
            if idx_q != -1:
                num  += self.digit[s[idx_q - 1:idx_q]] * 1000
            if idx_b != -1:
                num  += self.digit[s[idx_b - 1:idx_b]] * 100
            if idx_s != -1:
            # 十前忽略一的處理
                num  += self.digit.get(s[idx_s - 1:idx_s], 1) * 10
            if s[-1] in self.digit:
                num  += self.digit[s[-1]]
            if idx_負 != -1:
                num = num*(-1)
        return num
    def parse(self, chn): # recursive
        chn = chn.replace('零', '')
        idx_y, idx_w = chn.rfind('億'), chn.rfind('萬')
        if idx_w < idx_y:
            idx_w = -1
            num_y, num_w = 100000000, 10000
        if idx_y != -1 and idx_w != -1:
            return self.parse(chn[:idx_y]) * num_y + self._trans(chn[idx_y + 1:idx_w]) * num_w + self._trans(chn[idx_w + 1:])
        elif idx_y != -1:
            return self.parse(chn[:idx_y]) * num_y + self._trans(chn[idx_y + 1:])
        elif idx_w != -1:
            return self._trans(chn[:idx_w]) * num_w + self._trans(chn[idx_w + 1:])
        return self._trans(chn)
    @staticmethod
    def remove_comma(m):
        parser = Trans_digit()
        loop = m.split("，")
        tmp = [parser.parse(k) for k in loop]
        tmp = list(filter(None, tmp))
        return np.mean(tmp)
    
    @staticmethod
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
    @staticmethod
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
    
   
    

        
