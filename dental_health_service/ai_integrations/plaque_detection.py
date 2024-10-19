# import os
import subprocess
import time
import logging
import shutil
from functools import wraps
from pathlib import Path

import cv2
import numpy as np
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
# from .detect_range import YoloDetector, torch

logger = logging.getLogger()
weights_folder_path = Path(__file__).absolute().parent / 'weights_models'


def timelog(func):
    """Decorator for recording function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            logger.info(f'[Phase: {func.__name__}] ------------- START')
            return func(*args, **kwargs)
        finally:
            elapsed_time = time.time() - start_time
            logger.info(f"[Phase: {func.__name__}] ------------- END in {elapsed_time:.3f}(s)")
    return wrapper


def django_save_image(save_path: str, image):
    """Saving image via Django default_storage."""
    logger.debug(f"django_save_image: {save_path}")
    # Encode the image as a PNG to a memory buffer
    success, buffer = cv2.imencode('.png', image)
    if not success:
        raise ValueError("Could not encode image")

    # Create a ContentFile from the buffer
    content = ContentFile(buffer.tobytes())

    # Save the ContentFile using Django's storage system
    default_storage.save(save_path, content)

    return True


class DentalPlaqueAnalysis:

    @timelog
    def __init__(self, img_root_folder_path):
        logger.debug('<Initialize the DentalPlaqueAnalysis>')
        self.img_root_path = img_root_folder_path  # A path instance for image root folder
        self.ori_img_path = self.img_root_path / 'original_image.png'  # A path instance for original image
        self.tooth_img_target_size = (640, 640)

        # Section of extract_each_tooth parameters.
        self.core = 'cpu'  # Processing Units. (e.g. cpu, gpu)

        self.cfg = get_cfg()
        self.cfg.MODEL.DEVICE = "cpu"
        self.cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"))
        self.cfg.OUTPUT_DIR = str(self.img_root_path)
        # Load your trained model weights
        self.cfg.MODEL.WEIGHTS = str(weights_folder_path / 'model_final.pth')
        self.cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1
        self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
        self.cfg.DATASETS.TEST = ('tooth_test',)
        # Initialize the predictor.
        self.predictor = DefaultPredictor(self.cfg)

        # List for saving tooth alignment information.
        self.teeth_alignment_list = []

        # Create a folder to save all of each tooth image.
        self.teeth_folder = self.img_root_path / 'teeth'
        self.teeth_folder.mkdir(parents=True, exist_ok=True)

        # Create a folder to save all of each detected tooth detection picture.
        self.teeth_detect_folder = self.img_root_path / 'teeth_detect'
        self.teeth_detect_folder.mkdir(parents=True, exist_ok=True)

        self.teeth_range_img_size = None

        logger.debug('<Initialize the DentalPlaqueAnalysis successfully>')

    @timelog
    def crop_teeth_range(self):
        logger.debug('------ Crop teeth range ------')
        im = cv2.imread(str(self.ori_img_path))
        if im is not None:
            logger.debug(f'Image read successfully.')
        else:
            logger.error(f'Image read failure!!')
            return

        logger.info(f'Using Yolov7 for Full mouth teeth prediction...')
        detect_script_path = Path(__file__).parent / 'detect_range.py'
        weight_path = weights_folder_path / 'best.pt'
        for file in [detect_script_path, weight_path]:
            if not file.exists():
                logger.error(f'file not found with {detect_script_path}')
                return

        command = [
            'python3', str(detect_script_path),
            '--weights', str(weight_path),
            '--conf', '0.5',
            '--img-size', '640',
            '--source', str(self.img_root_path),
            '--output-folder', str(self.img_root_path),
            '--view-img',
            '--no-trace',
            '--device', 'cpu'
        ]

        logger.debug(f'Running command: {" ".join(command)}')
        detect_result = subprocess.run(command, capture_output=True, text=True)

        # Check if the command was successful
        if detect_result.returncode == 0:
            logger.info("detect_range.py executed successfully.")
            logger.debug(f'detect_range.py[stdout]=> {detect_result.stdout}, [stderr]=> {detect_result.stderr}')
        else:
            logger.warning("detect_range.py executed unsuccessfully!!")
            logger.error(f'detect_range.py '
                         f'[returncode]=>{detect_result.returncode},'
                         f' [stdout]=> {detect_result.stdout}, '
                         f'[stderr]=> {detect_result.stderr}')

        # detect_args = [
        #     '--weights', './ai_integrations/models/best.pt',
        #     '--conf', '0.5',
        #     '--img-size',  '640',
        #     '--source', f'{self.img_root_path}',
        #     '--output-folder', f'{self.img_root_path}',
        #     '--view-img',
        #     '--no-trace',
        #     '--device', 'cpu',
        # ]
        # yolo = YoloDetector(detect_args)
        # with torch.no_grad():
        #     yolo.detect()

        return True

    @timelog
    def extract_each_tooth(self):
        logger.debug('------ Extract each tooth ------')
        teeth_range_img_path = str(self.img_root_path / 'teeth_range.png')
        im = cv2.imread(teeth_range_img_path)
        if im is not None:
            logger.info('Read teeth_range.png successfully.')
        else:
            logger.error('Failed on reading teeth_range.png!')
            return

        logger.debug(f'Using Detection2 for single tooth prediction...')

        # Capture each tooth by the detection result of YOLO model.
        outputs = self.predictor(im)
        instances = outputs["instances"].to(self.core)
        masks = instances.pred_masks

        # Save the teeth_range image size.
        height, width, channels = self.teeth_range_img_size = im.shape
        logger.debug(f'teeth_range image size => Width: {width}, Height: {height}')

        # Traverse the prediction mask of each instance
        for i, mask in enumerate(masks):
            # Create a new image, retaining the teeth parts and making the rest black
            extracted_tooth_img = im.copy()
            extracted_tooth_img[~mask] = [0, 0, 0]  # Set the rest parts to black.

            # Find the MBR(minimum bounding rectangle) which contain the teeth.
            mask = mask.byte().numpy()
            x, y, w, h = cv2.boundingRect(mask)
            extracted_tooth_img = extracted_tooth_img[y:y + h, x:x + w]

            # Scale image to the target size while maintaining the aspect ratio.
            resized_tooth_img = cv2.resize(extracted_tooth_img, self.tooth_img_target_size)

            # Save single tooth image.
            single_tooth_img_path = str(self.teeth_folder / f'tooth_{i}.png')
            # cv2.imwrite(single_tooth_img_path, extracted_tooth_img)  # save file to local path
            logger.debug(f'save image {single_tooth_img_path}')
            django_save_image(single_tooth_img_path, extracted_tooth_img)
            # Add the tooth alignment information to list.
            self.teeth_alignment_list.append(
                (x, y, w, h, extracted_tooth_img, resized_tooth_img, single_tooth_img_path)
            )
        return True

    @timelog
    def detect_each_tooth(self):
        """Process each tooth image to detect dental plaque."""
        logger.debug('------ Detect each tooth ------')

        total_teeth_area = 0  # area of full mouth teeth.
        total_black_pixels = 0  # dental plaque of full mouth teeth.

        # Get the teeth_range image size.
        height, width, channels = self.teeth_range_img_size
        logger.debug(f'teeth_range image size => Width: {width}, Height: {height}')

        # Create a blank image with the same size as original image.
        blank_image = np.full((height, width), 255, dtype=np.uint8)

        for tooth_data in self.teeth_alignment_list:
            x, y, w, h, extracted_tooth_img, resized_tooth_img, single_tooth_img_path = tooth_data
            # Extract the tooth portion onto a blank image.
            cvt_img = cv2.cvtColor(extracted_tooth_img, cv2.COLOR_BGR2HSV)
            H, S, V = cv2.split(cvt_img)
            cvt_img[:, :, 2] = V * 0 + 255
            cvt_img = cv2.cvtColor(cvt_img, cv2.COLOR_HSV2BGR)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
            cvt_img = cv2.morphologyEx(cvt_img, cv2.MORPH_OPEN, kernel)
            grayscale_img = cv2.cvtColor(cvt_img, cv2.COLOR_BGR2GRAY)

            _, thresholded_image = cv2.threshold(grayscale_img, 0.7 * 255, 255, cv2.THRESH_BINARY)

            blank_image[y:y + h, x:x + w] = thresholded_image

            fname = Path(single_tooth_img_path).name
            logger.debug(f"--------------- {fname} ---------------")

            # Process the resized image and calculate the area excluding black.
            grayscale_img = cv2.cvtColor(resized_tooth_img, cv2.COLOR_BGR2GRAY)
            _, thresholded_image = cv2.threshold(grayscale_img, 1, 255, cv2.THRESH_BINARY)
            tooth_area = cv2.countNonZero(thresholded_image)
            total_teeth_area += tooth_area

            cvt_img = cv2.cvtColor(resized_tooth_img, cv2.COLOR_BGR2HSV)
            H, S, V = cv2.split(cvt_img)
            cvt_img[:, :, 2] = V * 0 + 255
            cvt_img = cv2.cvtColor(cvt_img, cv2.COLOR_HSV2BGR)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
            cvt_img = cv2.morphologyEx(cvt_img, cv2.MORPH_OPEN, kernel)
            grayscale_img = cv2.cvtColor(cvt_img, cv2.COLOR_BGR2GRAY)

            _, thresholded_image = cv2.threshold(grayscale_img, 0.7 * 255, 255, cv2.THRESH_BINARY)
            total_pixels = thresholded_image.size  # Get total number of pixels from the image.
            white_pixels = cv2.countNonZero(thresholded_image)  # Get the number of white pixels.
            black_pixels = total_pixels - white_pixels  # Calculate the number of black pixels
            total_black_pixels += black_pixels

            processed_tooth_img_name = Path(single_tooth_img_path).stem + '_imgr.png'
            processed_tooth_img_path = str(self.teeth_detect_folder / processed_tooth_img_name)
            # cv2.imwrite(processed_tooth_img_path, thresholded_image)  # save file to local path
            logger.debug(f'save image {processed_tooth_img_path}')
            django_save_image(processed_tooth_img_path, thresholded_image)

        # Save the composite image of full mouth teeth.
        teeth_range_detect_img_path = str(self.img_root_path / "teeth_range_detect.png")
        # cv2.imwrite(teeth_range_detect_img_path, blank_image)  # save file to local path
        logger.info(f'save image {teeth_range_detect_img_path}')
        django_save_image(teeth_range_detect_img_path, blank_image)

        # Calculate the dental plaque ratio for the full mouth.
        try:
            percentage_plaque_total = (total_black_pixels / total_teeth_area) * 100
            logger.info(f"Dental Plaque ratio for the full mouth: {percentage_plaque_total:.2f}%")
        except ZeroDivisionError:
            logger.error(f'Calculate percentage_plaque_total ERROR(division by zero), '
                         f'total_black_pixels=> [{total_black_pixels}]'
                         f'total_teeth_area=> [{total_teeth_area}]')
            return {
                'returncode': 1,
                'message': '計算錯誤！！(division by zero)',
                'data': {"total_black_pixels": total_black_pixels, "total_teeth_area": total_teeth_area}
            }

        return {
            'returncode': 0,
            'message': f"整口牙齒的牙菌斑占百分比: {percentage_plaque_total:.2f}%",
            'data': {'percentage_plaque_total': f'{percentage_plaque_total:.2f}'}
        }

    @timelog
    def clear_folders(self):
        logger.debug('------ Clear folders ------')

        folder_list = ['teeth', 'teeth_detect']
        for folder_name in folder_list:
            folder_path = self.img_root_path / folder_name
            if folder_path.exists():
                logger.debug(f'Remove ({folder_path}) folder')
                try:
                    shutil.rmtree(folder_path)  # remove folder content.
                except PermissionError:
                    logger.error(f'Permission denied: Unable to delete "{folder_path}"')
            logger.debug(f'Create ({folder_path}) folder')
            folder_path.mkdir(parents=True, exist_ok=True)  # re-create folder

    @classmethod
    @timelog
    def analyze_dental_plaque(cls, img_root_folder_path) -> dict:
        """Get started with teeth analysis!!"""
        logger.info("Get started with teeth analysis!!")
        message = None
        service = cls(img_root_folder_path)

        service.clear_folders()

        for _ in range(1):
            if not service.crop_teeth_range():
                message = 'run crop_teeth_range failed!!'
                logger.error(message)
                break

            if not service.extract_each_tooth():
                message = 'run extract_each_tooth failed!!'
                logger.error(message)
                break

            if ret := service.detect_each_tooth():
                logger.info(f'run extract_each_tooth success.')
                return ret
            else:
                logger.error(f'run extract_each_tooth failed!!')

        if not message:
            message = 'Dental Plaque analysis failure!!'

        return {
            'returncode': 1,
            'message': message,
            'data': True
        }


if __name__ == '__main__':
    trial_run_path = Path(__file__).absolute().parent / 'test_images'
    print(str(trial_run_path))
    result = DentalPlaqueAnalysis.analyze_dental_plaque(trial_run_path)
    print(result)
