# Connector.py

# Importing libraries
import os
import json
import logging
import requests
from .ConnectorException import ConnectorException
from urllib.parse import quote
from dotenv import load_dotenv
from os.path import dirname, abspath


class Connector:

    # Object constructor. Reads the configuration from .env file and checks for errors
    def __init__(self):

        # Try to load .env file and save configuration into object properties
        try:
            env = dirname(dirname(abspath(__file__))) + "/.env"
            load_dotenv(dotenv_path=env)
            self.token = os.getenv('ACCESSTOKEN', "")
            self.refreshToken = os.getenv('REFRESHTOKEN', "")
            self.clientId = os.getenv('CLIENTID', "")
            self.clientSecret = os.getenv('CLIENTSECRET', "")
            self.fileName = os.getenv('FILENAME', "")
            self.chunkSize = os.getenv('BLOCKSIZE', "")
            self.logLevel = os.getenv('LOGLEVEL', "INFO")
        except Exception:
            raise ConnectorException("Cannot read from .env file.")

        # Try to access log file or throw an exception
        logfile = dirname(dirname(abspath(__file__))) + "/connector.log"
        try:
            if os.path.isfile(logfile):
                fp = open(logfile, "a")
            else:
                fp = open(logfile, "w")
        except Exception:
            raise ConnectorException("Cannot write to log file")
        fp.close()
        logLevel = logging.getLevelName(self.logLevel)
        logging.basicConfig(filename=logfile, filemode='a',
                            format='[%(asctime)-15s] %(levelname)s: %(message)s',
                            level=logLevel, datefmt='%Y-%m-%d %H:%M:%S')

        # If (part of) configuration is missing, throw an exception
        if (self.clientId == "" or self.clientSecret == "" or self.fileName == "" or self.chunkSize == ""):
            raise ConnectorException(
                "System has not been configured yet. Please update the .env file and restart the script.")

    # Login method. Prompts the user for the code, exchanges it for an authentication token and saves it into object properties

    def login(self):

        # Run only if token property is empty
        if (self.token == ""):
            try:

                # Generate the url to visit and show it to the user
                url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize" + \
                    "?client_id=" + self.clientId + \
                    "&response_type=code" + \
                    "&redirect_uri=" + quote("https://apps.francescorega.eu/1DToken") + \
                    "&scope=Files.ReadWrite+offline_access"
                print("The authentication token has not yet been set.")
                print("Please visit this address to authorize the app to access your account " +
                      "and paste below the token that will be returned to you:")
                print(url)
                inputCode = input("Paste token here: ")

                # Exchange temporary code with real authentication token
                self.__exchangeToken(inputCode)
            except Exception as e:
                raise ConnectorException(
                    "Error while creating authentication code: " + str(e))

    # Upload method

    def upload(self, requiredPath=""):

        # If filename path is relative add "files" folder, then normalize
        path = requiredPath if requiredPath != "" else self.fileName
        if not os.path.isabs(path):
            path = "files/" + path
        path = os.path.normpath(path)

        # If configured path is a directory
        if os.path.isdir(path):

            try:

                # Create a remote folder with the same name
                self.__createFolder(os.path.basename(path))

                # Read all files inside it
                filesCount = 0
                for root, dirs, files in os.walk(path):

                    # For each file get an upload url and upload it
                    for name in files:
                        self.__getUploadUrl(name, os.path.basename(path) + "/")
                        self.__uploadBytes(os.path.join(root, name))
                        filesCount += 1

                # Return a confirmation message
                return "Upload completed. " + str(filesCount) + " file(s) uploaded"
            except Exception as e:
                raise ConnectorException(
                    "Error while uploading directory files: " + str(e))

        # If configured path is a file, upload it directly
        elif os.path.isfile(path):
            try:
                self.__getUploadUrl(os.path.basename(path))
                chunks = self.__uploadBytes(path)
                return "Upload completed with " + str(chunks) + " chunk(s)"
            except Exception as e:
                raise ConnectorException(
                    "Error while uploading single file: " + str(e))

        # If configured filename is a special file, exit with a warning
        else:
            raise ConnectorException("Configured FILENAME is invalid")

    # Authentication method. Exchanges an authentication code or a refresh token with a new one and updates config

    def __exchangeToken(self, code, isRefresh=False):
        try:

            # Call endpoint
            url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
            data = {
                'client_id': self.clientId,
                'redirect_uri': 'https://apps.francescorega.eu/1DToken',
                'client_secret': self.clientSecret,
            }
            if isRefresh:
                data["refresh_token"] = code
                data["grant_type"] = 'refresh_token'
            else:
                data["code"] = code
                data["grant_type"] = 'authorization_code'
            response = requests.post(url, data)

            # Extract values from response
            body = response.text
            body = json.loads(body)

            # Update .env file with new values
            env = dirname(dirname(abspath(__file__))) + "/.env"
            with open(env, "w") as f:
                f.write("FILENAME=" + self.fileName + "\n")
                f.write("BLOCKSIZE=" + self.chunkSize + "\n")
                f.write("CLIENTID=" + self.clientId + "\n")
                f.write("CLIENTSECRET=" + self.clientSecret + "\n")
                f.write("LOGLEVEL=" + self.logLevel + "\n")
                f.write("ACCESSTOKEN=" + body["access_token"] + "\n")
                f.write("REFRESHTOKEN=" + body["refresh_token"])

            # Update object property
            self.token = body["access_token"]
            return body["access_token"]
        except Exception as e:
            raise ConnectorException(
                "Error while exchanging tokens: " + str(e))

    # Folder creation method. Create a new remote folder with the given name as the root subfolder

    def __createFolder(self, name):
        try:

            # Prepare  data for the call
            url = "https://graph.microsoft.com/v1.0/drive/root/children"
            data = {
                'name': name,
                'folder': {}
            }
            headers = {
                "Authorization": "Bearer " + self.token,
                "Content-Type": "application/json"
            }
            response = self.__callAPI(url, json.dumps(data), headers)

            # Return generated folder name for confirmation
            body = response.text
            body = json.loads(body)
            return body["name"]
        except Exception as e:
            raise ConnectorException(
                "Error while creating folder " + name + ": " + str(e))

    # Upload session creation method. Refreshes the token, if needed, and request, a new url for a large file upload

    def __getUploadUrl(self, fileName, folder=""):
        try:

            # Prepare  data for the call
            url = "https://graph.microsoft.com/v1.0/drive/root:/" + \
                folder + fileName + ":/createUploadSession"
            data = {}
            headers = {
                "Authorization": "Bearer " + self.token
            }
            response = self.__callAPI(url, data, headers)

            # Extract uploadUrl value from body, update object property and return it for confirmation
            body = response.text
            body = json.loads(body)
            self.uploadUrl = body["uploadUrl"]
            return body["uploadUrl"]
        except Exception as e:
            raise ConnectorException(
                "Error while requesting an upload url: " + str(e))

    # Bytes transfer method. Uploads a given file in chunks of bytes to the configured upload url

    def __uploadBytes(self, filePath):
        try:

            # If configured chunk size is larger than the maximum chunk size allowed by OneDrive correct it, but show a warning
            if int(self.chunkSize) > 60:
                self.chunkSize = 60
                print(
                    "Configured chunk size is larger than allowed: proceeding using 60MB chunks.")

            # Open local file and calculate size
            with open(filePath, "rb") as f:
                fileSize = os.path.getsize(f.name)
                chunkSizeBytes = int(self.chunkSize) * 1024 * 1024
                i = 0

                # Split it in chunks
                while (byte := f.read(chunkSizeBytes)):
                    rangeMin = chunkSizeBytes * i
                    rangeMax = chunkSizeBytes * i + chunkSizeBytes - 1

                    # Prevent the calculated rangeMax from being larger than the file size
                    if rangeMax > fileSize:
                        rangeMax = fileSize - 1

                    # Send upload request
                    url = self.uploadUrl
                    data = byte
                    headers = {
                        "Authorization": "Bearer " + self.token,
                        "Content-Length": str(rangeMax - rangeMin),
                        "Content-Range": "bytes " + str(rangeMin) + "-" + str(rangeMax) + "/" + str(fileSize)
                    }
                    self.__callAPI(url, data, headers, "put")

                    # Increase counter for next chunk
                    i += 1

                # Return chunks count for confirmation
                return i
        except Exception as e:
            raise ConnectorException("Error while uploading chunk: " + str(e))

    # API call method. Accepts the data to be sent, refreshes the token if necessary, and returns the response
    def __callAPI(self, url, data, headers, method="post"):
        try:

            # Loop indefinitely
            while True:

                # Log the request
                logging.debug("New request")
                logging.debug(url)
                logging.debug(headers)

                # Call endpoint with the given method
                if method == "post":
                    response = requests.post(url, data=data, headers=headers)
                elif method == "put":
                    response = requests.put(url, data=data, headers=headers)
                else:
                    raise ConnectorException("Missing method")

                # Log the response
                logging.debug("Response received")
                logging.debug(response)
                logging.debug(response.text)

                # If the request is successful, exit the loop
                if response.ok:
                    break

                # Check the error code
                body = response.text
                body = json.loads(body)
                errorCode = body["error"]["code"]

                # If token is expired, refresh it and update header
                if errorCode == "InvalidAuthenticationToken":
                    self.__exchangeToken(self.refreshToken, True)
                    headers["Authorization"] = "Bearer " + self.token
                    print("Token has been refreshed")

                # Otherwise raise an exception
                else:
                    raise ConnectorException(errorCode)

            # Return the response received
            return response
        except Exception as e:
            raise ConnectorException("Error while calling endpoint: " + str(e))
