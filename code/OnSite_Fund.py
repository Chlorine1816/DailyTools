# -*- coding: utf-8 -*-  
import time,re,requests,os,json
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
from tqdm.contrib.concurrent import process_map

headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.36'}

corpid=os.environ['CORPID']  #公司id
agentid=os.environ['AGENTID']  #机器人id
corpsecret=os.environ['CORPSECRET']  #机器人secret
touser=os.environ['TOUSER']  #接收id
media_id=os.environ['MEDIA'] #图片id

#图文图文消息的标题
title=f'OnSite Fund (GitHub)'

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
        return(f'{content}\n{note}\n')
    except:
        return(f'Happy every day !\n')

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

def pd_jz(ljjz_data,lj,num1,num2,cache1,cache2,dwjz,sio_content):
    quantile=np.quantile
    #q1=round(np.min(ljjz_data),3) 
    q2=round(quantile(ljjz_data,0.25),3) 
    q3=round(quantile(ljjz_data,0.5),3) 
    q4=round(quantile(ljjz_data,0.75),3) 
    #q5=round(np.max(ljjz_data),3)

    #if lj >= q5:
    #    sio_content+=f'<p>🚦📈</p>'
    if lj > q4:
        sio_content+=f'<p>🚦🍎🍎🍎</p>'
    elif lj > q3:
        sio_content+=f'<p>🚦🍎🍎🍏</p>'
    elif lj > q2:
        sio_content+=f'<p>🚦🍎🍏🍏</p>'
    else:
        sio_content+=f'<p>🚦🍏🍏🍏</p>'

    dict_jz={num1:'📉',num2:'📈',dwjz:'🔸',cache1:'🟩',cache2:'🟥'}
    for i in sorted(dict_jz,reverse=True):
        sio_content+=f'<p>{dict_jz[i]}{i}</p>'
        
    return (sio_content)

def get_color(ljjz_data):
    mean=np.mean
    mean5=round(mean(ljjz_data[-5:]),3) #前5天净值均值
    mean10=round(mean(ljjz_data[-10:]),3)#前10天净值均值
    mean20=round(mean(ljjz_data[-20:]),3)#前20天净值均值

    return(min(mean5,mean10,mean20),max(mean5,mean10,mean20))
    '''
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
    '''

def get_num(ljjz_data):
    num1=sum(ljjz_data[-9:-4])-sum(ljjz_data[-4:])
    num2=sum(ljjz_data[-19:-9])-sum(ljjz_data[-9:])
    return(min(num1,num2),max(num1,num2))

def working(code):
    edate=time.strftime("%Y-%m-%d", time.localtime(time.time()))
    sdate=time.strftime("%Y-%m-%d", time.localtime(time.time()-86400*80))
    data=get_fund(code,per=30,sdate=sdate,edate=edate)
    data['单位净值']=data['单位净值'].astype(float)
    data['累计净值']=data['累计净值'].astype(float)
    data=data[['净值日期','累计净值','单位净值']]
    data=data.sort_values(by='净值日期',axis=0,ascending=True).reset_index(drop=True)
    ljjz_data=data['累计净值'].values[-50:]

    name=get_fund2(code)

    date=data['净值日期'].values[-1]
    dwjz=data['单位净值'].values[-1]
    ljjz=ljjz_data[-1]
    num1,num2=get_num(ljjz_data) #求大幅跌涨累计净值
    cache1,cache2=get_color(ljjz_data) #求近20天均值极值点

    num1=round(dwjz+(num1-ljjz),3) #大幅下跌单位净值
    num2=round(dwjz+(num2-ljjz),3) #大幅上涨单位净值

    cache1=round(dwjz+(cache1-ljjz),3)
    cache2=round(dwjz+(cache2-ljjz),3)

    sio_content=f'<p><strong>{date}</strong></p>'
    sio_content+=f'<p><strong>{name}</strong></p>'
    sio_content=pd_jz(ljjz_data,ljjz,num1,num2,cache1,cache2,dwjz,sio_content)

    return (sio_content)

def try_many_times(code):
    #最多尝试5次
    for _ in range(5):
        try:
            return(working(code))
        except:
            time.sleep(1.1)
        else:
            break
    return('')

def main():
    start=time.perf_counter()
    fund_list=pd.read_excel('./data/OnSite_FundList.xlsx',dtype={'ID': 'string'})

    fund_list=fund_list['ID'].tolist()
    t = process_map(try_many_times, fund_list, max_workers=5)
    sio_content=''
    for i in t:
        sio_content+=i
    sio_digest=time.strftime(f'%Y-%m-%d UTC(%H:%M)', time.localtime())+'\n'
    sio_digest=f'{sio_digest}{get_daily_sentence()}⏱ {round((time.perf_counter()-start)/60,1)} 分钟'
    send_mpnews(title,sio_content,sio_digest)

if __name__=='__main__':
    main()