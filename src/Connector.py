# Connector.py

# Importing libraries
import os
import json
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
        except Exception:
            raise ConnectorException("Cannot read from .env file.")

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

    def upload(self):

        # If configured fileName is a directory
        if os.path.isdir("files/" + self.fileName):
            try:

                # Read all files inside it
                filesCount = 0
                for root, dirs, files in os.walk("files/" + self.fileName):

                    # For each file get an upload url and upload it
                    for name in files:
                        self.__getUploadUrl(name)
                        self.__uploadBytes(os.path.join(root, name))
                        filesCount += 1

                # Return a confirmation message
                return "Upload completed. " + str(filesCount) + " file(s) uploaded"
            except Exception as e:
                raise ConnectorException(
                    "Error while uploading directory files: " + str(e))

        # If configured filename is a file, upload it directly
        elif os.path.isfile("files/" + self.fileName):
            try:
                self.__getUploadUrl(self.fileName)
                chunks = self.__uploadBytes("files/" + self.fileName)
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
                f.write("ACCESSTOKEN=" + body["access_token"] + "\n")
                f.write("REFRESHTOKEN=" + body["refresh_token"])

            # Update object property
            self.token = body["access_token"]
        except Exception as e:
            raise ConnectorException(
                "Error while exchanging tokens: " + str(e))

    # Upload session creation method. Refreshes the token, if needed, and request, a new url for a large file upload

    def __getUploadUrl(self, fileName):
        try:

            # Loop indefinitely
            while True:

                # Call endpoint
                url = "https://graph.microsoft.com/v1.0/drive/root:/" + \
                    fileName + ":/createUploadSession"
                data = {}
                headers = {
                    "Authorization": "Bearer " + self.token
                }
                response = requests.post(url, data=data, headers=headers)

                # If the request is successful, exit the loop
                if response.ok:
                    break

                # If here, the request failed: let's update the token
                self.__exchangeToken(self.refreshToken, True)
                print("Token has been refreshed")

            # Extract uploadUrl value from body and update local var
            body = response.text
            body = json.loads(body)
            self.uploadUrl = body["uploadUrl"]
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
                    requests.put(url, data=data, headers=headers)

                    # Increase counter for next chunk
                    i += 1

                # Return chunks count for confirmation
                return i
        except Exception as e:
            raise ConnectorException("Error while uploading chunk: " + str(e))
