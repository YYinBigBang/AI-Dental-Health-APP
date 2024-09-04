from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

import argparse
import logging
import time
from pathlib import Path
import numpy as np

import cv2
import torch
import torch.backends.cudnn as cudnn
from models.experimental import attempt_load
from utils.torch_utils import select_device, load_classifier, time_synchronized, TracedModel
from utils.datasets import LoadStreams, LoadImages
from utils.plots import plot_one_box
from utils.general import (
    check_img_size,
    check_requirements,
    check_imshow,
    non_max_suppression,
    apply_classifier,
    scale_coords,
    xyxy2xywh,
    strip_optimizer,
    set_logging,
    increment_path
)

logger = logging.getLogger("root")


def check_pytorch():
    """For checking torch is working."""
    print(torch.__version__)
    print(torch.version.cuda)
    print(torch.cuda.is_available())
    print(torch.cuda.device_count())
    # Check if the CuDNN is enabled.
    print(torch.backends.cudnn.enabled)


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


class YoloDetector:

    def __init__(self, args: list = None):
        logger.debug(f"Initialize the YoloDetector")
        self.options = self.parse_args(args)
        logger.debug(f"YoloDetector options: {self.options}")
        self.source = self.options.source
        self.output_folder = self.options.output_folder
        self.weights = self.options.weights
        self.view_img = self.options.view_img
        self.save_txt = self.options.save_txt
        self.trace = not self.options.no_trace

        self.save_img = not (self.options.nosave or self.options.source.endswith('.txt'))  # save inference images
        self.webcam = (self.source.isnumeric() or
                       self.source.endswith('.txt') or
                       self.source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://')))

        self.device = select_device(self.options.device)
        self.half = self.device.type != 'cpu'  # half precision only supported on CUDA
        self.classify = False
        # Load model
        self.model = attempt_load(self.weights, map_location=self.device)
        self.stride = int(self.model.stride.max())  # model stride
        self.imgsz = check_img_size(self.options.img_size, s=self.stride)  # check img_size

        if self.trace:
            self.model = TracedModel(self.model, self.device, self.options.img_size)

        if self.half:
            self.model.half()  # to FP16

        logger.debug(f"Success to initialize the YoloDetector")

    @staticmethod
    def parse_args(args: list = None):
        """Parse command line arguments for the YOLO object detection script."""
        parser = argparse.ArgumentParser()

        parser.add_argument('--weights', nargs='+', type=str, default='yolov7.pt', help='model.pt path(s)')
        parser.add_argument('--source', type=str, default='inference/images', help='source')  # file/folder, 0 for webcam
        parser.add_argument('--output-folder', type=str, default='inference/images', help='output-folder')
        parser.add_argument('--img-size', type=int, default=640, help='inference size (pixels)')
        parser.add_argument('--conf-thres', type=float, default=0.25, help='object confidence threshold')
        parser.add_argument('--iou-thres', type=float, default=0.45, help='IOU threshold for NMS')
        parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
        parser.add_argument('--view-img', action='store_true', help='display results')
        parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
        parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
        parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
        parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 0 2 3')
        parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
        parser.add_argument('--augment', action='store_true', help='augmented inference')
        parser.add_argument('--update', action='store_true', help='update all models')
        parser.add_argument('--project', default='runs/detect', help='save results to project/name')
        parser.add_argument('--name', default='exp', help='save results to project/name')
        parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
        parser.add_argument('--no-trace', action='store_true', help='don`t trace model')

        return parser.parse_args(args)

    def detect(self):
        logger.debug('run detect function')

        # # Directories
        # save_dir = Path(
        #     increment_path(
        #         Path(self.options.project) / self.options.name, exist_ok=self.options.exist_ok))  # increment run
        # ('labels' if self.save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir

        # Second-stage classifier
        if self.classify:
            modelc = load_classifier(name='resnet101', n=2)  # initialize
            modelc.load_state_dict(
                torch.load('weights/resnet101.pt', map_location=self.device, weights_only=True)['model']).to(self.device).eval()

        # Set Dataloader
        vid_path, vid_writer = None, None
        if self.webcam:
            self.view_img = check_imshow()
            cudnn.benchmark = True  # set True to speed up constant image size inference
            dataset = LoadStreams(self.source, img_size=self.imgsz, stride=self.stride)
        else:
            dataset = LoadImages(self.source, img_size=self.imgsz, stride=self.stride)

        # Get names and colors
        names = self.model.module.names if hasattr(self.model, 'module') else self.model.names
        colors = [[np.random.randint(0, 255) for _ in range(3)] for _ in names]

        # Run inference
        if self.half:
            self.model(torch.zeros(1, 3, self.imgsz, self.imgsz).to(self.device).type_as(next(self.model.parameters())))  # run once
        old_img_w = old_img_h = self.imgsz
        old_img_b = 1

        t0 = time.time()
        for path, img, im0s, vid_cap in dataset:
            img = torch.from_numpy(img).to(self.device)
            img = img.half() if self.half else img.float()  # uint8 to fp16/32
            img /= 255.0  # 0 - 255 to 0.0 - 1.0
            if img.ndimension() == 3:
                img = img.unsqueeze(0)

            # Warmup
            if self.half and (
                    old_img_b != img.shape[0] or old_img_h != img.shape[2] or old_img_w != img.shape[3]):
                old_img_b = img.shape[0]
                old_img_h = img.shape[2]
                old_img_w = img.shape[3]
                for i in range(3):
                    self.model(img, augment=self.options.augment)[0]

            # Inference
            t1 = time_synchronized()
            with torch.no_grad():  # Calculating gradients would cause a GPU memory leak
                pred = self.model(img, augment=self.options.augment)[0]
            t2 = time_synchronized()

            # Apply NMS
            pred = non_max_suppression(pred,
                                       self.options.conf_thres,
                                       self.options.iou_thres,
                                       classes=self.options.classes,
                                       agnostic=self.options.agnostic_nms)
            t3 = time_synchronized()

            # Apply Classifier
            if self.classify:
                pred = apply_classifier(pred, modelc, img, im0s)

            # Process detections
            for i, det in enumerate(pred):  # detections per image
                if self.webcam:  # batch_size >= 1
                    p, s, im0, frame = path[i], '%g: ' % i, im0s[i].copy(), dataset.count
                else:
                    p, s, im0, frame = path, '', im0s, getattr(dataset, 'frame', 0)

                p = Path(p)  # to Path

                # save_path = str(save_dir / p.name)  # img.jpg
                # txt_path = str(save_dir / 'labels' / p.stem) + (
                #     '' if dataset.mode == 'image' else f'_{frame}')  # img.txt

                gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
                if len(det):
                    # Rescale boxes from img_size to im0 size
                    det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

                    # Print results
                    for c in det[:, -1].unique():
                        n = (det[:, -1] == c).sum()  # detections per class
                        s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                    # Write results
                    for *xyxy, conf, cls in reversed(det):
                        # if save_txt:  # Write to file
                        #     xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                        #     line = (cls, *xywh, conf) if self.options.save_conf else (cls, *xywh)  # label format
                        #     with open(txt_path + '.txt', 'a') as f:
                        #         f.write(('%g ' * len(line)).rstrip() % line + '\n')

                        if self.save_img or self.view_img:  # Add bbox to image
                            label = f'{names[int(cls)]} {conf:.2f}'
                            plot_one_box(xyxy, im0, label=label, color=colors[int(cls)], line_thickness=1)

                            if self.save_img:
                                x1, y1, x2, y2 = map(int, xyxy)
                                cropped_img = im0[y1:y2, x1:x2]  # Crop the boxed area

                                save_cropped_path = self.output_folder + '/' + "teeth_range.png"
                                # cv2.imwrite(save_cropped_path, cropped_img)  # save file to local path
                                django_save_image(save_cropped_path, cropped_img)
                                logger.info(f"Cropped image saved at: {save_cropped_path}")

                logger.debug(f'{s}Done. ({(1E3 * (t2 - t1)):.1f}ms) Inference, ({(1E3 * (t3 - t2)):.1f}ms) NMS')

        logger.debug(f'Done. ({time.time() - t0:.3f}s)')


if __name__ == '__main__':
    # detect_args = [
    #     '--weights', './weights_models/best.pt',
    #     '--conf', '0.5',
    #     '--img-size', '640',
    #     '--source', f'test_images',
    #     '--output-folder', f'test_images',
    #     '--view-img',
    #     '--no-trace',
    #     '--device', 'cpu',
    # ]
    # yolo = YoloDetector(detect_args)

    yolo = YoloDetector()
    print(yolo.options)
    with torch.no_grad():
        yolo.detect()

"""
python detect_range.py --weights weights_models/best.pt --conf 0.5 --img-size 640 --source test_images --output-folder test_images --view-img --no-trace --device cpu
"""

