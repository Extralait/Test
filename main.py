from time import sleep

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

import os
import re

"""
Версия chromedriver 91
"""

# Введите свои логин и пароль
LOGIN = ""
PASSWORD = ""

BASE_URL = "https://esia.gosuslugi.ru"
TAXES_URL = "https://lk.gosuslugi.ru/profile/taxes"
NEW_DIR_PATH = 'Госуслуги'
DOWNLOADS_DIR_PATH = os.path.expanduser('~') + '/Downloads/'


def auth(driver):
    """
    Авторизация на портале
    :param driver: Экземпляр драйвера
    :return:
    """
    driver.find_element_by_id('login').send_keys(LOGIN)
    driver.find_element_by_id('password').send_keys(PASSWORD)
    driver.find_element_by_id('loginByPwdButton').click()


def url_wait(driver, xpath='', url='', redirect=False):
    """
    Ожидание прогрузки страници и/или элемента
    :param driver: Экземпляр драйвера
    :param xpath: Путь до элемента
    :param url: url ожидаемой страницы
    :param redirect: Будет ли переадресация
    :return:
    """
    if redirect:
        # Ожидание совпадения url
        WebDriverWait(driver, 5).until(lambda driver: driver.current_url != url)
    if xpath:
        # Ожидание загрузки элемента
        WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, xpath)))


def wright_privat_info(driver):
    """
    Запись личных данных в файл
    :param driver: Экземпляр драйвера
    :return:
    """
    # Получение разметки необходимого div
    select_element = driver.find_element_by_css_selector(".data-box")
    html = select_element.get_attribute("innerHTML")

    soup = BeautifulSoup(html, 'lxml')

    # Получение необходимых наименований и значений
    titles = soup.select("div.col.span_3.push_1.dt")
    values = soup.select("div.col.span_6.dd")

    # Проверка наличия директории в корне проекта и создание директории при ее отсутствии
    if not os.path.exists(NEW_DIR_PATH):
        os.mkdir(NEW_DIR_PATH)

    # Создание txt файла и запись данных
    with open('Госуслуги/wright_privat_info.txt', 'w', encoding='utf-8') as file:
        for title, value in zip(titles, values):
            title = title.get_text().strip()
            value = value.get_text().strip()
            file.write(f"{title}: {value}\n")


def download_taxes(driver):
    """
    Скачивание данных о доходах
    :param driver: Экземпляр драйвера
    :return:
    """
    if driver.get_window_size()['width'] >= 1040:
        # Для широких экранов
        xpath = "/html/body/lk-root/main/lk-profile/div/div/div[2]/lk-taxes/div[1]/div[2]/div[2]/lib-actions-menu/div[3]/a[1]"
        # Максимальное время ожидания появления кнопки скачивания 360с
        WebDriverWait(driver, 360).until(ec.presence_of_element_located((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).click()
    else:
        # Для узких экранов
        xpath = "/html/body/lk-root/main/lk-profile/div/div/div[2]/lk-taxes/div[1]/div[2]/div[2]/lib-actions-menu/div[1]"
        WebDriverWait(driver, 360).until(ec.presence_of_element_located((By.XPATH, xpath)))
        driver.find_element_by_xpath(xpath).click()
        driver.find_element_by_xpath(
            '/html/body/lk-root/main/lk-profile/div/div/div[2]/lk-taxes/div[1]/div[2]/div[2]/lib-actions-menu/div[2]/div[1]/a').click()


def refactor_taxes(downloaded_files_names):
    """
    Перемещение загруженного файла в папку проекта
    :param downloaded_files_names:
    :return:
    """
    new_downloaded_files_names = os.listdir(DOWNLOADS_DIR_PATH)
    for file in new_downloaded_files_names:
        # Поиск нового файла и проверка формата
        if not file in downloaded_files_names and re.match(r'.*.pdf$', file):
            # Переименование и перенос файла в папку проекта
            os.rename(DOWNLOADS_DIR_PATH + file, 'Госуслуги/last_taxes.pdf')
            return
    # Рекурсивный повтор, в случае, если файл не до конца скачался
    sleep(0.5)
    refactor_taxes(downloaded_files_names)


def main():
    # Инициализация драйвера
    driver = webdriver.Chrome("chromedriver.exe")
    # Переход на страницу авторизации
    driver.get(BASE_URL)
    # Ожидание загрузки страницы
    url_wait(driver, '//*[@id="password"]', BASE_URL, True)
    # Авторизация
    auth(driver)

    # Ожидание загрузки интересующего блока
    url_wait(driver,
             '/html/body/my-app/div/div[1]/my-person/div/div/div[2]/my-common-information/div/div/div[8]/div[2]')
    # Запись данных в файл
    wright_privat_info(driver)

    # Переход на страницу данных о доходах
    driver.get(TAXES_URL)

    # Проверка получены ли данные о налогах на данный момент
    xpath = '/html/body/lk-root/main/lk-profile/div/div/div[2]/lk-taxes/div/div/div[2]/lib-button/div/button'
    try:
        url_wait(driver, xpath, TAXES_URL, True)
    except TimeoutException:
        pass
    else:
        driver.find_element_by_xpath(xpath).click()

    # Список файлов в папке загрузок
    downloaded_files_names = os.listdir(DOWNLOADS_DIR_PATH)
    # Скачивание файла с данными о доходах
    download_taxes(driver)
    # Перенос файла в директорию проекта
    refactor_taxes(downloaded_files_names)
    # Окончание сессии
    driver.quit()


if __name__ == '__main__':
    main()
