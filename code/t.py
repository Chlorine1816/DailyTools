# -*- coding: utf-8 -*-  
import time
import pandas as pd
import numpy as np
from bisect import bisect_right
from multiprocessing.pool import ThreadPool
from need.SendMess import Robot
from need.FundValues import FundV

def working(code):
    data=get_his(code) #获取历史净值
    name,gszf=get_fund2(code) #获取当日 涨幅
    dwjz=data['最新单位净值'].values[-1]
    lj_data=data['最新累计净值'].values  

    if gszf==False :
        gszf=0
        zf=0
        today_lj=lj_data[-1]
        color='black'
    else:
        zf=dwjz*gszf/100 #当日单位净值估值涨幅
        today_lj=round(lj_data[-1]+zf,4) #当日累计净值估值
        lj_data=np.append(lj_data,today_lj) #前1季度累计净值+当日估值
        color='red' if gszf > 0 else 'green'

    num_min20,num_max20=get_color(lj_data) #求近20天均值极值点

    state,tip=pd_jz(lj_data,today_lj)
    sio_content1=''
    sio_content2=''
    sio_content3=''
    if (tip > 85)and(today_lj >= num_max20):
        sio_content2=f'<p>{state} <font color="red"><small>{tip}%</small></font></p>'
        sio_content2+=f'<p><font color="red"><strong>{name}</strong></font><font color="{color}"><small> {gszf}%</small></font></p>'
        sio_content2+=f'<p>卖出<font color="red"> {round(max(tip-85,5)*0.88/(dwjz+zf),1)} </font>份</p>'
    elif (tip < 20):
        sio_content1=f'<p>{state} <font color="green"><small>{tip}%</small></font></p>'
        sio_content1+=f'<p><font color="green"><strong>{name}</strong></font><font color="{color}"><small> {gszf}%</small></font></p>'
        sio_content1+=f'<p>买入 <font color="green">{round(max(26-tip,10),1)}</font> 元</p>'
    else:
        sio_content3=f'<p>{state} <font color="black"><small>{tip}%</small></font></p>'
        sio_content3+=f'<p>{name}<font color="{color}"><small> {gszf}%</small></font></p>'
        sio_content3+='<p>再等等看吧</p>'

    return (sio_content1,sio_content2,sio_content3)

def try_many_times(code):
    for _ in range(5):
        try:
            return working(code)
        except Exception:
            time.sleep(1.1)
        else:
            break
    return ''

def main():
    start=time.perf_counter()
    fund_list=pd.read_excel('./data/ZFB_FundList.xlsx',dtype={'ID': 'string'})
    fund_list=fund_list['ID'].tolist()
    t = process_map(try_many_times, fund_list, max_workers=5)
    content1=''
    content2=''
    content3=''
    for i in t:
        content1+=i[0]
        content2+=i[1]
        content3+=i[2]
    digest = time.strftime('%Y-%m-%d UTC(%H:%M)', time.localtime()) + '\n'
    digest=f'{digest}{get_daily_sentence()}⏱ {round((time.perf_counter()-start)/60,1)} 分钟'
    send_mpnews(title,content1+content2+content3,digest)

if __name__=='__main__':
    main()
    