import socket
import json
import struct
from Client.config.Client_config_info import personal_config_info

coding = personal_config_info['CODING']

class FTP_pipe:

    #发送字典的静态方法
    @staticmethod
    def sk_send_dic(sk,dic):
        str_dic = json.dumps(dic).encode(coding)
        len_content = struct.pack('i',len(str_dic))
        sk.send(len_content)
        sk.send(str_dic)

    #接受字典的静态方法
    @staticmethod
    def sk_recv_dic(sk):
        len_dic_4 = sk.recv(4)
        len_dic = struct.unpack('i',len_dic_4)[0]
        str_dic = sk.recv(len_dic).decode(coding)
        dic = json.loads(str_dic)
        return dic


if __name__ == '__main__':
    pass


