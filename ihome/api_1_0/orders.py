
from datetime import datetime

from flask import current_app, request, g, jsonify

from . import api
from ihome import db, redis_store
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from ihome.models import House, Order


# POST 127.0.0.1:5000/api/v1.0orders
@api.route('/orders',methods=['POST'])
@login_required
def save_orders():
    '''保存订单'''


    # 获取下单人ID（用户id）
    user_id = g.user_id
    # 获取参数
    order_data = request.get_json()

    if not order_data:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')

    house_id = order_data.get('house_id')  # 预订的房间编号
    start_data_str = order_data.get('start_data') # 预订的入住时间
    end_data_str = order_data.get('end_data') # 预定的结束时间

    if not all([house_id,start_data_str,end_data_str]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')

    # 处理日期 (将字符串转换为时间：使用datetime.strptime())
    try:
        start_date = datetime.strptime(start_data_str,"%Y-%m-%d")
        end_date = datetime.strptime(end_data_str,"%Y-%m-%d")
        assert start_date<=end_date

        # 预订的总天数
        days = (end_date-start_date).days+1  # datetime.timedelta
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='日期格式错误')

    # 查询房子是否而存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取房屋信息失败')
    if not house:
        return jsonify(errno=RET.DATAERR,errmsg='房屋不存在')

    # 预定的用户是否是房东自己 防止刷单
    if user_id == house.user_id:
        return jsonify(errno=RET.ROLEERR,errmsg='禁止预定自己发布的房屋')


    # 保证用户预定的时间内,没有被别人下单
    # 查询时间冲突的订单
    try:
        confilct_orders = Order.query.filter(Order.house_id==house_id,
                                             Order.begin_date<=end_date,
                                             Order.end_date>=start_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询出错')

    if confilct_orders>0:
        return jsonify(errno=RET.DATAERR,errmsg='房屋被预定')

    #　订单总额
    amount = days * House.house_price

    # 保存订单数据
    order = Order(
        house_id=house_id,
        user_id=user_id,
        begin_date=start_date,
        end_date=end_date,
        days=days,
        house_price=house.price,
        amount=amount

    )

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存订单失败')
    return jsonify(errno=RET.OK,errmsg='ok',data={'order_id':order.id})


# 127.0.0.1:5000/api/v1.0/user/orders?role=custom role=landlord

@api.route('/user/orders',methods=['GET'])
@login_required
def get_user_order():
    '''查询用户的订单信息'''

    # 获取用户的id
    user_id = g.user_id

    # 判断用户的身份是房东还是游客　landlord or custom
    # 用户的身份，用户想要查询作为房客预定别人房子的订单，
    # 还是想要作为房东查询别人下的订单
    role = request.args.get('role','')

    try:
        if 'landlord' == role:
            # 身份为房东
            # 查询属于自己的房子
            houses = House.query.filter(House.user_id==user_id).all()
            house_ids = [house.id for house in houses]

            # 再查询被人预定了自己的房屋
            orders = Order.query.filter(House.user_id.in_(house_ids)).order_by(Order.create_time.desc()).all()

        else:
            # 身份为游客
            # 查询自己下的订单
            orders = Order.query.filter(Order.user_id==user_id).order_by(Order.create_time.desc()).all()

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询订单信息失败')

    # 将订单信息转换为字典
    orders_dict_li=[]
    if orders:
        for order in orders:
            orders_dict_li.append(order.to_dict())

    return jsonify(errno=RET.OK,errmsg='ok',data={'orders':orders_dict_li})


# PUT 127.0.0.1:5000/api/v1.0/orders/orderId/status

@api.route("/orders/<int:order_id>/status", methods=['PUT'])
@login_required
def accept_reject_order(order_id):
    """
    接单、拒单
    :param order_id: 订单 id
    :return:
    """
    # 获取用户id
    user_id = g.user_id

    # 获取参数
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # action参数表明客户端请求的是接单还是拒单的行为
    action = req_data.get("action")
    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        # 根据订单号查询订单，并且要求订单处于等待接单状态
        order = Order.query.filter(Order.id==order_id, Order.status=="WAIT_ACCEPT").first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='无法获取订单数据')

    # 确保房东只能修改属于自己房子的订单
    if not order or house.user_id != user_id:
        return jsonify(errno=RET.REQERR, errmsg='操作无效')

    if action == 'accept':
        # 接单，将订单状态设置为等待评论
        order.status = "WAIT_PAYMENT"
    elif action == 'reject':
        # 拒单，要求用户传递拒单原因
        reason = req_data.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
        order.status = "REJECTED"
        order.comment = reason

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='操作失败')

    return jsonify(errno=RET.OK, errmsg='OK')






# PUT 127.0.0.1:5000/api/v1.0/orders/orderId/comment

@api.route("/orders/<int:order_id>/comment", methods=['PUT'])
@login_required
def save_order_comment(order_id):
    """保存评论信息
    参数：订单编号
    """
    # 获取用户 id
    user_id = g.user_id

    # 获取参数
    req_data = request.get_json()
    comment = req_data.get("comment")

    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 根据订单编号,检验该订单是自己下的订单,并且处于待评论的状态, 否则不予许评论
    try:
        order = Order.query.filter(Order.id==order_id, Order.user_id==user_id, Order.status=='WAIT_COMMENT').first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='无法获取订单数据')

    if not order:
        return jsonify(errno=RET.REQERR, errmsg='无法操作')

    # 保存评论
    try:
        # 修改订单状态为"已完成"
        order.status = 'COMPLETE'
        # 添加评论内容
        order.comment = comment
        # 房子表中该房子被订单数量加 1
        house.order_count += 1
        # 提交
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='操作失败')

    # 因为房屋详情中有订单的评价信息，为了让最新的评价信息展示在房屋详情中，所以删除redis中关于本订单房屋的详情缓存
    try:
        redis_store.delete("house_info_%s" % order.house.id)
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(errno=RET.OK, errmsg='OK')






