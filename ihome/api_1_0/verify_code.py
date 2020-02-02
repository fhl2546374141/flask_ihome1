
from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store,constants,db
from flask import current_app,jsonify,make_response,request
from ihome.utils.response_code import RET
from ihome.models import User
import random
from ihome.libs.yuntongxun.SendTemplateSMS import CCP
# from ihome.tasks.task_sms import send_sms

from ihome.tasks.sms.tasks import send_sms

# GET 127.0.0.1:5000/api/v1.0/image_codes/<image_code_id>
@api.route('/image_codes/<image_code_id>')
def get_image_code(image_code_id):
    '''
    获取图片验证码
    :param image_code_id :图片验证码编号
    :return:验证码图片
    '''
    # 获取参数
    # 校验参数


    # 业务处理

    # 1 生成验证码图片
    # 名字，真实文本,图片数据
    name,text,image_code=captcha.generate_captcha()

    # 2 将验证码的图片和编号保存到redis中，设置有效期
    # redis:str hash set zset list
    # 使用哈希维护时，有效期只能整体设置,不能单条设置
    # "image_codes":{"id1":"xxx","":""}  哈希 hset("image_codes","id1","xxx")

    # 单条数据记录,选择字符串
    # "image_code_编号1":"真实值"
    # "image_code_编号2":"真实值"
    # "image_code_编号3":"真实值"

    # redis_store.set('image_code_%s' % image_code_id,text)
    # redis_store.expire('image_code_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES)
    try:
        # 设置图片编号和内容,同时设置有效期
        redis_store.setex('image_code_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='保存图片验证码失败')
    # 3 返回图片
    resp = make_response(image_code)
    resp.headers["Content-Type"] ="image/jpg"
    return resp



# # GET 127.0.0.1:5000/api/v1.0/sms_codes/<mobile>?image_code_id=xxx&image_code=xxx
# @api.route('/sms_codes/<re(r"1[34578]\d{9}"):mobile>')
# def get_sms_code(mobile):
#     '''获取短信验证码'''
#     # 获取参数
#     image_code_id = request.args.get('mage_code_id')
#     image_code = request.args.get('image_code')
#     # 校验参数?
#     if not all([image_code_id, image_code]):
#         return jsonify(err=RET.PARAMERR,errmsg='参数不完整')
#
#     # 业务处理
#     # 从redis中取去验证码图片的编号的真实值
#     try:
#         real_image_code = redis_store.get('image_code_%s' % image_code_id)
#     except Exception as e:
#         # 记录日志hi
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, errmsg='数据库查询错误')
#
#     # 判断 验证码图片的编号的真实值是否过期
#     if real_image_code is None:
#         return jsonify(errno=RET.DATAERR,errmsg='图片验证码过期')
#
#
#     # 删除reids中的图片验证码,防止用户使用同一个验证码验证多次
#     try:
#         redis_store.delete('image_code_%s' % image_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#
#
#     # 与用户填写的值进行对比 判断正确性
#     if real_image_code.decode().lower() != image_code.lower():
#         return jsonify(errno=RET.DATAERR,errmsg='图片验证码错误')
#
#
#     # 判断对于这个手机号的操作,在60秒内有没有之前的记录,如果有,则表示操作频繁，不进行处理
#     try:
#         send_flag = redis_store.get('send_sms_code_%s' % mobile)
#     except Exception as e:
#         current_app.logger.error(e)
#
#     else:
#         if send_flag is not None:
#             # 表示60秒内之前有发过短信
#             return jsonify(errno=RET.REQERR,errmag='请求过于频繁,请60秒后重试')
#
#
#     # 判断手机号是否已经注册
#     try:
#         user_mobile = User.query.filter_by(mobile=mobile).first()
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if user_mobile is not None:
#             return jsonify(errno=RET.DATAEXIST,errmsg='手机号已经存在')
#
#     # 如果不存在，则生成短信验证码
#     sms_code = '%06d' % random.randint(0,999999)  # %06d  表示生成6位整数，不够的前边补0 ，如029541
#
#     # 保存真实的短信验证码
#     try:
#         redis_store.setex('sms_code_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES,sms_code)
#         redis_store.setex('send_sms_code_%s' % mobile,constants.SEND_SMS_CODE_INTERVAL,1)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR,errmsg='保存短信验证码失败')
#
#     # 发送短信
#     cpp = CCP()
#     result = cpp.send_template_sms(mobile,[sms_code,int(constants.SMS_CODE_REDIS_EXPIRES/60)],1)
#
#     # 返回值
#     if result == 0:
#         return jsonify(errno=RET.OK,errmsg='发送成功')
#     else:
#         return jsonify(errno=RET.THIRDERR,errmsg='发送失败')



# GET 127.0.0.1:5000/api/v1.0/sms_codes/<mobile>?image_code_id=xxx&image_code=xxx
@api.route('/sms_codes/<re(r"1[34578]\d{9}"):mobile>')
def get_sms_code(mobile):
    '''获取短信验证码'''
    # 获取参数
    image_code_id = request.args.get('mage_code_id')
    image_code = request.args.get('image_code')
    # 校验参数?
    if not all([image_code_id, image_code]):
        return jsonify(err=RET.PARAMERR,errmsg='参数不完整')

    # 业务处理
    # 从redis中取去验证码图片的编号的真实值
    try:
        real_image_code = redis_store.get('image_code_%s' % image_code_id)
    except Exception as e:
        # 记录日志hi
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    # 判断 验证码图片的编号的真实值是否过期
    if real_image_code is None:
        return jsonify(errno=RET.DATAERR,errmsg='图片验证码过期')


    # 删除reids中的图片验证码,防止用户使用同一个验证码验证多次
    try:
        redis_store.delete('image_code_%s' % image_code_id)
    except Exception as e:
        current_app.logger.error(e)


    # 与用户填写的值进行对比 判断正确性
    if real_image_code.decode().lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR,errmsg='图片验证码错误')


    # 判断对于这个手机号的操作,在60秒内有没有之前的记录,如果有,则表示操作频繁，不进行处理
    try:
        send_flag = redis_store.get('send_sms_code_%s' % mobile)
    except Exception as e:
        current_app.logger.error(e)

    else:
        if send_flag is not None:
            # 表示60秒内之前有发过短信
            return jsonify(errno=RET.REQERR,errmag='请求过于频繁,请60秒后重试')


    # 判断手机号是否已经注册
    try:
        user_mobile = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user_mobile is not None:
            return jsonify(errno=RET.DATAEXIST,errmsg='手机号已经存在')

    # 如果不存在，则生成短信验证码
    sms_code = '%06d' % random.randint(0,999999)  # %06d  表示生成6位整数，不够的前边补0 ，如029541

    # 保存真实的短信验证码
    try:
        redis_store.setex('sms_code_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES,sms_code)
        redis_store.setex('send_sms_code_%s' % mobile,constants.SEND_SMS_CODE_INTERVAL,1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='保存短信验证码失败')

    # 发送短信
    # 使用celer异步发送短信，delay函数调用后立即返回
    send_sms.delay(mobile,[sms_code,int(constants.SMS_CODE_REDIS_EXPIRES/60)],1)

    # 返回值
    return jsonify(errno=RET.OK,errmsg='发送成功')


