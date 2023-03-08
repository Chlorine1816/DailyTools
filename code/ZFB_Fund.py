# -*- coding: utf-8 -*-  
import pandas as pd
import numpy as np
from bisect import bisect_right
from multiprocessing.pool import ThreadPool
from need.SendMess import Robot
from need.FundValues import FundV
from queue import Queue
import time

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
  df=pd.read_excel('./dailytools/Data/ZFB_FundList.xlsx',dtype={'ID': 'string'})
  zfb=ZFB(df['ID'].tolist()[:6])
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