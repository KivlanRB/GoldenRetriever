from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chromium.options import ChromiumOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.utils import ChromeType
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import datetime

class EmasAPI():

    __headless = True

    __login_site_link = "https://emas.ui.ac.id/login/index.php"
    __login_uname_css = "input#username"
    __login_pword_css = "input#password"
    __login_bttn_css  = "input#loginbtn"
    __login_error_css = "a#loginerrormessage"

    __timeline_site_link = "https://emas.ui.ac.id/my/?myoverviewtab=timeline"
    __timeline_task_name_css = "li > div.visible-desktop > div > div.event-name-container > a"
    __timeline_task_deadline_css = "li > div.visible-desktop > div > div.row-fluid > div.span5"
    __timeline_task_course_css = "li > div.visible-desktop > div > div.event-name-container > div > small"

    def __init__(self) -> None:
        try:
            options = ChromeOptions()
            if self.__headless:
                options.add_argument("headless")
                options.add_argument('disable-gpu')
            self.driver = webdriver.Chrome(options=options, executable_path=ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        except ValueError:
            try:
                options = ChromiumOptions()
                if self.__headless:
                    options.add_argument("headless")
                    options.add_argument('disable-gpu')
                self.driver = webdriver.Chrome(options=options, executable_path=ChromeDriverManager().install())
            except ValueError:
                try:
                    options = FirefoxOptions()
                    if self.__headless:
                        options.headless = True
                    self.driver = webdriver.Firefox(options=options, executable_path=GeckoDriverManager().install())
                except ValueError:
                    options = EdgeOptions()
                    options.use_chromium = True
                    options.add_argument("headless")
                    options.add_argument('disable-gpu')
                    self.driver = webdriver.Edge(options=options, executable_path=EdgeChromiumDriverManager().install())
    
    def __check_element(self, css:str) -> bool:
        try:
            element = self.driver.find_elements(By.CSS_SELECTOR, css)
        except NoSuchElementException:
            return False
        return element[0]
    
    def login(self, uname:str, pword:str) -> bool:
        """ 
        Logs in to the EMAS page. CSS selectors are initialized as
        the attributes of the class.

        Arguments - uname: Username of the account
                    pword: Password of the account

        Returns - Bool. True if no login errors detected, false otherwise.
        """
        self.driver.get(self.__login_site_link)
        uname_element:WebElement = self.driver.find_element(By.CSS_SELECTOR, self.__login_uname_css)
        pword_element:WebElement = self.driver.find_element(By.CSS_SELECTOR, self.__login_pword_css)
        bttn_element:WebElement = self.driver.find_element(By.CSS_SELECTOR, self.__login_bttn_css)
        uname_element.send_keys(uname)
        pword_element.send_keys(pword)
        bttn_element.click()
        self.driver.refresh()
        try:
            logerr_element:WebElement = self.driver.find_element(By.CSS_SELECTOR, self.__login_error_css)
        except NoSuchElementException:
            return True
        print(logerr_element.get_attribute("text"))
        return False
    
    def get_timeline(self) -> list:
        self.driver.get(self.__timeline_site_link)
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, self.__timeline_task_name_css)))
        task_names_element:list = self.driver.find_elements(By.CSS_SELECTOR, self.__timeline_task_name_css)
        task_deadlines_element:list = self.driver.find_elements(By.CSS_SELECTOR, self.__timeline_task_deadline_css)
        tasks = list()
        for task_name, task_deadline in zip(task_names_element, task_deadlines_element):
            deadline:str = task_deadline.text
            name:str = task_name.text
            date:datetime.datetime = datetime.datetime.strptime(deadline, "%d %b, %H:%M").replace(year=datetime.datetime.now().year)
            tasks.append({"name":name, "deadline":date})
        return tasks
        
    def check_timeout(self) -> bool:
        self.driver.refresh()

    def close(self) -> None:
        self.driver.close()

if __name__ == '__main__':
    eapi = EmasAPI()
    if eapi.login(input("username: "), input("password: ")):
        tasks = eapi.get_timeline()
    for task in tasks:
        print(task['name'], task['deadline'])
    eapi.close()
