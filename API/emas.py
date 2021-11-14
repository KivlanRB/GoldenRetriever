from requests.api import get
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from getpass import getpass
import datetime

class EmasAPI():

    __login_site_link = "https://emas.ui.ac.id/login/index.php"
    __login_uname_css = "input#username"
    __login_pword_css = "input#password"
    __login_bttn_css  = "input#loginbtn"
    __login_error_css = "a#loginerrormessage"

    __timeline_site_link = "https://emas.ui.ac.id/my/?myoverviewtab=timeline"
    __timeline_task_name_css = "li > div.visible-desktop > div > div.event-name-container > a"
    __timeline_task_deadline_css = "li > div.visible-desktop > div > div.row-fluid > div.span5"
    __timeline_task_course_css = "li > div.visible-desktop > div > div.event-name-container > div > small"

    __aca_login_link = "https://academic.ui.ac.id/main/Authentication/"
    __aca_login_uname_css = "input#u"
    __aca_login_pword_css = "input[name=\"p\"]"
    __aca_login_btn_css = "p#submit > input"
    __aca_login_err_css = "p.error"
    __aca_login_info_css = "div.linfo[style*=\"left\"]"

    def __init__(self, debug=False) -> None:
        try:
            options = FirefoxOptions()
            options.set_capability("acceptSslCerts", True)
            if not debug:
                options.headless = True
            self.driver = webdriver.Firefox(options=options, executable_path=GeckoDriverManager().install())
        except (ValueError, WebDriverException):
            raise OSError("Error loading firefox driver!")
        self.driver.set_page_load_timeout(5)
        self.emas_login_status = False
        self.academy_login_status = False
    
    def __or_EC(self, check1:EC, check2:EC) -> bool:
        if check1 or check2:
            return True
        else:
            return False

    def login(self, un, pw):
        self.uname = un
        self.pword = pw
    
    def emas_login(self) -> int:
        """ 
        Logs in to the EMAS page. CSS selectors are initialized as
        the attributes of the class.

        Arguments - uname: Username of the account
                    pword: Password of the account

        Returns - Integer. 1 If all success, 0 if there is an expected error, -1 if there is an unexpected error.
        """
        if self.emas_login_status:
            return 1, None

        try:
            self.driver.get(self.__login_site_link)
            bttn_element:WebElement = self.driver.find_element(By.CSS_SELECTOR, self.__login_bttn_css)
        except TimeoutException:
            bttn_element:WebElement = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable(
                                        (By.CSS_SELECTOR, self.__login_bttn_css)))
            
        uname_element:WebElement = self.driver.find_element(By.CSS_SELECTOR, self.__login_uname_css)
        pword_element:WebElement = self.driver.find_element(By.CSS_SELECTOR, self.__login_pword_css)
        uname_element.send_keys(self.uname)
        pword_element.send_keys(self.pword)
        try:
            bttn_element.click()
            if self.driver.title == "Dashboard":
                self.emas_login_status = True
                return 1, None
            else:
                try:
                    login_err:WebElement = self.driver.find_element(By.CSS_SELECTOR, self.__login_error_css)
                    self.emas_login_status = False
                    return 0, login_err.get_property("text")
                except Exception as e:
                    self.emas_login_status = False
                    return -1, e
        except TimeoutException:
            try:
                WebDriverWait(self.driver, 10).until(EC.title_is("Dashboard"))
                self.emas_login_status = True
                return 1, None
            except TimeoutException:
                try:
                    login_err:WebElement = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, self.__login_error_css)))
                    self.emas_login_status = False
                    return 0, login_err.get_property("text")
                except Exception as e:
                    self.emas_login_status = False
                    return -1, e
            
    def get_timeline(self) -> list:
        """ 
        Goes to the timeline page in EMAS

        Returns - list of dicts containing all information of a deadline, or -1 if it recieves an unexpected error.
        """
        if not self.emas_login_status:
            raise AttributeError("API is not logged in! Try doing EmasAPI.emas_login() first!")

        try:
            self.driver.get(self.__timeline_site_link)
            task_names_element:list = WebDriverWait(self.driver, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, self.__timeline_task_name_css)))
            task_deadlines_element:list = self.driver.find_elements(By.CSS_SELECTOR, self.__timeline_task_deadline_css)
            task_course_element:list = self.driver.find_elements(By.CSS_SELECTOR, self.__timeline_task_course_css)
        except TimeoutException:
            try:
                task_names_element:list = WebDriverWait(self.driver, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, self.__timeline_task_name_css)))
                task_deadlines_element:list = self.driver.find_elements(By.CSS_SELECTOR, self.__timeline_task_deadline_css)
                task_course_element:list = self.driver.find_elements(By.CSS_SELECTOR, self.__timeline_task_course_css)
            except TimeoutException:
                print("Unexpected error!")  
                return -1

        tasks = list()
        for task_name, task_deadline, task_course in zip(task_names_element, task_deadlines_element, task_course_element):
            deadline:str = task_deadline.text
            name:str = task_name.text
            course:str = task_course.text
            date:datetime.datetime = datetime.datetime.strptime(deadline, "%d %b, %H:%M").replace(year=datetime.datetime.now().year)
            tasks.append({"name":name, "desc":course, "date":date})
        return tasks
        
    def check_timeout(self) -> bool:
        self.driver.refresh()

    def close(self) -> None:
        self.driver.close()

if __name__ == '__main__':
    eapi = EmasAPI(True)
    eapi.login(input("Username: "), getpass("Password: "))
    result, msg = eapi.emas_login()
    if result == 1:
        print(eapi.get_timeline())

    
