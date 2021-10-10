import time
import logging
import pyotp

from kiteconnect import KiteConnect
from selenium import webdriver

from trading.constants import EXCHANGE
from trading.zerodha.kite.Retry import retry


class Authorizer:
    """
    Class to programmatically login to kite platform.

    The access token is valid for one day and flushed in the morning around 7am
    Hence, to reduce latency, we cache the access token once obtained and reuse the same
    If we get access denied error, it could mean that the access token has gone stale and we retry to get a new
    access token. If that attempt fails too, then it could indicate an issue and we will throw
    """
    def __init__(self, token_db):
        logging.basicConfig(format='%(asctime)s :: %(levelname)s :: %(message)s', level=logging.INFO)
        self.api_secret = "***"
        self.api_key = "***"
        self.kite_login_id = "***"
        self.kite_login_password = "***"

        self.token_db = token_db

        # Create a kite object
        self.kite = KiteConnect(api_key=self.api_key)

    def start_chrome(self):
        """
        Start selenium web driver for google chrome
        """
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--window-size=1420,1080')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')

        driver_path = "/usr/local/bin/chromedriver"

        # service_args = ['--verbose']
        # outputdir = os.path.dirname(os.path.realpath(__file__)) + '/logs'
        # service_log_path = "{}/chromedriver.log".format(outputdir)

        # display = Display(visible=0, size=(800, 800))
        # display.start()

        driver = webdriver.Chrome(driver_path, chrome_options=chrome_options)
        return driver

    @retry(tries=5, delay=2, backoff=2)
    def get_request_token(self):
        driver = self.start_chrome()
        driver.get(self.kite.login_url())
        driver.implicitly_wait(10)

        try:
            userid = driver.find_element_by_id("userid")
            userid.send_keys(self.kite_login_id)
            password = driver.find_element_by_id("password")
            password.send_keys(self.kite_login_password)
            driver.find_element_by_class_name("button-orange").click()
            pin = driver.find_element_by_id("totp")
            code = pyotp.TOTP("***")
            pin.send_keys(code.now())
            driver.find_element_by_class_name("button-orange").click()
            time.sleep(5)
            tokens = driver.current_url.split('&')
            for token in tokens:
                if "request_token" in token:
                    r = token.split('=')
                    logging.info("Got request token {}".format(r))
                    # print(r[1])
                    return r[1]
        finally:
            driver.quit()

    def authorize_and_get_access_token(self):
        request_token = self.get_request_token()
        data = self.generate_session(request_token)
        logging.info("Access token obtained from zerodha")

        return data["access_token"]

    def get_authorized_kite_object(self):
        at = self.token_db.get_access_token()

        if at.empty:
            logging.info("Access token not present in db. Re-authenticating with zerodha")
            access_token = self.authorize_and_get_access_token()
            self.kite.set_access_token(access_token)
            self.token_db.put_access_token(access_token)
        else:
            logging.info("Access token obtained from database")
            token = at['token'][0]
            # Now check if the token is valid
            try:
                logging.info("Validating access token obtained from database")
                self.get_instruments()
                self.kite.set_access_token(token)
            except:
                logging.info('Access token obtained from database has gone stale. Re-authenticating')
                # If the token is invalid, then authorize again
                access_token = self.authorize_and_get_access_token()
                self.kite.set_access_token(access_token)
                self.token_db.put_access_token(access_token)

        return self.kite

    def get_api_key(self):
        return self.api_key

    @retry(tries=5, delay=2, backoff=2)
    def get_instruments(self):
        self.kite.instruments(EXCHANGE)

    @retry(tries=5, delay=2, backoff=2)
    def generate_session(self, request_token):
        return self.kite.generate_session(request_token, api_secret=self.api_secret)