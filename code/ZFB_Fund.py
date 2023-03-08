# -*- coding: utf-8 -*-  
import pandas as pd
import numpy as np
from bisect import bisect_right
from multiprocessing.pool import ThreadPool
import requests
import json
from queue import Queue
import time
import os
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

class Robot:

  headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47'}

  def __init__(self,title,touser):
    #图文图文消息的标题
    self.title=title
    
    self.corpid=os.environ['CORPID']  #公司id
    self.agentid=os.environ['AGENTID']  #机器人id
    self.corpsecret=os.environ['CORPSECRET']  #机器人secret
    self.media_id=os.environ['MEDIA'] #图片id
    #self.touser=os.environ['TOUSER']  #接收id

    self.touser=touser
    self.digest = time.strftime('%Y-%m-%d UTC(%H:%M)', time.localtime()) + '\n'
    self.daily=self.get_daily_sentence()

  def get_token(self):
    payload_access_token = {'corpid': self.corpid, 'corpsecret': self.corpsecret}
    token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
    r = requests.get(url=token_url, params=payload_access_token,headers=self.headers)
    self.access_token = (r.json())['access_token']

  #发送图文信息
  def send_mpnews(self,content):
    self.get_token()
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.access_token}"
    data = {
      "touser":self.touser, #接收消息人员id
      "agentid":self.agentid, #机器人id
      'msgtype':'mpnews',
      'mpnews': {
        'articles':[
          {
            "title": self.title, #必须
            "thumb_media_id": self.media_id, #必须
            "author": "Chlorine", #非必须 作者
            "content": content, #必须 不超过666 K个字节
            "digest": self.digest #非必须 不超过512个字节
          }
        ]
      },
      "safe": 0 #是否加密
    }
    data = json.dumps(data, ensure_ascii=False)
    requests.post(url=url, data=data.encode("utf-8").decode("latin1"))

  def get_daily_sentence(self):
    url = "http://open.iciba.com/dsapi/"
    try:
      r = requests.get(url,timeout=5)
      r = json.loads(r.text)
      content = r["content"]
      note = r["note"]
      self.digest=f'{self.digest}{content}\n{note}\n'
    except Exception:
      self.digest=f'{self.digest}Happy every day !\n'

class ZFB:

  def __init__(self,code_list):
    self.R=Robot('ZFB Fund (GitHub)','Chlorine')
    self.fund_list=Queue()
    self.content1=Queue()
    self.content2=Queue()
    self.content3=Queue()
    self.code_list=code_list

  def pd_jz(self,lj_data,jz):
    lj_data.sort()
    num = round(bisect_right(lj_data,jz)/len(lj_data)*100,1)
    if num < 20:
      return ('🍏🍏🍏',num)
    elif num < 50:
      return ('🍎🍏🍏',num)
    elif num < 80:
      return ('🍎🍎🍏',num)
    else:
      return ('🍎🍎🍎',num)
    
  def get_color(self,ljjz_data):
    mean=np.mean
    mean5=round(mean(ljjz_data[-5:]),4) #前5天净值均值
    mean10=round(mean(ljjz_data[-10:]),4)#前10天净值均值
    mean20=round(mean(ljjz_data[-20:]),4)#前20天净值均值
    return(min(mean5,mean10,mean20),max(mean5,mean10,mean20))

  def get_detail(self,code):
    f=FundV()
    f.get_dayfund_his(code) #获取 历史净值
    f.get_today_value(code) #获取 名称 当日涨幅
    self.fund_list.put(f)

  def try_many_times(self,code):
    for _ in range(5):
      try:
        self.get_detail(code)
      except Exception:
        time.sleep(1.1)
      else:
        break

  def working(self):
    pool=ThreadPool(5)
    list(pool.imap(self.try_many_times,self.code_list))

    while not self.fund_list.empty():
      F=self.fund_list.get()
      dwjz=F.his_data['最新单位净值'].values[-1]
      lj_data=F.his_data['最新累计净值'].values  

      if F.gszf==False :
        F.gszf=0
        zf=0
        today_lj=lj_data[-1]
        color='black'
      else:
        zf = dwjz * F.gszf / 100 #当日单位净值估值涨幅
        today_lj=round(lj_data[-1]+zf,4) #当日累计净值估值
        lj_data=np.append(lj_data,today_lj) #前1季度累计净值+当日估值
        color='red' if F.gszf > 0 else 'green'

      num_min20,num_max20=self.get_color(lj_data) #求近20天均值极值点

      state,tip=self.pd_jz(lj_data,today_lj)
      sio_content=''
      if (tip > 85)and(today_lj >= num_max20):
        sio_content=f'<p>{state} <font color="red"><small>{tip}%</small></font></p>'
        sio_content+=f'<p><font color="red"><strong>{F.name}</strong></font><font color="{color}"><small> {F.gszf}%</small></font></p>'
        sio_content+=f'<p>卖出<font color="red"> {round(max(tip-85,5)*0.88/(dwjz+zf),1)} </font>份</p>'
        self.content2.put(sio_content)
      elif (tip < 20):
        sio_content=f'<p>{state} <font color="green"><small>{tip}%</small></font></p>'
        sio_content+=f'<p><font color="green"><strong>{F.name}</strong></font><font color="{color}"><small> {F.gszf}%</small></font></p>'
        sio_content+=f'<p>买入 <font color="green">{round(max(26-tip,10),1)}</font> 元</p>'
        self.content1.put(sio_content)
      else:
        sio_content=f'<p>{state} <font color="black"><small>{tip}%</small></font></p>'
        sio_content+=f'<p>{F.name}<font color="{color}"><small> {F.gszf}%</small></font></p>'
        sio_content+='<p>再等等看吧</p>'
        self.content3.put(sio_content)

def main():
  df=pd.read_excel('./Data/ZFB_FundList.xlsx',dtype={'ID': 'string'})
  zfb=ZFB(df['ID'].tolist())
  zfb.working()
  content=''
  while not zfb.content1.empty():
    content+=zfb.content1.get()

  while not zfb.content2.empty():
    content+=zfb.content2.get()
    
  while not zfb.content3.empty():
    content+=zfb.content3.get()
  
  zfb.R.send_mpnews(content)

if __name__=='__main__':
  main()