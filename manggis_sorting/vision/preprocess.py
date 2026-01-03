import cv2
import numpy as np
from skimage.feature import graycomatrix, graycoprops

# Use IMG_SIZE and full 256-level GLCM like your script
IMG_SIZE = 64

def extract_color_features(rgb):
    return [
        np.mean(rgb[:,:,0]),
        np.mean(rgb[:,:,1]),
        np.mean(rgb[:,:,2]),
        np.std(rgb[:,:,0]),
        np.std(rgb[:,:,1]),
        np.std(rgb[:,:,2])
    ]

def extract_texture_features(gray):
    # gray is float [0,1] — convert to uint8 and use 256 levels
    gray_uint8 = (gray * 255).astype(np.uint8)

    glcm = graycomatrix(
        gray_uint8,
        distances=[1],
        angles=[0],
        levels=256,
        symmetric=True,
        normed=True
    )

    return [
        graycoprops(glcm, 'contrast')[0,0],
        graycoprops(glcm, 'homogeneity')[0,0],
        graycoprops(glcm, 'energy')[0,0],
        graycoprops(glcm, 'correlation')[0,0]
    ]

def extract_features(img):
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) / 255.0
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) / 255.0

    color = extract_color_features(rgb)
    texture = extract_texture_features(gray)

    features = color + texture

    features_dict = {
        "mean_r": color[0], "mean_g": color[1], "mean_b": color[2],
        "std_r": color[3],  "std_g": color[4],  "std_b": color[5],
        "glcm_contrast": texture[0],
        "glcm_homogeneity": texture[1],
        "glcm_energy": texture[2],
        "glcm_correlation": texture[3],
    }

    return np.array(features).reshape(1, -1), features_dict
