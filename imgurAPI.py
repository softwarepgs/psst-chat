import requests
import json


def uploadImageAnonymous(imageData, imageName, imageTitle):
    clientId = "<insert client id>"
    url = "https://api.imgur.com/3/image"
    payload = {"image": imageData,
               "type": "base64",
               "name": imageName,
               "title": imageTitle}
    files = []
    headers = {'Authorization': 'Client-ID ' + clientId}
    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    responseJSON = json.loads(response.text)
    return responseJSON["data"]["link"]
