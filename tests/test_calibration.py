import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from utils.calibration import get_perspective_transform, transform_point


def test_transform_returns_array():
    image_pts = [[100, 100], [400, 100], [400, 400], [100, 400]]
    world_pts = [[0, 0], [10, 0], [10, 10], [0, 10]]
    matrix = get_perspective_transform(image_pts, world_pts)
    assert matrix.shape == (3, 3), "Transform matrix should be 3x3"


def test_transform_point():
    image_pts = [[100, 100], [400, 100], [400, 400], [100, 400]]
    world_pts = [[0, 0], [10, 0], [10, 10], [0, 10]]
    matrix = get_perspective_transform(image_pts, world_pts)
    result = transform_point([250, 250], matrix)
    assert len(result) == 2, "Transformed point should have 2 coordinates"


if __name__ == '__main__':
    test_transform_returns_array()
    test_transform_point()
    print("All calibration tests passed.")
