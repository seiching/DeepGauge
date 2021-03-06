import cv2
import numpy as np
from skimage import io
from google.cloud import storage
import tempfile

"""Background Cloud Function to be triggered by Cloud Storage.
       This function takes an image and detects a circle in it, replaces
       the background with single color
    Arg: 
    	data: object that holds img
    Returns:
        None; the output is saved to a file location
    """

def image_circle_detection(data):
    # Get the file from the storage bucket
    client = storage.Client()
    bucket_id = 'ocideepgauge-image-w-background'
    bucket = client.get_bucket(bucket_id)
    img = io.imread(data['mediaLink'])
    if img is None:  # Check if image exists
        print('Error opening image!')
        print("Fail")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # Convert to gray
    gray = cv2.medianBlur(gray, 5)

    rows = gray.shape[0]
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, rows / 4,
                               param1=200, param2=60,
                               minRadius=0, maxRadius=0)  # Hough Circle function
    mask = np.full((img.shape[0], img.shape[1]), 0, dtype=np.uint8)  # Mask creation
    circle_details = None
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            cv2.circle(mask, (i[0], i[1]), i[2], (255, 255, 255), -1)  # Circle on mask around gauge
            circle_details = i
        fg = cv2.bitwise_or(img, img, mask=mask)  # Compares img to mask
        mask = cv2.bitwise_not(mask)
        background = np.full(img.shape, 255, dtype=np.uint8)
        bk = cv2.bitwise_or(background, background, mask=mask)
        bk[mask == 255] = (255, 255, 255)  # Set color of mask background
        final = cv2.bitwise_or(fg, bk)

        cropped = final[circle_details[1] - circle_details[2]:circle_details[1] + circle_details[2],
                  circle_details[0] - circle_details[2]:circle_details[0] + circle_details[2]]
        final_resized = cv2.resize(cropped, (1920, 1080))  # Set img size
        newname = "mod-" + data['name']
        with tempfile.NamedTemporaryFile() as temp:
            # Extract name to the temp file
            iName = "".join([str(temp.name), ".jpg"])
            # Save image to temp file
            cv2.imwrite(iName, final_resized)
            # Storing the image temp file inside the bucket
            blob = bucket.blob(newname)
            blob.upload_from_filename(iName, content_type=data['contentType'])

    else:
        print("No Circles Found")
