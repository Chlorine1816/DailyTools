import requests
import time
import pandas as pd
import random
from bs4 import BeautifulSoup
import re

class FundV:

  headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47'}
  
  def __init__(self):
    self.name=''
    self.gszf=False
    self.his_data=pd.DataFrame()
  
  def get_dayfund_his(self,fund_id):
    time.sleep(random.randint(1,2)+random.random())
    #近1季度
    url=f'https://www.dayfund.cn/fundvalue/{fund_id}_q.html'
    r=requests.get(url,headers=self.headers,timeout=22)
    self.his_data=pd.read_html(r.text,encoding='utf-8',header=0)[0]
    self.his_data=self.his_data[['净值日期','基金名称','最新单位净值','最新累计净值']]
    self.his_data['最新单位净值']=self.his_data['最新单位净值'].astype(float)
    self.his_data['最新累计净值']=self.his_data['最新累计净值'].astype(float)
    self.his_data.dropna(subset=['净值日期','基金名称','最新单位净值','最新累计净值'],how='any',inplace=True)
    # 按照日期升序排序并重建索引
    self.his_data.sort_values(by='净值日期',axis=0,ascending=True,ignore_index=True,inplace=True)

  def get_eastmoney_his(self,fund_id,sdate='',edate=''):
    time.sleep(random.randint(1,2)+random.random())
    url='http://fund.eastmoney.com/f10/F10DataApi.aspx'
    params = {'type': 'lsjz', 'code': fund_id, 'page':1,'per': 45, 'sdate': sdate, 'edate': edate}
    r=requests.get(url,params=params,headers=self.headers,timeout=22)
    # 获取总页数
    pattern = re.compile(r'pages:(.*),')
    pages = int(re.search(pattern,r.text)[1])
    self.his_data=pd.read_html(r.text,encoding='utf-8',header=0)[0]
    for page in range(2,pages+1):
      time.sleep(0.2)
      params['page']=page
      r=requests.get(url,params=params,headers=self.headers,timeout=30)
      self.his_data=pd.concat([self.his_data,pd.read_html(r.text,encoding='utf-8',header=0)[0]])
    self.his_data=self.his_data[['净值日期','单位净值','累计净值']]
    self.his_data.sort_values('净值日期',inplace=True,ignore_index=True)
  
  def get_today_value(self,fund_id):
    time.sleep(random.randint(1,2)+random.random())
    url=f'http://fundf10.eastmoney.com/jjjz_{fund_id}.html'
    req=requests.get(url=url,headers=self.headers,timeout=22)
    req.encoding='utf-8'
    html=req.text
    bf=BeautifulSoup(html,'lxml')
    jz=bf.find_all('div',class_='bs_jz')
    jz=BeautifulSoup(str(jz),'lxml')

    #名称
    self.name=jz.find_all('h4',class_='title')[0].text
    #涨跌
    self.gszf=float(jz.find_all('span',id='fund_gszf')[0].text.strip('%'))

