import cv2
import numpy as np
from ultralytics import YOLO
from ultralytics.utils.ops import scale_boxes
from skimage.filters import gaussian
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def detect_boxes_and_centers(image_input, model_path, conf_threshold=0.5):
    """
    Detects bounding boxes and their centers using a YOLO model, adjusted for the original image size.
    Includes preprocessing to handle grayscale images, float inputs, single-channel images, and bounding box scaling.

    Args:
        image_input (str or np.ndarray): Path to the image or a NumPy array representing the image.
        model_path (str): Path to the YOLO model (.pt file).
        conf_threshold (float): Confidence threshold for detections (default is 0.5).

    Returns:
        list: A list of bounding boxes as [x_min, y_min, x_max, y_max], adjusted for the original image.
        list: A list of centers as [x_center, y_center], adjusted for the original image.
    """
    # Load the YOLO model
    model = YOLO(model_path)

    # Preprocessing
    if isinstance(image_input, str):
        # Load image from file path
        image = cv2.imread(image_input)
    elif isinstance(image_input, np.ndarray):
        image = image_input
        # Handle float arrays in [0, 1] range
        if image.dtype != np.uint8:
            image = (image * 255).astype('uint8')
    else:
        raise ValueError("image_input must be a file path (str) or a NumPy array.")

    # Ensure the image has 3 channels
    if len(image.shape) == 2:  # Grayscale image
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif image.shape[2] != 3:  # Unsupported format
        raise ValueError("Input image must have 1 or 3 channels.")

    # Store original dimensions
    orig_height, orig_width = image.shape[:2]

    # Resize image for YOLO (YOLO does this internally, but we need original dimensions for scaling)
    resize_width, resize_height = 640, 640  # YOLO's default size
    resized_image = cv2.resize(image, (resize_width, resize_height))

    # Perform inference
    results = model(resized_image, conf=conf_threshold)
    result = results[0]  # Access the first Results object

    # Initialize outputs
    boxes = []  # List of bounding boxes
    centers = []  # List of box centers

    # Check if there are detections
    if result.boxes is not None:
        # Extract bounding boxes
        xyxy_boxes = np.array([box.xyxy[0] for box in result.boxes])

        # Scale boxes to original image size
        scaled_boxes = scale_boxes(
            img1_shape=(resize_height, resize_width),  # YOLO input dimensions
            boxes=xyxy_boxes,
            img0_shape=(orig_height, orig_width)  # Original image dimensions
        )

        for box in scaled_boxes:
            x_min, y_min, x_max, y_max = map(int, box)
            boxes.append([x_min, y_min, x_max, y_max])

            # Calculate the center of the adjusted box
            x_center = (x_min + x_max) // 2
            y_center = (y_min + y_max) // 2
            centers.append([x_center, y_center])

    return boxes, centers
def get_qdot_coordinates(image,Xs,Ys,model_path,conf):
    qdot_coords = []
    boxes,centers = detect_boxes_and_centers(image_input=image,model_path=model_path,conf_threshold=conf)
    for center in centers:
        i = int(center[0])
        j = int(center[1])
        ###########
        ###########
        ###########
        '''very very import notice, to acquire the real position, the index should be ji instead of ij'''
        qdot_coord = (Xs[j][i],Ys[j][i])
        ###########
        ###########
        qdot_coords.append(qdot_coord)
    return qdot_coords

# The following are a set of image preprocessing that must be done for detection
def non_local_denoise(image,h_value=10):
    image = (image / np.max(image) * 255).astype(np.uint8)
    denoised_image = cv2.fastNlMeansDenoising(
        image,  # Input image
        h=h_value,  # Filter strength for noise removal (higher removes more noise)
        templateWindowSize=3,  # Size of the template patch (odd value, e.g., 7x7)
        searchWindowSize=9  # Size of the search window (odd value, e.g., 21x21)
    )
    denoised_image = denoised_image / np.max(denoised_image)
    return denoised_image

def edge_detection(input_array):
    """
    Perform edge detection on a given 2D NumPy array (grayscale image) and plot the results.

    Parameters:
        input_array (np.ndarray): 2D array representing a grayscale image.

    Returns:
        edges_canny (np.ndarray): Binary image with edges detected using Canny.
        edges_sobel (np.ndarray): Image with edges detected using Sobel operator.
        edges_laplacian (np.ndarray): Image with edges detected using Laplacian operator.
    """
    # Ensure the input is in the correct format (convert to uint8 if necessary)
    input_array = input_array / np.max(input_array) * 255
    input_array = np.asarray(input_array, dtype=np.uint8)

    # Apply GaussianBlur to reduce noise
    blurred_image = cv2.GaussianBlur(input_array, (5, 5), 0)

    # Perform Canny edge detection
    edges_canny = cv2.Canny(blurred_image, threshold1=50, threshold2=150)

    # Sobel Edge Detection (Gradient-based)
    sobelx = cv2.Sobel(input_array, cv2.CV_64F, 1, 0, ksize=3)  # Horizontal edges
    sobely = cv2.Sobel(input_array, cv2.CV_64F, 0, 1, ksize=3)  # Vertical edges
    edges_sobel = cv2.magnitude(sobelx, sobely)  # Combine horizontal and vertical edges

    # Laplacian Edge Detection (Second-order derivative)
    edges_laplacian = cv2.Laplacian(input_array, cv2.CV_64F)
    return edges_canny, edges_sobel, edges_laplacian


def local_contrast_normalization(image, sigma=5):
    local_mean = gaussian(image, sigma=sigma)
    normalized_image = image / (local_mean + 1)  # Avoid division by zero
    return normalized_image / np.max(normalized_image)


def image_preprocessing(image,local_normalize=True,denoise=True,h_value=10):
    if local_normalize:
        image_normalized = local_contrast_normalization(image)
    else:
        image_normalized = image / np.max(image)

    if denoise:
        image_denoised = non_local_denoise(image=image_normalized,h_value=h_value)
    else:
        image_denoised = image_normalized

    edges_canny, edges_sobel, edges_laplacian = edge_detection(image_denoised)
    edges_sobel = edges_sobel / np.max(edges_sobel)
    return edges_sobel

def plot_intensity_map_with_boxes(intensity_map, boxes, save=False,output_path='annotated_image.jpg', display=True):
    """
    Plots an intensity map with bounding boxes using Matplotlib and the viridis colormap.

    Args:
        intensity_map (np.ndarray): 2D NumPy array representing the intensity map.
        boxes (list): List of bounding boxes as [x_min, y_min, x_max, y_max].
        output_path (str): Path to save the annotated image (default: 'annotated_image.jpg').
        display (bool): Whether to display the annotated image (default: False).

    Returns:
        None: The function saves the annotated image and optionally displays it.
    """
    # Validate input
    if len(intensity_map.shape) != 2:
        raise ValueError("intensity_map must be a 2D NumPy array (one-channel).")

    # Create a Matplotlib figure
    fig, ax = plt.subplots(1, figsize=(12, 8))
    ax.imshow(intensity_map, cmap='viridis')

    # Add bounding boxes
    for box in boxes:
        x_min, y_min, x_max, y_max = box
        width = x_max - x_min
        height = y_max - y_min
        rect = patches.Rectangle(
            (x_min, y_min), width, height,
            linewidth=2, edgecolor='red', facecolor='none'
        )
        ax.add_patch(rect)

    # Save the annotated image
    plt.axis('off')  # Turn off axes for a cleaner look
    plt.tight_layout()
    if save:
        plt.savefig(output_path, bbox_inches='tight', pad_inches=0)

    # Optionally display the image
    if display:
        plt.show()
    else:
        plt.close()

