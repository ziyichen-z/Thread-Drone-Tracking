"""P1-ENG-ACQ-001 §3.3（K1/K3）：由帧元数据位姿算纯旋转单应 H = K·R_Δ·K⁻¹ 并施加到轨迹预测框。

只读**该帧自身**的平台元数据（`camera_rotation_xyzw`、`intrinsics_px`），不读任何目标真值。
相机约定与 `controller.reanchor.world_los` / `controller.geolocate` 相同：四元数把单位轴
x/y/z 分别转到 `camera_right/up/forward_world`；像素 u 向右、v 向下，故相机系 (x, y_up, z)
到齐次像素的矩阵是 K' = [[fx, 0, cx], [0, -fy, cy], [0, 0, 1]]。

相邻处理帧 t−1 → t：世界方向 d = R₁·K'⁻¹·p₁，t 帧相机系坐标 R₂ᵀ·d，所以
H = K'₂ · R₂ᵀ · R₁ · K'₁⁻¹（纯旋转、与景深无关；机身平移在 v1 忽略）。

施加方式（AC-5 合成测试择定）：对预测框四角施加 3×3 再取 AABB（`warp_box_xyxy`）；
退化的 2×3（丢弃透视行）在大角度扫视下误差超过 0.5 px，只作对照（`affine_part`）。
纯 Python（无 numpy 依赖）；numpy 数组的 KF 状态改写在 `controller.det_assoc_tracker` 里做。
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

Matrix3 = tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]

GMC_SOURCES: tuple[str, ...] = ("pose", "optflow", "none", "pose-center", "pose-aabb")
#: P1-ENG-CAPTURE-001 C2：由位姿单应补偿的来源；`pose` ≡ `pose-aabb`（四角 AABB，旧日志可解析），
#: `pose-center` 只移中心（宽高与宽高速度不变）。
POSE_SOURCES: tuple[str, ...] = ("pose", "pose-center", "pose-aabb")


def is_pose_source(source: str) -> bool:
    return source in POSE_SOURCES
IDENTITY: Matrix3 = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def _quaternion(metadata: Mapping[str, Any]) -> tuple[float, float, float, float]:
    raw = metadata.get("camera_rotation_xyzw")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or len(raw) != 4:
        raise ValueError("camera_rotation_xyzw must contain four values")
    x, y, z, w = (_finite(v, "camera_rotation_xyzw") for v in raw)
    norm = math.sqrt(x * x + y * y + z * z + w * w)
    if not 0.999 <= norm <= 1.001:
        raise ValueError("camera quaternion is not normalized")
    return x / norm, y / norm, z / norm, w / norm


def rotation_matrix(metadata: Mapping[str, Any]) -> Matrix3:
    """列 = (right, up, forward) 的世界方向（四元数转单位轴，与 `validate_camera_basis` 同一约定）。"""
    x, y, z, w = _quaternion(metadata)
    # 标准四元数 → 旋转矩阵（作用于列向量）。
    return (
        (1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
        (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
        (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)),
    )


def intrinsics_matrix(metadata: Mapping[str, Any]) -> Matrix3:
    intrinsics = metadata.get("intrinsics_px")
    if not isinstance(intrinsics, Mapping):
        raise ValueError("intrinsics_px must be an object")
    fx = _finite(intrinsics.get("fx"), "intrinsics_px.fx")
    fy = _finite(intrinsics.get("fy"), "intrinsics_px.fy")
    cx = _finite(intrinsics.get("cx"), "intrinsics_px.cx")
    cy = _finite(intrinsics.get("cy"), "intrinsics_px.cy")
    if fx <= 0.0 or fy <= 0.0:
        raise ValueError("focal lengths must be positive")
    return ((fx, 0.0, cx), (0.0, -fy, cy), (0.0, 0.0, 1.0))


def _matmul(a: Matrix3, b: Matrix3) -> Matrix3:
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))  # type: ignore[return-value]


def _transpose(a: Matrix3) -> Matrix3:
    return tuple(tuple(a[j][i] for j in range(3)) for i in range(3))  # type: ignore[return-value]


def _inverse_intrinsics(k: Matrix3) -> Matrix3:
    fx, cx = k[0][0], k[0][2]
    fy, cy = k[1][1], k[1][2]
    return ((1.0 / fx, 0.0, -cx / fx), (0.0, 1.0 / fy, -cy / fy), (0.0, 0.0, 1.0))


def pose_homography(previous: Mapping[str, Any], current: Mapping[str, Any]) -> Matrix3:
    """t−1 帧像素 → t 帧像素的纯旋转单应（归一化使 H[2][2] = 1）。"""
    h = _matmul(
        _matmul(intrinsics_matrix(current), _transpose(rotation_matrix(current))),
        _matmul(rotation_matrix(previous), _inverse_intrinsics(intrinsics_matrix(previous))),
    )
    scale = h[2][2]
    if not math.isfinite(scale) or abs(scale) < 1e-12:
        raise ValueError("degenerate homography")
    return tuple(tuple(value / scale for value in row) for row in h)  # type: ignore[return-value]


def rotation_angle_deg(previous: Mapping[str, Any], current: Mapping[str, Any]) -> float:
    """相邻帧相机姿态夹角（度）。"""
    a = _quaternion(previous)
    b = _quaternion(current)
    dot = abs(sum(x * y for x, y in zip(a, b)))
    return math.degrees(2.0 * math.acos(max(-1.0, min(1.0, dot))))


def map_point(h: Matrix3, u: float, v: float) -> tuple[float, float] | None:
    """像素点经 H 映射；落到相机背后（w ≤ 0）时返回 None。"""
    x = h[0][0] * u + h[0][1] * v + h[0][2]
    y = h[1][0] * u + h[1][1] * v + h[1][2]
    w = h[2][0] * u + h[2][1] * v + h[2][2]
    if not math.isfinite(w) or w <= 1e-9:
        return None
    return x / w, y / w


def affine_part(h: Matrix3) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """退化的 2×3（丢弃透视行，库 `multi_gmc` 形态）；只作 AC-5 对照。"""
    return (h[0], h[1])


def map_point_affine(a: Sequence[Sequence[float]], u: float, v: float) -> tuple[float, float]:
    return a[0][0] * u + a[0][1] * v + a[0][2], a[1][0] * u + a[1][1] * v + a[1][2]


def warp_box_xyxy(h: Matrix3, box: Sequence[float]) -> tuple[float, float, float, float] | None:
    """像素 xyxy 框四角施加 H 再取 AABB；任一角落到相机背后 → None（调用方保留原框）。"""
    x1, y1, x2, y2 = (float(v) for v in box)
    corners = [map_point(h, u, v) for u, v in ((x1, y1), (x2, y1), (x1, y2), (x2, y2))]
    if any(c is None for c in corners):
        return None
    xs = [c[0] for c in corners]  # type: ignore[index]
    ys = [c[1] for c in corners]  # type: ignore[index]
    return min(xs), min(ys), max(xs), max(ys)


def jacobian(h: Matrix3, u: float, v: float) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """H 在 (u, v) 处的 2×2 雅可比（用于把 KF 速度随映射转向）。"""
    w = h[2][0] * u + h[2][1] * v + h[2][2]
    if not math.isfinite(w) or w <= 1e-9:
        return None
    x = h[0][0] * u + h[0][1] * v + h[0][2]
    y = h[1][0] * u + h[1][1] * v + h[1][2]
    return (
        ((h[0][0] * w - x * h[2][0]) / (w * w), (h[0][1] * w - x * h[2][1]) / (w * w)),
        ((h[1][0] * w - y * h[2][0]) / (w * w), (h[1][1] * w - y * h[2][1]) / (w * w)),
    )


def project_world_point(point: Sequence[float], metadata: Mapping[str, Any]) -> tuple[float, float] | None:
    """世界点 → 像素（相机前方才有值）；供合成测试与位姿自检使用。"""
    position = metadata.get("camera_position_world_m")
    if not isinstance(position, Sequence) or len(position) != 3:
        raise ValueError("camera_position_world_m must contain three values")
    r = rotation_matrix(metadata)
    k = intrinsics_matrix(metadata)
    delta = [float(point[i]) - float(position[i]) for i in range(3)]
    camera = [sum(r[row][col] * delta[row] for row in range(3)) for col in range(3)]  # Rᵀ·delta
    if camera[2] <= 1e-9:
        return None
    return (
        k[0][0] * camera[0] / camera[2] + k[0][2],
        k[1][1] * camera[1] / camera[2] + k[1][2],
    )
