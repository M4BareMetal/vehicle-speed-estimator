import cv2
import numpy as np


def get_perspective_transform(image_points, world_points):
    """
    Build a 3x3 perspective transform matrix from 4 image points
    to 4 world points.
    """
    image_pts = np.array(image_points, dtype=np.float32)
    world_pts = np.array(world_points, dtype=np.float32)

    # Ensure correct shapes: (4, 2)
    image_pts = image_pts.reshape(4, 2)
    world_pts = world_pts.reshape(4, 2)

    matrix = cv2.getPerspectiveTransform(image_pts, world_pts)
    return matrix


def transform_point(point, matrix):
    """
    Apply perspective transform to a single (x, y) point.
    """
    # Normalize point to float32 and correct shape
    p = np.array(point, dtype=np.float32).reshape(1, 1, 2)
    transformed = cv2.perspectiveTransform(p, matrix)
    return transformed[0, 0]