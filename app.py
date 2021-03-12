# oneDriveUploader.py

# Importing libraries
import sys
from src.Connector import Connector
from src.ConnectorException import ConnectorException


def main():
    try:
        connector = Connector()
        connector.login()
        response = connector.upload()
        print(response)
    except ConnectorException as e:
        closeWithMessage(e)


# Function to terminate the script by showing an informational message requesting confirmation
def closeWithMessage(message, confirmation=True):
    print(message)
    if confirmation:
        input("Hit enter to close")
    sys.exit(1)


# When the script is started, run the main function
if __name__ == '__main__':
    main()
