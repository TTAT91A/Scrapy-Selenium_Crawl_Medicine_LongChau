import scrapy
from scrapy.http import Request, Response
from scrapy.utils.response import open_in_browser
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import datetime
import time

class medicineSpider(scrapy.Spider):
    name = "medicineSpider"
    
    def __init__(self):
        self.starting_time = datetime.datetime.now()

        self.start_urls = "https://nhathuoclongchau.com.vn/"
        self.lst_alphabet = ['A']
        self.browser = None
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0")
        self.options.add_argument("window-size=1920,1080")
        prefs = {"profile.managed_default_content_settings.images": 2}
        self.options.add_experimental_option("prefs", prefs)
        self.options.add_argument('log-level=3') #across error: "Third-party cookie will be blocked. Learn more in the Issues tab."
    def start_requests(self):
        urls = []
        # import string
        # for alphabet in string.ascii_uppercase:
        #    print(alphabet)
        for alphabet in self.lst_alphabet:
            urls.append(f"{self.start_urls}/thuoc/tra-cuu-thuoc-a-z?alphabet={alphabet}")
        for url in urls:
            # url_final  = f'{url}&page=1'
            url_final = url
            print("URL Final: ", url_final)
            yield scrapy.Request(url=url_final , callback=self.parse_alphabet , cb_kwargs={"alphabet": alphabet})
            

    def parse_alphabet(self, response, alphabet):
        total_page =  response.css('p.css-pqr9s7.text-text-primary::text').getall()[-1]

        if total_page is not None:
            total_page = int(total_page)
            for number in range(1,total_page+1):     
            # for number in range(13,21):     
                self.logger.info(f"::: Page: {number}")
                url_currentPage =  f'{self.start_urls}/thuoc/tra-cuu-thuoc-a-z?alphabet={alphabet}&page={number}'
                self.logger.info(f"::: URL: {url_currentPage}")
                yield response.follow(url_currentPage , callback=self.parse_lst)


    def parse_lst(self , response):
        lst_thuoc = response.css('div.brand_item-info__fXV4x')
        for data in lst_thuoc:
            link = data.css("a::attr(href)").get()
            link_detail = f'{self.start_urls}{link}'

            print("Link detail: ", link_detail)
            # self.logger.info(f"::: URL: {link_detail}")
            yield response.follow(link_detail , callback=self.parse_detail, cb_kwargs={"link_detail": link_detail} )

    def parse_detail(self, response, link_detail):
        time.sleep(2)
        def get_prices():
            self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
            self.browser.get(link_detail)
            # self.browser.get_screenshot_as_file("screenshot.png")

            # self.browser.delete_all_cookies()
            check_existed_prices = bool(self.browser.find_elements(By.CLASS_NAME,"sale-price"))
            if check_existed_prices:
                units = self.browser.find_elements(By.XPATH,"/html/body/div[1]/div[1]/div[2]/div[3]/div/div[1]/div[2]/div/div[5]/table/tbody/tr[1]/td[2]/div/span")
                prices = {}
                for unit in units:
                    unit.click()
                    WebDriverWait(self.browser, 5).until(EC.presence_of_element_located((By.XPATH,"/html/body/div[1]/div[1]/div[2]/div[3]/div/div[1]/div[2]/div/div[4]/div/div")))
                    str_price = self.browser.find_element(By.XPATH,"/html/body/div[1]/div[1]/div[2]/div[3]/div/div[1]/div[2]/div/div[4]/div/div/span[1]").text[:-1]
                    str_price = str_price.replace(".", "") #remove the dot (eg: 45.000 -> 45000)
                    unit_price = int(str_price)
                    prices[unit.text] = unit_price
            else:
                prices = None
            self.browser.quit()
            return prices

        #get medicine's name
        name  = response.css('h1.css-18o6y07.text-gray-10.inline.align-middle.font-medium::text').get()
        
        #get medicine's price
        check = bool(response.css('tr.content-container.\!mb-4'))
        if check:
            price = get_prices()
        else:
            price = None
        
        #get medicine's detail
        fields = response.css('tr.content-container')
        dct_detail = {}
        for field in fields:
            field_detail = field.css('p.css-1c4fxto.text-gray-7::text').get()
            value_detail = []
            value_two = field.css('span.css-1l7n2ui::text').getall()
            value_one = field.css('div.css-1e2qim1.text-gray-10::text').getall()
    
            if len(value_one) != 0:
                for i in value_one:
                    value_detail.append(i)
            
            if len(value_two) != 0:
                for i in value_two:
                    value_detail.append(i)
    
            dct_detail[field_detail] = value_detail

        yield {
            "name": name,
            "price": price,
            "dct_detail": dct_detail
        }

    def close(self):
        self.ending_time = datetime.datetime.now()
        duration = self.ending_time - self.starting_time
        print("Total time: ",duration)