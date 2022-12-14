# -*- coding: utf-8 -*-  
import time,requests,os,json
import pandas as pd
import numpy as np
from tqdm.contrib.concurrent import process_map
import random
from bisect import bisect_left

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

def get_his(fund_id):
    time.sleep(random.randint(1,2)+random.random())
    # 近1年
    url=f'https://www.dayfund.cn/fundvalue/{fund_id}_y.html'
    r=requests.get(url,headers=headers,timeout=30)
    df=pd.read_html(r.text,encoding='utf-8',header=0)[0]
    df=pd.DataFrame(df)
    df=df[['净值日期','基金名称','最新单位净值','最新累计净值']]
    df['最新单位净值']=df['最新单位净值'].astype(float)
    df['最新累计净值']=df['最新累计净值'].astype(float)
    df.dropna(subset=['净值日期','基金名称','最新单位净值','最新累计净值'],how='any',inplace=True)
    # 按照日期升序排序并重建索引
    df.sort_values(by='净值日期',axis=0,ascending=True,ignore_index=True,inplace=True)
    return(df)

def pd_jz(ljjz_data,ljjz,sio_content):
    ljjz_data.sort()
    num = round(bisect_left(ljjz_data,ljjz)/len(ljjz_data)*100,2)

    if num < 25:
        sio_content+=f'<p>🍏🍏🍏 <font color="green"><small>{num}%</small></font></p>'
    elif num < 50:
        sio_content+=f'<p>🍎🍏🍏 <font color="black"><small>{num}%</small></font></p>'
    elif num < 75:
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
    data=get_his(code)
    jzrq=data['净值日期'].values[-1]
    jjmc=data['基金名称'].values[-1]
    dwjz=data['最新单位净值'].values[-1]
    ljjz=data['最新累计净值'].values[-1]
    cache1,cache2=get_color(data['最新累计净值'].values) #求近20天均值极值点

    cache1=round(dwjz+(cache1-ljjz),3)
    cache2=round(dwjz+(cache2-ljjz),3)

    sio_content=f'<p><strong>{jzrq}</strong></p>'
    sio_content+=f'<p><strong>{jjmc}</strong></p>'
    sio_content=pd_jz(data['最新累计净值'].values,ljjz,sio_content)

    sio_content+=f'<p>📈{cache2}</p>'
    sio_content+=f'<p>📉{cache1}</p>'

    print(sio_content)
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