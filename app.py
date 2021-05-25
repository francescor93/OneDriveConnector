# oneDriveUploader.py

# Importing libraries
import sys
from src.Connector import Connector
from src.ConnectorException import ConnectorException


def main():
    try:
        args = sys.argv
        connector = Connector()
        connector.login()
        if len(args) > 1:
            response = connector.upload(args[1])
        else:
            response = connector.upload()
        print(response)
    except ConnectorException as e:
        print(e)
        sys.exit(1)


# When the script is started, run the main function
if __name__ == '__main__':
    main()
