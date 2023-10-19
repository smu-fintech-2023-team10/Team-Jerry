import cv2
import requests
from io import BytesIO
import numpy as np
from pyzbar.pyzbar import decode
def parseQrToString(imgURL):

    # URL of the QR code image
    url = imgURL

    # Send a GET request to the URL and retrieve the image
    response = requests.get(url)
    img = cv2.imdecode(np.asarray(bytearray(response.content), dtype=np.uint8), cv2.IMREAD_COLOR)

    # Decode the QR code
    decoded_objects = decode(img)

    # Extract and print the QR code data
    if decoded_objects:
        qr_data = decoded_objects[0].data.decode('utf-8')
        return {"success":True,
                "qrString": qr_data}
    else:
        return {"success":False,
                "qrString": "None"}
