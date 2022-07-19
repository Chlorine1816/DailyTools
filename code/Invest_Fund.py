# -*- coding: utf-8 -*-  
import time,requests,os,json
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
from multiprocessing import Pool
import random

headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.56'}

corpid=os.environ['CORPID']  #公司id
agentid=os.environ['AGENTID']  #机器人id
corpsecret=os.environ['CORPSECRET']  #机器人secret
media_id=os.environ['MEDIA'] #图片id
#touser=os.environ['TOUSER']  #接收id
touser='@all'  #接收id
#touser=f'Chlorine|HaiMing' #接收id

#图文图文消息的标题
title='Invest Fund (GitHub)'

def get_token():
    payload_access_token = {'corpid': corpid, 'corpsecret': corpsecret}
    token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
    r = requests.get(url=token_url, params=payload_access_token,headers=headers)
    dict_result = (r.json())
    return dict_result['access_token']

#发送图文信息
def send_mpnews(title,content,digest):
    time.sleep(1.2)
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
        r = requests.get(url)
        r = json.loads(r.text)
        content = r["content"]
        note = r["note"]
        return(f'{content}\n{note}\n')
    except:
        return(f'Happy every day !\n')

def get_his(fund_id):
    url=f'https://www.dayfund.cn/fundvalue/{fund_id}_q.html'
    r=requests.get(url,headers=headers)
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
    time.sleep(random.randint(1,2)+random.random())
    url=f'https://www.dayfund.cn/fundpre/{fund_id}.html'
    try:
        req=requests.get(url=url,headers=headers)
        req.encoding='utf-8'
        if req.status_code==200:
            html=req.text
    except:
        html=''
    bf=BeautifulSoup(html,'lxml')
    try:
        gszf=0
        gszf=bf.find_all(id='fvr_add')[0].text.strip()
        gszf=float(gszf.split(' ')[1].split('%')[0])
        if gszf == 0:
            return (True)
        else:
            return (gszf)
    except:
        return (True)

def get_fund2(fund_id):
    time.sleep(random.randint(1,2)+random.random())
    url=f'http://fundf10.eastmoney.com/jjjz_{fund_id}.html'
    #尝试5次
    for i in range(5):
        try:
            req=requests.get(url=url,headers=headers)
            req.encoding='utf-8'
            html=req.text
            bf=BeautifulSoup(html,'lxml')
            jz=bf.find_all('div',class_='bs_jz')
            jz=BeautifulSoup(str(jz),'lxml')
            #名称
            name=jz.find_all('h4',class_='title')[0].text
            #涨跌
            gszf=float(jz.find_all('span',id='fund_gszf')[0].text.strip('%'))
        except:
            time.sleep(1.1)
        else:
            return (name,gszf)
    #5次均失败 调用备用接口
    return (name,False)

def pd_jz(lj_data,jz):

    quantile=np.quantile
    q1=round(np.min(lj_data),4) + 0.0002
    q2=round(quantile(lj_data,0.25),4) 
    q3=round(quantile(lj_data,0.50),4) 
    q4=round(quantile(lj_data,0.75),4) 
    q5=round(np.max(lj_data),4) - 0.0002

    if (jz >= q5):
        return ('📈',-1)
    elif (jz > q4):
        return ('🍎🍎🍎',0)
    elif (jz > q3):
        return ('🍎🍎🍏',1)
    elif (jz > q2):
        return ('🍎🍏🍏',2)
    elif (jz > q1):
        return ('🍏🍏🍏',3)
    else:
        return ('📉',4)

def get_color(mean5,mean10,mean20):
    if (mean5 <= mean10 <= mean20):
        return('大幅下跌')
    elif(mean5 >= mean10 >= mean20):
        return('大幅上涨')
    elif (mean5 <= mean10)and(mean5 <= mean20)and(mean10 >= mean20):
        return ('破线向下')
    elif (mean5 >= mean10)and(mean5 >= mean20)and(mean10 <= mean20):
        return ('突破向上')
    else:
        return ('震荡筑底')

def working(code,moneylist):
    data=get_his(code)
    name,gszf=get_fund2(code) #获取当日 涨幅
    lj_data=data['最新累计净值'].values[-49:]
    dwjz=data['最新单位净值'].values[-1]

    if gszf==False :
        gszf=0
        lj_data=data['最新累计净值'].values[-50:]
        today_lj=lj_data[-1]
        color='black'
    else:
        dwjz=dwjz*gszf/100
        today_lj=round(lj_data[-1]+dwjz,4) #当日累计估值
        lj_data=np.append(lj_data,today_lj) #前49日累计净值+当日估值
        color='red' if gszf > 0 else 'green'

    mean=np.mean
    mean5=round(mean(lj_data[-5:]),4) #5日均值
    mean10=round(mean(lj_data[-10:]),4) #10日均值
    mean20=round(mean(lj_data[-20:]),4) #20日均值

    tip1=get_color(mean5,mean10,mean20)
    state,tip2=pd_jz(lj_data,today_lj)
    sio_content1=''
    sio_content2=''
    sio_content3=''
    if (tip2 <= 0)and(min(mean5,mean10,mean20)+0.0002 < today_lj < max(mean5,mean10,mean20)+0.0002):
        sio_content2=f'<p>{state}</p>'
        sio_content2+=f'<p><font color="red"><strong>{name}</strong></font><font color="{color}"><small> {gszf}%</small></font></p>'
        sio_content2+=f'<p><font color="red">可以卖出一部分</font><small> {tip1}</small></font></p>'
    elif(today_lj < min(mean5,mean10,mean20)-0.0002)and(gszf <= 0.5)and(tip2 > 0):
        sio_content1=f'<p>{state}</p>'
        sio_content1+=f'<p><font color="green"><strong>{name}</strong></font><font color="{color}"><small> {gszf}%</small></font></p>'
        sio_content1+=f'<p>买入 <font color="green">{moneylist[tip2]}</font> RMB<small> {tip1}</small></font></p>'
    else:
        sio_content3=f'<p>{state}</p>'
        sio_content3+=f'<p>{name}<font color="{color}"><small> {gszf}%</small></font></p>'
        sio_content3+=f'<p>再等等看吧<small> {tip1}</small></font></p>'

    return (sio_content1,sio_content2,sio_content3)

def try_many_times(code,moneylist):
    #最多尝试5次
    for _ in range(5):
        try:
            return(working(code,moneylist))
        except:
            time.sleep(1.1)
        else:
            break
    return('')

def main():
    start=time.perf_counter()
    fund_list=pd.read_excel('./data/Invest_FundList.xlsx',dtype={'ID': 'string'})
    code_list=fund_list['ID'].tolist()

    Zero=fund_list['Zero'].values
    One=fund_list['One'].values
    Two=fund_list['Two'].values
    Three=fund_list['Three'].values
    Four=fund_list['Four'].values

    pool=Pool(5)
    pool_data_list=[]
    for i,num in enumerate(code_list):
        moneylist=[Zero[i],One[i],Two[i],Three[i],Four[i]]
        pool_data_list.append(pool.apply_async(try_many_times,args=(num,moneylist)))

    print('- - - Start - - -',flush=True)
    pool.close()
    pool.join()
    print('- - - End - - -',flush=True)
    print('Get the Values ...',flush=True)

    content1=''
    content2=''
    content3=''
    for pool_data in pool_data_list:
        content1+=pool_data.get()[0]
        content2+=pool_data.get()[1]
        content3+=pool_data.get()[2]
    digest = time.strftime('%Y-%m-%d UTC(%H:%M)', time.localtime()) + '\n'
    digest=f'{digest}{get_daily_sentence()}⏱ {round((time.perf_counter()-start)/60,1)} 分钟'
    send_mpnews(title,content1+content2+content3,digest)

if __name__=='__main__':
    main()