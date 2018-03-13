from time import sleep
from django.template.loader import render_to_string
from django.conf import settings
import logging

from notifhain.event.models import DancefloorEvent

from pyvirtualdisplay import Display
from selenium import webdriver

logger = logging.getLogger('scrapy')


class PublishToRR():

    display = None
    driver = None

    # Open headless chromedriver
    def start_driver(self):
        # if not settings.DEBUG:
        self.display = Display(visible=0, size=(800, 600))
        print("starting display...")
        self.display.start()
        print("starting driver...")
        self.driver = webdriver.Chrome()

    # Close chromedriver
    def close_driver(self):
        print('closing driver...')
        if self.display:
            self.display.stop()
        self.driver.quit()
        print('closed!')

    # Tell the browser to get a page
    def get_page(self, url):
        print('getting page...')
        self.driver.get(url)

    def publish(self):
        logger.info("start-post-to-rr")
        klubnacht = DancefloorEvent.objects.get_next_klubnacht()
        if klubnacht and klubnacht.has_timetable and not klubnacht.is_posted_to_rr:
            print("post-to-rr")
            print("%s %s" % (klubnacht.pk, klubnacht.get_title()))
            self.start_driver()
            self.get_page('https://restrealitaet.de/r/login')
            username = self.driver.find_element_by_name('username')
            password = self.driver.find_element_by_name('password')
            username.send_keys(settings.RR_USERNAME)
            password.send_keys(settings.RR_PASSWORD)
            login = self.driver.find_element_by_css_selector(".loginform button")
            print("login...")
            login.click()
            sleep(1)
            bar = self.driver.find_element_by_css_selector('.other-buttons a[href="#forum/bar"]')
            self.driver.execute_script("arguments[0].click();", bar)
            new_message = self.driver.find_element_by_css_selector('button.new-btn')
            self.driver.execute_script("arguments[0].click();", new_message)
            print("click new message...")
            title_element = self.driver.find_element_by_name('title')
            text_element = self.driver.find_element_by_name('text')
            title_element.send_keys(klubnacht.get_title())
            print(title_element.get_attribute('value'))
            text = render_to_string('klubnacht-tt-rr.html', {'event': klubnacht})
            text_element.send_keys(text.strip())
            print(text_element.get_attribute('value'))
            sleep(3)
            send_btn = self.driver.find_element_by_css_selector('.thread-new button[data-call-method="newThread"]')
            print("click send button....")
            self.driver.execute_script("arguments[0].click();", send_btn)
            klubnacht.is_posted_to_rr = True
            klubnacht.save()
            self.close_driver()
        else:
            logger.info("No klubnacht event to publish")
