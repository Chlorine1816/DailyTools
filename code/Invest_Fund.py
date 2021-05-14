# -*- coding: utf-8 -*-  
import time,re,requests,os,json
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
from io import StringIO

headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.74'}

corpid=os.environ['CORPID']  #公司id
agentid=os.environ['AGENTID']  #机器人id
corpsecret=os.environ['CORPSECRET']  #机器人secret
media_id=os.environ['MEDIA'] #图片id
touser=f'@all'  #接收id

#图文图文消息的标题
title=f'Invest Fund'
#图文消息的描述，不超过512个字节
sio_digest=StringIO('')
sio_digest.write(time.strftime(f'%Y-%m-%d UTC(%H:%M)', time.localtime())+'\n')
#图文消息的内容，支持html标签，不超过666 K个字节
sio_content=StringIO('')

def get_token():
    payload_access_token = {'corpid': corpid, 'corpsecret': corpsecret}
    token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
    r = requests.get(url=token_url, params=payload_access_token,headers=headers)
    dict_result = (r.json())
    return dict_result['access_token']

#发送图文信息
def send_mpnews(title,content,digest):
    time.sleep(0.2)
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
    r = requests.get(url)
    r = json.loads(r.text)
    content = r["content"]
    note = r["note"]
    sio_digest.write(f'{content}\n{note}\n')
    return None

def get_fund(code,per=10,sdate='',edate='',proxies=None):
    url='http://fund.eastmoney.com/f10/F10DataApi.aspx'
    params = {'type': 'lsjz', 'code': code, 'page':1,'per': per, 'sdate': sdate, 'edate': edate}
    req=requests.get(url=url,params=params,headers=headers)
    req.encoding='utf-8'   
    html=req.text
    bf=BeautifulSoup(html,'lxml')
    # 获取总页数
    pattern=re.compile(r'pages:(.*),')
    result=re.search(pattern,html).group(1)
    pages=int(result)
    # 获取表头
    heads = []
    for head in bf.find_all("th"):
        heads.append(head.contents[0])
    # 数据存取列表
    records = []
    # 从第1页开始抓取所有页面数据
    page=1
    while page<=pages:
        time.sleep(0.2)
        params = {'type': 'lsjz', 'code': code, 'page':page,'per': per, 'sdate': sdate, 'edate': edate}
        req=requests.get(url=url,params=params,headers=headers,timeout=22)
        req.encoding='utf-8'   
        html=req.text
        bf=BeautifulSoup(html,'lxml')
        for row in bf.find_all("tbody")[0].find_all("tr"): 
            row_records = []
            for record in row.find_all('td'):
                val = record.contents
                # 处理空值
                if val == []:
                    row_records.append(0)
                else:
                    row_records.append(val[0])
            records.append(row_records)
        page+=1
    data=pd.DataFrame()
    records=np.array(records)
    for col,col_name in enumerate(heads):
        data[col_name]=records[:,col]
    return data

def get_fund1(fund_id):
    url=f'https://www.dayfund.cn/fundpre/{fund_id}.html'
    time.sleep(0.2)
    try:
        req=requests.get(url=url,headers=headers)
        req.encoding='utf-8'
        if req.status_code==200:
            html=req.text
    except:
        html=''
    bf=BeautifulSoup(html,'lxml')
    gszf=bf.find_all(id='fvr_add')[0].text.strip()
    gszf=float(gszf.split(' ')[1].split('%')[0])
    return gszf

def get_fund2(fund_id):
    url=f'http://fundf10.eastmoney.com/jjjz_{fund_id}.html'
    time.sleep(0.2)
    try:
        req=requests.get(url=url,headers=headers)
        req.encoding='utf-8'
        if req.status_code==200:
            html=req.text
    except:
        html=''
    bf=BeautifulSoup(html,'lxml')
    jz=bf.find_all('div',class_='bs_jz')
    jz=BeautifulSoup(str(jz),'lxml')
    #名称
    name=jz.find_all('h4',class_='title')[0].text
    #涨跌
    fund_gszf=float(jz.find_all('span',id='fund_gszf')[0].text.strip('%'))
    return (name,fund_gszf)

def writing(title,name,news,tip1,tip2):
    sio_content.write(f'<div>{title}</div>')
    sio_content.write(f'<div>{name}</div>')
    sio_content.write(f'<div>{news}</div>')
    sio_content.write(f'<div>买入 {tip1+tip2} 元</div>')
    return None

def pd_jz(lj_data,jz):
    q1=round(np.min(lj_data),3) #50日最小值
    q2=round(np.quantile(lj_data,0.25),3) #50日四分位数
    q3=round(np.quantile(lj_data,0.5),3) #50日四分位数
    q4=round(np.quantile(lj_data,0.75),3) #50日四分位数
    q5=round(np.max(lj_data),3) #50日最大值
    if (jz >= q5):
        return ('💗💗💗💗💗',0)
    elif (jz >= q4):
        return ('💗💗💗💗💚',0)
    elif (jz >= q3):
        return ('💗💗💗💚💚',0)
    elif (jz >= q2):
        return ('💗💗💚💚💚',0)
    elif (jz >= q1):
        return ('💗💚💚💚💚',10)
    else:
        return ('💚💚💚💚💚',10)

def working(code):
    #获取净值信息
    edate=time.strftime("%Y-%m-%d", time.localtime(time.time()))
    sdate=time.strftime("%Y-%m-%d", time.localtime(time.time()-6666666))
    data=get_fund(code,per=49,sdate=sdate,edate=edate)
    data['单位净值']=data['单位净值'].astype(float)
    data['累计净值']=data['累计净值'].astype(float)
    data['日增长率']=data['日增长率'].str.strip('%').astype(float)
    # 按照日期升序排序并重建索引
    data.drop(['申购状态','赎回状态','分红送配'],axis=1,inplace=True)
    data=data.sort_values(by='净值日期',axis=0,ascending=True).reset_index(drop=True)
    lj_data=data['累计净值'].values[-49:]
    gszf1=get_fund1(code) #基金速查网 估值涨幅
    name,gszf2=get_fund2(code) #天天基金网 估值涨幅
    today_lj=round(lj_data[-1]*(1+(gszf1+gszf2)/2/100),4) #当日累计估值
    lj_data=np.append(lj_data,today_lj) #前49日累计净值+当日估值

    mean5=round(np.mean(lj_data[-5:]),3) #5日均值
    mean10=round(np.mean(lj_data[-10:]),3)#10日均值
    mean30=round(np.mean(lj_data[-30:]),3)#30日均值

    state,tip1=pd_jz(lj_data,today_lj)

    if (mean5 > mean10 > mean30):
        news=f'<div><font color=\"warning\">大幅上涨</font></div>'
        name=f'<div><font color=\"warning\">{name}</font></div>'
        tip2=0
    elif (mean5 < mean10 < mean30):
        news=f'<div><font color=\"info\">大幅下跌</font></div>'
        name=f'<div><font color=\"info\">{name}</font></div>'
        tip2=20
    elif ((mean5 >= mean10)and(mean10 <= mean30))or((mean5 <= mean10)and(mean10 >= mean30)):
        news=f'<div><font color=\"warning\">上涨</font></div>'
        name=f'<div><font color=\"warning\">{name}</font></div>'
        tip2=0
    elif ((mean5 <= mean10)and(mean10 >= mean30))or((mean5 >= mean10)and(mean10 <= mean30)):
        news=f'<div><font color=\"info\">下跌</font></div>'
        name=f'<div><font color=\"info\">{name}</font></div>'
        tip2=10
    else:
        news=f'<div>未知</div>'
        name=f'<div>{name}</div>'
        tip2=0
    writing(state,name,news,tip1,tip2)
    return None

if __name__=='__main__':
    start=time.perf_counter()
    fund_list=pd.read_excel('./data/Invest_FundList.xlsx',dtype={'ID': 'string'})
    get_daily_sentence()
    for i in range(fund_list.shape[0]):
        time.sleep(0.2)
        code=fund_list['ID'].values[i]
        working(code)
    sio_digest.write(f'⏱ {round((time.perf_counter()-start)/60,1)} 分钟')
    send_mpnews(title,sio_content.getvalue(),sio_digest.getvalue())