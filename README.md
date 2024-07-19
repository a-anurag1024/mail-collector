# mail-collector
wrapper package to interact with gmail API, collect and create mail datasets from personal gmail account


# Setup

To set up the project, follow these steps:

1. Create a virtual environment:
    ```
    pip3 -m venv env
    ```

2. Install the package:
    ```
    cd mail-collector
    pip install -e .
    ```

3. Configure the Gmail API: Follow the instructions given in [this (google's documentation)](https://developers.google.com/gmail/api/quickstart/python) for configuring the API key. Store the **credentials.json** file as **gmail_API_client_secret.json** inside the ```./secrets``` folder.

4. Run the mail collector (with some default parameters):
    ```
    python collect_mails.py
    ```

5. Access the collected mail datasets stored inside the mount folder


Feel free to modify the collect_mails.py file as per your requirements. You can try the different search queries given mentioned in [this (again google's documentations)](https://support.google.com/mail/answer/7190)


