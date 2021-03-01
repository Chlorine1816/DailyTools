import requests,json,time,os
from bs4 import BeautifulSoup
from io import StringIO

url='https://s.weibo.com/top/summary?'
headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.74'}
data={'cate':'realtimehot'}

corpid=os.environ['CORPID']  #公司id
agentid=os.environ['AGENTID']  #机器人id
corpsecret=os.environ['CORPSECRET']  #机器人secret
touser=os.environ['TOUSER']  #接收id

def get_token(corpid=None,corpsecret=None):
    payload_access_token = {'corpid': corpid, 'corpsecret': corpsecret}
    token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
    r = requests.get(url=token_url, params=payload_access_token,headers=headers)
    dict_result = (r.json())
    return dict_result['access_token']

#发送信息
def send_message(touser,access_token,message):
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
    data = {
        "touser":touser, #接收消息人员id
        "agentid": agentid, #机器人id
        'msgtype':'text',
        'text': {
            "content":message.getvalue()
            },
        "safe": 0 #是否加密
        }
    data = json.dumps(data, ensure_ascii=False)
    requests.post(url=url, data=data.encode("utf-8").decode("latin1"))

def send_mpnews(media_id,access_token):
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
    data = {
        "touser":'Chlorine', #接收消息人员id
        "agentid": agentid, #机器人id
        'msgtype':'mpnews',
        'mpnews': {
            'articles':[
                {
                    "title": "🚀微博热搜", #必须
                    "thumb_media_id": media_id, #必须
                    "author": "Chlorine", #非必须 作者
                    "content": '详情', #必须 不超过666 K个字节
                    "digest": "图文消息的描述" #非必须 不超过512个字节
                }
            ]
            },
        "safe": 0 #是否加密
        }
    data = json.dumps(data, ensure_ascii=False)
    requests.post(url=url, data=data.encode("utf-8").decode("latin1"))

if __name__=='__main__': 
    sio=StringIO('')
    sio.write(f'微博热搜🚀\n')
    sio.write(time.strftime("%Y-%m-%d %H", time.localtime())+':00\n\n')

    try:
        req=requests.get(url=url,params=data,headers=headers)
        req.encoding='utf-8'
        if req.status_code==200:
            html=req.text
    except:
        html=''

    div_bf=BeautifulSoup(html,'lxml')
    ranktop=div_bf.find_all('td',class_='td-01 ranktop')

    ranktxt=div_bf.find_all('td',class_='td-02')
    ranktxt=BeautifulSoup(str(ranktxt),'lxml')
    txt=ranktxt.find_all('a')
    num=ranktxt.find_all('span')
    
    for i in range(10):
        #编号
        sio.write(ranktop[i].text+' ') 
        #热搜内容
        wburl='https://s.weibo.com/'+txt[i+1].get('href') 
        sio.write(f'<a href=\"{wburl}\">'+txt[i+1].text+'</a>\n')
        #热度
        sio.write('🔥'+num[i].text[:-4]+'W\n')
    
    access_token=get_token(corpid=corpid,corpsecret=corpsecret)
    send_message(touser=touser,access_token=access_token,message=sio)