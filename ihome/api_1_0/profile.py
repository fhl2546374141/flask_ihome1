

from . import api
from ihome.utils.commons import login_required
from flask import current_app,g,jsonify,request,session
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models import User
from ihome import db,constants

@api.route('/users/avatar',methods=['POST'])
@login_required
def set_user_avatar():
    '''
    设置用户的头像
    参数：用户图像 用户id
    :return:
    '''
    # 获取参数
    #装饰器的代码中已经将user_id 保存到g对象中,视图可以直接获取
    user_id = g.user_id

    # 获取图片 以request.files.get 获取图片
    image_file = request.files.get('avatar')

    if image_file is None:
        return jsonify(errno=RET.PARAMERR,errmsg='未上传图片')

    # 读取图片数据
    image_data = image_file.read()


    # 调用七牛上传图片,返回文件名
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='图片上传失败')

    # 将文件名保存到数据库
    try:
        User.query.filter_by(id=user_id).update({'avatar_url':file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='保存图片失败')

    avatar_url =constants.QINIU_URL_DOMAIN + file_name
    # 上传成功返回
    return jsonify(errno=RET.OK,errmsg='上传图片成功',data={'avatar_url':avatar_url})




@api.route('/users/name',methods=['PUT'])
@login_required
def change_user_name():
    '''修改用户名'''
    # 获取参数
    user_id = g.user_id
    req_data = request.get_json()

    # 参数校验
    if not req_data:
        return jsonify(errno=RET.PARAMERR,errmsg='数据不完整')

    # 获取要修改的用户名
    name = req_data.get('name')

    # 判读是否为空
    if name is None :
        return jsonify(errno=RET.PARAMERR,errmsg='姓名不能为空')


    # 将姓名保存到数据库
    try:
        User.query.filter_by(id=user_id).update({'name':name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.loggerl.error(e)
        return jsonify(errno=RET.DBERR,errmsg='设置用户名错误')

    #更新session中name的值
    session['name']=name

    # 返回结果
    return jsonify(errno=RET.OK,errmsg='修改成功')




@api.route('/user',methods=['GET'])

@login_required
def get_user_profile():
    '''
    个人主页中获取用户信息
    包括：用户头像，用户名，手机号
    格式：json
    :return:
    '''
    # 获取用户id
    user_id = g.user_id

    # 根据user_id查询用户信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='获取用户信息失败')

    # 判断user是否为空
    if user is None:
        return jsonify(errno=RET.NODATA,errmsg='无效操作')

    return jsonify(errno=RET.OK,errmsg='ok',data=user.to_dict())




@api.route('/users/auth',methods=['GET'])

@login_required
def get_user_auth():
    '''获取用户的实名认证信息'''
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,ermsg='获取用户实名认证信息失败')


    return jsonify(errno=RET.OK,errmsg='ok',data=user.auto_to_dict())





@api.route('/users/auth',methods=['POST'])

@login_required
def set_user_auth():
    '''保存实名认证信息'''

    # 获取参数
    user_id = g.user_id
    req_data = request.get_json()
    # 检验参数
    if not req_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数不完整')

    # 获取用户真实姓名和身份证号
    real_name = req_data.get('real_name')
    id_card = req_data.get('id_card')


    # 将用户实名认证信息保存到数据库中

    try:
        User.query.filter_by(id=user_id).update({'real_name':real_name,'id_card':id_card})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='保存用户实名信息失败')


    return jsonify(errno=RET.OK,errmsg='保存成功')





