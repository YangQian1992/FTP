#程序的接入点，模拟网页或者程序的接入界面
#例子：QQ的登录界面，包括登录按钮、关闭按钮、注册按钮
from Client.core.Client_fuction import UI_function
#表述功能的基本列表
fun_list = ['登录','注册','退出']
while True:
    my_UI_fnction = UI_function()
    dic_UI_button = {'登录':my_UI_fnction.login, '注册':my_UI_fnction.register,
                     '退出':my_UI_fnction.Please_quit}
    # 输出模拟界面上的功能选项
    print('登录界面'.center(20, '*'))
    for num,operation in enumerate(dic_UI_button,1):
        print(num,':',operation)
    # 选择模拟界面上的选项
    print('请选择相应的功能序号:')
    opt_index = input('>>>')
    try:
        func = dic_UI_button[fun_list[int(opt_index)-1]]
    except:
        print('那个选项都不是，你输入的不对，重新输入吧！')
        continue
    ret = func()
