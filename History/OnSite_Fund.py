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
touser=os.environ['TOUSER']  #接收id
media_id=os.environ['MEDIA'] #图片id

#图文图文消息的标题
title=f'OnSite Fund (GitHub)'
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
    url=f'https://www.dayfund.cn/fundvalue/{fund_id}.html'
    time.sleep(0.2)
    req=requests.get(url=url,headers=headers)
    req.encoding='utf-8'
    html=req.text
    bf=BeautifulSoup(html,'lxml')
    records=[]
    for row in bf.find_all('table',class_='mt1 clear')[0].find_all("tr"): 
        row_records = []
        for record in row.find_all('td'):
            val = record.contents
            # 处理空值
            if val == []:
                row_records.append(0)
            else:
                row_records.append(val[0])
        records.append(row_records)
    heads={}
    for i in records[0]:
        heads[i]=[]
    for i in records[1:]:
        if len(i)<5:
            continue
        for j,k in zip(i,heads):
            heads[k].append(j)
    heads=pd.DataFrame(heads)
    return(heads)

def get_fund(code,per=30,sdate='',edate='',proxies=None):
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
        req=requests.get(url=url,params=params,headers=headers)
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

def get_fund2(fund_id):
    url=f'http://fundf10.eastmoney.com/jjjz_{fund_id}.html'
    time.sleep(0.5)
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
    return (name)

def pd_jz(lj_data,lj,jz):
    quantile=np.quantile
    mean=np.mean
    mean5=round(mean(lj_data[-5:]),3) #前5天净值均值
    mean10=round(mean(lj_data[-10:]),3)#前10天净值均值
    mean20=round(mean(lj_data[-20:]),3)#前20天净值均值
    q1=round(np.min(lj_data)*jz/lj,3) 
    q2=round(quantile(lj_data,0.2)*jz/lj,3) 
    q3=round(quantile(lj_data,0.4)*jz/lj,3) 
    q4=round(quantile(lj_data,0.6)*jz/lj,3) 
    q5=round(quantile(lj_data,0.8)*jz/lj,3) 
    q6=round(np.max(lj_data)*jz/lj,3)
  
    dict_jz={q1:'🍏',q2:'🍏',q3:'🍏',q4:'🍎',q5:'🍎',q6:'🍎'}
    dict_jz[jz]=get_color(mean5,mean10,mean20)

    for i in sorted(dict_jz,reverse=True):
        sio_content.write(f'<p>{dict_jz[i]}{i}</p>')

def get_color(mean5,mean10,mean20):
    if (mean5 <= mean10 <= mean20):
        return('👇')
    elif(mean5 >= mean10 >= mean20):
        return('👆')
    elif(mean5 <= mean10)and(mean5 >= mean20):
        return('👇')
    elif(mean5 >= mean10)and(mean5 <= mean20):
        return('👆')
    else:
        return('👉')

def working(code):
    #获取净值信息
    #data=get_his(code)
    edate=time.strftime("%Y-%m-%d", time.localtime(time.time()))
    sdate=time.strftime("%Y-%m-%d", time.localtime(time.time()-86400*80))
    data=get_fund(code,per=30,sdate=sdate,edate=edate)
    data['单位净值']=data['单位净值'].astype(float)
    data['累计净值']=data['累计净值'].astype(float)
    # 按照日期升序排序并重建索引
    #data.drop(['上期单位净值','上期累计净值','当日增长值'],axis=1,inplace=True)
    data=data[['净值日期','累计净值','单位净值']]
    data=data.sort_values(by='净值日期',axis=0,ascending=True).reset_index(drop=True)
    lj_data=data['累计净值'].values[-50:]
    #name=data['基金名称'].values[-1]+' '+str(data['基金代码'].values[-1])
    name=get_fund2(code)
    jz_date=data['净值日期'].values[-1]
    jz_data=round(data['单位净值'].values[-1],3)
    sio_content.write(f'<p><strong>{jz_date}</strong></p>')
    sio_content.write(f'<p><strong>{name}</strong></p>')
    pd_jz(lj_data,lj_data[-1],jz_data)

if __name__=='__main__':
    start=time.perf_counter()
    fund_list=pd.read_excel('./data/OnSite_FundList.xlsx',dtype={'ID': 'string'})
    get_daily_sentence()
    for code in fund_list['ID']:
        time.sleep(1)
        #最多尝试10次
        for t in range(10):
            try:
                working(code)
            except:
                time.sleep(0.5)
            else:
                break
    sio_digest.write(f'⏱ {round((time.perf_counter()-start)/60,1)} 分钟')
    send_mpnews(title,sio_content.getvalue(),sio_digest.getvalue())