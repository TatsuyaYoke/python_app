import os
import sys
from os.path import join, dirname
import signal
import requests
import random
from bs4 import BeautifulSoup
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    WebDriverException,
    InvalidArgumentException,
    NoSuchElementException,
    TimeoutException
)

# Original import
from my_package.logger import logger


# Seleniumドライバ設定
def set_driver(isHeadless=False, isManager=False, isSecret=False, isExtension=False, extension_path='', profile_path=''):

    options = ChromeOptions()

    user_agent = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    ]

    if os.name == 'nt':  # Windows
        driver_path = 'chromedriver.exe'
    elif os.name == 'posix':  # Mac
        driver_path = 'chromedriver'

    if isHeadless:
        options.add_argument('--headless')
        options.add_argument('--single-process')

    if isExtension:
        if extension_path:
            options.add_extension(extension_path)
    else:
        options.add_argument('--disable-extensions')

    if isSecret:
        options.add_argument('--incognito')  # シークレットモードの設定を付与
    else:
        # プロファイル設定することで、初回手動でログインや拡張機能追加したものを2回目以降使用可能
        # シークレットモードではプロファイル設定を使用できない
        # ヘッドレスモードではプロファイル設定、Chrome拡張機能を使用できない
        # 拡張機能を有効にして、以下のエラーが出た場合、その拡張機能は使用できない
        # failed to wait for extension background page to load
        # その場合は、プロファイル設定にて手動で機能を追加して、ヘッドレスモードかつ拡張機能Enableで使用する
        if (not isHeadless) or (not isExtension):
            # options.add_argument('--user-data-dir=' + profile_path)
            # options.add_argument('--profile-directory=Profile 1')
            if getattr(sys, 'frozen', False):
                directory_path = os.path.dirname(sys.executable)
                if '.app' in directory_path:
                    idx = directory_path.find('.app')
                    directory_path = directory_path[:idx]
                    idx = directory_path.rfind('/')
                    directory_path = directory_path[:idx]
            else:
                directory_path = os.getcwd()
            options.add_argument('--user-data-dir=' + os.path.join(directory_path,"profile"))

    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('log-level=3')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument(f'--user-agent={user_agent[random.randrange(0, len(user_agent), 1)]}')
    options.add_argument('--start-maximized')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-desktop-notifications')
    options.add_argument('--disable-application-cache')
    options.add_argument('--lang=ja')


    if isManager:  # 自動取得
        try:
            driver = Chrome(ChromeDriverManager().install(), options=options)
        except InvalidArgumentException as err:
            logger.error(err)
            logger.error('既存のブラウザを閉じで実行してください。')
            return None
        except Exception as err:
            logger.error(err)

    else:  # 手動取得

        try:
            if getattr(sys, 'frozen', False):
                directory_path = os.path.dirname(sys.executable)
                if '.app' in directory_path:
                    idx = directory_path.find('.app') 
                    directory_path = directory_path[:idx]
                    idx = directory_path.rfind('/')
                    directory_path = directory_path[:idx]
            else:
                directory_path = os.getcwd()
            path = join(directory_path, driver_path)
            driver = Chrome(executable_path=path, options=options)
        except InvalidArgumentException as err:
            logger.error(err)
            logger.error('既存のブラウザを閉じで実行してください。')
            return None
        except WebDriverException as err:
            logger.error(err)
            logger.error('Chromeと同じバージョンのChrome Driverをダウンロードしてください。')
            return None

    return driver


# ドライバによるページ移動＋ページの全要素がDOM上に現れ, かつheight・widthが0以上になるまで待機
def get_with_wait(driver, url, isWait=False, timeout=30):

    driver.get(url)

    if isWait:
        wait = WebDriverWait(driver, timeout)
        wait.until(EC.presence_of_all_elements_located)


# ドライバを開いたままにする設定
def keep_open_driver(driver):

    os.kill(driver.service.process.pid, signal.SIGTERM)


# サイトがJavaScriptによる表示をしており、画面表示していなければ、要素を取得できない場合、最下部までスクロール
def scroll_bottom(driver, step):

    height = driver.execute_script('return document.body.scrollHeight')
    for x in range(1, height, step):
        driver.execute_script(f'window.scrollTo(0, {str(x)});')


# requestsによるhtmlのparse(ロボット判定されやすいので要注意)
def parse_html(url):

    html = requests.get(url)
    soup = BeautifulSoup(html.content, 'lxml')

    return soup


# Seleniumによるhtmlのparse
def parse_html_selenium(driver):

    html_text = driver.page_source
    soup = BeautifulSoup(html_text, 'lxml')

    return soup
