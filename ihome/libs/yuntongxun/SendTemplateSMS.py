# coding: UTF-8

from ihome.libs.yuntongxun.CCPRestSDK import REST
import configparser

#主帐号
accountSid= '8a216da86eb206c4016ed6301fd815c2'

#主帐号Token
accountToken= 'c21e289396f040efa4c4b4b0e41962f5'

#应用Id
appId='8aaf07086eb122c3016ed63699cb165c'

#请求地址，格式如下，不需要写http://
serverIP='app.cloopen.com'

#请求端口 
serverPort='8883'

#REST版本号
softVersion='2013-12-26'

  # 发送模板短信
  # @param to 手机号码
  # @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
  # @param $tempId 模板Id


#自己封装的发送短息的辅助类 为了只执行一次 初始化的REST SDK  采用单例模式

class CCP(object):
    '''自己封装的发送短息的辅助类'''
    # 用来保持保存对象的类属性
    instance = None
    def __new__(cls):
        # 判断CCP类有没有已经创建好的对象,如果没有。创建一个对象并且保存
        # 如果有直接将保存的对象返回
        if cls.instance is None:
            obj = super(CCP,cls).__new__(cls)
            # 初始化REST SDK
            obj.rest = REST(serverIP, serverPort, softVersion)
            obj.rest.setAccount(accountSid, accountToken)
            obj.rest.setAppId(appId)

            cls.instance = obj

        return cls.instance

    def send_template_sms(self,to,datas,temp_id):
        result = self.rest.sendTemplateSMS(to,datas,temp_id)
        # for k,v in result.items():
        #
        #     if k ==' templateSMS' :
        #         for k,s in v.items():
        #             print('%s:%s' % (k, s))
        #     else:
        #         print('%s:%s' % (k, v))

        status_code = result.get('statusCode')
        if status_code == '000000':
            # 表示发送成功
            return 0
        else:
            return 1
    

# if __name__ =='__main__':
#     cpp = CCP()
#     cpp.send_template_sms('15591486203',['1234',5],1)


#sendTemplateSMS(手机号码,内容数据,模板Id)