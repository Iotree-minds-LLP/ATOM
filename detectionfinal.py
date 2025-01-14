import numpy as np
import sys
import tarfile
import tensorflow as tf
import zipfile
from flask import Flask, render_template, request, send_file, send_from_directory
from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
import matplotlib.image as mpimg
from PIL import Image
from flask import jsonify

# if tf.__version__ != '1.4.1':
#   raise ImportError('Please upgrade your tensorflow installation to v1.4.1!')

from utils import label_map_util

from utils import visualization_utils as vis_util

# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_CKPT =  'ssd_mobilenet_RoadDamageDetector.pb' 

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = 'crack_label_map.pbtxt'

NUM_CLASSES = 8

damage_data = {
  "D00":{
    "damage_type":"Longitudinal Linear Crack",
    "detail": "Wheel Mark Part"
  },
  "D01":{
    "damage_type":"Longitudinal Linear Crack",
    "detail": "Construction Joint Part"
  },
  "D10":{
    "damage_type":"Lateral Linear Crack",
    "detail": "Equal Interval"
  },
  "D11":{
    "damage_type":"Lateral Linear Crack",
    "detail": "Construction Joint Part"
  },
  "D20":{
    "damage_type":"Alligator Crack",
    "detail": "Partial Pavement, Overall Pavement"
  },
  "D40":{
    "damage_type":"Other Corruption",
    "detail": "Rutting, Bump, Pathole, Seperation"
  },
  "D43":{
    "damage_type":"Other Corruption",
    "detail": "Cross Walk Blur"
  },
  "D44":{
    "damage_type":"Other Corruption",
    "detail": "White Line Blur"
  }
}



def load_image_into_numpy_array(image):
  (im_width, im_height) = image.size
  return np.array(image.getdata()).reshape(
      (im_height, im_width, 3)).astype(np.uint8)


def detect(test_image, plot_show = False):
  detection_graph = tf.Graph()
  with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
      serialized_graph = fid.read()
      od_graph_def.ParseFromString(serialized_graph)
      tf.import_graph_def(od_graph_def, name='')

  label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
  categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
  category_index = label_map_util.create_category_index(categories)
  cat = np.array(["D00","D01","D10","D11","D20","D40","D43","D44"])
  
  #INPUT FILE
  if str(type(test_image))!="<class 'list'>":
    TEST_IMAGE_PATHS=[test_image]  
  else:
    TEST_IMAGE_PATHS=test_image
  IMAGE_SIZE = (12, 8)
  final_images,boxes_collect,scores_collect,classes_collect,num_collect = [],[],[],[],[]
  with detection_graph.as_default():
    with tf.Session(graph=detection_graph) as sess:
      # Definite input and output Tensors for detection_graph
      image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
      # Each box represents a part of the image where a particular object was detected.
      detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
      # Each score represent how level of confidence for each of the objects.
      # Score is shown on the result image, together with the class label.
      detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
      detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
      num_detections = detection_graph.get_tensor_by_name('num_detections:0')
      for image_path in TEST_IMAGE_PATHS:
        image = Image.open(image_path)
        # the array based representation of the image will be used later in order to prepare the
        # result image with boxes and labels on it.
        image_np = load_image_into_numpy_array(image)
        # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
        image_np_expanded = np.expand_dims(image_np, axis=0)
        # Actual detection.
        (boxes, scores, classes, num) = sess.run(
            [detection_boxes, detection_scores, detection_classes, num_detections],
            feed_dict={image_tensor: image_np_expanded})
        min_score_thresh = 0.4
        
        #Select the boxes based on threshold
        sc = np.where(scores[0] > min_score_thresh)[0]
        scores_sel = scores[0][sc]
        boxes_sel = boxes[0][sc,:]
        classes_ind = classes[0][sc]
       
        classes_names = [(cat[int(i-1)]) for i in classes_ind]
        
        # Visualization of the results of a detection.
        vis_util.visualize_boxes_and_labels_on_image_array(
            image_np,
            np.squeeze(boxes),
            np.squeeze(classes).astype(np.int32),
            np.squeeze(scores),
            category_index,
            min_score_thresh=min_score_thresh,
            use_normalized_coordinates=True,
            line_thickness=8)
        if plot_show == True:
          plt.figure(figsize=IMAGE_SIZE)
          plt.imshow(image_np)
        final_images.append(image_np)
        boxes_collect.append(boxes_sel)
        scores_collect.append(scores_sel)
        classes_collect.append(classes_names)
        num_collect.append(num)
  
  return image_np,boxes_collect,scores_collect,classes_collect,test_image

"""
app = Flask(__name__)

@app.post('/upload_image')
def upload_image():
  raw_data = request.get_data()
  with open("input.jpg", "wb")  as outfile:
    outfile.write(raw_data)
  
  image_np,boxes_collect,scores_collect,classes_collect,test_image = detect("/home/asv0018/Desktop/roaddamagedetection/ATOM/input.jpg")
  print("###############################")
  plt.figure(figsize=(12,12))
  mpimg.imsave("output.jpg", image_np)
  print("###########")
  print(scores_collect[0])
  print(classes_collect[0])
  if len(scores_collect[0])!=0 and len(classes_collect[0])!=0:
    resp = {
      "message":"The road is damaged",
      "score_collect": float(str(scores_collect[0][0])),
      "classes_collect":classes_collect[0][0],
      "damage_data": damage_data[classes_collect[0][0]]
      }
    return jsonify(resp)
  else:
    resp = {
      "message":"The road is clean"
      }
    return jsonify(resp)

@app.route("/fetch_image_output")
def fetch_assets():
    return send_file("/home/asv0018/Desktop/roaddamagedetection/ATOM/output.jpg")

if __name__ == '__main__':
  app.run(debug=True)

"""
image_np,*_ = detect("/home/asv0018/Desktop/roaddamagedetection/ATOM/input.jpg")
print("###############################")
plt.figure(figsize=(12,12))
#plt.imshow(image_np)
#plt.show()
mpimg.imsave("out.jpg", image_np)
