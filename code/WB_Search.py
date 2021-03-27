import requests,json,time,os
from bs4 import BeautifulSoup
from io import StringIO
from requests_toolbelt import MultipartEncoder

url='https://s.weibo.com/top/summary?'
headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.74'}
data={'cate':'realtimehot'}

corpid=os.environ['CORPID']  #公司id
agentid=os.environ['AGENTID']  #机器人id
corpsecret=os.environ['CORPSECRET']  #机器人secret
touser=os.environ['TOUSER']  #接收id
media_id=os.environ['MEDIA'] #图片id

def get_token():
    payload_access_token = {'corpid': corpid, 'corpsecret': corpsecret}
    token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
    r = requests.get(url=token_url, params=payload_access_token,headers=headers)
    dict_result = (r.json())
    return dict_result['access_token']

#上传文件
def upload_file(filepath,filename,access_token):
    headers = {"content-type": "multipart/form-data"}
    url = f"https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=image"
    m=MultipartEncoder(fields={'image':(filename,open(filepath+filename,'rb'),f'image/plain')})
    r = json.loads(requests.post(url=url,data=m,headers=headers).content)
    return (r['media_id'])

#发送图文信息
def send_mpnews(title,content,digest):
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

def get_wb(top_num):
    url='https://s.weibo.com/top/summary?'
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.74'}
    data={'cate':'realtimehot'}
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
    #图文图文消息的标题
    title=f'微博热搜'
    #图文消息的描述，不超过512个字节
    sio_digest=StringIO('')
    sio_digest.write(time.strftime("%Y-%m-%d", time.localtime())+'\n')
    sio_digest.write(f'🔥'+txt[1].text+'\n')
    sio_digest.write(f'🔥'+txt[2].text+'\n')
    sio_digest.write(f'🔥'+txt[3].text+'\n')
    sio_digest.write(f'点击查看更多...')
    #图文消息的内容，支持html标签，不超过666 K个字节
    sio_content=StringIO('')
    for i in range(top_num):
        #编号
        sio_content.write(f'['+ranktop[i].text+'] ') 
        #热搜内容
        wburl='https://s.weibo.com/'+txt[i+1].get('href') 
        sio_content.write(f'<a href=\"{wburl}\">'+txt[i+1].text+'</a>\n')
        #热度
        #sio_content.write(f'热度 🔥'+num[i].text+'\n')
        sio_content.write(f'<div>热度🔥 <font color=\"warning\">'+num[i].text+'</font></div>')
    return (title,sio_content.getvalue(),sio_digest.getvalue())

if __name__=='__main__': 
    #filepath=f'./data/'
    #filename=f'qq.jpg' 
    access_token=get_token()
    #media_id=upload_file(filepath,filename,access_token)
    title,content,digest=get_wb(top_num=50)
    send_mpnews(title,content,digest)