# coding=utf-8
import os,requests, time, re, rsa, base64,random,json
from io import StringIO

s = requests.Session()
headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.74'}

username=os.environ['USERNAME'] #帐号
password=os.environ['PASSWORD'] #密码
corpid=os.environ['CORPID']  #公司id
agentid=os.environ['AGENTID']  #机器人id
corpsecret=os.environ['CORPSECRET']  #机器人secret
touser=os.environ['TOUSER']  #接收id
media_id=os.environ['MEDIA'] #图片id

#程序休眠时间
sleep_time=random.randint(11,22)

#图文图文消息的标题
title=f'天翼云盘签到'
#图文消息的描述，不超过512个字节
sio_digest=StringIO('')
sio_digest.write(time.strftime("%Y年%m月%d日", time.localtime())+'\n')
sio_digest.write(f'Sleep {sleep_time} S 🔥 \nFrom {username[-4:]} 🔥\n点击查看更多...')
#图文消息的内容，支持html标签，不超过666 K个字节
sio=StringIO('')

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

def main(arg1,arg2):
    if(username == "" or password == ""):
        sio.write(f'<div>签到失败：用户名或密码为空，请设置!</div>')
        sio_content = sio.getvalue()
        pushWechat(sio_content)
        return None
    msg = login(username, password)
    if(msg == "error"):
        sio_content = sio.getvalue()
        pushWechat(sio_content)
        return None
    else:
        pass
    rand = str(round(time.time()*1000))
    surl = f'https://api.cloud.189.cn/mkt/userSign.action?rand={rand}&clientType=TELEANDROID&version=8.6.3&model=SM-G930K'
    url = f'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN&activityId=ACT_SIGNIN'
    url2 = f'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN_PHOTOS&activityId=ACT_SIGNIN'
    headers = {
        'User-Agent':'Mozilla/5.0 (Linux; Android 5.1.1; SM-G930K Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 Ecloud/8.6.3 Android/22 clientId/355325117317828 clientModel/SM-G930K imsi/460071114317824 clientChannelId/qq proVersion/1.0.6',
        "Referer" : "https://m.cloud.189.cn/zhuanti/2016/sign/index.jsp?albumBackupOpened=1",
        "Host" : "m.cloud.189.cn",
        "Accept-Encoding" : "gzip, deflate",
    }
    #签到
    response = s.get(surl,headers=headers)
    netdiskBonus = response.json()['netdiskBonus']
    if(response.json()['isSign'] == "false"):
        sio.write(f'<div>签到提示：未签到，获得{netdiskBonus}M 🎉</div>')
    else:
        sio.write(f'<div>签到提示：已签到，获得{netdiskBonus}M 🎉</div>')
    headers = {
        'User-Agent':'Mozilla/5.0 (Linux; Android 5.1.1; SM-G930K Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.136 Mobile Safari/537.36 Ecloud/8.6.3 Android/22 clientId/355325117317828 clientModel/SM-G930K imsi/460071114317824 clientChannelId/qq proVersion/1.0.6',
        "Referer" : "https://m.cloud.189.cn/zhuanti/2016/sign/index.jsp?albumBackupOpened=1",
        "Host" : "m.cloud.189.cn",
        "Accept-Encoding" : "gzip, deflate",
    }
    #第一次抽奖
    response = s.get(url,headers=headers)
    if ("errorCode" in response.text):
        if(response.json()['errorCode'] == "User_Not_Chance"):
            sio.write(f'<div>第一次抽奖：抽奖次数不足</div>')
        else:
            sio.write(f'<div>第一次抽奖失败</div><div>{response.text}</div>')
    else:
        description = response.json()['description']
        sio.write(f'<div>第一次抽奖：抽奖获得{description} 🎉</div>')
    #第二次抽奖
    response = s.get(url2,headers=headers)
    if ("errorCode" in response.text):
        if(response.json()['errorCode'] == "User_Not_Chance"):
            sio.write(f'<div>第二次抽奖：抽奖次数不足</div>')
        else:
            sio.write(f'<div>第二次抽奖失败</div><div>{response.text}</div>')
    else:
        description = response.json()['description']
        sio.write(f'<div>第二次抽奖：抽奖获得{description} 🎉</div>')
    sio_content = sio.getvalue()
    pushWechat(sio_content)
    return sio_content

BI_RM = list("0123456789abcdefghijklmnopqrstuvwxyz")
def int2char(a):
    return BI_RM[a]

b64map = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
def b64tohex(a):
    d = ""
    e = 0
    c = 0
    for i in range(len(a)):
        if list(a)[i] != "=":
            v = b64map.index(list(a)[i])
            if 0 == e:
                e = 1
                d += int2char(v >> 2)
                c = 3 & v
            elif 1 == e:
                e = 2
                d += int2char(c << 2 | v >> 4)
                c = 15 & v
            elif 2 == e:
                e = 3
                d += int2char(c)
                d += int2char(v >> 2)
                c = 3 & v
            else:
                e = 0
                d += int2char(c << 2 | v >> 4)
                d += int2char(15 & v)
    if e == 1:
        d += int2char(c << 2)
    return d

def rsa_encode(j_rsakey, string):
    rsa_key = f"-----BEGIN PUBLIC KEY-----\n{j_rsakey}\n-----END PUBLIC KEY-----"
    pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(rsa_key.encode())
    result = b64tohex((base64.b64encode(rsa.encrypt(f'{string}'.encode(), pubkey))).decode())
    return result

def login(username, password):
    url = "https://cloud.189.cn/udb/udb_login.jsp?pageId=1&redirectURL=/main.action"
    r = s.get(url)
    captchaToken = re.findall(r"captchaToken' value='(.+?)'", r.text)[0]
    lt = re.findall(r'lt = "(.+?)"', r.text)[0]
    returnUrl = re.findall(r"returnUrl = '(.+?)'", r.text)[0]
    paramId = re.findall(r'paramId = "(.+?)"', r.text)[0]
    j_rsakey = re.findall(r'j_rsaKey" value="(\S+)"', r.text, re.M)[0]
    s.headers.update({"lt": lt})

    username = rsa_encode(j_rsakey, username)
    password = rsa_encode(j_rsakey, password)
    url = "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/76.0',
        'Referer': 'https://open.e.189.cn/',
        }
    data = {
        "appKey": "cloud",
        "accountType": '01',
        "userName": f"{{RSA}}{username}",
        "password": f"{{RSA}}{password}",
        "validateCode": "",
        "captchaToken": captchaToken,
        "returnUrl": returnUrl,
        "mailSuffix": "@189.cn",
        "paramId": paramId
        }
    r = s.post(url, data=data, headers=headers, timeout=5)
    if(r.json()['result'] == 0):
        message=r.json()['msg']
        sio.write(f'<div>登录提示：</div><div>{message}</div>')
    else:
        if(corpid == "")or(agentid=='')or(corpsecret==''):
            message=r.json()['msg']
            sio.write(f'<div>登录提示：</div><div>{message}</div>')
        else:
            message = r.json()['msg']
            sio.write(f'<div>签到失败：登录出错！</div><div>错误提示：</div><div>{message}</div>')
        return "error"
    redirect_url = r.json()['toUrl']
    r = s.get(redirect_url)
    return s
    
# 微信推送
def pushWechat(sio_content):
    if '失败' in sio_content :
        sio_content=(f'天翼云盘签到失败！\n')
    time.sleep(2) #延迟2秒推送    
    send_mpnews(title,sio_content,sio_digest.getvalue())

if __name__ == "__main__":
    arg1 = 0
    arg2 = 0
    time.sleep(sleep_time)
    main(arg1,arg2)