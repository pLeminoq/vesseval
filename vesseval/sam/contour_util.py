import cv2 as cv
import numpy as np


class BoundingBox:
    """
    Helper class for bounding boxes.
    """

    def __init__(self, left, top, width, height):
        """
        Initialize a bounding box with the top-left coordinate
        and its width and height.
        """
        self.left = left
        self.right = left + width

        self.top = top
        self.bottom = top + height

        self.width = width
        self.height = height

    def __str__(self):
        return (
            str(self.left)
            + ", "
            + str(self.top)
            + " x "
            + str(self.width)
            + ", "
            + str(self.height)
        )

    def __repr__(self):
        return self.__str__()

    def slice(self):
        return (slice(self.top, self.bottom), slice(self.left, self.right))

    def union(self, other):
        """
        Create a union of two bounding boxes.
        """
        left = min(self.left, other.left)
        right = max(self.right, other.right)

        top = min(self.top, other.top)
        bottom = max(self.bottom, other.bottom)

        return BoundingBox(left, top, right - left, bottom - top)

    def intersection(self, other):
        """
        Create the intersection of two bounding boxes.

        raise: ValueError if the intersection is empty
        """
        left = max(self.left, other.left)
        right = min(self.right, other.right)

        top = max(self.top, other.top)
        bottom = min(self.bottom, other.bottom)

        if left >= right or top >= bottom:
            raise ValueError()

        return BoundingBox(left, top, right - left, bottom - top)

    def intersects(self, other):
        try:
            self.intersection(other)
            return True
        except:
            return False

    def tl(self):
        return np.array((self.top, self.left))

    def tr(self):
        return np.array((self.top, self.left + self.width))

    def bl(self):
        return np.array((self.top + self.height, self.left))

    def br(self):
        return np.array((self.top + self.height, self.left + self.width))

    def corner_points(self):
        return [self.tl(), self.tr(), self.br(), self.bl()]


class Contour:

    def __init__(self, points):
        self.points = points

    def get_bounding_box(self):
        return BoundingBox(*cv.boundingRect(self.points))

    def area(self):
        return cv.contourArea(self.points)

    def intersection_count(self, other):
        bb = self.get_bounding_box()
        bb_other = other.get_bounding_box()

        # quick check if bounding boxes do not overlap
        if not bb.intersects(bb_other):
            return 0

        bb_union = bb.union(bb_other)
        offset = -bb_union.tl()[::-1]

        img_cnt = np.zeros((bb_union.height, bb_union.width), np.uint8)
        cv.drawContours(
            img_cnt, [self.points], -1, color=255, thickness=-1, offset=offset
        )

        img_cnt_other = np.zeros((bb_union.height, bb_union.width), np.uint8)
        cv.drawContours(
            img_cnt_other, [other.points], -1, color=255, thickness=-1, offset=offset
        )

        return np.logical_and(img_cnt, img_cnt_other).sum()

    @classmethod
    def from_mask(cls, mask):
        mask = mask.astype(np.uint8)
        cnts, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        areas = list(map(lambda cnt: cv.contourArea(cnt), cnts))
        cnt = cnts[np.argmax(areas)]
        cnt = cnt[:, 0, :]
        return cls(cnt)


if __name__ == "__main__":
    cnt1 = Contour(np.array([[10, 10], [100, 10], [100, 100], [10, 100]]))
    cnt2 = Contour(np.array([[50, 70], [150, 70], [150, 150], [50, 150]]))

    bb1 = cnt1.get_bounding_box()
    bb2 = cnt2.get_bounding_box()
    bb_union = bb2.union(bb1)

    img1 = np.zeros((bb_union.height, bb_union.width), np.uint8)
    img2 = np.zeros((bb_union.height, bb_union.width), np.uint8)

    cv.drawContours(
        img1, [cnt1.points], -1, color=255, thickness=-1, offset=-bb_union.tl()
    )
    cv.drawContours(
        img2, [cnt2.points], -1, color=255, thickness=-1, offset=-bb_union.tl()
    )

    cv.imshow("Test", cv.addWeighted(img1, 0.5, img2, 0.5, 0.0))
    cv.waitKey(0)
