import datetime
import pytz
import urllib3
import sys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import re

# 加载web驱动路径
web_path = 'D:/chromedriver'

# 禁用警告
urllib3.disable_warnings()

# 获取墨尔本大学时区
UMEL = pytz.timezone('Australia/Melbourne')

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

# UMEL墨尔本大学课表
def spider_umel_course(user_dict):
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
    login_url = 'https://mytimetable.students.unimelb.edu.au/even/student'
    # 加载目标地址
    browser.get(login_url)
    print('---获取课表信息中---')
    # 获取账号密码框
    WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="usernameInput"]')))
    browser.find_element_by_xpath('//*[@id="usernameInput"]').clear()
    browser.find_element_by_xpath('//*[@id="usernameInput"]').send_keys(user_dict['user'])
    # 获取账号密码框
    WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="passwordInput"]')))
    browser.find_element_by_xpath('//*[@id="passwordInput"]').clear()
    browser.find_element_by_xpath('//*[@id="passwordInput"]').send_keys(user_dict['password'])
    # 获取登陆框
    submit_first = WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//button[@class="button cta"]')))
    browser.execute_script("arguments[0].click();", submit_first)

    print('---校验登陆中---')

    try:
        # 获取账号密码提示框
        WebDriverWait(browser, 5).until( EC.presence_of_element_located((By.XPATH, '//div[@id="errorMessage"]')))
        if browser.find_element_by_xpath('//div[@id="errorMessage"]').text != '':
            print('账号密码错误!')
            browser.close()
            raise TypeError
    except TimeoutException:
        pass
        print('账号密码正确!')

    submit = WebDriverWait(browser, 100).until(
        EC.presence_of_element_located(
            (By.XPATH, '//ul[@class="top-menu desktop-only"]/li/a[text()="Timetable"]')))
    browser.execute_script("arguments[0].click();", submit)
    print('点击Timetable')

    submit_next = WebDriverWait(browser, 60).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="timetable-tpl"]//a[@title="Show as list"]')))
    browser.execute_script("arguments[0].click();", submit_next)
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

    # 判断有无数据
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
        item = {}
        # 获取类别
        type = i.find_element_by_xpath('td[3]').text
        if re.search('Lecture', type):
            type = 'Lecture'
        elif re.search('Workshop', type):
            type = 'Workshop'
        elif re.search('Tutorial', type):
            type = 'Tutorial'
        else:
            type = 'Other Plan'
        # 获取年份
        year = datetime.datetime.now().astimezone(UMEL).year
        # 获取拼接参数3星期代号
        weekday = ''
        # 获取星期
        week = i.find_element_by_xpath('td[5]').text
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
        day_list = i.find_element_by_xpath('td[10]').text
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
        During_Time = i.find_element_by_xpath('td[9]').text
        hour = float(During_Time.split(' ')[0])
        Time_Start_hour = time_start.split(':')[0]
        Time_Start_minute = time_start.split(':')[1]
        start = datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0,
                                   minutes=int(Time_Start_minute), hours=int(Time_Start_hour), weeks=0)
        # 计算出结束时间
        time_end = ':'.join(str(start + datetime.timedelta(hours=hour)).split(':')[:2])
        # 获取学期
        semester = re.findall('\d+', i.find_element_by_xpath('td[1]').text.split('_')[-1])[0]

        # 获取老师
        teacher = ''

        # 数据格式化
        item['day_nums'] = day_nums
        item['type'] = type
        item['location'] = location
        item['time_start'] = time_start
        item['time_end'] = time_end
        item['title'] = title
        item['week'] = week
        item['semester'] = semester
        item['teacher'] = teacher

        print(item)

        item_list.append(item)

    # 数据解析和爬取完毕后关闭
    browser.close()






# UMEL墨尔本大学作业
def spider_umel_homework(user_dict):
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
    login_url_usyd_homework = 'https://canvas.lms.unimelb.edu.au/calendar'
    # 加载目标地址
    browser.get(login_url_usyd_homework)
    print('---获取作业信息中---')
    # 加载首页面
    WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//ul[@class="pathfinder-2 white"]/li/a[@href="https://canvas.lms.unimelb.edu.au/login/saml"]')))
    # 点击跳转到登陆页面
    browser.find_element_by_xpath('//ul[@class="pathfinder-2 white"]/li/a[@href="https://canvas.lms.unimelb.edu.au/login/saml"]/strong').click()
    # 加载用户框
    WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.XPATH, '//input[@id="usernameInput"]')))
    # 输入用户
    browser.find_element_by_xpath('//input[@id="usernameInput"]').send_keys(user_dict['user'])
    # 加载密码框
    WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.XPATH, '//input[@id="passwordInput"]')))
    # 输入密码
    browser.find_element_by_xpath('//input[@id="passwordInput"]').send_keys(user_dict['password'])

    # 获取登陆提交按钮
    submit = WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//div/button[@value="Login"]')))
    # 由于普通元素获取但是无法点击，可以通过js点击解决
    browser.execute_script("arguments[0].click();", submit)
    print('点击登陆!')

    # 登陆校验
    try:
        browser.find_element_by_xpath('//*[@id="errorMessage"]')
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
    try:
        # 等待数据加载完毕
        WebDriverWait(browser, 60).until(
            EC.presence_of_element_located(
                (By.XPATH, '//div[@class="agenda-container"]/div[@class="agenda-event__container"]/ul/li')))
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
                due = re.findall('\d+:\d+', a.find_element_by_xpath('span[1]').text)[0]
            except:
                due = ''
            # 获取名字
            name = a.find_element_by_xpath('span[4]').text.replace('Calendar', '').replace('日历', '').strip()
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
            day = a.find_element_by_xpath('../../preceding-sibling::div[1]/h3/span[2]').text.split(',')[1].strip().split()[
                1]
            # 获取月
            month = \
            a.find_element_by_xpath('../../preceding-sibling::div[1]/h3/span[2]').text.split(',')[1].strip().split()[0]
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
            dict_item['name'] = name
            dict_item['type'] = type

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
if school == 'UMEL':
    # 判断选择的类别
    if type1 == 'course':
        spider_umel_course(user_dict)
    elif type1 == 'exam':
        pass
    elif type1 == 'homework':
        spider_umel_homework(user_dict)


