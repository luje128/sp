import datetime
import json
import time
import urllib.parse

import pytz
import requests
import urllib3
import sys

from fake_useragent import UserAgent
from lxml import etree
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import re

# 加载驱动路径
web_path = 'D:/chromedriver'

# 禁用警告
urllib3.disable_warnings()

# 获取昆士兰大学时区
UQ = pytz.timezone('Australia/Brisbane')

# 解决日期问题
def getBetweenDay(begin_date,end_date,weekday):
    date_list = []
    begin_date = datetime.datetime.strptime(begin_date, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    while begin_date <= end_date:
        if begin_date.weekday() == weekday:
            date_str = begin_date.strftime("%Y-%m-%d")
            date_list.append(date_str)
        begin_date += datetime.timedelta(days=1)
    return date_list


# 将am/pm转换成24小时制度
def am_pm(exam_begin_at):
    str1 = exam_begin_at[-2:]  # 格式
    data1 = exam_begin_at[:-2]  # 时间
    if str1.lower() == "am" and int(exam_begin_at[-7:-5]) > 12:
        hour1 = "00"
        data1 = exam_begin_at[0:12] + hour1 + exam_begin_at[-5:-2]
    if str1.lower() == "pm":
        if int(exam_begin_at[-7:-5]) < 12:
            hour1 = str(int(exam_begin_at[-7:-5]) + 12)
        else:  # int(time_str[-7:-5]) == 12
            hour1 = "12"
        data1 = hour1 + exam_begin_at[-5:-2]
    return data1




# UQ昆士兰课表
def spider_uq_course(user_dict):
    # 定义chrome的配置
    option = webdriver.ChromeOptions()
    option.add_argument('headless')
    option.add_argument('no-sandbox')
    option.add_argument('disable-dev-shm-usage')
    option.add_argument('disable-gpu')
    # 修改chrome的配置
    prefs = {
        'profile.default_content_setting_values': {
            'images': 2,  # 限制图片加载
            # 'javascript': 2  # 禁用js
        }
    }
    # 将变量传入
    option.add_experimental_option('prefs', prefs)
    # 传入驱动路径，导入设置，生成webdriver.Chrome对象
    browser = webdriver.Chrome(web_path, chrome_options=option)
    # 目标地址
    login_url = 'https://timetable.my.uq.edu.au/even/student'
    # 加载目标地址
    browser.get(login_url)

    # 获取账号框
    WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="username"]')))
    browser.find_element_by_xpath('//*[@id="username"]').send_keys(user_dict['user'])
    # 获取密码框
    WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="password"]')))
    browser.find_element_by_xpath('//*[@id="password"]').send_keys(user_dict['password'])
    # 获取登录框
    submit_first = WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//input[@value="LOGIN"]')))
    browser.execute_script("arguments[0].click();", submit_first)
    print('点击提交登陆!')

    print('---登陆校验中---')

    # 校验账号密码是否正确
    try:
        browser.find_element_by_xpath('//div[@class="sign-on__form-error"]/p')
        print('账号密码错误!')
        browser.close()
        raise TypeError
    except NoSuchElementException:
        print('账号密码正确！')

    print('---跳转中，正在加载目标页面信息---')

    # 等待目标页面元素加载完毕
    submit_Timetable = WebDriverWait(browser, 100).until(
        EC.presence_of_element_located(
            (By.XPATH, '//ul[@class="top-menu desktop-only"]/li/a[text()="Timetable"]')))
    browser.execute_script("arguments[0].click();", submit_Timetable)
    print('点击Timetable')

    submit_show = WebDriverWait(browser, 60).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="timetable-tpl"]//a[@title="Show as list"]')))
    browser.execute_script("arguments[0].click();", submit_show)
    print('点击show as list')

    submit_last = WebDriverWait(browser, 60).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="week_dropdown_mobile"]/button')))
    browser.execute_script("arguments[0].click();", submit_last)
    print('点击列表按钮')

    submit_last_last = WebDriverWait(browser, 60).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="week_dropdown_mobile"]/ul/li[@onclick="allWeekBtn()"]')))
    browser.execute_script("arguments[0].click();", submit_last_last)
    print('选择并点击All Weeks')

    print('---正在解析中---')

    try:
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//table[@class="aplus-table"]//tr[@class="tr-shade"]')))
    except:
        print('无数据!')
        browser.close()
        exit()

    # 解析元素节点列表
    item_list = []
    for i in browser.find_elements_by_xpath('//table[@class="aplus-table"]//tr[@class="tr-shade"]'):
        # 获取类别
        type = i.find_element_by_xpath('td[3]').text
        if re.search('LEC', type):
            type = 'Lecture'
        elif re.search('WOR', type):
            type = 'Workshop'
        elif re.search('TUT', type):
            type = 'Tutorial'
        else:
            type = 'Other Plan'
        # 获取年份
        year = datetime.datetime.now().astimezone(UQ).year
        # 获取拼接参数3星期代号
        weekday = ''
        # 获取星期
        week = i.find_element_by_xpath('td[5]').text
        # 判断星期数据是否存在多个
        if len(week.split(',')) > 1:
            # 遍历星期数据
            for we in week.split(','):
                if we.strip() == 'Mon':
                    week = 'Monday'
                    weekday = 0
                elif we.strip() == 'Tue':
                    week = 'Tuesday'
                    weekday = 1
                elif we.strip() == 'Wed':
                    week = 'Wednesday'
                    weekday = 2
                elif we.strip() == 'Thu':
                    week = 'Thursday'
                    weekday = 3
                elif we.strip() == 'Fri':
                    week = 'Friday'
                    weekday = 4
                elif we.strip() == 'Sat':
                    week = 'Saturday'
                    weekday = 5
                elif we.strip() == 'Sun':
                    week = 'Sunday'
                    weekday = 6
                # 获取天数
                day_list = i.find_element_by_xpath('td[11]').text
                # 创建天数列表
                day_nums = []
                for every in day_list.split(','):
                    s_m = ''
                    s_d = ''
                    e_m = ''
                    e_d = ''
                    try:
                        s_m = every.strip().split('-')[0].split('/')[1]
                        s_d = every.strip().split('-')[0].split('/')[0]
                        e_m = every.strip().split('-')[1].split('/')[1]
                        e_d = every.strip().split('-')[1].split('/')[0]
                    except:
                        s_m = every.strip().split('/')[1]
                        s_d = every.strip().split('/')[0]
                        e_m = every.strip().split('/')[1]
                        e_d = every.strip().split('/')[0]
                    # 获取年月日的拼接参数1开始时间
                    begin_date = str(year) + '-' + str(s_m) + '-' + str(s_d)
                    # 获取年月日的拼接参数2结束时间
                    end_date = str(year) + '-' + str(e_m) + '-' + str(e_d)
                    # 遍历合并到主列表
                    day_nums.extend(getBetweenDay(begin_date, end_date, weekday))
                # 获取名字
                title = i.find_element_by_xpath('td[1]').text
                # 获取地点
                location = i.find_element_by_xpath('td[8]').text
                # 获取开始时间
                time_start = i.find_element_by_xpath('td[6]').text
                # 获取持续时间
                During_Time = i.find_element_by_xpath('td[10]').text
                hour = float(During_Time.split(' ')[0])
                Time_Start_hour = time_start.split(':')[0]
                Time_Start_minute = time_start.split(':')[1]
                start = datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0,minutes=int(Time_Start_minute), hours=int(Time_Start_hour), weeks=0)
                # 计算出结束时间
                time_end = ':'.join(str(start + datetime.timedelta(hours=hour)).split(':')[:2])
                # 获取学期
                semester = re.findall('\d+', i.find_element_by_xpath('td[1]').text.split('_')[1])[0]
                # 获取老师
                teacher = ''
                # 数据结构化
                item_list.append(
                    {'day_nums': day_nums, 'type': type, 'location': location, 'time_start': time_start,
                     'time_end': time_end, 'title': title, 'week': week, 'semester': semester, 'teacher': teacher})

        # 判断星期数据是否只有一个
        else:
            if week == 'Mon':
                week = 'Monday'
                weekday = 0
            elif week == 'Tue':
                week = 'Tuesday'
                weekday = 1
            elif week == 'Wed':
                week = 'Wednesday'
                weekday = 2
            elif week == 'Thu':
                week = 'Thursday'
                weekday = 3
            elif week == 'Fri':
                week = 'Friday'
                weekday = 4
            elif week == 'Sat':
                week = 'Saturday'
                weekday = 5
            elif week == 'Sun':
                week = 'Sunday'
                weekday = 6
            # 获取天数
            day_list = i.find_element_by_xpath('td[11]').text
            # 创建天数列表
            day_nums = []
            for every in day_list.split(','):
                s_m = ''
                s_d = ''
                e_m = ''
                e_d = ''
                try:
                    s_m = every.strip().split('-')[0].split('/')[1]
                    s_d = every.strip().split('-')[0].split('/')[0]
                    e_m = every.strip().split('-')[1].split('/')[1]
                    e_d = every.strip().split('-')[1].split('/')[0]
                except:
                    s_m = every.strip().split('/')[1]
                    s_d = every.strip().split('/')[0]
                    e_m = every.strip().split('/')[1]
                    e_d = every.strip().split('/')[0]
                # 获取年月日的拼接参数1开始时间
                begin_date = str(year) + '-' + str(s_m) + '-' + str(s_d)
                # 获取年月日的拼接参数2结束时间
                end_date = str(year) + '-' + str(e_m) + '-' + str(e_d)
                # 遍历合并到主列表
                day_nums.extend(getBetweenDay(begin_date,end_date,weekday))
            # 获取名字
            title = i.find_element_by_xpath('td[1]').text
            # 获取地点
            location = i.find_element_by_xpath('td[8]').text
            # 获取开始时间
            time_start = i.find_element_by_xpath('td[6]').text
            # 获取持续时间
            During_Time = i.find_element_by_xpath('td[10]').text
            hour = float(During_Time.split(' ')[0])
            Time_Start_hour = time_start.split(':')[0]
            Time_Start_minute = time_start.split(':')[1]
            start = datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0,minutes=int(Time_Start_minute), hours=int(Time_Start_hour), weeks=0)
            # 计算出结束时间
            time_end = ':'.join(str(start + datetime.timedelta(hours=hour)).split(':')[:2])
            # 获取学期
            semester = re.findall('\d+',i.find_element_by_xpath('td[1]').text.split('_')[1])[0]
            # 获取老师
            teacher = ''
            # 数据结构化
            item_list.append({'day_nums':day_nums, 'type':type, 'location':location, 'time_start':time_start, 'time_end':time_end, 'title':title, 'week':week, 'semester':semester, 'teacher':teacher})

    # 打印出数据给php后端调用
    for res in item_list:
        print(res)

    # 数据解析和爬取完毕后关闭
    browser.close()












# UQ昆士兰大学作业
def spider_uq_homework(user_dict):
    # 保持登陆状态
    s = requests.session()
    # 设置随机请求头
    ua = UserAgent()
    # 构建第一次请求头
    headers = {
        'User-Agent': ua.random,
    }
    # 构建第一次请求的url
    url_1 = 'https://learn.uq.edu.au/webapps/login/?new_loc=%2Fwebapps%2Fcalendar%2FviewPersonal'
    # 构建第二次请求的url
    url_2 = 'https://auth.uq.edu.au/idp/module.php/core/loginuserpass.php?'
    # 构建第三次请求的url
    url_3 = 'https://learn.uq.edu.au/Shibboleth.sso/SAML2/POST'
    # 构建第四次请求的url
    url_4 = 'https://learn.uq.edu.au/webapps/calendar/calendarData/selectedCalendarEvents?'
    # 第一次请求
    res_1 = s.get(url=url_1,headers=headers)

    # 判断教务网是否在维护
    try:
        # 获取AuthState
        AuthState = etree.HTML(res_1.text).xpath('//input[@name="AuthState"]/@value')[0]
    except:
        print(204)
        raise TabError

    # 对AuthState参数进行url编码
    referer = urllib.parse.quote(AuthState)
    # 构建第二次请求头
    next_headers = {
        'User-Agent': ua.random,
        'Host': 'auth.uq.edu.au',
        'Origin': 'https://auth.uq.edu.au',
        'Referer': 'https://auth.uq.edu.au/idp/module.php/core/loginuserpass.php?AuthState='.format(referer),
        # 'Sec-Fetch-Dest': 'document',
        # 'Sec-Fetch-Mode': 'navigate',
        # 'Sec-Fetch-Site': 'same-origin',
        # 'Sec-Fetch-User': '?1',
        # 'Upgrade-Insecure-Requests': '1',
    }
    # 构建第二次post表单
    next_data = {
        'username': user_dict['user'],
        'password': user_dict['password'],
        'submit': 'LOGIN',
        'AuthState': AuthState,
    }
    # 第二次请求
    res_2 = s.post(url=url_2,headers=next_headers,data=next_data,verify=False)

    try:
        # 获取SAMLResponse
        SAMLResponse = etree.HTML(res_2.text).xpath('//input[@name="SAMLResponse"]/@value')[0]
        # 获取RelayState
        RelayState = etree.HTML(res_2.text).xpath('//input[@name="RelayState"]/@value')[0]
    except:
        print(401)
        raise TypeError

    # 构建第三次请求头
    last_headers = {
        'User-Agent': ua.random,
        'Host': 'learn.uq.edu.au',
        'Origin': 'https://auth.uq.edu.au',
        'Referer': 'https://auth.uq.edu.au/idp/module.php/core/loginuserpass.php?',
        # 'Sec-Fetch-Dest': 'document',
        # 'Sec-Fetch-Mode': 'navigate',
        # 'Sec-Fetch-Site': 'same-site',
        # 'Upgrade-Insecure-Requests': '1',
    }
    # 构建第三次post请求表单
    last_data = {
        'SAMLResponse':SAMLResponse,
        'RelayState':RelayState,
    }
    # 第三次请求
    res_3 = s.post(url=url_3,headers=last_headers,data=last_data,verify=False)
    # 第四次请求
    res_4 = s.get(url=url_4,headers=headers)

    try:
        # 解析json数据
        for res in json.loads(res_4.text):
            # 创建一个空字典来存储数据
            item = {}
            # 获取名字
            title = res['calendarName'].split('.')[0]
            # 获取备注
            remark = res['title']
            # 获取时间
            time = ' '.join(res['start'].split('T'))
            # 数据结构化
            if re.findall('Assignment',remark) or re.findall('assignment',remark):
                item['type'] = 'Assignment'
            elif re.findall('Quiz',remark) or re.findall('quiz',remark):
                item['type'] = 'Quiz'
            else:
                item['type'] = 'Assignment'
            item['title'] = title
            item['remark'] = remark
            item['time'] = time
            # 打印结果
            print(item)
    except:
        pass




# 构建命令参数1
school = sys.argv[1]
# 构建命令参数2
type1 = sys.argv[2]
# 构建命令参数3
user = sys.argv[3]
# 构建命令参数4
password = sys.argv[4]
# 构建用户和密码参数传递给爬虫执行
user_dict = {
    'user': user,
    'password': password,
}
# 根据脚本命令执行相应的爬虫
# 判断选择的院校
if school == 'UQ':
    # 判断选择的类别
    if type1 == 'course':
        spider_uq_course(user_dict)
    elif type1 == 'exam':
        pass
    elif type1 == 'homework':
        spider_uq_homework(user_dict)