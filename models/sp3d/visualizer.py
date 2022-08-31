import math

import cv2
import numpy as np

from models.sp3d.interface import Corner, Image, Shape


class Visulalizer:
    def __init__(self, container_shape: Shape) -> None:
        self.container_shape = container_shape
        cos15 = math.cos(math.pi / 12)
        sin15 = math.sin(math.pi / 12)
        container_depth, container_width, container_height = self.container_shape
        self.image_width = cos15 * (container_depth + container_width)
        self.image_height = container_height + sin15 * (container_depth + container_width)
        self.image_size = max(self.image_width, self.image_height)
        self.origin_pos = (cos15 * container_width, container_height)
        self.depth_vector = (cos15 * container_depth, sin15 * container_depth)
        self.width_vector = (-cos15 * container_width, sin15 * container_width)
        self.height_vecotr = (0.0, -container_height)
        self.container_depth = container_depth
        self.container_width = container_width
        self.container_height = container_height

    def rescale(self, x: float, size: int, padding: int) -> int:
        return int(size * x / self.image_size) + padding

    def corner_to_pos(self, corner: Corner, size: int, padding: int) -> tuple[int, int]:
        back, left, bottom = corner
        ox, oy = self.origin_pos
        vdx, vdy = self.depth_vector
        vwx, vwy = self.width_vector
        vhx, vhy = self.height_vecotr
        x = (
            ox
            + back * vdx / self.container_depth
            + left * vwx / self.container_width
            + bottom * vhx / self.container_height
        )
        y = (
            oy
            + back * vdy / self.container_depth
            + left * vwy / self.container_width
            + bottom * vhy / self.container_height
        )
        return self.rescale(x, size, padding), self.rescale(y, size, padding)

    def draw_box(
        self, image: Image, corner: Corner, shape: Shape, size: int, padding: int
    ) -> None:
        back, left, bottom = corner
        depth, width, height = shape
        o = self.corner_to_pos((back, left, bottom), size, padding)
        d = self.corner_to_pos((back + depth, left, bottom), size, padding)
        w = self.corner_to_pos((back, left + width, bottom), size, padding)
        h = self.corner_to_pos((back, left, bottom + height), size, padding)
        wh = self.corner_to_pos((back, left + width, bottom + height), size, padding)
        dh = self.corner_to_pos((back + depth, left, bottom + height), size, padding)
        dw = self.corner_to_pos((back + depth, left + width, bottom), size, padding)
        dwh = self.corner_to_pos((back + depth, left + width, bottom + height), size, padding)
        cv2.line(image, o, d, (192, 192, 192), 1, cv2.LINE_AA)
        cv2.line(image, o, w, (192, 192, 192), 1, cv2.LINE_AA)
        cv2.line(image, o, h, (192, 192, 192), 1, cv2.LINE_AA)
        cv2.line(image, d, dh, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.line(image, d, dw, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.line(image, w, dw, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.line(image, w, wh, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.line(image, h, wh, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.line(image, h, dh, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.line(image, wh, dwh, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.line(image, dh, dwh, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.line(image, dw, dwh, (0, 0, 0), 1, cv2.LINE_AA)

    def render(self, size: int, padding: int) -> Image:
        image = np.full(
            (
                self.rescale(self.image_height, size, padding) + padding,
                self.rescale(self.image_width, size, padding) + padding,
                3
            ),
            (255, 255, 255),
            np.uint8
        )
        self.draw_box(image, (0.0, 0.0, 0.0), self.container_shape, size, padding)
        return image
