import socket
import json
import struct
from Client.config.Client_config_info import personal_config_info
from Client.core import Client_ftp_coperation as Cfc
from Client.core.Client_pipline import FTP_pipe

coding = personal_config_info['CODING']
IP_PORT = (personal_config_info['SERVER_IP'],personal_config_info['SERVER_PORT'])
#模拟客户端建立连接并包含登录和注册功能

class UI_function:
    #模块1---->全局初始变量
    def __init__(self):
        self.sk = socket.socket()
        self.sk.connect(IP_PORT)

    #模块2---->模拟登录输入信息
    def login(self):
        #首先要输入用户名和密码
        username = input('请输入您的用户名(按“q”退出)>>>')
        #如果用户输入q直接退出程序
        if username == 'q':
            return {'opt':'登录','status':False}
        #输入密码
        pwd = input('请输入您的密码>>>')
        #如果用户名和密码不为空，就往服务端发消息，这个消息需要到达的功能
        #1.通知服务器这是要登录
        #2.包含登录的用户名和密码
        if username and pwd:
            dic_client_info = {'opt':'登录','username':username,'pwd':pwd}
            #发送字典
            FTP_pipe.sk_send_dic(self.sk,dic_client_info)
            #接受字典
            ret = FTP_pipe.sk_recv_dic(self.sk)
            print(ret[1])
            if ret[0]:
                print('当前所在家目录>>>', ret[2])
                self.FTP_client = Cfc.FTP_client(username,ret[2],self.sk)
                self.FTP_client.choose_operation()

    def register(self):
        while True:
            username = input('请输入您的用户名(按q退出)>>>')
            if username == 'q':
                return {'opt':'注册','状态':'注册失败'}
            elif username:
                while True:
                    pwd = input('请输入您的密码>>>')
                    pwd_again = input('请再次输入您的密码>>>')
                    if pwd == pwd_again:
                        rigester_info = {'opt':'注册','username':username,'pwd':pwd}
                        # 发送字典
                        FTP_pipe.sk_send_dic(self.sk,rigester_info)
                        # 接受字典
                        ret = FTP_pipe.sk_recv_dic(self.sk)
                        print(ret[1])
                        if ret[0]:
                            print('新建家目录>>>',ret[2])
                        break
                    else:
                        print('输入密码不一致，请重新输入！')
    def Please_quit(self):
        exit()
