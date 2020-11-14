# -*- coding: utf-8 -*-

import sqlite3
from random import randint
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


class FaqEntity:
    def __init__(self, target: str, section: str, action: str, url: str):
        self.target: str = target
        self.section: str = section
        self.action: str = action
        self.url: str = url
        self.question: str = ""
        self.answer: str = ""

    def save(self):
        cursor.execute(
            "INSERT OR IGNORE INTO `faq` VALUES (?, ?, ?, ?, ?, ?)",
            [self.section, self.action, self.url, self.question, self.answer, self.target]
        )
        conn.commit()

    def parse_detail_page(self):
        try:
            cursor.execute("SELECT COUNT(url) cnt FROM `faq` WHERE url = ?", [self.url])
            if cursor.fetchone()[0] > 0:
                return

            print(self.url)
            driver.get(self.url)
            article = driver.find_element_by_tag_name('article')
            self.question = str(article.find_element_by_tag_name('h2').get_attribute('innerText')).strip()
            self.answer = article.find_element_by_class_name('rt-font-small-paragraph').get_attribute('innerHTML')
            self.save()
            sleep(randint(1, 3))
        finally:
            pass


def parse_support_faq():
    ignore_url = [
        'https://moscow.rt.ru/support/documents#internet',
        'https://moscow.rt.ru/support/documents#mobile',
        'https://moscow.rt.ru/support/documents#wink',
        'https://moscow.rt.ru/support/documents#phone',
        'https://moscow.rt.ru/support/documents#key',
        'https://moscow.rt.ru/mobile/mobile_tariff',
        'https://moscow.rt.ru/mobile/mobile_tariff#zone',
        'https://moscow.rt.ru/support/hometv/setting/digital-tv',
        'https://moscow.rt.ru/legal',
        'https://moscow.rt.ru/bonus',
        'https://moscow.rt.ru/support/phone/connect/connect-phone-to-house-apartment'
    ]

    driver.get('https://moscow.rt.ru/support')
    WebDriverWait(driver, 20).until(
        ec.presence_of_element_located((By.ID, 'block-rt-ru-super-wiki-page-menu'))
    )

    items = []
    try:
        for group in driver.find_elements_by_class_name('menu-wiki-intro__spoiler'):
            head = str(group.find_element_by_tag_name('h4').get_attribute('innerText')).strip()
            for half in group.find_elements_by_class_name('rt-md-space-top-half'):
                paragraph = str(
                    half.find_element_by_class_name('menu-wiki-intro__link').get_attribute('innerText')
                ).strip()
                for link in half.find_elements_by_tag_name('a'):
                    url = str(link.get_attribute('href')).strip()
                    if url not in ignore_url:
                        items.append(FaqEntity('support', head, paragraph, url))
    finally:
        for it in items:
            it.parse_detail_page()


def parse_info_faq():
    pages = {
        'https://moscow.rt.ru/homeinternet': ['info', 'Интернет', 'Подключение'],
        'https://moscow.rt.ru/hometv': ['info', 'Телевидение', 'Подключение'],
        'https://moscow.rt.ru/videocontrol': ['info', 'Видеонаблюдение', 'Подключение'],
        'https://moscow.rt.ru/smarthome': ['info', 'Умный дом', 'Подключение'],
    }
    for page_url, args in pages.items():
        driver_no_js.get(page_url)
        faq_list = driver_no_js.find_element_by_class_name('rtb-faq-unordered-list')
        i = 1
        for annotation in faq_list.find_elements_by_tag_name('rt-annotation'):
            fe = FaqEntity(args[0], args[1], args[2], page_url + '#%s' % i)
            fe.question = str(annotation.get_attribute('label')).strip()
            content = annotation.find_element_by_tag_name('rt-template')
            fe.answer = str(content.get_attribute('innerText')).strip()
            fe.save()
            i += 1


def up():
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS `faq`
          (
            `section` VARCHAR(255) NOT NULL,
            `action` VARCHAR(255) NOT NULL,
            `url` VARCHAR(255) NOT NULL,
            `question` TEXT,
            `answer` TEXT,
            `target` VARCHAR(255) NOT NULL
          )
        """
    )
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS url_unx ON faq(url)")
    conn.commit()


if __name__ == '__main__':
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    up()

    driver = webdriver.Chrome()
    no_js = webdriver.ChromeOptions()
    no_js.add_experimental_option('prefs', {'profile.managed_default_content_settings.javascript': 2})
    no_js.add_argument('"--disable-javascript"')
    driver_no_js = webdriver.Chrome(options=no_js)

    parse_support_faq()
    parse_info_faq()

    driver.quit()
    driver_no_js.quit()
