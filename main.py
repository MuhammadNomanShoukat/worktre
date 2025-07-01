from inactivity_manager import start_inactivity_timer, stop_inactivity_timer, reset_idle_timer
import webview
import sys
import os
import logging
import requests
import socket
import json
import ctypes
import time
import threading
import shutil
import xml.etree.ElementTree as ET
from cryptography.fernet import Fernet


STORAGE_PATH = 'remember_me.json'
KEY_PATH = 'remember_me.key'

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

current_window = None

# =============================

APPDATA = os.path.join(os.environ.get("APPDATA", "."), "WorkTree")
os.makedirs(APPDATA, exist_ok=True)

log_path = os.path.join(APPDATA, "log.txt")
logging.basicConfig(
    filename=log_path,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filemode="a"
)
logging.info("🚀 App started")

def cleanup_temp_dir():
    temp_path = os.path.join(os.getcwd(), 'webview_temp')
    try:
        shutil.rmtree(temp_path, ignore_errors=True)
    except Exception:
        pass

cleanup_temp_dir()



def get_dynamic_ip():
    try:
        # Connect to an external host to determine the IP address
        # This does not establish an actual connection
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # Google's public DNS server
            ip = s.getsockname()[0]
            print("IP--->", ip)
        return ip
    except Exception as e:
        print(f"Error getting IP address: {e}")
        return None


url = "https://worktre.com:443/webservices/worktre_soap_2.0/services.php"
# ---------------------- Your JS API ----------------------

def get_key_path():
    # Get a safe writable directory
    base_dir = os.path.expanduser("~\\AppData\\Roaming\\WorkTree")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "remember_me.key")

def load_key():
    try:
        key_path = get_key_path()  # ✅ This ensures we use AppData path

        if not os.path.exists(key_path):
            key = Fernet.generate_key()
            with open(key_path, 'wb') as f:
                f.write(key)
        else:
            with open(key_path, 'rb') as f:
                key = f.read()

        return Fernet(key)

    except Exception as e:
        print("[ERROR] Failed to load or create key:", e)
        return None

# Load it on start
fernet = load_key()

def save_remembered_user(email, password):
    if email and password:
        encrypted = fernet.encrypt(password.encode()).decode()
        with open(STORAGE_PATH, 'w') as f:
            json.dump({"email": email, "password": encrypted}, f)
    elif os.path.exists(STORAGE_PATH):
        os.remove(STORAGE_PATH)

def get_remembered_user():
    if os.path.exists(STORAGE_PATH):
        with open(STORAGE_PATH, 'r') as f:
            try:
                data = json.load(f)
                data['password'] = fernet.decrypt(data['password'].encode()).decode()
                print("Decrypted remembered data:", data)
                return data
            except Exception as e:
                print("Error reading remembered user:", e)
    return {}

def on_warning():
    # print("⚠️ Handle warning: maybe update UI or notify frontend")

    try:
        if webview.windows:
            webview.windows[0].evaluate_js("showInactivityWarningModal();")
    except Exception as e:
        with open("warn.log", "a", encoding="utf-8") as f:
            f.write(f"Error showing modal: {e}\n")



def on_exit():
    # print("⛔ Preparing to exit: save state or notify backend")
    if webview.windows:
        webview.windows[0].evaluate_js("window.inactivityTimeExceed()")

class API:
    def __init__(self):
        self._monitor_thread = None
        self._stop_monitor = threading.Event()
        self._user_logged_in = False

        self.user_info = None
        self.break_type = ""

        # Timeouts (in seconds)
        self._warn_after = None
        self._kick_after = None
        self._warned = False




    def get_remembered_user(self):
        return get_remembered_user()

    def save_remembered_user(self, email, password):
        save_remembered_user(email, password)

    def loginUser(self, data):
        email = data.get('email')
        password = data.get('password')
        remember = data.get('remember')
        print(f"Login Attempt - Email: {email}, Password: {password}, Remember: {remember}")
        return {"success": email == "admin@admin.com" and password == "admin123"}

    def login(self, username, password, max_retries=2, delay=2):
        logging.info("🔄 login")
        computer_name = socket.gethostname()
        ip = get_dynamic_ip()
        # Headers
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "https://worktre.com/webservices/worktre_soap_2.0/services.php/login",
        }

        # SOAP request payload
        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                          xmlns:web="https://worktre.com/">
           <soapenv:Header/>
           <soapenv:Body>
              <web:login>
                 <employeeaccount>{username}</employeeaccount>
                 <password>{password}</password>
                 <ComputerName>{computer_name}</ComputerName>
                 <wtversion>2.0</wtversion>
                 <ipaddress>{ip}</ipaddress>
              </web:login>
           </soapenv:Body>
        </soapenv:Envelope>
        """

        # Retry logic
        for attempt in range(max_retries):
            try:
                # Send the POST request
                response = requests.post(url, data=payload, headers=headers, timeout=10)  # Timeout set to 10 seconds

                # Check if the response is successful (status code 200)
                if response.status_code == 200:
                    soap_response = response.text
                    user_info = self.process_soap_response(soap_response)
                    parsed = json.loads(user_info)
                    self.user_info = parsed["data"]

                    data = parsed["data"]



                    # ✅ Convert minutes → seconds
                    # warn_after = int(data.get("InactivityBreakTime", 15)) * 60
                    # warn_after = 1 * 60
                    #
                    # kick_after = 2 * 60
                    #
                    # print(f"[INFO] Warn after {warn_after}s, Kick after {kick_after}s")
                    #
                    # self._user_logged_in = True
                    # self._stop_monitor.clear()
                    #
                    # self.start_inactivity_monitor(
                    #     warn_after=warn_after,
                    #     kick_after=kick_after,
                    #     user_info=data,
                    #     break_type="Short Break"
                    # )
                    threading.Thread(
                        target=start_inactivity_timer,
                        args=(0.5, 1),
                        kwargs={"on_warn": on_warning, "on_exit": on_exit},
                        daemon=True
                    ).start()
                    # print("88888888:", json.loads(user_info)["data"]['InactivityBreakTime'])





                    return user_info
                else:
                    raise requests.exceptions.RequestException(f"Unexpected status code: {response.status_code}")

            except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                # Print the error and wait before retrying
                print(f"Error during request: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff (increase the delay after each attempt)

        # If we reach here, all retry attempts failed
        return json.dumps(
            {"status": False, "msg": "Unable to connect to the server. Network Error.", "data": {}})


    def process_soap_response(self, soap_response):
        # Parse the SOAP response
        root = ET.fromstring(soap_response)

        # Find the 'return' element
        namespaces = {
            'SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns1': 'https://worktre.com/',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'SOAP-ENC': 'http://schemas.xmlsoap.org/soap/encoding/'
        }

        return_element = root.find('.//ns1:loginResponse/return', namespaces)
        print("-----RETURN ELEMENT --------",return_element)
        if return_element is not None:

            items = return_element.findall('item', namespaces)

            # Get the keys (first element)
            keys = items[0].text.split(",") if items[0].text else []

            # Strip extra spaces in keys
            keys = [key.strip() for key in keys]
            print("KEYS : ", keys)
            # Get the values (remaining elements)
            values = [item.text or "" for item in items[1:]]
            print("Values : ", values)
            result = {}
            for i in range(len(keys)):
                key = keys[i]
                value = values[i]
                result[key] = value

            try:
                if result["invalidCredentials"] == "0":
                    resp = {"status": False, "msg": "Invalid Credentials", "data": {}}
            except:
                resp = {"status": True, "data": result}

            try:
                if result["IPAddresNotFound"] == "Invalid IP Address":
                    resp = {"status": False, "error": "ip", "msg": "[color=#0000FF][u]Click here[/u][/color]", "data": result}
            except:
                resp = resp

            json_response = json.dumps(resp)
            print("Login API Resp:", json_response)
            return json_response
        else:
            resp = {"status": False, "data": {}}
            json_response = json.dumps(resp)
            return json_response

    def inactivity(self, userid, breaktype="inactivity"):
        computer_name = socket.gethostname()

        # Headers for the SOAP request
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "https://worktre.com/webservices/worktre_soap_2.0/services.php/breakout/inactivity",
        }

        # SOAP request payload
        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                          xmlns:web="https://worktre.com/">
           <soapenv:Header/>
           <soapenv:Body>
              <web:inactivity>
                 <userid>{userid}</userid>
                 <breaktype>{breaktype}</breaktype>
                 <system_name>{computer_name}</system_name>
              </web:inactivity>
           </soapenv:Body>
        </soapenv:Envelope>
        """

        # Endpoint URL
        url = "https://worktre.com:443/webservices/worktre_soap_2.0/services.php/breakout"

        print("============")
        print(headers)
        # print(headers)
        # print(payload)


        # Send the POST request
        try:
            response = requests.post(url, data=payload, headers=headers, timeout=10)

            soap_response = response.text
            # print("SOAP Response:", soap_response)
        except requests.exceptions.RequestException as e:
            return json.dumps({"status": False, "msg": "Request failed", "data": {"error": str(e)}})



        try:
            # Parse the SOAP response
            root = ET.fromstring(soap_response)
        except ET.ParseError:
            return json.dumps({"status": False, "msg": "Error parsing XML response", "data": {}})

        # Define namespaces
        namespaces = {
            'SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns1': 'https://worktre.com/',
        }

        # Find the response element
        return_element = root.find('.//ns1:inactivityResponse/return', namespaces)

        # print(response)
        # print(return_element)
        print("====================")

        if return_element is not None:
            result = {
                "message": return_element.text or "Success"
            }
            return json.dumps({"status": True, "data": result})
        else:
            return json.dumps({"status": False, "msg": "No response data", "data": {}})


    def logoutinactivity(self, userid, breaktype="inactivity"):
        # Endpoint URL
        url = "https://worktre.com:443/webservices/worktre_soap_2.0/services.php"

        # Headers
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "https://worktre.com/webservices/worktre_soap_2.0/services.php/logoutinactivity",
        }

        # SOAP request payload
        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                          xmlns:web="https://worktre.com/">
           <soapenv:Header/>
           <soapenv:Body>
              <web:logoutinactivity>
                 <userid>{userid}</userid>
                 <breaktype>{breaktype}</breaktype>
              </web:logoutinactivity>
           </soapenv:Body>
        </soapenv:Envelope>
        """

        # Send the POST request
        response = requests.post(url, data=payload, headers=headers, timeout=10)

        soap_response = response.text

        # Parse the SOAP response
        root = ET.fromstring(soap_response)

        # Define namespaces
        namespaces = {
            'SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns1': 'https://worktre.com/',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'SOAP-ENC': 'http://schemas.xmlsoap.org/soap/encoding/'
        }

        # Find the 'return' element
        return_element = root.find('.//ns1:logoutinactivityResponse/return', namespaces)

        print("==========")
        print(headers)
        # print(payload)
        # print(response)
        # print(soap_response)
        # print(return_element)
        print("==========")

        if return_element is not None:
            items = return_element.findall('item', namespaces)

            # Get the keys (first element)
            keys = items[0].text.split(",") if items[0].text else []

            # Strip extra spaces in keys
            keys = [key.strip() for key in keys]

            # Get the values (remaining elements)
            values = [item.text or "" for item in items[1:]]

            result = {}
            for i in range(len(keys)):
                key = keys[i]
                value = values[i]
                result[key] = value

            resp = {"status": True, "data": result}
            json_response = json.dumps(resp)
            return json_response
        else:
            resp = {"status": True, "data": {}}
            json_response = json.dumps(resp)
            return json_response

    def crashlogin(self, userid, breaktype, onbreak):
        computer_name = socket.gethostname()
        ip = get_dynamic_ip()
        # Headers
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "https://worktre.com/webservices/worktre_soap_2.0/services.php/crashlogin",
        }

        # SOAP request payload
        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                          xmlns:web="https://worktre.com/">
           <soapenv:Header/>
           <soapenv:Body>
              <web:crashlogin>
                 <userid>{userid}</userid>
                 <breaktype>{breaktype}</breaktype>
                 <onbreak>{onbreak}</onbreak>
                 <ComputerName>{computer_name}</ComputerName>
                 <wtversion>2.0</wtversion>
                 <ipaddress>{ip}</ipaddress>
              </web:crashlogin>
           </soapenv:Body>
        </soapenv:Envelope>
        """

        # Send the POST request
        response = requests.post(url, data=payload, headers=headers, timeout=10)

        soap_response = response.text
        print("CrashLogin API Resp:",soap_response)

        # Parse the SOAP response
        root = ET.fromstring(soap_response)

        # Find the 'return' element
        namespaces = {
            'SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns1': 'https://worktre.com/',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'SOAP-ENC': 'http://schemas.xmlsoap.org/soap/encoding/'
        }

        return_element = root.find('.//ns1:crashloginResponse/return', namespaces)

        if return_element is not None:
            items = return_element.findall('item', namespaces)

            # Get the keys (first element)
            keys = items[0].text.split(",") if items[0].text else []

            # Strip extra spaces in keys
            keys = [key.strip() for key in keys]
            print("KEYS : ", keys)
            # Get the values (remaining elements)
            values = [item.text or "" for item in items[1:]]
            print("Values : ", values)
            result = {}
            for i in range(len(keys)):
                try:
                    key = keys[i]
                    value = values[i]
                    result[key] = value
                except:
                    pass

            resp = {"status": True, "data": result}
            json_response = json.dumps(resp)
            return json_response
        else:
            resp = {"status": True, "data": {}}
            json_response = json.dumps(resp)
            return json_response

    def logout(self, userid, eod, total_chats, total_billable_chats):

        print("===================")
        print(self.user_info)
        print("===================")
        self._user_logged_in = False

        # Headers
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "https://worktre.com/webservices/worktre_soap_2.0/services.php/logout",
        }

        # SOAP request payload
        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                          xmlns:web="https://worktre.com/">
           <soapenv:Header/>
           <soapenv:Body>
              <web:logout>
                 <userid>{userid}</userid>
                 <eod>{eod}</eod>
                 <totalchats>{total_chats}</totalchats>
                 <totalbillablechats>{total_billable_chats}</totalbillablechats>
              </web:logout>
           </soapenv:Body>
        </soapenv:Envelope>
        """

        # Send the POST request
        response = requests.post(url, data=payload, headers=headers, timeout=10)

        soap_response = response.text
        # Parse the SOAP response
        root = ET.fromstring(soap_response)

        # Find the 'return' element
        namespaces = {
            'SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns1': 'https://worktre.com/',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'SOAP-ENC': 'http://schemas.xmlsoap.org/soap/encoding/'
        }

        return_element = root.find('.//ns1:logoutResponse/return', namespaces)
        print("Logout API Resp:",return_element)
        if return_element is not None:
            items = return_element.findall('item', namespaces)

            # Get the keys (first element)
            keys = items[0].text.split(",") if items[0].text else []

            # Strip extra spaces in keys
            keys = [key.strip() for key in keys]

            # Get the values (remaining elements)
            values = [item.text or "" for item in items[1:]]

            result = {}
            for i in range(len(keys)):
                key = keys[i]
                value = values[i]
                result[key] = value

            resp = {"status": True, "data": result}
            json_response = json.dumps(resp)
            return json_response
        else:
            resp = {"status": True, "data": {}}
            json_response = json.dumps(resp)
            return json_response

    def breakin(self, userid, breaktype, comments, training_type_id="", trainer_id="", website="", ticket_no="", expected_duration=""):
        computer_name = socket.gethostname()
        self.break_type = breaktype

        # Headers for the SOAP request
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "https://worktre.com/webservices/worktre_soap_2.0/services.php/breakin",
        }

        # SOAP request payload
        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                          xmlns:web="https://worktre.com/">
           <soapenv:Header/>
           <soapenv:Body>
              <web:breakin>
                 <userid>{userid}</userid>
                 <breaktype>{breaktype}</breaktype>
                 <comments>{comments}</comments>
                 <system_name>{computer_name}</system_name>
                 <training_type_id>{training_type_id}</training_type_id>
                 <trainer_id>{trainer_id}</trainer_id>
                 <website>{website}</website>
                 <ticket_no>{ticket_no}</ticket_no>
                 <expected_duration>{expected_duration}</expected_duration>
              </web:breakin>
           </soapenv:Body>
        </soapenv:Envelope>
        """

        # Endpoint URL
        url = "https://worktre.com:443/webservices/worktre_soap_2.0/services.php"

        # Send the POST request
        response = requests.post(url, data=payload, headers=headers, timeout=10)

        soap_response = response.text
        print("_+_+_+_+-----",soap_response)
        try:
            # Parse the SOAP response
            root = ET.fromstring(soap_response)
        except:
            root = None

        # Define namespaces
        namespaces = {
            'SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns1': 'https://worktre.com/',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'SOAP-ENC': 'http://schemas.xmlsoap.org/soap/encoding/'
        }
        if root is not None:
            # Find the response element
            return_element = root.find('.//ns1:breakinResponse/return', namespaces)
        else:
            return_element = None

        if return_element is not None:
            result = {
                "message": return_element.text or "Success"
            }

            try:
                print(result)
                resp = {"status": True, "data": result}
            except Exception as e:
                resp = {"status": False, "msg": "Error parsing response", "data": {"error": str(e)}}
        else:
            resp = {"status": False, "msg": "No response data", "data": {}}

        json_response = json.dumps(resp)
        return json_response

    def breakout(self, userid, breaktype, comments=""):

        # Headers for the SOAP request
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "https://worktre.com/webservices/worktre_soap_2.0/services.php/breakout",
        }

        # SOAP request payload
        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                          xmlns:web="https://worktre.com/">
           <soapenv:Header/>
           <soapenv:Body>
              <web:breakout>
                 <userid>{userid}</userid>
                 <breaktype>{breaktype}</breaktype>
                 <comments>{comments}</comments>
              </web:breakout>
           </soapenv:Body>
        </soapenv:Envelope>
        """

        # Endpoint URL
        url = "https://worktre.com:443/webservices/worktre_soap_2.0/services.php"

        # Send the POST request
        response = requests.post(url, data=payload, headers=headers, timeout=10)



        soap_response = response.text


        # Parse the SOAP response
        root = ET.fromstring(soap_response)

        # Define namespaces
        namespaces = {
            'SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns1': 'https://worktre.com/',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'SOAP-ENC': 'http://schemas.xmlsoap.org/soap/encoding/'
        }

        # Check for breakoutResponse
        return_element = root.find('.//ns1:breakoutResponse', namespaces)

        print("==========")
        print(headers)
        # print(payload)
        # print(response)
        # print(soap_response)
        # print(return_element)
        print("==========")
        # return

        if return_element is not None:
            result = {
                "message": "Breakout successfully processed"
            }

            try:
                print(result)
                resp = {"status": True, "data": result}
            except Exception as e:
                resp = {"status": False, "msg": "Error parsing response", "data": {"error": str(e)}}
        else:
            resp = {"status": False, "msg": "No response data", "data": {}}

        json_response = json.dumps(resp)
        return json_response



    def version_check(self):
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "https://worktre.com/webservices/worktre_soap_2.0/services.php/versioncheck",
        }

        payload = """<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                          xmlns:xsd="http://www.w3.org/2001/XMLSchema">
           <soapenv:Body>
              <ns1:versioncheck soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
                                xmlns:ns1="https://worktre.com/"/>
           </soapenv:Body>
        </soapenv:Envelope>
        """

        url = "https://worktre.com:443/webservices/worktre_soap_2.0/services.php/versioncheck"

        try:
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            soap_response = response.text
            print("SOAP Response:", soap_response)
        except requests.exceptions.RequestException as e:
            return {
                "status": False,
                "msg": "Request failed",
                "data": {"error": str(e)}
            }

        try:
            root = ET.fromstring(soap_response)
        except ET.ParseError:
            return {
                "status": False,
                "msg": "Error parsing XML response",
                "data": {}
            }

        # Extract <item> values (no namespace)
        items = root.findall(".//{https://worktre.com/}versioncheckResponse/return/item")
        if not items:
            items = root.findall(".//return/item")

        values = [item.text for item in items]

        if len(values) >= 7:
            version_info = {
                "id": values[0],
                "version": values[1],
                "platform": values[2],
                "download_url": values[3],
                "active": values[4],
                "description": values[5],
                "release_date": values[6],
            }
            return {
                "status": True,
                "data": version_info
            }
        else:
            return {
                "status": False,
                "msg": "Incomplete version data",
                "data": {"raw_items": values}
            }


    def handleForgetPassword(self, email):
        print(f"Forgot Password requested for: {email}")

    def resetInactivityTimer(self):
        reset_idle_timer()

# ---------------------- Path Helper ----------------------


def resource_path(relative_path):
    try:
        # For PyInstaller
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# ---------------------- Set App Window Icon ----------------------
def set_window_icon():
    try:
        window = webview.windows[0]

        # Only works for tkinter GUI
        if window.gui == 'tkinter':
            tk_window = window.gui.window
            icon_path = resource_path('desktop.ico')

            if os.path.exists(icon_path):
                tk_window.iconbitmap(icon_path)

            # Set fixed window size
            tk_window.resizable(False, False)
            tk_window.maxsize(1092, 700)
            tk_window.minsize(1092, 700)

        else:
            logger.info(f"Skipping icon/resizing: GUI backend '{window.gui}' doesn't support it.")

    except Exception as e:
        logger.warning(f"Unable to set icon or disable maximize: {e}")



# ---------------------- Webview Loader ----------------------
def start_app(api, html_file):
    global current_window



    html_path = resource_path(html_file)
    if not os.path.exists(html_path):
        logger.error(f"{html_file} not found!")
        sys.exit(1)

    current_window = webview.create_window(
        title='WorkTre',
        url=f'file://{html_path}',
        width=1092,
        height=700,
        js_api=api,
        minimized=False
    )

    logging.info("🔄 started")

    # You can change 'edgechromium' to 'tkinter' here if needed
    webview.start(debug=True, gui='edgechromium', func=set_window_icon)

def inactivity_window(api, html_file):
    global current_window

    html_path = resource_path(html_file)



    if not os.path.exists(html_path):
        logger.error(f"{html_file} not found!")
        sys.exit(1)

    current_window = webview.create_window(
        title='WorkTre',
        url=f'file://{html_path}',
        width=600,
        height=500,
        js_api=api,
        minimized=False
    )

    # You can change 'edgechromium' to 'tkinter' here if needed
    webview.start(debug=False, gui='edgechromium', func=set_window_icon)




# ---------------------- Entry Point ----------------------
if __name__ == '__main__':
    # from api import API  # Assuming API is defined in api.py or above
    start_app(API(), 'index.html')
