import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
import random

class TrainTicketBot:
    def __init__(self, from_station, to_station, departure_time, isstudent,starttime,endtime):
        self.from_st = from_station
        self.to_st = to_station
        self.de_time = departure_time
        self.isstudent = isstudent
        self.train_schedules = None
        self.starttime = starttime
        self.endtime = endtime

        # Edge选项
        self.options = Options()
        self.options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_argument('--disable-infobars')
        
        # 最简单的方式：直接启动Edge，让系统自动查找驱动
        self.driver = webdriver.Edge(options=self.options)
        self.driver.maximize_window()

    def is_element_exist(self, element):
        # 判断元素是否存在
        flag = True
        try:
            self.driver.find_element(By.XPATH, element)
            return flag
        except:
            flag = False
            return flag

    def random_sleep(self, min_seconds=0.5, max_seconds=2.0):  # 添加self参数
        """随机等待时间"""
        sleep_time = random.uniform(min_seconds, max_seconds)
        time.sleep(sleep_time)
        return sleep_time
    
    def select_train_by_time_range(self, schedules, start_time, end_time):
        """选择指定时间范围内的车次"""
        if not schedules:
            return None
        
        print(f"寻找 {start_time} 到 {end_time} 之间的车次...")
        
        # 将时间字符串转换为分钟数便于比较
        def time_to_minutes(time_str):
            """将"HH:MM"转换为分钟数"""
            try:
                if ':' in time_str:
                    hour, minute = map(int, time_str.split(':'))
                    return hour * 60 + minute
                else:
                    return 0
            except:
                return 0
        
        start_minutes = time_to_minutes(start_time)
        end_minutes = time_to_minutes(end_time)
        
        # 收集符合时间范围的车次
        available_trains = []
        
        for schedule in schedules:
            if schedule.get('has_ticket', True):  # 默认认为有票，如果有检查逻辑的话
                depart_time = schedule.get('depart_time', '')
                depart_minutes = time_to_minutes(depart_time)
                
                # 检查是否在时间范围内
                if start_minutes <= depart_minutes <= end_minutes:
                    available_trains.append({
                        'schedule': schedule,
                        'depart_minutes': depart_minutes
                    })
                    print(f"找到符合时间的车次: {depart_time}")
        
        if not available_trains:
            print(f"在 {start_time} 到 {end_time} 之间没有找到车次")
            return None
        
        # 选择策略：选择最早的一班
        available_trains.sort(key=lambda x: x['depart_minutes'])
        selected = available_trains[0]['schedule']
        
        print(f"选择最早一班: {selected.get('depart_time', '未知')}")
        return selected

    def get_train_schedule(self):
        """获取车次时间信息及对应的预订按钮"""
        self.train_schedules = []
        
        # 找到所有包含.cds的行的父元素（通常是<tr>）
        rows = self.driver.find_elements(
            By.XPATH, 
            '//*[contains(@class, "cds")]/ancestor::tr[1]'
        )
        
        for i, row in enumerate(rows):
            try:
                # 在行内查找时间元素
                time_element = row.find_element(By.CSS_SELECTOR, '.cds')
                text = time_element.text.strip()
                
                if text and len(text) >= 10:
                    # 在行内查找预订按钮
                    book_button = row.find_element(
                        By.XPATH, 
                        './/*[contains(text(), "预订")]'
                    )
                    
                    self.train_schedules.append({
                        'index': i,
                        'time_element': time_element,
                        'book_button': book_button,  # ✅ 现在一定在同一行
                        'text': text,
                        'depart_time': text[:5],
                        'arrive_time': text[5:],
                        'has_ticket': True
                    })
                    
            except:
                # 如果这行没有预订按钮，跳过
                continue
        
        return self.train_schedules
    # 选择可购车票信息
    def check_ticket(self):
        # 打开登录页面
        self.driver.get("https://kyfw.12306.cn/otn/resources/login.html")

        
        
        # 判断是否登录成功
        while not self.is_element_exist('//a[@class="txt-primary underline"]'):
            # 循环等待用于扫码登录
            self.random_sleep(1.3, 3.0)

        # 点击跳转页面
        self.driver.find_element(By.XPATH, '//a[@class="txt-primary underline"]').click()
        self.random_sleep(0.3, 1.0)


        retry_count = 0
        max_retries = 30

        while retry_count < max_retries:
            try:
                if (self.isstudent):
                    self.driver.find_element(By.XPATH, '//input[@id="sf2"]').click()
                    self.random_sleep(0.3, 1.0)

                # 定位出发地输入框，并输入站点名
                self.driver.find_element(By.XPATH, '//input[@id="fromStationText"]').click()
                self.driver.find_element(By.XPATH, '//input[@id="fromStationText"]').send_keys(self.from_st)
                elements = self.driver.find_elements(By.XPATH, '//span[@class="ralign"]')
                for element in elements:
                    if element.text == self.from_st:
                        element.click()
                        break
                self.random_sleep(0.3, 1.0)

                # 定位目的地输入框，并输入站点名
                self.driver.find_element(By.XPATH, '//input[@id="toStationText"]').click()
                self.driver.find_element(By.XPATH, '//input[@id="toStationText"]').send_keys(self.to_st)
                elements = self.driver.find_elements(By.XPATH, '//span[@class="ralign"]')
                for element in elements:
                    if element.text == self.to_st:
                        element.click()
                        break
                self.random_sleep(0.3, 1.0)

                # 定位日期输入框，并输入对应的日期
                self.driver.find_element(By.XPATH, '//input[@id="train_date"]').clear()
                self.driver.find_element(By.XPATH, '//input[@id="train_date"]').send_keys(self.de_time)
                self.random_sleep(0.3, 1.0)

                # 定位搜索按钮，并点击搜索
                self.driver.find_element(By.XPATH, '//a[@id="query_ticket"]').click()
                self.random_sleep(0.3, 1.0)
                schedules = self.get_train_schedule()
                if not schedules:
                            raise Exception("未获取到车次信息")
                
                selected = self.select_train_by_time_range(
                    schedules, 
                    start_time=self.starttime, 
                    end_time=self.endtime
                )
                if not selected:
                    raise Exception("没有符合条件的车次")
                
                selected['book_button'].click()
                self.random_sleep(0.5, 1.0)

                # 选择乘车人
                self.driver.find_element(By.XPATH, '//input[starts-with(@id, "normalPassenger_")][1]').click()
                self.random_sleep(0.3, 1.0)
                print('选择成功')

                if (self.isstudent):
                    self.driver.find_element(By.ID, "dialog_xsertcj_ok").click()
                    print('确认成功')
                    self.random_sleep(0.5, 1.5)


                # 点击提交订单
                self.driver.find_element(By.XPATH, '//a[text()="提交订单"]').click()
                print('提交成功')
                self.random_sleep(1.0, 3.0)

                # 点击提交订单
                self.driver.find_element(By.ID, 'qr_submit_id').click()
                print('确认成功')
                
                retry_count += 1  # 增加计数器
                break
            except Exception as e:
                print('================选票重试中================')
                print(f'第 {retry_count + 1} 次尝试出错: {e}')
                retry_count += 1
                
                if retry_count < max_retries:
                    # 出错时等待更长时间
                    wait_time = 3 + random.uniform(-1, 1) + (retry_count * 0.3)
                    wait_time = max(2, wait_time)  # 至少2秒
                    print(f"出错，等待 {wait_time:.1f} 秒后重试...")
                    time.sleep(wait_time)


        if retry_count >= max_retries:
            print(f"尝试 {max_retries} 次后仍未抢到票，程序结束")
        else:
            print('请在15分钟内支付订单')

        time.sleep(60)


if __name__ == '__main__':
    # 定义出发地
    from_station = '常州'

    # 定义目的地
    to_station = '上海虹桥'

    # 设置出行日期日期(最多只能设置15天内)
    departure_time = '2026-01-10'

    isstudent = True

    st = "10:00"

    et = "12:00"
    # 实例化类
    T = TrainTicketBot(from_station, to_station, departure_time,isstudent,st,et)

    # 开始自动抢票
    T.check_ticket()

