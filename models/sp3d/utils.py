from models.sp3d.error import NoStablePointFound
from models.sp3d.interface import INF, Box, Corner, Shape

Event = tuple[float, int, int]


def calc_no_fit_poly(
    new_shape: Shape, shapes: list[Shape], corners: list[Corner]
) -> list[Box]:
    nfps: list[Box] = []
    new_depth, new_width, new_height = new_shape
    for shape, corner in zip(shapes, corners):
        depth, width, height = shape
        back, left, bottom = corner
        box_back = back - new_depth
        box_left = left - new_width
        box_height = bottom - new_height
        box_front = back + depth
        box_right = left + width
        box_top = bottom + height
        nfps.append(
            (box_back, box_front, box_left, box_right, box_height, box_top)
        )
    return nfps


def cumsum(count: list[list[list[int]]]) -> None:
    x_size = len(count)
    y_size = len(count[0])
    z_size = len(count[0][0])
    for x in range(x_size):
        for y in range(y_size):
            for z in range(z_size - 1):
                count[x][y][z + 1] += count[x][y][z]
    for z in range(z_size):
        for x in range(x_size):
            for y in range(y_size - 1):
                count[x][y + 1][z] += count[x][y][z]
    for y in range(y_size):
        for z in range(z_size):
            for x in range(x_size - 1):
                count[x + 1][y][z] += count[x][y][z]


def calc_events(
    nfps: list[Box],
) -> tuple[list[Event], list[Event], list[Event]]:
    xs = sorted(
        [(box[0], 1, idx) for idx, box in enumerate(nfps)]
        + [(box[1], -1, idx) for idx, box in enumerate(nfps)],
        key=lambda t: (t[0], -t[1]),
    )
    ys = sorted(
        [(box[2], 1, idx) for idx, box in enumerate(nfps)]
        + [(box[3], -1, idx) for idx, box in enumerate(nfps)],
        key=lambda t: (t[0], -t[1]),
    )
    zs = sorted(
        [(box[4], 1, idx) for idx, box in enumerate(nfps)]
        + [(box[5], -1, idx) for idx, box in enumerate(nfps)],
        key=lambda t: (t[0], -t[1]),
    )
    return xs, ys, zs


def calc_overlaps(
    n_boxes: int, xs: list[Event], ys: list[Event], zs: list[Event]
) -> list[Corner]:
    x_idx_flag_to_order = {
        (idx, flag): order for order, (_, flag, idx) in enumerate(xs)
    }
    y_idx_flag_to_order = {
        (idx, flag): order for order, (_, flag, idx) in enumerate(ys)
    }
    z_idx_flag_to_order = {
        (idx, flag): order for order, (_, flag, idx) in enumerate(zs)
    }
    size = 2 * n_boxes
    count = [[[0] * size for _ in range(size)] for _ in range(size)]
    for idx in range(n_boxes):
        back_order = x_idx_flag_to_order[idx, 1]
        front_order = x_idx_flag_to_order[idx, -1]
        left_order = y_idx_flag_to_order[idx, 1]
        right_order = y_idx_flag_to_order[idx, -1]
        bottom_order = z_idx_flag_to_order[idx, 1]
        top_order = z_idx_flag_to_order[idx, -1]
        count[back_order][left_order][bottom_order] += 1
        count[front_order][left_order][bottom_order] -= 1
        count[back_order][right_order][bottom_order] -= 1
        count[back_order][left_order][top_order] -= 1
        count[back_order][right_order][top_order] += 1
        count[front_order][left_order][top_order] += 1
        count[front_order][right_order][bottom_order] += 1
        count[front_order][right_order][top_order] -= 1
    cumsum(count)
    return count


def calc_front_and_corner(
    new_shape: Shape, shapes: list[Shape], corners: list[Corner]
) -> tuple[float, Corner]:
    nfps = calc_no_fit_poly(new_shape, shapes, corners)
    n_boxes = len(nfps)
    xs, ys, zs = calc_events(nfps)
    overlaps = calc_overlaps(n_boxes, xs, ys, zs)
    for x_idx in range(1, len(xs)):
        for y_idx in range(1, len(ys)):
            for z_idx in range(1, len(zs)):
                settlable = overlaps[x_idx][y_idx][z_idx] == 0
                stable = (
                    overlaps[x_idx - 1][y_idx][z_idx] > 0
                    and overlaps[x_idx][y_idx - 1][z_idx] > 0
                    and overlaps[x_idx][y_idx][z_idx - 1] > 0
                )
                if settlable and stable:
                    x_coord = xs[x_idx][0]
                    y_coord = xs[y_idx][0]
                    z_coord = xs[z_idx][0]
                    front = x_coord + new_shape[0]
                    return front, (x_coord, y_coord, z_coord)
    raise NoStablePointFound


if __name__ == "__main__":
    shapes = [
        (300, 300, 300),
        (300, 300, 300),
        (300, 300, 300),
        (300, 300, 300),
        (300, 300, 300),
        (40, 40, 40),
        (40, 40, 40),
    ]
    corners = [
        (-300, -100, -100),
        (-100, -300, -100),
        (-100, -100, -300),
        (-100, 100, -100),
        (-100, -100, 100),
        (0, 0, 0),
        (0, 0, 40),
    ]
    new_shape = (40, 40, 40)
    front, corner = calc_front_and_corner(new_shape, shapes, corners)
    print(front, corner)
