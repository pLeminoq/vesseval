from typing import Tuple

import cv2 as cv
import numpy as np

from .state import ContourState, DisplayImageState


def compute_contours(mask: np.ndarray, angle_step: int = 10):
    cnt_inner = []
    cnt_outer = []

    center = np.array(mask.shape[::-1]) / 2
    for angle_deg in np.arange(0, 360, angle_step):
        angle = np.deg2rad(angle_deg)
        direction = np.array([np.cos(angle), np.sin(angle)]) * max(mask.shape)

        _line = np.zeros(mask.shape, np.uint8)
        _line = cv.line(
            _line,
            tuple(center.astype(int)),
            tuple((center + direction).astype(int)),
            255,
            1,
        )
        _line = cv.bitwise_and(mask, mask, mask=_line)
        left, top, width, height = cv.boundingRect(_line)
        if width == 0 and height == 0:
            continue

        if 0 <= angle_deg < 90:
            cnt_inner.append((left, top))
            cnt_outer.append((left + width, top + height))
        elif 90 <= angle_deg < 180:
            cnt_inner.append((left + width, top))
            cnt_outer.append((left, top + height))
        elif 180 <= angle_deg < 270:
            cnt_inner.append((left + width, top + height))
            cnt_outer.append((left, top))
        else:
            cnt_inner.append((left, top + height))
            cnt_outer.append((left + width, top))

    return np.array(cnt_inner), np.array(cnt_outer)


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
    display_image: DisplayImageState,
    contour: ContourState,
):
    image = display_image.image_state.value
    contour = transform_contour(contour.to_numpy(), display_image)

    mask = np.zeros(image.shape[:2], np.uint8)
    mask = cv.drawContours(mask, [contour], 0, 255, -1)

    l, t, w, h = cv.boundingRect(contour)
    mask = mask[t : t + h, l : l + w]
    image = image[t : t + h, l : l + w]

    image = cv.bitwise_and(image, image, mask=mask)
    return image


def compute_thickness(contour_inner: np.ndarray, contour_outer: np.ndarray) -> float:
    """
    Compute the thickness of a cell layer of a vessel.

    The thickness is estimated as the average closest distance of each point
    in `contour_inner` to `contour_outer`.

    Parameters
    ----------
    contour_inner: np.ndarray
        contour following the inner border of the cell layer of the vessel
    contour_outer: np.ndarray
        contour following the outer border of the cell layer of the vessel

    Returns
    -------
    float
        the estimated distance in pixels
    """
    # format contour as list of points with integer coordinates
    points = [tuple([int(v) for v in point]) for point in contour_inner]
    # compute closest distance from each point in `contour_inner` to `contour_outer`
    distances = list(
        map(
            lambda point: cv.pointPolygonTest(contour_outer, point, measureDist=True),
            points,
        )
    )
    # estimate thickness as the absolute average distance
    return np.average(np.absolute(distances))
