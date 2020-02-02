import sys
sys.path.append("..")

import redis
import pymysql

pymysql.install_as_MySQLdb()

class Config(object):
    '''配置信息'''
    SECRET_KEY = 'sdauifghiweuabgfuiobewaiogw8aobfio'

    # 数据库
    SQLALCHEMY_DATABASE_URI = 'mysql://root:fhl980203@127.0.0.1:3306/ihome_python4'
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    #　redis
    REDIS_HOST = '127.0.0.1'
    REDIS_POST = 6379

    # flask_session配置
    SESSION_TYPE = 'redis'  # 指定要使用的会话接口的类型

    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST,port=REDIS_POST)

    # 是否签名会话cookie sid，如果设置为True，则必须设置 flask.Flask.secret_key，默认为 False
    SESSION_USE_SIGNER =  True  # 对cookie中的session_id进行隐藏

    PERMANENT_SESSION_LIFETIME = 86400 # session数据的有效期　单位：秒



class DevelopmentConfig(Config):
    '''开发模式的配置信息'''
    DEBUG = True

class ProductionConfig(Config):
    '''生产环境模式的配置信息'''
    pass


# 映射关系
config_map = {
    "develop": DevelopmentConfig,
    "product": ProductionConfig,
}





























