import os
import hashlib
from Server.config.Server_config_info import server_config_info
from Server.core.Server_pipline import FTP_pipe
code = server_config_info['CODING']
def ls(user_info,usr,current_path):
    if user_info.user_info_dic[usr]['root_path'] in current_path:
        try:
            dir_list = os.listdir(current_path)
            li_dic = {'dir':[],'file':[]}
            for i in dir_list:
                file_path = os.path.join(current_path,i)

                if os.path.isdir(file_path):
                    li_dic['dir'].append(file_path)
                elif os.path.isfile(file_path):
                    li_dic['file'].append(file_path)
        except Exception as e:
            return [False,['错误目录']]

        return [True,li_dic]
    else:
        return [False,['错误目录']]


def mk_dir(user_info,usr,current_path,dir_name):
    if user_info.user_info_dic[usr]['root_path'] in current_path:
        new_path = os.path.join(current_path,dir_name)
        os.mkdir(new_path)
    return ls(user_info,usr,current_path)

def upload(sk,file_name,current_path,root_path):
    if root_path in current_path:
        server_upload_path = os.path.join(current_path,file_name)
        if os.path.exists(server_upload_path):
            server_file_size = os.path.getsize(server_upload_path)
            server_file_md5 = content_md5(server_upload_path,server_file_size)
            info_li = [False,server_file_size,server_file_md5]
            FTP_pipe.sk_send_dic(sk,info_li)
        else:
            info_li = [True]
            FTP_pipe.sk_send_dic(sk,info_li)

        #如果是完全不同的文件---> ret = ['断点续传',不是一个文件]
        ret = FTP_pipe.sk_recv_dic(sk)
        if ret['opt'] == 'resume_breakpoint':
            rest_file_size = ret['rest_file_size']
            start_position = ret['start_position']
            rest_file_md5 = recv_file(sk,server_upload_path,rest_file_size,start_position)
            FTP_pipe.sk_send_dic(sk,[rest_file_md5])
        elif ret['opt'] == 'upload_from_null':
            upload_file_size = ret['upload_file_size']
            rest_file_md5 = recv_file(sk, server_upload_path, upload_file_size, 0)
            FTP_pipe.sk_send_dic(sk, [rest_file_md5])

def recv_file(sk,server_upload_path,rest_file_size,start_position):
    m = hashlib.md5()
    with open(server_upload_path,mode='ab') as f:
        f.seek(start_position)
        block = server_config_info['BLOCK_SIZE']
        while rest_file_size:
            if rest_file_size > block:
                content = FTP_pipe.sk_recv_dic(sk)[0]
                rest_file_size -= block
            else:
                content = FTP_pipe.sk_recv_dic(sk)[0]
                rest_file_size -= rest_file_size
            if content.strip() == b'':
                break
            f.write(content.encode(code))
            m.update(content.encode(code))
    return m.hexdigest()


def content_md5(server_upload_path,server_file_szie,start_position = 0):
    m = hashlib.md5()
    if server_file_szie > 1024 * 10:
        block = int(server_file_szie/10)
    else:
        block = server_config_info['BLOCK_SIZE']
    #获得当前路径下的文件内容的md5值
    with open(server_upload_path,mode='rb') as f:
        f.seek(start_position)
        while server_file_szie:
            if server_file_szie > block:
                content = f.read(1024)
                m.update(content)
                f.seek(f.tell()-1024+block)
                server_file_szie -= block
            else:
                content = f.read(server_file_szie)
                m.update(content)
                server_file_szie -= server_file_szie
    return m.hexdigest()

def download_send(sk,rest_download_file_size,download_path,start_position):
    m = hashlib.md5()
    block = server_config_info['BLOCK_SIZE']
    with open(download_path,mode='rb') as f:
        f.seek(start_position)
        while rest_download_file_size:
            if rest_download_file_size > block:
                content = f.read(block)
                m.update(content)
                content = content.decode(code)
                rest_download_file_size -= block
            else:
                content = f.read(rest_download_file_size)
                m.update(content)
                content = content.decode(code)
                rest_download_file_size -= rest_download_file_size
            FTP_pipe.sk_send_dic(sk,[content])
    return m.hexdigest()



def download(sk,current_path,file_name,root_path,local_file_size,local_dowload_file_md5):
    download_path = os.path.join(current_path,file_name)
    if root_path in download_path:
        if not os.path.exists(download_path):
            return [False,'下载文件不存在，请重新输命令!']
        else:
            download_file_size = os.path.getsize(download_path)
            if download_file_size < local_file_size:
                FTP_pipe.sk_send_dic(sk,[False,'本地文件比服务器文件大！不能下载！'])
                return
            elif download_file_size == local_file_size:
                server_download_file_md5 = content_md5(download_path,download_file_size,0)
                if server_download_file_md5 == local_dowload_file_md5:
                    FTP_pipe.sk_send_dic(sk,[False,'本地目标路径上已经有一个完全相同的文件，不用再下载了！'])
                else:
                    FTP_pipe.sk_send_dic(sk,[False,'本地目标路径上已经有一个大小完全相同，但是内容不同的文件，不能再下载了！'])
                return
            elif download_file_size > local_file_size and local_file_size != 0:
                server_download_file_md5 = content_md5(download_path, local_file_size, 0)
                if server_download_file_md5 == local_dowload_file_md5:
                    FTP_pipe.sk_send_dic(sk, [True, 1, download_file_size])
                    #接受断点续传命令
                    order = FTP_pipe.sk_recv_dic(sk)[0]
                    if order == 'y':
                        rest_download_file_size = download_file_size - local_file_size
                        start_position = local_file_size
                        server_download_after_file_md5 = download_send(sk, rest_download_file_size, download_path, start_position)
                        FTP_pipe.sk_send_dic(sk,[server_download_after_file_md5])

                    else:
                        FTP_pipe.sk_send_dic(sk,[False,'不断点续传，那就关了吧！'])
                else:
                    FTP_pipe.sk_send_dic(sk, [False, '本地文件比文件小，但是内容也不一样，不能下载！'])
                #先检查客户端是否有该文件
            elif local_file_size == 0:
                FTP_pipe.sk_send_dic(sk, [True,2,download_file_size])
                #非断点续传的情况
                server_download_after_file_md5 = download_send(sk,download_file_size,download_path,0)
                FTP_pipe.sk_send_dic(sk,[server_download_after_file_md5])
    else:
        FTP_pipe.sk_send_dic(sk,[False,'文件夹错误！'])












