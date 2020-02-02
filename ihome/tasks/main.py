
from celery import Celery
from ihome.tasks import config


# 创建一个Celery类的实例对象
app = Celery('ihome_task')


# 引入配置信息
app.config_from_object(config)

#自动搜寻异步任务
app.autodiscover_tasks(['ihome.tasks.sms'])