# oneDriveUploader.py

# Importing libraries
import os
import sys
import json
import urllib
import requests
from urllib.parse import quote
from dotenv import load_dotenv
from os.path import dirname, abspath


def main():

    # Try to load .env file and extract configured values
    try:
        env = dirname(abspath(__file__)) + "/.env"
        load_dotenv(dotenv_path=env)
        config = {
            'token': os.getenv('ACCESSTOKEN', ""),
            'refreshToken': os.getenv('REFRESHTOKEN', ""),
            'clientId': os.getenv('CLIENTID', ""),
            'clientSecret': os.getenv('CLIENTSECRET', ""),
            'fileName': os.getenv('FILENAME', ""),
            'chunkSize': os.getenv('BLOCKSIZE', "")
        }
    except Exception:
        closeWithMessage("Cannot read from .env file.")

    # If (part of) configuration is missing, exit with a warning
    if (config["clientId"] == "" or config["clientSecret"] == "" or config["fileName"] == "" or config["chunkSize"] == ""):
        closeWithMessage(
            "System has not been configured yet. Please update the .env file and restart the script.")

    # If token is empty
    if (config["token"] == ""):
        try:

            # Generate the url to visit and show it to the user
            url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=" + config["clientId"] + "&response_type=code&redirect_uri=" + urllib.parse.quote(
                "https://apps.francescorega.eu/1DToken") + "&scope=User.ReadBasic.All+Files.ReadWrite+offline_access"
            print("The authentication token has not yet been set.")
            print("Please visit this address to authorize the app to access your account and paste below the token that will be returned to you:")
            print(url)
            inputCode = input("Paste token here: ")

            # Exchange temporary code with real authentication token and get updated config
            config = exchangeToken(inputCode, config)
        except Exception as e:
            closeWithMessage(
                "Error while creating authentication code: " + str(e))

    # If configured fileName is a directory
    if os.path.isdir("files/" + config["fileName"]):
        try:

            # Read all files inside it
            filesCount = 0
            for root, dirs, files in os.walk("files/" + config["fileName"]):

                # For each file get an upload url and then upload it
                for name in files:
                    config = getUploadUrl(config, name)
                    uploadBytes(config, os.path.join(root, name))
                    filesCount += 1

            # Exit with a confirmation message
            closeWithMessage("Upload completed. " +
                             str(filesCount) + " file(s) uploaded", False)
        except Exception as e:
            closeWithMessage(
                "Error while uploading directory files: " + str(e))

    # If configured filename is a file, upload it directly
    elif os.path.isfile("files/" + config["fileName"]):
        try:
            config = getUploadUrl(config, config["fileName"])
            chunks = uploadBytes(config, "files/" + config["fileName"])
            closeWithMessage("Upload completed with " +
                             str(chunks) + " chunk(s)", False)
        except Exception as e:
            closeWithMessage("Error while uploading single file: " + str(e))

    # If configured filename is a special file, exit with a warning
    else:
        closeWithMessage("Configured FILENAME is invalid")


# Function to exchange an authentication code or a refresh token with a new pair of valid authentication and refresh tokens
def exchangeToken(code, config, isRefresh=False):
    try:

        # Call endpoint
        url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        data = {
            'client_id': config["clientId"],
            'redirect_uri': 'https://apps.francescorega.eu/1DToken',
            'client_secret': config["clientSecret"],
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
        env = dirname(abspath(__file__)) + "/.env"
        with open(env, "w") as f:
            f.write("FILENAME=" + config["fileName"] + "\n")
            f.write("BLOCKSIZE=" + config["chunkSize"] + "\n")
            f.write("CLIENTID=" + config["clientId"] + "\n")
            f.write("CLIENTSECRET=" + config["clientSecret"] + "\n")
            f.write("ACCESSTOKEN=" + body["access_token"] + "\n")
            f.write("REFRESHTOKEN=" + body["refresh_token"])

        # Update local var
        config["token"] = body["access_token"]

        # Return updated config
        return config
    except Exception as e:
        closeWithMessage("Error while exchanging tokens: " + str(e))


# Function to get a new upload url for a file
def getUploadUrl(config, fileName):
    try:

        # Loop indefinitely
        while True:

            # Call endpoint
            url = "https://graph.microsoft.com/v1.0/drive/root:/" + \
                fileName + ":/createUploadSession"
            data = {}
            headers = {
                "Authorization": "Bearer " + config["token"]
            }
            response = requests.post(url, data=data, headers=headers)

            # If the request is successful, exit the loop
            if response.ok:
                break

            # If here, the request failed: let's update the token
            config = exchangeToken(config["refreshToken"], config, True)
            print("Token has been refreshed")

        # Extract uploadUrl value from body and update local var
        body = response.text
        body = json.loads(body)
        config["uploadUrl"] = body["uploadUrl"]

        # Return updated config
        return config
    except Exception as e:
        closeWithMessage(e)


# Function to upload a single file in chunks of bytes
def uploadBytes(config, filePath):
    try:

        # If configured chunk size is larger than the maximum chunk size allowed by OneDrive correct it, but show a warning
        if int(config["chunkSize"]) > 60:
            config["chunkSize"] = 60
            print(
                "Configured chunk size is larger than allowed: proceeding using 60MB chunks.")

        # Open local file and calculate size
        with open(filePath, "rb") as f:
            fileSize = os.path.getsize(f.name)
            chunkSizeBytes = int(config["chunkSize"]) * 1024 * 1024
            i = 0

            # Split it in chunks
            while (byte := f.read(chunkSizeBytes)):
                rangeMin = chunkSizeBytes * i
                rangeMax = chunkSizeBytes * i + chunkSizeBytes - 1

                # Prevent the calculated rangeMax from being larger than the file size
                if rangeMax > fileSize:
                    rangeMax = fileSize - 1

                # Send upload request
                url = config["uploadUrl"]
                data = byte
                headers = {
                    "Authorization": "Bearer " + config["token"],
                    "Content-Length": str(rangeMax - rangeMin),
                    "Content-Range": "bytes " + str(rangeMin) + "-" + str(rangeMax) + "/" + str(fileSize)
                }
                response = requests.put(url, data=data, headers=headers)
                body = response.text

                # Increase counter for next chunk
                i += 1

            # Return chunks count for confirmation
            return i
    except Exception as e:
        closeWithMessage("Error while uploading chunk: " + str(e))


# Function to terminate the script by showing an informational message requesting confirmation
def closeWithMessage(message, confirmation=True):
    print(message)
    if confirmation:
        exit = input("Hit enter to close")
    sys.exit(1)


# When the script is started, run the main function
if __name__ == '__main__':
    main()
