# -*- coding: utf-8 -*-  
import time,requests,os,json,re
import pandas as pd
import numpy as np
from tqdm.contrib.concurrent import process_map
import random
from bisect import bisect_right
from bs4 import BeautifulSoup

headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36 Edg/99.0.1150.36'}

corpid=os.environ['CORPID']  #公司id
agentid=os.environ['AGENTID']  #机器人id
corpsecret=os.environ['CORPSECRET']  #机器人secret
touser=os.environ['TOUSER']  #接收id
media_id=os.environ['MEDIA'] #图片id

#图文图文消息的标题
title = 'OnSite Fund (GitHub)'

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
    except Exception:
        return(f'Happy every day !\n')

def get_his(code,per=45,sdate='',edate='',proxies=None):
    time.sleep(random.randint(1,2)+random.random())
    url='http://fund.eastmoney.com/f10/F10DataApi.aspx'
    params = {'type': 'lsjz', 'code': code, 'page':1,'per': per, 'sdate': sdate, 'edate': edate}
    r=requests.get(url,params=params,headers=headers,timeout=30)
    # 获取总页数
    pattern = re.compile(r'pages:(.*),')
    pages = int(re.search(pattern,r.text)[1])
    df=pd.read_html(r.text,encoding='utf-8',header=0)[0]
    for page in range(2,pages+1):
        time.sleep(0.2)
        params['page']=page
        r=requests.get(url,params=params,headers=headers,timeout=30)
        df=pd.concat([df,pd.read_html(r.text,encoding='utf-8',header=0)[0]])
    df=df[['净值日期','单位净值','累计净值']]
    df.sort_values('净值日期',inplace=True,ignore_index=True)
    return df

def get_fund_name(fund_id):
    time.sleep(random.randint(1,2)+random.random())
    url=f'http://fundf10.eastmoney.com/jjjz_{fund_id}.html'
    try:
        req=requests.get(url=url,headers=headers)
        req.encoding='utf-8'
        if req.status_code==200:
            html=req.text
    except Exception:
        html=''
    bf=BeautifulSoup(html,'lxml')
    jz=bf.find_all('div',class_='bs_jz')
    jz=BeautifulSoup(str(jz),'lxml')

    return jz.find_all('h4',class_='title')[0].text

def pd_jz(ljjz_data,ljjz,sio_content):
    ljjz_data.sort()
    num = round(bisect_right(ljjz_data,ljjz)/len(ljjz_data)*100,1)
    if num < 20:
        sio_content+=f'<p>🍏🍏🍏 <font color="green"><small>{num}%</small></font></p>'
    elif num < 50:
        sio_content+=f'<p>🍎🍏🍏 <font color="black"><small>{num}%</small></font></p>'
    elif num < 80:
        sio_content+=f'<p>🍎🍎🍏 <font color="black"><small>{num}%</small></font></p>'
    else:
        sio_content+=f'<p>🍎🍎🍎 <font color="red"><small>{num}%</small></font></p>'    
    return sio_content

def get_color(ljjz_data):
    mean=np.mean
    mean5=round(mean(ljjz_data[-5:]),3) #前5天净值均值
    mean10=round(mean(ljjz_data[-10:]),3)#前10天净值均值
    mean20=round(mean(ljjz_data[-20:]),3)#前20天净值均值
    return (min(mean5,mean10,mean20),max(mean5,mean10,mean20))

def working(code):
    edate=time.strftime("%Y-%m-%d", time.localtime(time.time()))
    sdate=time.strftime("%Y-%m-%d", time.localtime(time.time()-365*24*3600))
    data=get_his(code=code,sdate=sdate,edate=edate)
    jjmc=get_fund_name(code)
    #num20=data['累计净值'].quantile(q=0.2) # 累计净值分位数
    jzrq=data['净值日期'].values[-1]
    difference=data['累计净值'].values[-1]-data['单位净值'].values[-1] # 累计与单位的差值
    min20,max20=get_color(data['累计净值'].values) #求近20天累计均值极值点

    min20=round(min20-difference,3)
    max20=round(max20-difference,3)
    #num20=round(num20-difference,3)

    sio_content=f'<p><strong>{jzrq}</strong></p>'
    sio_content+=f'<p><strong>{jjmc}</strong></p>'
    sio_content=pd_jz(data['累计净值'].values,data['累计净值'].values[-1],sio_content)

    dict_jz={min20:'📉',max20:'📈',data['单位净值'].values[-1]:'🚩'}
    for i in sorted(dict_jz,reverse=True):
        sio_content+=f'<p>{dict_jz[i]}{i}</p>'

    return sio_content

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
    fund_list=pd.read_excel('./data/OnSite_FundList.xlsx',dtype={'ID': 'string'})

    fund_list=fund_list['ID'].tolist()
    t = process_map(try_many_times, fund_list, max_workers=5)
    sio_content = ''.join(t)
    sio_digest = time.strftime('%Y-%m-%d UTC(%H:%M)', time.localtime()) + '\n'
    sio_digest=f'{sio_digest}{get_daily_sentence()}⏱ {round((time.perf_counter()-start)/60,1)} 分钟'
    send_mpnews(title,sio_content,sio_digest)

if __name__=='__main__':
    main()