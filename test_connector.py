import os
import json
import unittest
import requests_mock
from src.Connector import Connector
from src.ConnectorException import ConnectorException


class TestConnector(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        if not os.path.exists("./.env"):
            with open("./.env", "w") as f:
                f.write("FILENAME=FAKE_FILENAME\n")
                f.write("BLOCKSIZE=FAKE_BLOCKSIZE\n")
                f.write("CLIENTID=FAKE_CLIENTID\n")
                f.write("CLIENTSECRET=FAKE_CLIENTSECRET\n")
                f.write("ACCESSTOKEN=FAKE_ACCESSTOKEN\n")
                f.write("REFRESHTOKEN=FAKE_REFRESHTOKEN")

    def test_init(self):
        try:
            Connector()
        except ConnectorException as e:
            self.fail("Connector() raised a ConnectorException: " + str(e))

    def test_exchange_token_new(self):
        expected_result = {
            "token_type": "Bearer",
            "scope": "Files.ReadWrite",
            "expires_in": 3600,
            "access_token": "FAKE_ACCESSTOKEN",
            "refresh_token": "FAKE_REFRESHTOKEN"
        }
        with requests_mock.Mocker() as m:
            m.register_uri('POST', '/common/oauth2/v2.0/token',
                           text=json.dumps(expected_result))
            try:
                connector = Connector()
                token = connector._Connector__exchangeToken("FAKE_CODE")
                self.assertEqual("FAKE_ACCESSTOKEN", token)
            except ConnectorException as e:
                self.fail(
                    "__exchangeToken() raised a ConnectorException: " + str(e))

    def test_create_folder(self):
        expected_result = {
            "createdBy": {
                "user": {
                    "displayName": "Francesco Rega",
                    "id": "000000-000000-000000"
                }
            },
            "createdDateTime": "2021-01-01T00:00:00Z",
            "eTag": "000000-000000-000000",
            "id": "000000-000000-000000",
            "lastModifiedBy": {
                "user": {
                    "displayName": "Francesco Rega",
                    "id": "000000-000000-000000"
                }
            },
            "lastModifiedDateTime": "2021-01-01T00:00:00Z",
            "name": "FAKE_FOLDER",
            "parentReference": {
                "driveId": "000000-000000-000000",
                "id": "000000-000000-000000",
                "path": "/drive/root:/"
            },
            "size": 0,
            "folder": {
                "childCount": 0
            }
        }
        with requests_mock.Mocker() as m:
            m.register_uri('POST', '/v1.0/drive/root/children',
                           text=json.dumps(expected_result))
            try:
                connector = Connector()
                folder = connector._Connector__createFolder("FAKE_FOLDER")
                self.assertEqual("FAKE_FOLDER", folder)
            except ConnectorException as e:
                self.fail(
                    "__createFolder() raised a ConnectorException: " + str(e))

    def test_upload_session(self):
        expected_result = {
            "uploadUrl": "https://sn1234.up.1drv.com/up/fakeurl",
            "expirationDateTime": "2021-01-01T00:00:00.000Z"
        }
        with requests_mock.Mocker() as m:
            m.register_uri('POST', '/v1.0/drive/root:/fakefile:/createUploadSession',
                           text=json.dumps(expected_result))
            try:
                connector = Connector()
                url = connector._Connector__getUploadUrl("fakefile")
                self.assertEqual("https://sn1234.up.1drv.com/up/fakeurl", url)
            except ConnectorException as e:
                self.fail(
                    "__getUploadUrl() raised a ConnectorException: " + str(e))
