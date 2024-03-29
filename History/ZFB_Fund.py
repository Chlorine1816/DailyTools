# -*- coding: utf-8 -*-  
import time,requests,os,json
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
from tqdm.contrib.concurrent import process_map
import random
from bisect import bisect_right

headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47'}

corpid=os.environ['CORPID']  #公司id
agentid=os.environ['AGENTID']  #机器人id
corpsecret=os.environ['CORPSECRET']  #机器人secret
media_id=os.environ['MEDIA'] #图片id
touser=os.environ['TOUSER']  #接收id
#touser='Chlorine'

#图文图文消息的标题
title='ZFB Fund (GitHub)'

def get_token():
    payload_access_token = {'corpid': corpid, 'corpsecret': corpsecret}
    token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
    r = requests.get(url=token_url, params=payload_access_token,headers=headers)
    dict_result = (r.json())
    return dict_result['access_token']

#发送图文信息
def send_mpnews(title,content,digest):
    access_token=get_token()
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
    data = {
        "touser":touser, #接收消息人员id
        "agentid": agentid, #机器人id
        'msgtype':'mpnews',
        'mpnews': {
            'articles':[
                {
                    "title": title, #必须
                    "thumb_media_id": media_id, #必须
                    "author": "Chlorine", #非必须 作者
                    "content": content, #必须 不超过666 K个字节
                    "digest": digest #非必须 不超过512个字节
                }
            ]
            },
        "safe": 0 #是否加密
        }
    data = json.dumps(data, ensure_ascii=False)
    requests.post(url=url, data=data.encode("utf-8").decode("latin1"))

def get_daily_sentence():
    url = "http://open.iciba.com/dsapi/"
    try:
        r = requests.get(url,timeout=5)
        r = json.loads(r.text)
        content = r["content"]
        note = r["note"]
        return(f'{content}\n{note}\n')
    except Exception:
        return(f'Happy every day !\n')

def get_his(fund_id):
    time.sleep(random.randint(1,2)+random.random())
    #近1季度
    url=f'https://www.dayfund.cn/fundvalue/{fund_id}_q.html'
    r=requests.get(url,headers=headers,timeout=22)
    df=pd.read_html(r.text,encoding='utf-8',header=0)[0]
    df=pd.DataFrame(df)
    df=df[['净值日期','基金名称','最新单位净值','最新累计净值']]
    df['最新单位净值']=df['最新单位净值'].astype(float)
    df['最新累计净值']=df['最新累计净值'].astype(float)
    df.dropna(subset=['净值日期','基金名称','最新单位净值','最新累计净值'],how='any',inplace=True)
    # 按照日期升序排序并重建索引
    df.sort_values(by='净值日期',axis=0,ascending=True,ignore_index=True,inplace=True)
    return(df)

def get_fund1(fund_id):
    url=f'https://www.dayfund.cn/fundpre/{fund_id}.html'
    time.sleep(random.randint(1,2)+random.random())
    try:
        req=requests.get(url=url,headers=headers,timeout=22)
        req.encoding='utf-8'
        if req.status_code==200:
            html=req.text
    except Exception:
        html=''
    bf=BeautifulSoup(html,'lxml')

    try:
        gszf=0
        gszf=bf.find_all(id='fvr_add')[0].text.strip()
        gszf=float(gszf.split(' ')[1].split('%')[0])
        return True if gszf == 0 else gszf
    except Exception:
        return (True)

def get_fund2(fund_id):
    time.sleep(random.randint(1,2)+random.random())
    url=f'http://fundf10.eastmoney.com/jjjz_{fund_id}.html'
    #尝试5次
    for _ in range(5):
        try:
            req=requests.get(url=url,headers=headers,timeout=22)
            req.encoding='utf-8'
            html=req.text
            bf=BeautifulSoup(html,'lxml')
            jz=bf.find_all('div',class_='bs_jz')
            jz=BeautifulSoup(str(jz),'lxml')
            #名称
            name=jz.find_all('h4',class_='title')[0].text
            #涨跌
            gszf=float(jz.find_all('span',id='fund_gszf')[0].text.strip('%'))
        except Exception:
            time.sleep(1.1)
        else:
            return (name,gszf)
    #5次均失败 调用备用接口
    return (name,False)

def pd_jz(lj_data,jz):
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

def get_color(ljjz_data):
    mean=np.mean
    mean5=round(mean(ljjz_data[-5:]),4) #前5天净值均值
    mean10=round(mean(ljjz_data[-10:]),4)#前10天净值均值
    mean20=round(mean(ljjz_data[-20:]),4)#前20天净值均值
    return(min(mean5,mean10,mean20),max(mean5,mean10,mean20))

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
    