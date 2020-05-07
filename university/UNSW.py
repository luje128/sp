import time
import datetime
import json
import re
import sys
import pytz
import requests
import urllib3
from fake_useragent import UserAgent
from lxml import etree

# 禁用警告
urllib3.disable_warnings()

# 获取新南大学时区
UNSW = pytz.timezone('Australia/Sydney')

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

# 新南大学课程表
def spider_unsw_course(user_dict):
    print('---获取课程信息中---')
    # 获取登陆地址
    login_url = 'https://ssologin.unsw.edu.au/cas/login?service=https%3A%2F%2Fmy.unsw.edu.au%2Factive%2FstudentTimetable%2Ftimetable.xml'
    # 获取跳转地址
    next_url = 'https://my.unsw.edu.au/active/studentTimetable/timetable.xml'
    # 获取json数据地址
    json_url = 'https://my.unsw.edu.au/active/studentTimetable/timetable.xml?data=classes'
    # 设置随机请求头
    ua = UserAgent()
    # 请求头信息
    headers = {
        'User-Agent': ua.random
    }
    # 请求第一次提交登陆表单的参数
    ll = requests.get(url='https://my.unsw.edu.au/active/studentTimetable/timetable.xml',headers=headers)
    # 获取参数
    ll_html = etree.HTML(ll.text)
    try:
        # 转换成字符串
        lt = ll_html.xpath('//input[@name="lt"]/@value')[0].strip()
    except:
        raise TabError
    # 设置form表单
    data = {
        '_eventId': 'submit',
        'username': user_dict['user'],
        'password': user_dict['password'],
        'submit': 'Agree and sign on',
        'lt': lt,
    }
    # print('---获取课程信息中---')
    # 保持登陆状态
    s = requests.session()
    # 为了避免ssl认证，可以将verify=False,
    p = s.post(url=login_url, data=data, headers=headers, verify=False)
    # 创建html对象
    p_first = etree.HTML(p.text)
    # 验证账号密码是否正确
    if len(p_first.xpath('//*[@id="error-div"]/text()')) == 0:
        # print('账号密码正确!')
        pass
    else:
        # print('账号密码错误!')
        raise TypeError
    # 获取登陆跳转的目标页面
    g = s.get(url=next_url, headers=headers, verify=False)
    # 创建html对象
    html_next = etree.HTML(g.text)
    # 获取二次登陆提交表单参数
    bsdsSequence = html_next.xpath('//input[@name="bsdsSequence"]/@value')[0]
    # 获取二次登陆提交表单参数
    term = ''
    # 获取学期数
    semester = ''
    try:
        term = html_next.xpath('//option[text()="Term 1 2020"]/@value')[0]
        # 获取学期
        if len(re.findall('\w+\s(\d+)\s\w+',html_next.xpath('//option[text()="Term 1 2020"]/text()')[0])) == 0:
            semester = ''
        else:
            semester = re.findall('\w+\s(\d+)\s\w+',html_next.xpath('//option[text()="Term 1 2020"]/text()')[0])[0]
    except:
        # print('暂无最新学期课表信息')
        # 如果无最新学期课表信息则终止程序，下面代码无法进行，只是中断程序，不会报错
        exit()
    # 构建二次登陆提交表单参数
    data_next = {
        'bsdsSequence': bsdsSequence,
        'term': term,
        'bsdsSubmit-refresh': '',
    }
    p_next = s.post(url=next_url, data=data_next, headers=headers, verify=False)
    # 创建html对象
    html_next_next = etree.HTML(p_next.text)
    # 请求json数据地址
    h = s.get(url=json_url, headers=headers, verify=False)
    # 获取响应文本
    res = h.content.decode()
    # json数据转换成python字典
    json_res = json.loads(res)

    # 创建一个空列表
    item_list = []
    for j in json_res['meetings']:
        # 创建一个空字典
        item = {}
        week = ''
        if j['day'] == 1:
            week = 'Monday'
        elif j['day'] == 2:
            week = 'Tuesday'
        elif j['day'] == 3:
            week = 'Wednesday'
        elif j['day'] == 4:
            week = 'Thursday'
        elif j['day'] == 5:
            week = 'Friday'
        elif j['day'] == 6:
            week = 'Saturday'
        elif j['day'] == 7 or j['day'] == 0:
            week = 'Sunday'
        # 定义一个存放周数的空列表
        week_nums = []
        # 将全部数据进行切割
        for u in j['weeks'].split(','):
            # 判断是否为连续周
            if re.findall('\d+-\d+', u):
                for r in re.findall('\d+-\d+', u):
                    for o in range(int(r.split('-')[0]), int(r.split('-')[1]) + 1):
                        week_nums.append(o)
            # 判断是否为单周
            else:
                week_nums.append(int(u.strip()))
        # 获取地点
        location = ''
        # 获取类型
        type = ' '
        instructor = ''
        for i in html_next_next.xpath('//td[@colspan="4"]/table//tr/td[1]'):
            if int(i.xpath('string(.)')) == int(j['cn']):

                try:
                    location = i.xpath('../td[8]/text()')[0]
                except:
                    location = ''

                try:
                    instructor = i.xpath('../td[10]/text()')[0]
                except:
                    instructor = ''

                type = i.xpath('string(../td[2])')
                if re.search('Lecture', type):
                    type = 'Lecture'
                elif re.search('Tutorial', type):
                    type = 'Tutorial'
                elif re.search('Workshop', type):
                    type = 'Workshop'
                else:
                    type = 'Other Plan'
        Time_Start = ':'.join(j['start'].split(':')[:2])
        Time_End = ':'.join(j['end'].split(':')[:2])
        if len(re.findall('\d', Time_Start)) == 3:
            ts = '0' + Time_Start
        else:
            ts = Time_Start
        if len(re.findall('\d', Time_End)) == 3:
            td = '0' + Time_End
        else:
            td = Time_End

        # 数据格式化
        item['week_nums'] = week_nums
        item['type'] = type
        item['location'] = location
        item['time_start'] = ts
        item['time_end'] = td
        item['title'] = j['title']
        item['week'] = week
        item['semester'] = semester
        item['teacher'] = instructor

        item_list.append(item)

        # 打印并测试
        print(item)


# 新南大学作业
def spider_unsw_homework(user_dict):
    print('---获取作业信息中---')
    # 第一次请求url
    first_url = 'https://ssologin.unsw.edu.au/cas/login?service=https://moodle.telt.unsw.edu.au/login/index.php?authCAS=CAS'
    # 第三次请求url
    third_url = 'https://moodle.telt.unsw.edu.au/calendar/view.php'
    # 设置随机请求头
    ua = UserAgent()
    # 请求头信息
    headers = {
        'User-Agent': ua.random,
    }
    # 第一次请求
    first_g = requests.get(url=first_url,headers=headers)
    # 获取第二次请求的post参数
    lt =  etree.HTML(first_g.text).xpath('//input[@name="lt"]/@value')[0]
    # 获取第二次请求的post参数
    second_text = etree.HTML(first_g.text).xpath('//form[@id="muLoginForm"]/@action')[0]
    # 构建第二次请求的post参数
    second_data = {
        'lt':lt,
        '_eventId': 'submit',
        'username': user_dict['user'],
        'password': user_dict['password'],
        'submit': 'Agree and sign on',
    }
    # 保持登陆状态
    s = requests.session()
    # 第二次请求
    second_p = s.post(url=first_url,data=second_data,headers=headers,verify=False)
    # 第三次请求
    third_g = s.get(url=third_url,headers=headers)

    # 校验
    if etree.HTML(third_g.text).xpath('//span[@class="usertext mr-1"]/text()'):
        # 账号密码正确
        pass
    else:
        # 账号密码有误
        raise TypeError

    # 新建一个空列表
    item_list = []
    # 解析数据
    for res in etree.HTML(third_g.text).xpath('//div[@class="eventlist my-1"]/div'):
        # 新建一个空字典
        item = {}
        # 获取今天日期并转换时区
        today = datetime.datetime.now().astimezone(UNSW)
        # 获取明天日期并转换时区
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        # 获取年
        year = today.year
        # 获取月
        month = ''
        # 获取日
        day = ''
        # 获取due
        due = ''
        # 判断是否是今天
        if re.findall('Today',res.xpath('div/div[@class="description card-body"]/div[1]/div//text()')[0]):
            # 获取月
            month = today.month
            # 获取日
            day = today.day
            try:
                # 获取due
                due = res.xpath('div/div[@class="description card-body"]/div[@class="row"]/div[@class="col-xs-11"]/text()')[0].replace(',', '').replace(' ', '')
            except:
                # 获取due
                due = res.xpath('div/div[@class="description card-body"]/div[@class="row"]/div[@class="col-xs-11"]/span/text()')[0].replace(',', '').replace(' ', '')

        # 判断是否是明天
        elif re.findall('Tomorrow',res.xpath('div/div[@class="description card-body"]/div[1]/div//text()')[0]):
            # 获取月
            month = tomorrow.month
            # 获取日
            day = tomorrow.day
            try:
                # 获取due
                due = res.xpath('div/div[@class="description card-body"]/div[@class="row"]/div[@class="col-xs-11"]/text()')[0].replace(',', '').replace(' ', '')
            except:
                # 获取due
                due = res.xpath('div/div[@class="description card-body"]/div[@class="row"]/div[@class="col-xs-11"]/span/text()')[0].replace(',', '').replace(' ', '')

        else:
            # 获取月
            month = res.xpath('div/div[@class="description card-body"]/div[1]/div/a/text()')[0].split(',')[1].strip().split()[1]
            # 获取日
            day = res.xpath('div/div[@class="description card-body"]/div[1]/div/a/text()')[0].split(',')[1].strip().split()[0]
            # 获取due
            due = res.xpath('div/div[@class="description card-body"]/div[@class="row"]/div[@class="col-xs-11"]/text()')[0].replace(',', '').replace(' ', '')

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

        num = ''
        try:
            # 获取编号代码
            num = re.findall('[a-zA-Z0-9]*',res.xpath('div/div[@class="description card-body"]/div[last()]/div/a/text()')[0])[0]
        except:
            # 获取编号代码
            num = re.findall('[a-zA-Z0-9]*',res.xpath('div/div[@class="description card-body"]/div[last()-1]/div/a/text()')[0])[0]

        # 获取名字
        name = res.xpath('div/div[1]//h3[@class="name d-inline-block"]/text()')[0].replace('is due','').strip()
        # 获取类别
        type = ''
        if re.search('Exam', name) or re.search('exam', name):
            type = 'Assignment'
        elif re.search('Quiz', name) or re.search('quiz', name):
            type = 'Quiz'
        elif re.search('Assignment', name) or re.search('assignment', name):
            type = 'Assignment'
        else:
            type = 'Assignment'

        # 构建标题
        title = num + ' ' + name

        # item['week'] = week
        item['title'] = title
        item['type'] = type
        item['time'] = str(year) + '-' + str(month) + '-' + str(day) + ' ' + am_pm(due) + ':' + '00'
        item['remark'] = res.xpath('div/div[1]//h3[@class="name d-inline-block"]/text()')[0]

        item_list.append(item)

        # 打印测试
        print(item)








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
if school == 'UNSW':
    if type1 == 'course':
        spider_unsw_course(user_dict)
    elif type1 == 'homework':
        spider_unsw_homework(user_dict)


