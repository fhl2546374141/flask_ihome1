from . import api
from ihome.utils.response_code import RET
from flask import current_app,g,jsonify,request,session
from ihome.utils.commons import login_required
from ihome.utils.image_storage import storage
from ihome.models import Area,House,Facility,HouseImage,User,Order
from ihome import db,constants,redis_store
import json
from datetime import datetime


@api.route('/areas',methods=['GET'])
def get_area_info():
    '''获取城区信息     使用redis设置缓存'''

    #　先从redis中获取数据
    try:
        resp_json = redis_store.get('area_info')
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json is not None:
            # 返回给前端的数据是html格式，要转化json格式　表示redis中有缓存数据
            return resp_json,200,{'Content-Type':'application/json'}


    # 在查询数据库，读取城区信息
    try:
        area_li = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据库异常')

    # 将对象转换为字典
    area_dict_li=[]
    for area in area_li:
        area_dict_li.append(area.to_dict())

    # return jsonify(errno=RET.OK,errmsg='ok',data=area_dict_li)
    # 将从数据库获取的数据 先保存到redis中, 前端先从redis中获取数据,为空时, 再从数据库获取数据  此为设置缓存

    # 将给前端返回的数据转换为json字符串 dict()可以设置为字典
    resp_dict = dict(errno=RET.OK,errmsg='ok',data=area_dict_li)
    resp_json = json.dumps(resp_dict)


    # 将数据保存到redis中 设置过期时间
    try:
        redis_store.setex('area_info',constants.AREA_INFO_REDIS_CACHE_EXPIRE,resp_json)
    except Exception as e:
        current_app.logger.error(e)

    # 返回给前端的数据是html格式，要转化json格式
    return resp_json, 200, {'Content-Type':'application/json'}




@api.route('/houses/info',methods=['POST'])
@login_required
def save_house_info():
    '''
    保存房屋的基本信息
    前端传过来的json数据包括：
    {
        "title": "",5
        "price": "",
        "area_id": "1",
        "address": "",
        "room_count": "",
        "acreage": "",
        "unit": "",
        "capacity": "",
        "beds": "",
        "deposit": "",
        "min_days": "",
        "max_days": "",
        "facility": ["7", "8",....]
    }
    '''
    # 获取参数
    user_id = g.user_id
    house_data = request.get_json()

    title = house_data.get('title')  # 标题
    price = house_data.get('price')  # 单价
    area_id = house_data.get('area_id')  # 区域的编号
    address = house_data.get('address')  # 地址
    room_count = house_data.get('room_count')  # 房间数
    acreage = house_data.get('acreage')  # 面积
    unit = house_data.get('unit')  # 布局（几厅几室）
    capacity = house_data.get('capacity')  # 可容纳人数
    beds = house_data.get('beds')  # 卧床数目
    deposit = house_data.get('deposit')  # 押金
    min_days = house_data.get('min_days')  # 最小入住天数
    max_days = house_data.get('max_days')  # 最大入住天数

    # 检验参数 facility为非必填参数,可选填
    if not all([title,price,area_id,address,room_count,acreage,unit,capacity,beds,deposit,min_days,max_days]):
        return jsonify(errno=RET.PARAMERR,errmsg='数据不完整')



    # 对单价和押金进行检验,是否为数字　检验方法：可否转换为数字
    try:
        price = int(float(price)*100)
        deposit = int(float(deposit)*100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')

    # 判断区域是否存在，防止发布的城区在数据库中没有，进行过滤操作
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据库异常')

    # 如果城区在数据库不存在
    if area is None:
        return jsonify(errno=RET.NODATA,errmsg='城区信息异常')


    # 保存数据
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        room_count=room_count,
        address=address,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )



    # try:
    #     db.session.add(house)
    #     db.session.commit()
    # except Exception as e:
    #     db.session.rollback()
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DBERR,errmsg='保存数据异常')

    # 处理房屋设施信息
    facility_ids = house_data.get('facility')


    # 如果用户勾选了信息在保存到数据库
    if facility_ids:
        # [7,8,...]
        # 过滤出设施数据在数据库中存在的数据
        # select * from ih_facility_info where id in []
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='数据库异常')

        # 如果facility存在
        if facilities:
            # 表示有合法的数据存在

            # 保存设施数据
            house.facilities = facilities



    # 将房屋的基本信息和房屋设施信息保存到数据库中　
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')

    # 保存数据成功
    return jsonify(errno=RET.OK, errmsg='保存数据成功', data={"house_id": house.id})





@api.route('/houses/image',methods=['POST'])
@login_required
def save_house_image():
    '''
    保存房屋图片信息
    参数户：房屋3图片，房屋的id
    格式：json
    '''

    #　获取参数
    image_file = request.files.get('house_image')
    house_id = request.form.get('house_id')  # 表单提交　可以通过form获取参数

    # 检验参数
    if not all([image_file,house_id]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不完整')

    # 检验房屋是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,ermsg='数据库异常')

    if house is None:
        return jsonify(errno=RET.NODATA,errmsg='房屋不存在')


    # 读取图片数据
    image_data = image_file.read()

    # 调用七牛上传图片,返回文件名
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='图片上传失败')

    # 将图片保存到数据库
    house_image = HouseImage(house_id=house_id, url=file_name)
    db.session.add(house_image)

    #处理房屋的主图片
    if not house.index_image_url:
        house.index_image_url = file_name
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='数据库异常')

    # 返回结果
    image_url = constants.QINIU_URL_DOMAIN + file_name
    return jsonify(errno=RET.OK,errmsg='ok',data={'image_url':image_url})

# GET 127.0.0.1:5000/user/houses
@api.route('user/houses',methods=['GET'])
@login_required
def get_user_houses():
    '''获取房东发布的房源的信息的条目'''
    #　获取参数
    user_id = g.user_id
    # 检验参数
    try:
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='获取数据失败')

    if not houses:
        return jsonify(errno=RET.NODATA,errmsg='数据不存在')

    # 将查询到的房屋信息转换为字典存到列表中
    houses_li=[]
    for house in houses:
        houses_li.append(house.to_basic_dict())
    return jsonify(errno=RET.OK,errmsg='ok',data={'houses':houses_li})



# GET 127.0.0.1:5000/houses/index
@api.route('houses/index',methods=['GET'])
def get_house_index():
    '''
    获取主页幻灯片展示房屋基本信息
    使用redis缓存
    '''
    # 获取参数
    # 从缓存中获取参数
    try:
        ret = redis_store.get('index_home_data')
    except Exception as e:
        current_app.logger.error(e)
        ret=None
    if ret:
        # 因为redis中保存的就是json字符串,直接进行字符串拼接返回
        return '{"errno":0,"errmsg":"ok","data":%s}' % ret,200,{"Content-Type":"application/json"}
    else:
        # 查询数据库,返回房屋订单最多的５条记录  (降序排列)
        try:
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='数据库查询数据失败')

        # 数据不存在
        if not houses:
            return jsonify(errno=RET.NODATA,errmsg='数据不存在')

        # 将查询到的信息转换为字典存到列表中
        houses_li=[]
        for house in houses:
            houses_li.append(house.to_basic_dict())

        # 将数据转换为json,并保存到redis中
        json_houses = json.dumps(houses_li)

        try:
            redis_store.setex('index_home_data',constants.HOME_PAGE_DATA_REDIS_EXPIRES,json_houses)
        except Exception as e:
            current_app.logger.error(e)

        return '{"errno":0,"errmsg":"ok","data":%s}' % json_houses,200,{"Content-Type":"application/json"}


# GET 127.0.0.1:5000/api/v1.0/houses/1
@api.route('houses/<int:house_id>',methods=['GET'])
def get_house_detail(house_id):
    '''获取房屋详情页数据'''
    # 前端在房屋详情信息展示时,如果浏览的用户不是该房屋的房东,则展示 "预定" 按钮,否则不展示
    # 所以需要后端返回登录用户的id

    # 尝试获取用户登录的信息,若登录，返回给前端登录用户的id,否则返回user_id = -1
    user_id = session.get('user_id',-1)

    # 检验参数
    if not user_id:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 从redis中获取数据
    try:
        ret = redis_store.get('house_info_%s' % house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret=None
    if ret:
        return '{"errno":0 ,""errmsg:"ok", "data":{"user_id":%s,"house":%s}}' % (user_id,ret), 200, {"Content-Type":"application/json"}

    else:
        try:
            # 从数据库中查询房屋的详细信息
            house = House.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='数据库查询失败')

        if not house:
            return jsonify(errno=RET.NODATA,errmsg='房屋详细数据不存在')


        # 将房屋对象转换为字典　并保存到redis中
        house_detail_data=  house.to_full_dict()
        json_house_detail = json.dumps(house_detail_data)

        try:
            redis_store.setex('house_info_%s' % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND, json_house_detail)
        except Exception as e:
            current_app.logger.error(e)

        return '{"errno":0, ""errmsg:"ok", "data":{"user_id":%s, "house":%s}}' % (user_id,house_detail_data), 200, {"Content-Type":"application/json"}


# 从时间转换为字符串：使用datetime.strftime()
# 从字符串转换为时间：使用datetime.strptime()
# 127.0.0.1:5000/api/v1.0/houses?sd=2019-1-1&ed=2019-1-31&aid=1&sk=new&p=1
# 参数：入住时间，结束时间，。区域编号，页码
@api.route('/houses',methods=['GET'])
def get_house_list():
    '''获取服房屋的列表信息(搜索页面)'''
    # 获取参数
    start_data = request.args.get('sd','') # 用户想要的起始时间
    end_data = request.args.get('ed','') #　用户想要的而结束时间
    area_id = request.args.get('aid','') #　区域的编号
    sort_key = request.args.get('sk','new') #　排序关键字  设置默认排序
    page = request.args.get('p') #　页数

    # 处理时间
    try:
        if start_data:
             start_data = datetime.strptime(start_data,"%Y-%m-%d")

        if end_data:
            end_data = datetime.strptime(end_data,"%Y-%m-%d")

        if start_data and end_data:
            assert start_data <= end_data

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='日期参数错误')


    # 判断区域编号
    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR,errmsg='区域参数错误')

    # 页数的处理
    try:
        page=int(page)
    except Exception as e:
        current_app.logger.error(e)
        page=1

    # 从redis中获取缓存数据
    redis_key = 'house_%s_%s_%s_%s' % (start_data,end_data,area_id,sort_key)
    try:
        resp_json = redis_store.hget(redis_key,page)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json:
            return resp_json,200,{'Content-Type':'application/json'}



    # 过滤条件的参数列表容器
    filter_params = []

    # 填充过滤的参数
    confilct_orders=None
    try:
        if start_data and end_data:
            # 查询冲突的订单
            confilct_orders = Order.query.filter(Order.begin_date<=end_data,Order.end_date>=start_data).all()
        elif start_data:
            # 查询冲突的订单
            confilct_orders = Order.query.filter(Order.end_date>=start_data).all()
        elif end_data:
            # 查询冲突的订单
            confilct_orders = Order.query.filter(Order.begin_date<=end_data).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="数据库异常")

    if confilct_orders:
        # 从冲突的订单中获取房屋的ID
        confilct_house_ids = [Order.house_id for Order in confilct_orders]
        # 如果冲突的ID不为空，向查询参数中添加条件 　　notin_()表示没有在该条件内
        if confilct_house_ids:
            filter_params.append(House.id.notin_(confilct_house_ids))

    # 区域条件
    if area_id:
        filter_params.append(House.area_id == area_id)

    # 查询数据库
    # 补充排序条件

    if sort_key =='booking':
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key =='price_inc':
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key =='price_des':
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    # 其他情况都是按照默认的新旧排序
    else:
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())


    # 处理分页
    try:
        #                                 当前页　　　　　　　　　　每页数量　　　　　　　　　　　　　　　　　自动的错误输出
        page_obj = house_query.paginate(page=page,per_page=constants.HOUSE_LIST_PAGE_CAPACITY,error_out=False)
    except Exception as e:
        return jsonify(errno=RET.DBERR,errmsg='数据库异常')



    # 获取页面数据
    house_li = page_obj.items
    houses=[]
    for house in house_li:
        houses.append(house.to_basic_dict())

    # 获取总页数
    total_page = page_obj.pages

    # 将数据转换为字典
    resp_dict = dict(errno=RET.OK,errmsg='OK',data={'total_page':total_page,'houses':houses,'current_page':page})
    # 转换为json格式的数据
    resp_json = json.dumps(resp_dict)

    # redis  在redis中存储数据　使用哈希
    # house_起始_结束_区域id_排序：hash
    # {
    #     "1": {},
    #     "2": {},
    # }


    # 设置key值
    redis_key = 'house_%s_%s_%s_%s' % (start_data,end_data,area_id,sort_key)
    if page<=total_page:
        # 哈希类型
        try:
            # # 设置缓存数据
            # redis_store.hset(redis_key,page,resp_json)
            # # 设置缓存时间
            # redis_store.expire(redis_key,constants.HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRE)

            # 创建redis管道对象,可以一次性执行多条语句
            pipeline = redis_store.pipeline()

            # 开启多个语句的记录
            pipeline.multi()
            # 设置缓存数据
            redis_store.hset(redis_key, page, resp_json)
            # 设置缓存时间
            redis_store.expire(redis_key, constants.HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRE)
            # 执行语句
            pipeline.execute()

        except Exception as e:
            current_app.logger.error(e)

    return resp_json,200,{'Content-Type':'application/json'}
























