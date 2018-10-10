import sys
import os
import hashlib
from Server.config.Server_config_info import server_config_info

#建立基础常量
IP_PORT = (server_config_info['SERVER_IP'],server_config_info['SERVER_PORT'])


class user_info:

    def __init__(self):
        #sys.path[0]='G:\\PycharmProjects\\项目\\ftp_proj_base\\Server\\core'
        server_path_li = sys.path[0].split(os.sep)[:-1]
        #server_path_li =['G:','PycharmProjects','项目','ftp_proj_base','Server']
        server_path_li.extend(['usr&pwd','username&password'])
        # server_path_li =['G:','PycharmProjects','项目','ftp_proj_base','Server',
        # 'usr&pwd','username&password']
        self.server_path = (os.sep).join(server_path_li)
        #server_path='G:\\PycharmProjects\\项目\\ftp_proj_base\\Server\\usr&pwd\\username&password'
        self.ftp_root = server_config_info['FTP_ROOT'] #家目录
        self.auth_key = server_config_info['AUTH_KEY']
        self.coding = server_config_info['CODING']



    def get_pwd(self,pwd):
        md5_obj = hashlib.md5(pwd.encode(self.coding))
        md5_obj.update(self.auth_key.encode(self.coding))
        return md5_obj.hexdigest()

    #将用户密码本中的信息首先加载到一个字典中
    #{'杨倩'：{'password':password(md5),'times':0,'root_path',root_path},
    # '张三'：{'password':password(md5)........}}
    def load_user_info(self):
        self.user_info_dic = {}
        with open(self.server_path,encoding=self.coding,mode='r') as f:
            for info in f:
                username, password = info.split()
                root_path = '%s%s%s' % (self.ftp_root,os.sep,username)
                self.user_info_dic[username] ={'password':password,
                                                'times': 0,
                                                'root_path':root_path}
                if not os.path.exists(root_path):
                    os.mkdir(root_path)

    #服务器判定客户端登录是否成功的方法
    def login(self,usr,pwd):
        pwd = self.get_pwd(pwd)
        #如果用户名不在文本中
        if usr not in self.user_info_dic.keys():
            return [False,'登录失败','用户名不存在，请注册！']
        if (self.user_info_dic[usr] !='') and (self.user_info_dic[usr]['times'] < 3) \
                and (self.user_info_dic[usr]['password'] == pwd):
            self.user_info_dic[usr]['times'] +=0
            return [True,'登录成功！',self.user_info_dic[usr]['root_path']]
        elif self.user_info_dic[usr] != '' and self.user_info_dic[usr]['times'] < 3\
            and self.user_info_dic[usr]['password'] != pwd:
            self.user_info_dic[usr]['times'] += 1
            return [False,'登录失败，密码错误，还剩%d次机会！' % (3-self.user_info_dic[usr]['times'])]
        elif self.user_info_dic[usr] != '' and self.user_info_dic[usr]['times'] == 3\
            and self.user_info_dic[usr]['password'] != pwd:
            return [False,'登录失败，账户被锁，隔一段时间再登录吧！']
        else:
            return [False,'登录失败，当前用户不存在，请先注册！']

    #服务端判定是否注册成功的方法
    def register(self,usr,pwd):
        if usr in self.user_info_dic.keys():
            return [False, '你注册的用户名以存在，请更换']
        else:
            pwd = self.get_pwd(pwd)
            self.user_info_dic[usr] = {'password':pwd,'times':0}
            #将注册成功后的信息写入密码本
            with open(self.server_path, encoding=self.coding,mode='a') as f:
                f.write('\n%s %s' % (usr,pwd))
            root_path = '%s%s%s' % (self.ftp_root,os.sep,usr)
            os.mkdir(root_path) #根据注册成功后的用户的信息，建立专属家目录
            self.user_info_dic[usr]['root_path'] = root_path #更新家目录
            return [True,'注册成功！', root_path]










