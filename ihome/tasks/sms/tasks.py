

from ihome.tasks.main import app
from ihome.libs.yuntongxun.SendTemplateSMS import CCP

# 定义任务函数
@app.task
def send_sms(to,datas,temp_id):
    '''发送短信的异步任务'''
    ccp=CCP()
    ccp.send_template_sms(to,datas,temp_id)
