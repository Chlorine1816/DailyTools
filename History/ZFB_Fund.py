# -*- coding: utf-8 -*-  
import time,re,requests,os,json
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
from io import StringIO

headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.56'}

corpid=os.environ['CORPID']  #公司id
agentid=os.environ['AGENTID']  #机器人id
corpsecret=os.environ['CORPSECRET']  #机器人secret
media_id=os.environ['MEDIA'] #图片id
touser=os.environ['TOUSER']  #接收id
#touser='Chlorine'

#图文图文消息的标题
title=f'ZFB Fund (GitHub)'
#图文消息的描述，不超过512个字节
sio_digest=StringIO('')
sio_digest.write(time.strftime(f'%Y-%m-%d UTC(%H:%M)', time.localtime())+'\n')
#图文消息的内容，支持html标签，不超过666 K个字节
sio_content0=StringIO('') #不操作
sio_content1=StringIO('') #买入
sio_content2=StringIO('') #卖出

def get_token():
    payload_access_token = {'corpid': corpid, 'corpsecret': corpsecret}
    token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
    r = requests.get(url=token_url, params=payload_access_token,headers=headers)
    dict_result = (r.json())
    return dict_result['access_token']

#发送图文信息
def send_mpnews(title,content,digest):
    time.sleep(1)
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
        sio_digest.write(f'{content}\n{note}\n')
    except:
        sio_digest.write(f'Happy!\n')

def get_his(fund_id):
    url=f'https://www.dayfund.cn/fundvalue/{fund_id}_q.html'
    r=requests.get(url,headers=headers)
    df=pd.read_html(r.text,encoding='utf-8',header=0)[0]
    df=pd.DataFrame(df)
    df=df[['净值日期','基金名称','最新单位净值','最新累计净值']]
    df['最新单位净值']=df['最新单位净值'].astype(float)
    df['最新累计净值']=df['最新累计净值'].astype(float)
    df.dropna(subset=['净值日期','基金名称','最新单位净值','最新累计净值'],how='any',inplace=True)
    return(df)

def get_fund1(fund_id):
    url=f'https://www.dayfund.cn/fundpre/{fund_id}.html'
    time.sleep(0.5)
    try:
        req=requests.get(url=url,headers=headers)
        req.encoding='utf-8'
        if req.status_code==200:
            html=req.text
    except:
        html=''
    bf=BeautifulSoup(html,'lxml')
    gszf=0
    gszf=bf.find_all(id='fvr_add')[0].text.strip()
    gszf=float(gszf.split(' ')[1].split('%')[0])
    return gszf

def get_fund2(fund_id):
    url=f'http://fundf10.eastmoney.com/jjjz_{fund_id}.html'
    time.sleep(0.2)
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
    return (name,get_fund1(fund_id))

def pd_jz(lj_data,jz):
    quantile=np.quantile
    q1=round(np.min(lj_data),4) 
    q2=round(quantile(lj_data,0.25),4) 
    q3=round(quantile(lj_data,0.50),4) 
    q4=round(quantile(lj_data,0.75),4) 
    q5=round(np.max(lj_data),4)

    if (jz >= q5):
        return('📈',-1)
    elif (jz > q4):
        return ('🍎🍎🍎',0)
    elif (jz > q3):
        return ('🍎🍎🍏',10)
    elif (jz > q2):
        return ('🍎🍏🍏',15)
    elif (jz > q1):
        return ('🍏🍏🍏',20)
    else:
        return ('📉',25)

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

def working(code):
    #获取历史净值
    data=get_his(code)
    # 按照日期升序排序并重建索引
    data=data.sort_values(by='净值日期',axis=0,ascending=True,ignore_index=True)
    dwjz=data['最新单位净值'].values[-1]
    lj_data=data['最新累计净值'].values[-49:]
    name,gszf=get_fund2(code) #获取当日 涨幅
    dwjz=dwjz*gszf/100
    today_lj=round(lj_data[-1]+dwjz,4) #当日累计估值
    lj_data=np.append(lj_data,today_lj) #前49日累计净值+当日估值

    mean=np.mean
    mean5=round(mean(lj_data[-5:]),4) #5日均值
    mean10=round(mean(lj_data[-10:]),4) #10日均值
    mean20=round(mean(lj_data[-20:]),4) #20日均值

    tip1=get_color(mean5,mean10,mean20)
    state,tip2=pd_jz(lj_data,today_lj)
    color='red' if gszf > 0 else 'green'
    if(tip2 <= 0)and((tip1=='大幅上涨') or (tip1=='破线向下')):
        sio_content2.write(f'<p>{state}</p>')
        sio_content2.write(f'<p><font color="red"><strong>{name}</strong></font><font color="{color}"><small> {gszf}%</small></font></p>')
        sio_content2.write(f'<p><font color="red">可以卖出一部分</font></p>')
    elif ((tip1=='大幅下跌')and (gszf <= 0))or (tip1=='震荡筑底'):
        sio_content1.write(f'<p>{state}</p>')
        sio_content1.write(f'<p><font color="green"><strong>{name}</strong></font><font color="{color}"><small> {gszf}%</small></font></p>')
        sio_content1.write(f'<p>买入 <font color="green">{tip2}</font> RMB</p>')
    else:
        sio_content0.write(f'<p>{state}</p>')
        sio_content0.write(f'<p>{name}<font color="{color}"><small> {gszf}%</small></font></p>')
        sio_content0.write(f'<p>再等等看吧</p>')

if __name__=='__main__':
    start=time.perf_counter()
    fund_list=pd.read_excel('./data/ZFB_FundList.xlsx',dtype={'ID': 'string'})
    get_daily_sentence()
    for code in fund_list['ID']:
        time.sleep(1)
        #最多尝试5次
        for t in range(5):
            try:
                working(code)
            except:
                time.sleep(1.1)
            else:
                break
    sio_digest.write(f'⏱ {round((time.perf_counter()-start)/60,1)} 分钟')
    send_mpnews(title,sio_content1.getvalue()+sio_content2.getvalue()+sio_content0.getvalue(),sio_digest.getvalue())