import datetime
import time
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


def getBetweenDay(begin_date, end_date, weekday):
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
def spider_uoa_course():
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
    login_url = 'https://www.student.auckland.ac.nz/psc/ps/EMPLOYEE/SA/c/UOA_MENU_FL.UOA_VW_CAL_FL.GBL'
    # 加载目标地址
    browser.get(login_url)

    print('---获取课表信息中---')

    # time.sleep(999999)

    # 获取并加载用户框
    WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="username"]')))
    browser.find_element_by_xpath('//*[@id="username"]').clear()
    browser.find_element_by_xpath('//*[@id="username"]').send_keys('zwu551')

    # 获取并加载密码框
    WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="password"]')))
    browser.find_element_by_xpath('//*[@id="password"]').clear()
    browser.find_element_by_xpath('//*[@id="password"]').send_keys('19991219')

    # 获取并加载登陆提交按钮
    submit_first = WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="_eventId_proceed"]')))
    browser.execute_script("arguments[0].click();", submit_first)

    print('---校验登陆中---')

    try:
        browser.find_element_by_xpath('//p[@role="alert"]')
        print('账号密码错误!')
        browser.close()
        raise TypeError
    except NoSuchElementException:
        print('账号密码正确！')

    print('---跳转中，正在加载目标页面信息---')

    # 等待跳转页面加载完毕
    sub = WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.XPATH, '//label[text()="List View"]')))
    # 点击列表详情
    browser.execute_script("arguments[0].click();", sub)
    print('点击List View')

    # 等待跳转页面加载完毕
    WebDriverWait(browser, 60).until(
        EC.presence_of_element_located((By.XPATH, '//tr[@class="ps_grid-row psc_rowact"]')))

    # 循环
    for x in range(999):

        time.sleep(1)

        # 获取元素节点列表
        submit_second = browser.find_elements_by_xpath('//tr[@class="ps_grid-row psc_rowact"]')

        time.sleep(1)

        try:
            # 点击
            browser.execute_script("arguments[0].click();", submit_second[x])
            print('点击Details')
        except:
            print('元素节点列表遍历完毕,结束进程')
            browser.close()
            break

        time.sleep(1)

        # 切换句柄iframe
        WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.XPATH, '//iframe[@title="Popup window"]')))
        browser.switch_to.frame(browser.find_element_by_xpath('//iframe[@title="Popup window"]'))
        print('切换到iframe')

        time.sleep(1)

        # 点击Meeting Information
        submit_third = WebDriverWait(browser, 60).until(
            EC.presence_of_element_located((By.ID, 'DERIVED_SSR_FL_SSR_CL_DTLS_LFF$68$_LBL')))
        browser.execute_script("arguments[0].click();", submit_third)
        print('点击Meeting Information')

        time.sleep(3)

        # 获取并加载数据
        WebDriverWait(browser, 60).until(
            EC.presence_of_element_located((By.XPATH, '//tr[@class="ps_grid-row"]/td[1]/div/span')))
        for res in browser.find_elements_by_xpath('//tr[@class="ps_grid-row"]/td[1]/div/span'):
            print(res.find_element_by_xpath('.').text)

        time.sleep(1)

        # 解析完毕后关闭窗口
        WebDriverWait(browser, 60).until(EC.presence_of_element_located((By.ID, '#ICCancel')))
        submit = browser.find_element_by_id('#ICCancel')
        browser.execute_script("arguments[0].click();", submit)
        print('点击close')

        time.sleep(1)

        # 初始化iframe
        browser.switch_to.default_content()
        print('退出所有iframe，初始化')

        time.sleep(1)




if __name__ == '__main__':
    spider_uoa_course()
