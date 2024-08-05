from typing import Tuple

import cv2 as cv
import numpy as np

from .state import AppState, DisplayImageState


def transform_contour(
    contour: np.ndarray, display_image_state: DisplayImageState
) -> np.ndarray:
    shape = display_image_state.display_image_state.value.shape

    t_x = (display_image_state.resolution_state.width.value - shape[1]) // 2
    t_y = (display_image_state.resolution_state.height.value - shape[0]) // 2

    contour[:, 0] = contour[:, 0] - t_x
    contour[:, 1] = contour[:, 1] - t_y
    contour = np.rint(contour / display_image_state.scale_state.value).astype(int)
    return contour


def compute_area(
    cnt_inner: np.ndarray, cnt_outer: np.ndarray, mask: np.ndarray = None
) -> int:
    shape = mask.shape if mask is not None else np.max(cnt_outer, axis=0)[::-1]
    contour_mask = np.zeros(shape, np.uint8)

    contour_mask = cv.drawContours(contour_mask, [cnt_outer], 0, 255, -1)
    contour_mask = cv.drawContours(contour_mask, [cnt_inner], 0, 0, -1)

    if mask is not None:
        contour_mask = cv.bitwise_and(contour_mask, contour_mask, mask=mask)

    return contour_mask.sum() // 255


def mask_image(
    app_state: AppState,
):
    image = app_state.display_image_state.image_state.value
    contour = app_state.contour_state.to_numpy()
    display_image_state = app_state.display_image_state

    contour = transform_contour(contour, display_image_state)

    mask = np.zeros(image.shape[:2], np.uint8)
    mask = cv.drawContours(mask, [contour], 0, 255, -1)

    l, t, w, h = cv.boundingRect(contour)
    mask = mask[t : t + h, l : l + w]
    image = image[t : t + h, l : l + w]

    image = cv.bitwise_and(image, image, mask=mask)
    return image
