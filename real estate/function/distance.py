import time
import random
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup

from math import radians, cos, sin, asin, sqrt
import gc
import pandas as pd

options = webdriver.ChromeOptions()
options.add_argument("headless")

def get_coordinate(addr):
    time.sleep(1 + random.uniform(0,5 )) # 避免被鎖
    #browser = webdriver.Chrome(executable_path,options=options)
    browser = webdriver.Chrome('./chromedriver',options=options)

    browser.get("http://www.map.com.tw/")
    search = browser.find_element_by_id("searchWord")
    search.clear()
    search.send_keys(addr)
    browser.find_element_by_xpath("/html/body/form/div[10]/div[2]/img[2]").click() 
    time.sleep(2)
    
    iframe = browser.find_elements_by_class_name("winfoIframe")[0] # 改成這個
    browser.switch_to.frame(iframe)
    coor_btn = browser.find_element_by_xpath("//img[@alt='座標']")
    coor_btn.click()
    coor = browser.find_element_by_xpath("/html/body/form/div[5]/table/tbody/tr[2]/td")
    coor = coor.text.strip().split(" ")
    lat = coor[-1].split("：")[-1]
    log = coor[0].split("：")[-1]
    time.sleep(2)
    browser.quit()
    return (lat, log)

def convert2lat_lon(v):#
    lat1 = v[v.find('(')+1:v.find(',')]
    lon1 = v[v.find(',')+1:v.find(')')]
    try:
        lat1 = float(lat1)
        lon1 = float(lon1)
    except:
        lat1 = pd.to_numeric("".join(list(lat1)[1:-2]))
        lon1 = pd.to_numeric("".join(list(lon1)[2:-2]))
    return (lat1,lon1) 

def greatCircleDistance(v1, v2):
    lat1, lon1 = v1 # 25,121
    lon2, lat2 = v2 # 121,25 ** mall 25,121
    if lon2<40:
        lon2,lat2=lat2,lon2
    # 之前抓的時候沒有，現在補上
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    gc.collect()
    def haversin(x):
        return sin(x/2)**2 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    dist = r * 2 * asin(sqrt(haversin(lat2-lat1) +cos(lat1) * cos(lat2) * haversin(lon2-lon1)))
    return dist 

def haversine(v1, v2):
    lat1, lon1 = v1 # 25,121
    lon2, lat2 = v2 # 121,25 ** mall 25,121
    if lon2<40:
        lon2,lat2=lat2,lon2
    R = 6374.293 
    dLat,dLon,lat1,lat2 = map(radians,[lat2 - lat1,lon2 - lon1,lat1,lat2])
    gc.collect()
    a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2
    c = 2*asin(sqrt(a))
    return R * c

def radius (B):
    B= radians(B) #converting into radians
    a = 6378.137  #Radius at sea level at equator
    b = 6356.752  #Radius at poles
    c = (a**2*cos(B))**2
    d = (b**2*sin(B))**2
    e = (a*cos(B))**2
    f = (b*sin(B))**2
    R = sqrt((c+d)/(e+f))
    return R