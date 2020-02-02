
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from config import config_map
from flask_sqlalchemy import SQLAlchemy
import redis
from flask_session import Session
from flask_wtf import CSRFProtect
from ihome.utils.commons import ReConverter



#数据库
db = SQLAlchemy() # 先创建db对象,没有与app绑定，什么时候执行create_app,什么时候将app对象传给db

# 创建redis链接对象
redis_store = None



# logging.error('wsefw') # 错误级别
# logging.warn('wsefw')　# 警告级别
# logging.info('wsefw')　# 信息提示级别
# logging.debug('wsefw')　# 调试级别

# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG)  # 调试debug级
# 创建日志记录器，指明日志的保存路径，每个日志文件的最大大小，保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式                等级      输入日志信息的文件名    行数       日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（current_app）添加日志记录器
logging.getLogger().addHandler(file_log_handler)



# 工厂模式
def create_app(config_name):
    """
    创建flask应用对象
    :param config_name:　str 配置模式的模式的名字('develop','product')
    :return:　app对象
    """

    # 根据配置模式的名字获取模式的类
    app = Flask(__name__)
    config_class = config_map.get(config_name)
    app.config.from_object(config_class)

    # 使用app初始化db
    db.init_app(app)

    # 初始化redis工具
    global redis_store
    redis_store = redis.StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_POST)

    # 利用flask_session,将session数据保存到redis中
    Session(app)

    # 将自定义的转换器添加到flask的应用中
    app.url_map.converters['re']=ReConverter

    # 为flask补充csrf防护
    CSRFProtect(app)


    from ihome import api_1_0
    # 注册蓝图
    app.register_blueprint(api_1_0.api,url_prefix = '/api/v1.0')

    # 注册提供静态页面的蓝图
    from ihome import web_html
    app.register_blueprint(web_html.html)

    return app