import base64
import requests
import re
import json
import time
import rsa
import binascii
from lxml import etree
from fake_useragent import UserAgent

ua = UserAgent()


class Login(object):
    def __init__(self, username, password):
        self.nonce = ""
        self.pubkey = ""
        self.rsakv = ""
        self.s = requests.session()
        self.headers = {
            "User-Agent": ua.random,
        }
        self.username = username
        self.password = password

    def pre_login(self):
        url = 'https://login.sina.com.cn/sso/prelogin.php?entry=weibo&su=&rsakt=mod&client=ssologin.js(v1.4.19)&_={}'.format(
            int(time.time() * 1000))
        response = requests.get(url=url, headers=self.headers)
        handled_text = response.text
        start = handled_text.find("(")
        handled_text = json.loads(handled_text[start + 1:])
        self.nonce, self.pubkey, self.rsakv = handled_text.get("nonce"), handled_text.get(
            "pubkey"), handled_text.get("rsakv")

    def sso_login(self, password, username):
        data = {
            "entry": "weibo",
            "gateway": "1",
            "from": "",
            "savestate": "7",
            "qrcode_flag": "false",
            "useticket": "1",
            "pagerefer": "https://login.sina.com.cn/crossdomain2.php?action=logout&r=https%3A%2F%2Fpassport.weibo.com%2Fwbsso%2Flogout%3Fr%3Dhttps%253A%252F%252Fweibo.com%26returntype%3D1",
            "vsnf": "1",
            "su": username,
            "service": "miniblog",
            "servertime": str(int(time.time())),
            "nonce": self.nonce,
            "pwencode": "rsa2",
            "rsakv": self.rsakv,
            "sp": password,
            "sr": "2560*1440",
            "encoding": "UTF-8",
            "prelt": "230",
            "url": "https://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack",
            "returntype": "META",
        }
        url = 'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.19)'
        r = self.s.post(url, headers=self.headers, data=data)
        cookie = requests.utils.dict_from_cookiejar(r.cookies)
        return cookie

    def encode_username(self, username):
        return base64.b64encode(username.encode("utf-8"))[:-1]

    def encode_password(self, password):
        hex_pubkey = int(self.pubkey, 16)
        pub_key = rsa.PublicKey(hex_pubkey, 65537)
        crypto = rsa.encrypt(password.encode('utf8'), pub_key)
        return binascii.b2a_hex(crypto)

    def login(self):
        self.pre_login()
        username = self.encode_username(self.username)
        text = str(int(time.time())) + '\t' + str(self.nonce) + '\n' + str(self.password)
        password = self.encode_password(text)
        cookie = self.sso_login(password, username)
        if len(cookie) == 1:
            print("账号密码有误，请重新登陆!")
            exit()
        else:
            print("登陆成功!")
            return cookie
