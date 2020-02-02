

// js读取cookie的方法
function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;  //三目运算 python写法：r[1] if r else undefined
}

// 保存图片验证码编号 全局变量
var imageCodeId = "";

//封装的函数 通过js能产生(UUID:通用唯一识别码)
function generateUUID() {
    var d = new Date().getTime();
    if(window.performance && typeof window.performance.now === "function"){
        d += performance.now(); //use high-precision timer if available
    }
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random()*16)%16 | 0;
        d = Math.floor(d/16);
        return (c=='x' ? r : (r&0x3|0x8)).toString(16);
    });
    return uuid;
}

function generateImageCode() {
    // 形成图片验证码的后端地址， 设置到页面中，让浏览请求验证码图片
    // 1. 生成图片验证码编号
    imageCodeId = generateUUID();
    // 设置图片url
    var url = "/api/v1.0/image_codes/" + imageCodeId; //后端图片验证码地址
    $(".image-code img").attr("src", url);  //设置scr 属性 为：url
}


function sendSMSCode() {
    // 点击发送短信验证码后被执行的函数
    $(".phonecode-a").removeAttr("onclick");

    var mobile = $("#mobile").val();
    var re = /^1[3456789]\d{9}$/;

    if (!mobile) {
        $("#mobile-err span").html("请填写正确的手机号！");
        $("#mobile-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    }

    if (!re.test(mobile)) {
        $("#mobile-err span").html("请填写正确的手机号！");
        $("#mobile-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    }


    var imageCode = $("#imagecode").val();
    if (!imageCode) {
        $("#image-code-err span").html("请填写验证码！");
        $("#image-code-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    }


    // 构造向后端发送请求的参数
    var req_data = {
        image_code: imageCode,  //图片验证码的值
        mage_code_id: imageCodeId //图片验证码的编号(全局变量)
    };

    //向后端发送get请求
    $.get('/api/v1.0/sms_codes/' + mobile, req_data, function (data) {
        // data是后端返回的响应值,后端返回的是json字符串，
        // 所以ajax就帮助我们把这个json对象转换为js对象,data就是这个转换后的对象
        if (data.errno == '0') {
            var num = 60;
            //表示发送成功
            var timer = setInterval(function () {
                //修改文本
                if (num > 1) {
                    $('.phonecode-a').html(num + '秒');
                    num -= 1
                } else {
                    $('.phonecode-a').html('获取验证码');
                    $(".phonecode-a").attr("onclick", "sendSMSCode();");
                    clearInterval(timer)
                }

            }, 1000, 60)
        } else {
            alert(data.errmsg);
            $(".phonecode-a").attr("onclick", "sendSMSCode();");

        }
    });
}


$(document).ready(function() {
    generateImageCode();
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#imagecode").focus(function(){
        $("#image-code-err").hide();
    });
    $("#phonecode").focus(function(){
        $("#phone-code-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
        $("#password2-err").hide();
    });
    $("#password2").focus(function(){
        $("#password2-err").hide();
    });


    // 为表单的提交添加自定义的函数行为
    $(".form-register").submit(function(e){

        e.preventDefault(); //阻止浏览器对于表单的默认的提交行为

        // 之后使用自定义的表单的提交的行为
        var mobile = $("#mobile").val();
        var phoneCode = $("#phonecode").val();
        var passwd = $("#password").val();
        var passwd2 = $("#password2").val();

        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        }

        if (!phoneCode) {
            $("#phone-code-err span").html("请填写短信验证码！");
            $("#phone-code-err").show();
            return;
        }

        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }

        if (passwd != passwd2) {
            $("#password2-err span").html("两次密码不一致!");
            $("#password2-err").show();
            return;
        }

        // 调用ajax向后端发送注册请求
        var req_data = {
            mobile: mobile,
            sms_code: phoneCode,
            password: passwd,
            password2: passwd2
        };
        var req_json = JSON.stringify(req_data);  //转换为json数据

        $.ajax({
            url: '/api/v1.0/users',
            type: 'post',
            data: req_json,
            contentType: 'application/json',
            dataType: 'json',
            headers:{  // 自定义请求头
                "X-CSRFToken": getCookie("csrf_token") //配合后端的csrf防护机制
            }, //请求头 将csrf_token值放到请求中,方便后端scrf进行验证
            success: function (resp) {
                if (resp.errno == '0'){
                    location.href = 'index.html';
                } else {
                    alert(resp.errmsg);
                }
            }
        });
    });
});
