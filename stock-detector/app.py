from counterfit_connection import CounterFitConnection
CounterFitConnection.init('127.0.0.1', 5000)

import io
from counterfit_shims_picamera import PiCamera

from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from msrest.authentication import ApiKeyCredentials

from PIL import Image, ImageDraw, ImageColor

from shapely.geometry import Polygon

camera = PiCamera()
camera.resolution = (640, 480)
camera.rotation = 0

image = io.BytesIO()
camera.capture(image, 'jpeg')
image.seek(0)

with open('image.jpg', 'wb') as image_file:
    image_file.write(image.read())

prediction_url = 'https://stockdetectorvgu-prediction.cognitiveservices.azure.com/customvision/v3.0/Prediction/a443424e-34a4-407e-8746-9b7ea679445d/detect/iterations/Iteration3/image'
prediction_key = '719a0d029d24464c8d72fbce65b94a82'

parts = prediction_url.split('/')
endpoint = 'https://' + parts[2]
project_id = parts[6]
iteration_name = parts[9]

prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": prediction_key})
predictor = CustomVisionPredictionClient(endpoint, prediction_credentials)

image.seek(0)
results = predictor.detect_image(project_id, iteration_name, image)

threshold = 0.3
overlap_threshold = 0.20

predictions = list(prediction for prediction in results.predictions if prediction.probability > threshold)

for prediction in predictions:
    print(f'{prediction.tag_name}:\t{prediction.probability * 100:.2f}%\t{prediction.bounding_box}')

with Image.open('image.jpg') as im:
    draw = ImageDraw.Draw(im)

    for prediction in predictions:
        scale_left = prediction.bounding_box.left
        scale_top = prediction.bounding_box.top
        scale_right = prediction.bounding_box.left + prediction.bounding_box.width
        scale_bottom = prediction.bounding_box.top + prediction.bounding_box.height
        
        left = scale_left * im.width
        top = scale_top * im.height
        right = scale_right * im.width
        bottom = scale_bottom * im.height

        draw.rectangle([left, top, right, bottom], outline=ImageColor.getrgb('red'), width=2)

    im.save('image.jpg')

def create_polygon(prediction):
    scale_left = prediction.bounding_box.left
    scale_top = prediction.bounding_box.top
    scale_right = prediction.bounding_box.left + prediction.bounding_box.width
    scale_bottom = prediction.bounding_box.top + prediction.bounding_box.height

    return Polygon([(scale_left, scale_top), (scale_right, scale_top), (scale_right, scale_bottom), (scale_left, scale_bottom)])
to_delete = []

for i in range(0, len(predictions)):
    polygon_1 = create_polygon(predictions[i])

    for j in range(i+1, len(predictions)):
        polygon_2 = create_polygon(predictions[j])
        overlap = polygon_1.intersection(polygon_2).area

        smallest_area = min(polygon_1.area, polygon_2.area)

        if overlap > (overlap_threshold * smallest_area):
            to_delete.append(predictions[i])
            break

for d in to_delete:
    predictions.remove(d)

print(f'Counted {len(predictions)} stock items')