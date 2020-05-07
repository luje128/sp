import requests
import urllib3
from fake_useragent import UserAgent
from lxml import etree
import sys
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import re

# 加载web驱动路径
web_path = 'D:/chromedriver'

# 禁用警告
urllib3.disable_warnings()

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

# 悉尼大学课表
def spider_usyd_course(user_dict):
    # 获取登陆地址
    login_url = 'https://wasm.usyd.edu.au/login.cgi?apprealm=usyd&appID=tt-studentweb&destURL=https%3A//www.timetable.usyd.edu.au/personaltimetable/'
    # 获取跳转地址
    next_url = 'https://www.timetable.usyd.edu.au/personaltimetable/timetable/{}/current/?mode=schedule'
    # 设置随机请求头
    ua = UserAgent()
    # 请求头信息
    headers = {
        'User-Agent': ua.random
    }
    # 设置form表单
    data = {
        'appID': 'tt-studentweb',
        'appRealm': 'usyd',
        'destURL': 'https://www.timetable.usyd.edu.au/personaltimetable/',
        'credential_0': user_dict['user'],
        'credential_1': user_dict['password'],
        'Submit': '登入'
    }
    # print('---获取课程信息中---')
    # 保持登陆状态
    s = requests.session()
    # 为了避免ssl认证，可以将verify=False,
    p = s.post(url=login_url, data=data, headers=headers, verify=False)
    # 创建html对象
    html = etree.HTML(p.text)
    # 验证账号密码是否正确
    if len(html.xpath('//p[@class="error-text"]/span/text()')) == 0:
        pass
        # print('账号密码正确!')
        # 如果账号密码正确，则更新数据库
        # db_UD_User_Info.update_many({'openId': user_dict['openId']},{'$set': {'user_id': user_dict['user'], 'user_password': user_dict['password']}})
    else:
        # print('账号密码错误!')
        raise TypeError
    # 获取拼接的字符串
    str = html.xpath('//div[@class="auth-info"]/span/text()')[0]
    # 获取拼接的字符串
    res_str = re.search('[0-9]+', str).group()
    # 二次请求跳转
    g = s.get(url=next_url.format(res_str), headers=headers, verify=False)
    # 创建html对象
    html_next = etree.HTML(g.text)
    # print('---正在解析中---')
    # 定义一个空列表
    item_list = []
    # 判断是否有数据
    # if html_next.xpath('//p[@class="class-details"]'):
    # 遍历元素节点列表
    for detail in html_next.xpath('//p[@class="class-details"]'):
        # 定义一个空字典
        item = {}
        # 获取周数
        weeks = detail.xpath('strong/span/text()')[0].replace('of', '').replace('weeks', '').replace('week', '').strip()
        # 定义一个存放周数的空列表
        week_nums = []
        # 将全部数据进行切割
        for u in weeks.split(','):
            # 判断是否为连续周
            if re.findall('\d+-\d+', u):
                for r in re.findall('\d+-\d+', u):
                    for o in range(int(r.split('-')[0]), int(r.split('-')[1]) + 1):
                        week_nums.append(o)
            # 判断是否为单周
            else:
                week_nums.append(int(u.strip()))
        # 获取具体星期
        week = detail.xpath('../h3/text()')[0].strip()
        # 获取学期数
        semester = detail.xpath('strong/span/span/text()')[0].split(' ')[1]
        # 获取开始和结束时间段
        time = detail.xpath('strong/text()')[0]
        # 时间结构化
        if len(re.findall('\d+', time.split('to')[0].strip())) == 1:
            TS = time.split('to')[0].strip().replace('.', '').replace(' ', ':00')
        else:
            TS = time.split('to')[0].strip().replace('.', '').replace(' ', '')
        if len(re.findall('\d+', time.split('to')[1].strip())) == 1:
            TE = time.split('to')[1].strip().replace('.', '').replace(' ', ':00').replace(',', '')
        else:
            TE = time.split('to')[1].strip().replace('.', '').replace(' ', '').replace(',', '')
        # 转换成24小时制
        if len(re.findall('\d', am_pm(TS))) == 3:
            ts = '0' + am_pm(TS)
        else:
            ts = am_pm(TS)
        if len(re.findall('\d', am_pm(TE))) == 3:
            te = '0' + am_pm(TE)
        else:
            te = am_pm(TE)

        try:
            # 获取上课地点
            location = detail.xpath('a/text()')[0].strip()
        except:
            # 获取上课地点
            location = detail.xpath('text()')[0].split('in')[1].replace('*','').strip()

        # 获取课程名字
        title = ' '.join(detail.xpath('text()')[0].replace(':', '').replace('in', '').split(' ')[1:]).split(' ')[0].strip()
        # 获取课程类别
        type = detail.xpath('text()')[0]
        if re.search('Lecture', type):
            type = 'Lecture'
        elif re.search('Tutorial', type):
            type = 'Tutorial'
        elif re.search('Workshop', type):
            type = 'Workshop'
        else:
            type = 'Other Plan'
        # 获取老师信息
        teacher = ''
        # 数据格式化
        item['week_nums'] = week_nums
        item['type'] = type
        item['location'] = location
        item['time_start'] = ts
        item['time_end'] = te
        item['title'] = title
        item['week'] = week
        item['semester'] = semester
        item['teacher'] = teacher

        item_list.append(item)

        # 打印并测试
        print(item)



# USYD悉尼大学作业
def spider_usyd_homework(user_dict):
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
    login_url_usyd_homework = 'https://canvas.sydney.edu.au/calendar'
    # 加载目标地址
    browser.get(login_url_usyd_homework)
    print('---获取作业信息中---')
    # 获取并加载用户输入框
    WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="userNameInput"]')))
    # 清空
    browser.find_element_by_xpath('//*[@id="userNameInput"]').clear()
    # 输入用户名
    browser.find_element_by_xpath('//*[@id="userNameInput"]').send_keys(user_dict['user'])
    # 获取并加载密码输入框
    WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="passwordInput"]')))
    # 清空
    browser.find_element_by_xpath('//*[@id="passwordInput"]').clear()
    # 输入密码
    browser.find_element_by_xpath('//*[@id="passwordInput"]').send_keys(user_dict['password'])
    # 获取并加载登陆提交按钮
    WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="submitButton"]')))
    # 登陆提交
    browser.find_element_by_xpath('//*[@id="submitButton"]').click()
    print('登陆校验中!')
    # 获取账号密码错误信息提示
    try:
        browser.find_element_by_xpath('//*[@id="errorText"]')
        print('账号密码错误!')
        browser.close()
        raise TypeError
    except NoSuchElementException:
        print('账号密码正确!')
    # 获取并点击左边列表的按钮(calendar)
    WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="global_nav_calendar_link"]')))
    browser.find_element_by_xpath('//*[@id="global_nav_calendar_link"]').click()
    print('点击calendar跳转')
    # 获取并点击上边列表的按钮(agenda)
    WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="agenda"]')))
    browser.find_element_by_xpath('//*[@id="agenda"]').click()
    print('点击agenda跳转')

    # 判断是否有数据
    try :
        # 等待数据加载完毕
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="agenda-container"]/div[@class="agenda-event__container"]/ul/li')))
    except:
        print('无数据!')
        browser.close()
        exit()

    # 定义一个空列表
    list_item = []
    # 获取年
    year = re.findall('\d{4}', browser.find_element_by_xpath('//h2[@class="navigation_title"]/span').text)[0]
    for a in browser.find_elements_by_xpath('//div[@class="agenda-container"]/div[@class="agenda-event__container"]/ul/li'):
        # 判断是否是目标数据
        if re.findall('Due', a.find_element_by_xpath('span[1]').text) or re.findall('due', a.find_element_by_xpath('span[1]').text):
            # 定义一个空字典
            dict_item = {}
            # 获取due
            try:
                due = re.findall('\d+:\d+',a.find_element_by_xpath('span[1]').text)[0]
            except:
                due = '23:59'
            # 获取名字
            title = a.find_element_by_xpath('span[4]').text.replace('Calendar','').replace('日历','').strip()
            # 获取类别
            type = a.find_element_by_xpath('span[2]').text
            if re.search('Exam', type) or re.search('exam', type):
                type = 'Exam'
            elif re.search('Quiz', type) or re.search('quiz', type):
                type = 'Quiz'
            elif re.search('Assignment', type) or re.search('assignment', type):
                type = 'Assignment'
            else:
                type = 'Assignment'
            # 获取天
            day = a.find_element_by_xpath('../../preceding-sibling::div[1]/h3/span[2]').text.split(',')[1].strip().split()[1]
            # 获取月
            month = a.find_element_by_xpath('../../preceding-sibling::div[1]/h3/span[2]').text.split(',')[1].strip().split()[0]
            if month == 'January' or month == '一月':
                month = 1
            elif month == 'February' or month == '二月':
                month = 2
            elif month == 'March' or month == '三月':
                month = 3
            elif month == 'April' or month == '四月':
                month = 4
            elif month == 'May' or month == '五月':
                month = 5
            elif month == 'June' or month == '六月':
                month = 6
            elif month == 'July' or month == '七月':
                month = 7
            elif month == 'August' or month == '八月':
                month = 8
            elif month == 'September' or month == '九月':
                month = 9
            elif month == 'October' or month == '十月':
                month = 10
            elif month == 'November' or month == '十一月':
                month = 11
            elif month == 'December' or month == '十二月':
                month = 12

            # dict_item['week'] = week
            dict_item['time'] = str(year) + '-' + str(month) + '-' + str(day) + ' ' + due + ':' + '00'
            dict_item['title'] = title
            dict_item['type'] = type
            dict_item['remark'] = a.find_element_by_xpath('span[2]').text

            list_item.append(dict_item)

            print(dict_item)

    # 数据解析和爬取完毕后关闭
    browser.close()





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
if school == 'USYD':
    # 判断选择的类别
    if type1 == 'course':
        spider_usyd_course(user_dict)
    elif type1 == 'exam':
        pass
    elif type1 == 'homework':
        spider_usyd_homework(user_dict)
