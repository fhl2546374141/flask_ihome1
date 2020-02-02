

from . import api
from ihome.utils.response_code import RET
from ihome import redis_store,db,constants
from flask import request,jsonify,current_app,session
import re
from ihome.models import User
from sqlalchemy.exc import IntegrityError


# 127.0.0.1:5000/users
@api.route('/users',methods=['POST'])
def register():
    '''
    注册
    请求的参数：手机号，短信验证码，密码,确认密码
    参数格式：json
    '''
    # 获取请求的参数，返回字典
    req_dict = request.get_json()

    mobile = req_dict.get('mobile')
    sms_code = req_dict.get('sms_code')
    password = req_dict.get('password')
    password2 = req_dict.get('password2')


    # 校验参数
    if not all([mobile,sms_code,password,password2]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不完整')

    if not re.match(r'1[34578]\d{9}',mobile):
        return jsonify(errno=RET.PARAMERR,errmsg='手机格式错误')

    if password != password2:
        return jsonify(errno=RET.PARAMERR,errmsg='两次密码不一致')



    # 验证短信验证码是否正确
    # 从redis中获取手机对应的短信验证码
    try:
        real_sms_code = redis_store.get('sms_code_%s'% mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='读取短信验证码异常')

    # 判断是否过期
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA,errmag='短信验证码失效')


    # 删除reids中的图片验证码,防止用户使用同一个验证码验证多次
    try:
        redis_store.delete('sms_code_%s' % mobile)
    except Exception as e:
        current_app.logger.error(e)


    # # 判断用户填写短信验证码的正确性
    # if real_sms_code != sms_code:
    #     return jsonify(errno=RET.DATAERR,errmag='短信验证码错误')
    #
    # # 判断手机号是否已经注册
    # try:
    #     user_mobile = User.query.filter_by(mobile=mobile).first()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DBERR,errmsg='数据库异常')
    # else:
    #     if user_mobile is not None:
    #         return jsonify(errno=RET.DATAEXIST,errmsg='手机号已经存在')

    # 保存用户的注册信息到数据库中
    user= User(name=mobile,mobile=mobile)
    user.password = password  # 设置属性


    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        # 表示手机号出现重复,手机号被注册过了
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST,errmsg='手机号已存在')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据库查询异常')


    # 保存登录状态到session中
    session['name']=mobile
    session['mobile']=mobile
    session['user_id']=user.id

    # 返回结果
    return jsonify(errno=RET.OK,errmsg='注册成功')





# POST 127.0.0.1:5000/sessions
@api.route('/sessions',methods=['POST'])
def login():
    '''
    登录
    请求的参数：手机号，密码,
    参数格式：json
    '''
    # 获取参数
    req_dict = request.get_json()

    mobile = req_dict.get('mobile')
    password = req_dict.get('password')

    #检验参数
    if not all([mobile,password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不完整')

    # 验证手机号格式
    if not re.match(r'1[34578]\d{9}',mobile):
        return jsonify(errno=RET.PARAMERR,errmsg='手机格式错误')

    # 判断错误次数超过限制次数,如果超过则返回
    # redis记录： access_num_请求的ip地址i：'次数'
    user_ip = request.remote_addr  # 获取用户ip地址

    try:
        access_num = req_dict.get('access_num_%s' % user_ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_num is not None and int(access_num)>constants.LOGIN_ERROR_MAX_TIMES:
            return jsonify(errno=RET.REQERR,errmsg='登录次数过多,请稍后重试')

    # 从数据库中查询用户手机号对应的对象数据（密码 ）
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='获取用户信息失败')

    # 用数据库中的密码与用户填写的密码进行对比
    if user is None or not user.check_password(password):
        # 如果失败 记录错误的次数,返回提示信息
        try:
            redis_store.incr('access_num_%s' % user_ip,1)
            redis_store.expire('access_num_%s' % user_ip,constants.LOGIN_ERROR_FORBID_TIME)
        except Exception as e:
            current_app.logger.error(e)

        return jsonify(errno=RET.DATAERR,errmsg='手机号或者密码')

    # 如果验证相同，登录成功，保存登录的状态到session中
    session['name']=user.name
    session['mobile']=mobile
    session['user_id']=user.id

    return jsonify(errno=RET.OK,errmsg='登录成功')


@api.route('/session', methods=['GET'])
def check_login():
    """检查登陆状态"""
    # 尝试从session中获取用户的名字
    name = session.get('name')
    # 如果session中的name存在，则表示已经登陆，否则未登录
    if name is not None:
        return jsonify(errno=RET.OK, errmsg='true', data={"name": name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg='false')




@api.route('/session', methods=['DELETE'])
def logout():
    """退出"""
    # 清除session数据
    # print('清除前:',session)
    csrf_token = session.get("csrf_token")
    # print('清除前的csrf_token:', csrf_token)
    session.clear()
    session['csrf_token'] = csrf_token
    # print('清除后:', session)
    return jsonify(errno=RET.OK, errmsg='ok')









