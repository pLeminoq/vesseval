import os
import time
import threading
import urllib

import cv2 as cv
import numpy as np
from numpy.typing import NDArray
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
import torch


URL_WEIGHTS = (
    "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt"
)
FILE_CHECKPOINT = "./checkpoints/sam2.1_hiera_tiny.pt"
FILE_MODEL_CFG = "configs/sam2.1/sam2.1_hiera_t.yaml"


class ImagePredictor:
    """
    Wrapper around the `SAM2ImagePredictor` that wraps its initialization
    and `set_image` into threads so that it does not take place on the
    main GUI thread.
    """

    def __init__(self) -> None:
        self.checkpoint = FILE_CHECKPOINT
        self.model_cfg = FILE_MODEL_CFG
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._predictor = None

        self.download_weights_thread = threading.Thread(
            target=self.download_weights,
            name="Download SAM Weights",
        )
        self.download_weights_thread.start()

        self.init_thread = threading.Thread(
            target=self.init_model, name="Initialize Predictor"
        )
        self.init_thread.start()

        self.embedding_thread = None
        self.embedding_lock = threading.Lock()

    def download_weights(self) -> None:
        if os.path.isfile(FILE_CHECKPOINT):
            return
        print(f"Download SAM Model ...")
        since = time.time()
        urllib.request.urlretrieve(URL_WEIGHTS, FILE_CHECKPOINT)
        print(f"Download SAM Model ... DONE in {time.time() - since:.3f}s!")

    def init_model(self) -> None:
        self.download_weights_thread.join()

        since = time.time()
        print(f"Init SAM Model ...")

        torch.inference_mode()
        torch.autocast(self.device, dtype=torch.bfloat16)

        self._predictor = SAM2ImagePredictor(
            build_sam2(self.model_cfg, self.checkpoint, self.device)
        )
        print(f"Init SAM Model ... DONE in {time.time() - since:.3f}s!")

    def set_image(self, image: NDArray) -> None:
        with self.embedding_lock:
            self.embedding_thread = threading.Thread(
                target=self._set_image_sync, args=(image,)
            )
            self.embedding_thread.start()

    def _set_image_sync(self, image: NDArray) -> None:
        with self.embedding_lock:
            if np.all(image == 0):
                print(f"Skip embedding because image is all zeros...")
                self.embedding_thread = None
                return

            since = time.time()
            print(f"Compute SAM Embedding ... {image.shape=}")

            self.init_thread.join()
            self._predictor.set_image(image)

            print(f"Compute SAM Embedding ... DONE in {time.time() - since:.3f}s!")


    def predict(
        self, point_coords: NDArray, point_labels: NDArray, box: NDArray
    ) -> NDArray:
        if self.embedding_thread is None:
            raise RuntimeError(
                "Cannot predict mask without computing the embedding first"
            )

        self.embedding_thread.join()

        since = time.time()
        print(f"Predict SAM mask ...")

        multi_mask = (
            False
            if point_coords is None or len(point_labels) > 1 or box is not None
            else True
        )
        masks, scores, _ = self._predictor.predict(
            point_coords=point_coords,
            point_labels=point_labels,
            multimask_output=multi_mask,
            box=box,
        )
        print(f"Predict SAM Mask ... DONE in {time.time() - since:.3f}s!")
        return masks[np.argmax(scores)]

    def predict_as_contour(
        self, point_coords: NDArray, point_labels: NDArray, box: NDArray
    ) -> NDArray:
        mask = self.predict(
            point_coords=point_coords, point_labels=point_labels, box=box
        )
        mask = mask.astype(np.uint8)
        cnts, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        areas = list(map(lambda cnt: cv.contourArea(cnt), cnts))
        cnt = cnts[np.argmax(areas)]
        cnt = cnt[:, 0, :]
        return cnt
