# OneDriveConnector

This is a simple script to upload files to your OneDrive cloud using *Microsoft Graph API*.

It can be used, for example, as a scheduled job to regularly transfer your content in the background. But any other proposal is welcome.

## Prerequisites

Since this script will access your OneDrive, you need to have previously created and configured an app on Microsoft Azure Portal.

To do this, you have to follow this steps:

1. Login to [Azure Portal](https://portal.azure.com) with your Microsoft account.

2. In the left sidebar select **Active Directory** and, within it, select **App registrations** > **New registration**.

3. On the *Register an application* page enter the name you would like to give to your application and select **Accounts in any organizational directory and personal Microsoft accounts** as *Supported account types*. As *Redirect URI (optional)* select type **Web** from the drop-down menu; in the url field you can enter **<https://apps.francescorega.eu/1DToken>**[*] or any address of a page owned by you, if you prefer; the purpose of this page will be only to show you the temporary code returned by *Microsoft* at the authentication to paste inside the script, as explained later in the *Configuration* paragraph. When you're done, click **Register**: you will be shown an overview page with the information of the app and the *Client ID*; make a note of this code as you will need it later.

4. In the left sidebar select **Certificates & secrets** > **New client secret**. Enter a description and select a duration, and click **Add**: a new valid client secret for your application will be shown to you. Make sure you copy that value to a safe place - you won't be able to view it again after closing the page.

5. In the left sidebar select **Expose an API** > **Add a scope**. In the *Request API permissions* pane select **Microsoft Graph** and then **Delegated persmissions**. Scroll down and expand *Files*; check **Files.ReadWrite** and click **Add permissions**.

[*]: Please note: I created that page just to make it easier for you to see the temporary access code returned by Microsoft. No code or other sensitive information will be stored by the site. If despite this you are still concerned about your privacy, you can create a similar page on your web space: just make sure that it shows the *code* parameter received as a querystring.

##  Installation

To run this code, just download or clone the repository to your environment:

```git clone https://github.com/francescor93/OneDriveConnector.git```

Then enter the created folder and install missing dependencies using:

```pip install -r requirements.txt```

Finally copy the ```.env.example``` file and rename it to ```.env```.

## Configuration

Before use it is necessary to make some configurations. The customization of the script is done by editing the ```.env``` file: so open this file and change it according to your needs, defining all the values shown below.

* **FILENAME**: This has to be set to the name of the file or folder you want to upload. The given file or folder must be placed inside the ```files``` folder and will be uploaded to the root of your *OneDrive*.

* **BLOCKSIZE**: To upload large files to *OneDrive* it is necessary to transfer them in smaller chunks of bytes: set this parameter with the maximum size, in MB, that each single chunk must have. Please note that the maximum allowed is 60 MB.

* **CLIENTID**: Enter here the *Client ID* value you copied earlier when creating your application on the *Microsoft Azure portal*. This is required to request and allow the script to access your *OneDrive*.

* **CLIENTSECRET**: Enter here the *Client Secret* value you copied earlier when creating your application on the *Microsoft Azure portal*. This is required to request and allow the script to access your *OneDrive*.

During use, the script will also add the *ACCESSTOKEN* and *REFRESHTOKEN* parameters to the ```.env``` file. These are required to maintain authentication: never change them or you will have to repeat the login procedure from the beginning.

## Usage

To start using the script simply start it via your favorite CLI, for example by running:

```python app.py```

At the first run you will be shown a URL to visit to gain access: click it to grant permissions to your application and, from the page to which you will be redirected, copy your *authorization code*. Then paste it in your terminal, where you are asked *Paste token here*: in this way it will be stored locally and it will not be necessary to repeat the procedure later.

At this point the script will continue its operation by uploading the necessary file(s) to OneDrive.

At the end you will be shown a success message indicating how many chunks were needed (in the case of a single file) or how many files were uploaded (in the case of an entire folder).

In the event of an error, a detailed message will explain what went wrong, and the script will require user confirmation to exit.

## More informations

This project is open to anyone who wants to contribute - just make your changes separately and send me a pull request describing your change and motivation.

If you have problems or suggestions, feel free to open an issue describing them: I will be with you as soon as possible.

For any other needs contact me through GitHub or through my website.

Please note that this project is under development and is provided "as is", and it is by no means assured that it will be free from bugs or other problems. Also note that it was created in a personal capacity and is in no way affiliated with Microsoft Corporation.

Thanks for taking an interest in **OneDriveConnector**!
