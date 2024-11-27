import time
import threading

import numpy as np
from numpy.typing import NDArray
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
import torch


class ImagePredictor:
    """
    Wrapper around the `SAM2ImagePredictor` that wraps its initialization
    and `set_image` into threads so that it does not take place on the
    main GUI thread.
    """

    def __init__(self) -> None:
        self.checkpoint = "./checkpoints/sam2.1_hiera_tiny.pt"
        self.model_cfg = "configs/sam2.1/sam2.1_hiera_t.yaml"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self._predictor = None
        self.init_thread = threading.Thread(
            target=self.init_model, name="Initialize Predictor"
        )
        self.init_thread.start()

        self.embedding_thread = None

    def init_model(self) -> None:
        torch.inference_mode()
        torch.autocast(self.device, dtype=torch.bfloat16)

        self._predictor = SAM2ImagePredictor(
            build_sam2(self.model_cfg, self.checkpoint, self.device)
        )

    def set_image(self, image: NDArray) -> None:
        self.embedding_thread = threading.Thread(
            target=self._set_image_sync, args=(image,)
        )
        self.embedding_thread.start()

    def _set_image_sync(self, image: NDArray) -> None:
        self.init_thread.join()
        self._predictor.set_image(image)

    def predict(self, point_coords: NDArray, point_labels: NDArray) -> NDArray:
        if self.embedding_thread is None:
            raise RuntimeError(
                "Cannot predict mask without computing the embedding first"
            )

        self.embedding_thread.join()

        masks, scores, _ = self._predictor.predict(
            point_coords=point_coords, point_labels=point_labels, multimask_output=True
        )
        return masks[np.argmax(scores)]


since = time.time()
IMAGE_PREDICTOR = ImagePredictor()
print(f"Building predictor took {time.time() - since}s")
