
from werkzeug.routing import BaseConverter
import functools
from flask import session,jsonify,g
from ihome.utils.response_code import RET


class ReConverter(BaseConverter):
    '''自定义转换器'''
    def __init__(self,url_map,regex):

        # 调用父类
        super().__init__(url_map)
        # 将正则表达式的参数保存到对象的属性中，flask会去使用这个属性来进行路由的正则匹配
        self.regex = regex




# Python装饰器（decorator）在实现的时候，被装饰后的函数其实已经是另外一个函数了（函数名等函数属性会发生改变），
# 为了不影响，Python的functools包中提供了一个叫wraps的decorator来消除这样的副作用。写一个decorator的时候，
# 最好在实现之前加上functools的wrap，它能保留原有函数的名称和docstring.   @functools.wraps(该参数为外层函数的参数)

def login_required(view_func):

    @functools.wraps(view_func)
    def wrapper(*args,**kwargs):
        # 判断用户的登录状态
        user_id = session.get('user_id')
        # 如果用户是登录的返回视图函数
        if user_id is not None:
            g.user_id = user_id  # 将user_id保存到g对象中，在视图函数中可以通过g对象获取保存的数据
            return view_func(*args,**kwargs)
        else:
            # 如果未登录,返回未登录的信息
            return jsonify(errno=RET.SESSIONERR,errmsg='用户未登录')
    return wrapper


