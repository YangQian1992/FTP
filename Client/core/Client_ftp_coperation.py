from Client.config.Client_config_info import personal_config_info
from Client.core.Client_pipline import FTP_pipe
import os
import hashlib
import sys
import time

class FTP_client:

    def __init__(self,usr,path,sk):
        self.usr = usr
        self.root_path = path
        self.current_path = path
        self.sk = sk
        self.coding = personal_config_info['CODING']
        self.block = personal_config_info['BLOCK_SIZE']

    def ls(self):
        data = self.get_dir()
        self.show_ls(data)

    def get_dir(self):
        get_dir_dic = {'opt':'ls','current_path':self.current_path,
                       'username':self.usr}

        #发送字典
        FTP_pipe.sk_send_dic(self.sk,get_dir_dic)
        #接收含有文件夹和文件目录的列表
        # 获取字典
        data = FTP_pipe.sk_recv_dic(self.sk)
        return data

    def show_ls(self,data):
        #data = [True(权限),{'dir(文件夹)':[...],'file(文件)':[....]}]
        #data = [False(权限),'权限不够']
        if data[0] == True and data[1]['file'] == [] and data[1]['dir'] ==[]:
            print('文件夹为空')
        elif data[0] == True and type(data[1]) is dict and data[1]['dir'] !=[] or data[1]['file'] != []:
            if data[1]['dir'] != []:
                print('文件夹如下:')
                for i in data[1]['dir']:
                    print('\t',i)

            if data[1]['file'] != []:
                print('文件如下:')
                for i in data[1]['file']:
                    print('\t',i)
        else:
            print(data[1])

    def cd(self):
        data = self.get_dir()
        while True:
            dir_name = self.aim
            temp_path = os.path.join(self.current_path, dir_name)
            if dir_name == 'q':
                return
            elif temp_path in data[1]['dir']:
                self.current_path = temp_path
                data = self.get_dir()
                print('已经进入了文件夹%s下的目录' % (dir_name))
                self.show_ls(data)
                print('当前路径为', self.current_path)
                return
            else:
                print('对不起，你输入的文件夹不存在，请改正！')
                print('当前路径为', self.current_path)
                return

    def cd_back(self):
        temp_current_path = self.current_path
        path_li = (self.current_path.rstrip(os.sep)).split(os.sep)
        path_li.pop()
        self.current_path = (os.sep).join(path_li)
        if self.root_path in self.current_path:
            print('已经返回上一级目录了,本层目录的内容如下：')
            self.ls()
            print('当前路径为', self.current_path)
            return
        else:
            print('已经达到根目录，不能再返回上一层了！')
            self.current_path    = temp_current_path
            print('当前路径为', self.current_path)
            return

    def mk_dir(self):
        data = self.get_dir()
        dir_name = self.aim
        print('当前路径下目录')
        self.show_ls(data)
        print('当前路径')
        print(self.current_path)
        temp_path = os.path.join(self.current_path,dir_name)
        if temp_path in data[1]['dir']:
            print('文件夹已经存在！')
        elif dir_name != '':
            mk_dir_info = {
                'opt':'mk_dir',
                'current_path':self.current_path,
                'dir_name':dir_name,
                'username':self.usr
            }
            # 发送字典
            FTP_pipe.sk_send_dic(self.sk,mk_dir_info)
            # 接收含有文件夹和文件目录的列表
            # 获取字典
            data = FTP_pipe.sk_recv_dic(self.sk)
            print('文件夹创建成功！！！')
            self.show_ls(data)
            print('当前路径为', self.current_path)

    def upload(self):
        '''
        步骤1：首先输入你要上传文件的路径
        步骤2：通过文件路径获得上传文件的文件名、大小、服务器当前所在文件夹
        步骤3：将文件名和文件大小传递到服务器，判断该文件是否已经存在，并判断是不是断点续传
        步骤4：如果服务器文件存在重名文件---则判断大小
                ·如果服务器文件大小要待上传的文件大小，则返回提示-->已经存在相同文件名，
                不能上传，或者提示是否进行覆盖，或者将待上传文件在重命名为***(1)之后上传
                ·如果服务器文件小于要待上传的文件大小，则返回提示--->断点续传
                如果服务器文件不存在重名文件--则直接上传
        :return:
        '''
        upload_file_path = input('请输入要上传的文件路径>>>')
        self.file_size = os.path.getsize(upload_file_path)
        self.upload_file_name = upload_file_path.rstrip(os.sep).split(os.sep).pop()
        dic_info = {'opt':'upload','file_name':self.upload_file_name,
                    'current_path':self.current_path,'root_path':self.root_path}
        FTP_pipe.sk_send_dic(self.sk,dic_info)
        #[False,server_file_size,server_file_md5]
        # [True]
        ret = FTP_pipe.sk_recv_dic(self.sk)
        if ret[0] == True: #在服务器完全重新上传的情况
            dic_info = {'opt':'upload_from_null',
                        'upload_file_size':self.file_size}
            FTP_pipe.sk_send_dic(self.sk,dic_info)
            client_upload_file_md5 = self.file_send(self.sk,upload_file_path,self.file_size,0)
            server_upload_file_md5 = FTP_pipe.sk_recv_dic(self.sk)[0]
            if client_upload_file_md5 == server_upload_file_md5:
                print('上传成功！')
            else:
                print('上传失败，请重新上传')
                return

        elif ret[0] == False: #在服务器需要断点续传的情况
            server_file_size = ret[1]
            server_file_md5 = ret[2]
            rest_file_size = self.file_size - server_file_size
            dic_info = {'opt': 'resume_breakpoint',
                        'rest_file_size': rest_file_size,
                        'start_position':server_file_size}
            FTP_pipe.sk_send_dic(self.sk, dic_info)
            client_upload_file_md5 = self.content_md5(upload_file_path, self.file_size)
            if server_file_size > self.file_size:
                print('服务器已经存在内容不同却名字相同而且比上传文件大的的文件！不能上传')
            elif server_file_size == self.file_size:
                if client_upload_file_md5 ==  server_file_md5:
                    print('服务端存在两个完全一样的文件，不能上传！')
                else:
                    print('服务端存在两个一样大小但内容不同的文件，不能上传！')
            elif server_file_size < self.file_size and (client_upload_file_md5 != server_file_md5):
                print('两个文件重名，服务器文件小，但是内容不一样，不能上传！')
            else:
                client_upload_file_md5 = self.content_md5(upload_file_path,server_file_size)
                if client_upload_file_md5 == ret[2]:
                    order = input('是否需要断点续传(y/n)>>>')
                    if order == 'y':
                        client_upload_file_md5= self.file_send(self.sk,upload_file_path,rest_file_size,server_file_size)
                        server_rest_file_md5 = FTP_pipe.sk_recv_dic(self.sk)[0]
                        if client_upload_file_md5 == server_rest_file_md5:
                            print('断点续传成功！')
                    else:
                        return



    def file_send(self,sk,file_path,rest_file_size,start_point):
        m = hashlib.md5()
        with open(file_path,mode='rb') as f:
            f.seek(start_point)
            block = personal_config_info['BLOCK_SIZE']
            total = rest_file_size
            num = 0
            while rest_file_size:
                if rest_file_size > block:
                    content = f.read(block)
                    m.update(content)
                    content = content.decode(self.coding)
                    rest_file_size -= block
                    num += block
                else:
                    content = f.read(rest_file_size)
                    m.update(content)
                    content = content.decode(self.coding)
                    rest_file_size -= rest_file_size
                    num +=rest_file_size
                FTP_pipe.sk_send_dic(sk,[content])
                self.processBar(num,total)
        return m.hexdigest()

    def content_md5(self,upload_file_path, server_file_szie):
        m = hashlib.md5()
        if server_file_szie > 1024 * 10:
            block = int(server_file_szie / 10)
        else:
            block = personal_config_info['BLOCK_SIZE']
        # 获得当前路径下的文件内容的md5值
        with open(upload_file_path,mode='rb') as f:
            while server_file_szie:
                if server_file_szie > block:
                    content = f.read(1024)
                    m.update(content)
                    f.seek(f.tell() - 1024 + block)
                    server_file_szie -= block
                else:
                    content = f.read(server_file_szie)
                    m.update(content)
                    server_file_szie -= server_file_szie
        return m.hexdigest()


    def download(self):
        current_path = self.current_path
        file_name = self.aim
        local_download_path = input('请输入您要保存的路径>>>')
        file_li = os.listdir(local_download_path)
        local_download_file_path = os.path.join(local_download_path, file_name)
        #判断下载的本地路径下是不是有重名的文件
        if file_name in file_li:
            #文件有三种可能
            #·本地大小可能小于服务器文件，且内容相同---->断点续传
            #·本地文件大小和服务器文件大小相同，且内容相同---->已经下载了，不能继续下载
            #·本地文件和服务器文件仅仅名字一样----->完全不相干，不能继续下载，可改名后下载(以后扩展)

            #先将本地信息传到服务器，然后服务器传回和本地文件大小相同的内容的md5校验值进行比较
            local_dowload_file_size = os.path.getsize(local_download_file_path)
            local_dowload_file_md5 = self.content_md5(local_download_file_path,local_dowload_file_size)
        else:
            local_dowload_file_size = 0
            local_dowload_file_md5 = None
        info_dic = {'opt':'download',
                    'current_path':current_path,
                    'file_name':file_name,
                    'root_path':self.root_path,
                    'local_file_size':local_dowload_file_size,
                    'local_dowload_file_md5':local_dowload_file_md5}
        FTP_pipe.sk_send_dic(self.sk,info_dic) #---->dic_operation
        ret = FTP_pipe.sk_recv_dic(self.sk)
        #[False,'本地目标路径上已经有一个完全相同的文件，不用再下载了！']
        #[False,'本地目标路径上已经有一个大小完全相同，但是内容不同的文件，不能再下载了！']
        #[True, 1, download_file_size]
        #[False,'不断点续传，那就关了吧！']
        #[True,2,download_file_size]
        #[False,'文件夹错误！']
        if ret[0] == False:
            print(ret[1])
        elif ret[0] == True and ret[1] == 1:
            order = input('你确定要断点续传吗(y/n)>>>')
            FTP_pipe.sk_send_dic(self.sk,[order])
            download_file_size = ret[2]
            rest_file_size = download_file_size - local_dowload_file_size
            start_position = local_dowload_file_size
            client_local_dowload_after_file_md5 = self.recv_file(self.sk,local_download_file_path,
                                                                rest_file_size,start_position)
            server_download_after_file_md5 = FTP_pipe.sk_recv_dic(self.sk)[0]
            if client_local_dowload_after_file_md5 == server_download_after_file_md5:
                print('断点续传下载成功！！')
            else:
                print('断点续传下载失败！')
        elif ret[0] ==True and ret[1] == 2:
            download_file_size = ret[2]
            client_local_dowload_after_file_md5 = self.recv_file(self.sk,local_download_file_path,
                                                                download_file_size,0)
            server_download_after_file_md5 = FTP_pipe.sk_recv_dic(self.sk)[0]
            if client_local_dowload_after_file_md5 == server_download_after_file_md5:
                print('非断点续传下载成功！')


    def recv_file(self,sk, client_download_path, rest_file_size, start_position):
        m = hashlib.md5()
        with open(client_download_path, mode='ab') as f:
            f.seek(start_position)
            block = personal_config_info['BLOCK_SIZE']
            total = rest_file_size
            num = start_position
            while rest_file_size:
                if rest_file_size > block:
                    content = FTP_pipe.sk_recv_dic(sk)[0]
                    rest_file_size -= block
                    num +=block
                else:
                    content = FTP_pipe.sk_recv_dic(sk)[0]
                    rest_file_size -= rest_file_size
                    num += rest_file_size
                if content == b'':
                    break
                f.write(content.encode(self.coding))
                m.update(content.encode(self.coding))
                # self.processBar(num,total)
        return m.hexdigest()
    #没有成功，有待探究
    def processBar(self,num,total):
        rate = num / total
        rate_num = int(rate * 100)
        time.sleep(0.05)
        r = '\r[%s%s]%d%%' % ("=" * rate_num, " " * (100 - rate_num), rate_num,)
        sys.stdout.write(r)
        sys.stdout.flush()

    def myquit(self):
        dic = {'opt':'exit'}
        FTP_pipe.sk_send_dic(self.sk,dic)
        exit()

    def choose_operation(self):
        operation_dic ={1:'查看当前目录(ls)',2:'返回上一级目录(cd_back)',
                       3:'进入下一级目录(cd)',4:'创建文件夹(mk_dir)',5:'退出(exit)',
                        6:'上传(upload)',7:'下载(download)'}

        while True:
            for num, operation in operation_dic.items():
                print(num,':',operation)
            operation_aim = input('请输入您需要进行的操作(命令+空格+文件名(ls\cd_back\exite什么也不加))>>>').strip()
            try:
                operation, self.aim = operation_aim.split(' ')
            except:
                operation = operation_aim

            if operation == 'ls':
                self.ls()
            elif operation == 'cd_back':
                self.cd_back()
            elif operation == 'cd':
                self.cd()
            elif operation == 'mk_dir':
                self.mk_dir()
            elif operation == 'upload':
                self.upload()
            elif operation == 'download':
                self.download()
            elif operation == 'exit':
                self.myquit()
                break
            else:
                print('您输入命令是错误的,请重新输入！')
                continue


