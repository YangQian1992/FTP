import socketserver
from Server.config.Server_config_info import server_config_info
from Server.core.Server_commication_User import user_info
from Server.core import Server_ftp_operation as Sfo
from Server.core.Server_pipline import FTP_pipe

IP_PORT = (server_config_info['SERVER_IP'],server_config_info['SERVER_PORT'])
coding = server_config_info['CODING']

#建立socketserver连接
class MySocketServer(socketserver.BaseRequestHandler):

    user_info = user_info()

    def handle(self):
        #获取字典
        dic = FTP_pipe.sk_recv_dic(self)

        username = dic['username']
        password = dic['pwd']
        self.user_info.load_user_info()
        ret = {}
        if dic['opt'] == '登录':
            ret = self.user_info.login(username,password)
        elif dic['opt'] == '注册':
            ret = self.user_info.register(username,password)
        FTP_pipe.sk_send_dic(self,ret)

        while True:
            #接收含有在操作指令的字典
            # 获取字典
            dic_operation = FTP_pipe.sk_recv_dic(self)
            if dic_operation['opt'] == 'ls':
            # get_dir_dic = {'opt': 'ls', 'current_path': self.current_path,
            #                'username': self.usr}
                username = dic_operation['username']
                current_path = dic_operation['current_path']
                ret = Sfo.ls(self.user_info,username,current_path)
                FTP_pipe.sk_send_dic(self, ret)
            elif dic_operation['opt'] == 'mk_dir':
            # mk_dir_info = {
            #     'operation': 'mk_dir',
            #     'current_path': self.current_path,
            #     'dir_name': dir_name,
            #     'username': self.usr
            # }
                current_path = dic_operation['current_path']
                dir_name = dic_operation['dir_name']
                username = dic_operation['username']
                ret = Sfo.mk_dir(self.user_info, username, current_path,dir_name)
                FTP_pipe.sk_send_dic(self, ret)
            elif dic_operation['opt'] == 'upload':
                #dic_operation = {'opt':'upload','file_name':self.upload_file_name,
                    # 'file_size':self.file_size,'current_path':self.current_path,
                    # 'root_path':self.root_path}
                file_name = dic_operation['file_name']
                current_path = dic_operation['current_path']
                root_path = dic_operation['root_path']
                Sfo.upload(self,file_name,current_path,root_path)
            elif dic_operation['opt'] == 'download':
                current_path = dic_operation['current_path']
                file_name = dic_operation['file_name']
                root_path = dic_operation['root_path']
                local_file_size = dic_operation['local_file_size']
                local_dowload_file_md5 = dic_operation['local_dowload_file_md5']
                Sfo.download(self,current_path,file_name,root_path,
                                   local_file_size,local_dowload_file_md5)
            elif dic_operation['opt'] == 'exit':
                exit()

ser = socketserver.ThreadingTCPServer(IP_PORT,MySocketServer)
ser.serve_forever()