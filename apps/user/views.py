from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth import authenticate, login, logout

from user.models import User, Address
from celery_tasks.tasks import send_register_active_email
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from utils.mixin import LoginRequiredMixin
import re


# /user/register
def register(request):
    '''注册页面'''
    if request.method == 'GET':
        #显示注册页面
        return render(request, 'register.html')
    else:
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': "请同意协议"})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})
        # 进行业务处理：注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 返回应答,跳转到首页
        return redirect(reverse('goods:index'))


def register_handle(request):
    '''处理注册'''
    #接收数据
    username = request.POST.get('user_name')
    password = request.POST.get('pwd')
    email = request.POST.get('email')
    allow = request.POST.get('allow')

    #进行数据校验
    if not all([username, password, email]):
        #数据不完整
        return render(request, 'register.html', {'errmsg':'数据不完整'})
    #校验邮箱
    if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'errmsg':'邮箱格式不正确'})

    if allow != 'on':
        return render(request, 'register.html', {'errmsg':"请同意协议"})

    #校验用户名是否重复
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        #用户名不存在
        user = None

    if user:
        #用户名已存在
        return render(request, 'register.html', {'errmsg':'用户名已存在'})
    #进行业务处理：注册
    user = User.objects.create_user(username, email, password)
    user.is_active = 0
    user.save()

    #返回应答,跳转到首页
    return redirect(reverse('goods:index'))


class RegisterView(View):
    '''注册'''
    def get(self, request):
        '''显示注册页面'''
        return render(request, 'register.html')

    def post(self, request):
        '''注册处理'''
        # 接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        # 校验邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': "请同意协议"})

        # 校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在
            user = None

        if user:
            # 用户名已存在
            return render(request, 'register.html', {'errmsg': '用户名已存在'})
        # 进行业务处理：注册
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        #发送激活邮件，包含激活链接
        #激活链接中需要包含用户的身份信息, 并且加密身份信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm':user.id}
        token = serializer.dumps(info) #bytes
        token = token.decode()

        #发邮件
        send_register_active_email.delay(email, username, token)

        # 返回应答,跳转到首页
        return redirect(reverse('goods:index'))


class ActiveView(View):
    '''用户激活'''
    def get(self, request, token):
        '''进行用户激活'''
        #进行解密，获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            #获取待激活用户的id
            user_id = info['confirm']

            #根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            #跳转到登陆页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            #激活链接已过期
            return HttpResponse('激活链接已过期')


class LoginView(View):
    '''登陆'''
    def get(self, request):
        '''显示登陆页面'''
        #判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        #使用模板
        return render(request, 'login.html', {'username':username, 'checked':checked})

    def post(self, request):
        '''登录校验'''
        #接受数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        #校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg':'数据不完整'})

        user = authenticate(username=username, password=password)
        if user is not None:
            #用户名密码正确
            if user.is_active:
                #用户已激活
                #记录用户登录状态
                login(request, user)

                #获取登陆后要跳转的地址
                next_url = request.GET.get('next', reverse('goods:index'))
                # 跳转到首页
                response =  redirect(next_url)

                #判断是否需要记住用户名
                remember = request.POST.get('remember')

                if remember == 'on':
                    #记住用户名
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                #返回response
                return response

            else:
                #用户未激活
                return render(request, 'login.html', {'errmsg':'账户未激活'})
        else:
            # the authentication system was unable to verify the username and password
            return render(request, 'login.html', {'errmsg':'用户名或密码错误'})


class LogoutView(View):
    '''退出登录'''
    def get(self, request):
        #清除用户的session
        logout(request)

        #跳转到首页
        return redirect(reverse('goods:index'))

# /user
class UserInfoView(LoginRequiredMixin, View):
    '''用户中心-信息页'''
    def get(self, request):
        '''显示'''
        # 获取用户的个人信息
        # 获取用户的最近浏览
        return render(request, 'user_center_info.html', {'page':'user'})

# /user/order
class UserOrderView(LoginRequiredMixin, View):
    '''用户中心-订单页'''
    def get(self, request):
        '''显示'''
        # 获取用户的订单信息
        return render(request, 'user_center_order.html', {'page':'order'})

# user/address
class AddressView(LoginRequiredMixin, View):
    '''用户中心-地址页'''
    def get(self, request):
        '''显示'''

        # 获取登陆用户对应的user对象
        user = request.user
        # 获取用户的默认收货地址
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收货收货地址
        #     address = None
        address = Address.objects.get_default_address(user)

        return render(request, 'user_center_site.html', {'page':'address', 'address': address})

    def post(self, request):
        '''地址添加'''
        #接受数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        #校验数据
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg':'数据不完整'})
        #校验手机号
        if not re.match('^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg':'手机格式错误'})

        #业务处理
        #如果用户已存在默认收货地址，添加的地址不作为默认收货地址,否则用作默认收货地址
            # 获取登陆用户对应的user对象
        user = request.user
            # 获取用户的默认收货地址
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #         # 不存在默认收货收货地址
        #     address = None

        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True

        #添加地址
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone = phone,
                               is_default=is_default)

        #返回应答,刷新地址页面
        return redirect(reverse('user:address'))