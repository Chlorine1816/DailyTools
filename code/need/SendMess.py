# -*- coding: utf-8 -*-  
import requests
import json
import time

class Robot:

  headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47'}

  def __init__(self,title,corpid,agentid,corpsecret,media_id,touser):
    #图文图文消息的标题
    self.title=title
    
    self.corpid=corpid
    self.agentid=agentid
    self.corpsecret=corpsecret
    self.media_id=media_id
    self.touser=touser

    self.digest = time.strftime('%Y-%m-%d UTC(%H:%M)', time.localtime()) + '\n'
    self.daily=self.get_daily_sentence()

  def get_token(self):
    payload_access_token = {'corpid': self.corpid, 'corpsecret': self.corpsecret}
    token_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
    r = requests.get(url=token_url, params=payload_access_token,headers=self.headers)
    self.access_token = (r.json())['access_token']

  #发送图文信息
  def send_mpnews(self,content):
    self.get_token()
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={self.access_token}"
    data = {
      "touser":self.touser, #接收消息人员id
      "agentid":self.agentid, #机器人id
      'msgtype':'mpnews',
      'mpnews': {
        'articles':[
          {
            "title": self.title, #必须
            "thumb_media_id": self.media_id, #必须
            "author": "Chlorine", #非必须 作者
            "content": content, #必须 不超过666 K个字节
            "digest": self.digest #非必须 不超过512个字节
          }
        ]
      },
      "safe": 0 #是否加密
    }
    data = json.dumps(data, ensure_ascii=False)
    requests.post(url=url, data=data.encode("utf-8").decode("latin1"))

  def get_daily_sentence(self):
    url = "http://open.iciba.com/dsapi/"
    try:
      r = requests.get(url,timeout=5)
      r = json.loads(r.text)
      content = r["content"]
      note = r["note"]
      self.digest=f'{self.digest}{content}\n{note}\n'
    except Exception:
      self.digest=f'{self.digest}Happy every day !\n'