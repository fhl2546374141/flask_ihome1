

from flask import Blueprint,current_app,make_response
from flask_wtf import csrf

# 提供静态页面的蓝图

html = Blueprint('web_html',__name__)


@html.route('/<re(r".*"):html_file_name>')
def get_html(html_file_name):
    '''提供html文件'''
    # 如果访问的地址问空,则表示的是请求主页
    if not html_file_name:
        html_file_name='index.html'

    # 如果html_file_name 不是　favicon.ico
    if html_file_name != 'favicon.ico':
        html_file_name = 'html/' + html_file_name

    # 创建一个csrf_token的值
    csrf_token = csrf.generate_csrf()

    #　flask 提供的返回静态文件的方法
    resp = make_response(current_app.send_static_file(html_file_name))

    # 设置cookie值
    resp.set_cookie('csrf_token',csrf_token)

    return resp

