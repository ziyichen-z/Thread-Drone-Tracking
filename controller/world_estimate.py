"""P1-M3-BODY-001 batch 1a-beta: the world-frame target estimator.

Proposal section 3.4: a constant-velocity Kalman filter over the ground-frame
state ``x = [x, z, vx, vz]`` (metres, metres per second), fed by the same
``controller/geolocate.py`` ground intersection the gimbal already consumes.
The measurement covariance is not a fixed constant (the charter forbids that);
it is propagated per frame from three error sources through the analytic
Jacobian of the ray/ground-plane intersection:

* ``sigma_px`` - tracker box-centre pixel noise (calibrated offline by tool 3
  and frozen as a scalar in ``config/p1-m3-body-001.json``);
* ``sigma_att_deg`` - camera attitude noise, applied as small rotations about
  the camera right/up/forward axes;
* ``sigma_y_m`` - ground-plane height noise. The plane itself is the frozen
  scenario constant ``target.route_world_m[*].y = 0.2`` (proposal section
  3.4: an explicit finite ground-plane calibration argument, never inferred
  from target-route truth).

Batch 1 scope limits (proposal section 3.4, BC-BODY1-3): no L1 coast ladder,
no covariance inflation, no T1 timer, and **no decision consumes this
estimate** - the threshold policy reads published platform state only. The
covariance is computed and logged for batch 2 and for the offline NEES/NIS
consistency analysis. The online path reads frame metadata and tracker boxes
only; it never touches ground truth (BC-BODY1-8) and never reads any
visibility or occlusion prediction artifact (BC-BODY1-4).
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from .body_planner import WorldEstimate
from .geolocate import box_ground_intersection
from .trackers import clip_box_norm


def _finite(value: Any, label: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _vector3(metadata: Mapping[str, Any], key: str) -> tuple[float, float, float]:
    raw = metadata.get(key)
    if (
        not isinstance(raw, Sequence)
        or isinstance(raw, (str, bytes))
        or len(raw) != 3
    ):
        raise ValueError(f"{key} must be a three-element vector")
    return tuple(_finite(raw[index], f"{key}[{index}]") for index in range(3))  # type: ignore[return-value]


def _cross(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def measurement_covariance_xz(
    box_norm: Sequence[float],
    metadata: Mapping[str, Any],
    ground_plane_y_m: float,
    *,
    sigma_px: float,
    sigma_att_deg: float,
    sigma_y_m: float,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Analytic-Jacobian measurement covariance of the ground intersection.

    Returns the 2x2 covariance (row-major, ``(x, z)`` rows) of
    ``box_ground_intersection(box_norm, metadata, ground_plane_y_m)`` under
    independent noise on the box pixel, the camera attitude (small rotations
    about the camera right/up/forward axes) and the ground-plane height.

    The ray math mirrors ``controller/geolocate.py`` term for term; the tests
    pin the reconstructed ray against ``GroundIntersection.ray_direction_world``.
    """
    width = int(metadata.get("width", 0))
    height = int(metadata.get("height", 0))
    if width <= 0 or height <= 0:
        raise ValueError("metadata image dimensions must be positive")
    intrinsics = metadata.get("intrinsics_px")
    if not isinstance(intrinsics, Mapping):
        raise ValueError("intrinsics_px must be an object")
    fx = _finite(intrinsics.get("fx"), "intrinsics_px.fx")
    fy = _finite(intrinsics.get("fy"), "intrinsics_px.fy")
    cx = _finite(intrinsics.get("cx"), "intrinsics_px.cx")
    cy = _finite(intrinsics.get("cy"), "intrinsics_px.cy")
    if fx <= 0.0 or fy <= 0.0:
        raise ValueError("focal lengths must be positive")

    box = clip_box_norm(box_norm)
    if box is None:
        raise ValueError("invalid_box")
    intersection = box_ground_intersection(
        box, metadata, ground_plane_y_m
    )
    origin = _vector3(metadata, "camera_position_world_m")
    right = _vector3(metadata, "camera_right_world")
    up = _vector3(metadata, "camera_up_world")
    forward = _vector3(metadata, "camera_forward_world")
    ray = intersection.ray_direction_world
    ground_y = _finite(ground_plane_y_m, "ground_plane_y_m")
    if ray[1] >= -1e-12:
        raise ValueError("measurement ray is not downward")

    # Same pixel as geolocate: box bottom-edge centre, image coordinates.
    u = (box[0] + box[2] * 0.5) * width
    v = (box[1] + box[3]) * height

    # Rebuild the unnormalized ray w = right*a - up*b' + forward (a, b' pixel
    # offsets normalized by focal length) to differentiate the normalization.
    a = (u - cx) / fx
    b = -(v - cy) / fy
    w = (
        right[0] * a + up[0] * b + forward[0],
        right[1] * a + up[1] * b + forward[1],
        right[2] * a + up[2] * b + forward[2],
    )
    norm = math.sqrt(sum(component * component for component in w))
    if norm <= 1e-12:
        raise ValueError("degenerate measurement ray")

    t = (ground_y - origin[1]) / ray[1]
    if not math.isfinite(t) or t <= 0.0:
        raise ValueError("non-positive measurement distance")

    # d ray/d var = (I - ray ray^T) (d w/d var) / |w|, then
    # d point/d var = t * d ray/d var + ray * d t/d var with
    # d t/d var = -t * (d ray_y/d var) / ray_y.
    sigma_att = math.radians(_finite(sigma_att_deg, "sigma_att_deg"))
    sigmas = (
        _finite(sigma_px, "sigma_px"),
        _finite(sigma_px, "sigma_px"),
        sigma_att,
        sigma_att,
        sigma_att,
        _finite(sigma_y_m, "sigma_y_m"),
    )
    for index, sigma in enumerate(sigmas):
        if sigma <= 0.0:
            raise ValueError(f"measurement sigma[{index}] must be positive")

    dw_du = (right[0] / fx, right[1] / fx, right[2] / fx)
    dw_dv = (-up[0] / fy, -up[1] / fy, -up[2] / fy)
    dw_variants = (
        dw_du,
        dw_dv,
        _cross(right, w),
        _cross(up, w),
        _cross(forward, w),
        None,  # ground height enters through t only
    )

    jacobian_rows = ([], [])  # x row, z row
    for dw in dw_variants:
        if dw is None:
            d_point = (ray[0] / ray[1], ray[2] / ray[1])
        else:
            d_ray = tuple(
                (dw[axis] - ray[axis] * sum(ray[k] * dw[k] for k in range(3)))
                / norm
                for axis in range(3)
            )
            d_t = -t * d_ray[1] / ray[1]
            d_point = (
                t * d_ray[0] + ray[0] * d_t,
                t * d_ray[2] + ray[2] * d_t,
            )
        jacobian_rows[0].append(d_point[0])
        jacobian_rows[1].append(d_point[1])

    covariance = [[0.0, 0.0], [0.0, 0.0]]
    for column, sigma in enumerate(sigmas):
        for row in range(2):
            for other in range(2):
                covariance[row][other] += (
                    jacobian_rows[row][column]
                    * jacobian_rows[other][column]
                    * sigma
                    * sigma
                )
    return (
        (covariance[0][0], covariance[0][1]),
        (covariance[1][0], covariance[1][1]),
    )


class WorldEstimateFilter:
    """Constant-velocity Kalman filter, state ``[x, z, vx, vz]`` (proposal 3.4).

    The filter is deterministic given its inputs: no wall clock, no I/O, no
    truth. All timestamps are the shared ``capture_monotonic_s`` clock.
    """

    def __init__(
        self,
        *,
        q_accel_mps2: float,
        sigma_px: float,
        sigma_att_deg: float,
        sigma_y_m: float,
        initial_velocity_sigma_mps: float,
    ):
        self.q_accel_mps2 = _finite(q_accel_mps2, "q_accel_mps2")
        self.sigma_px = _finite(sigma_px, "sigma_px")
        self.sigma_att_deg = _finite(sigma_att_deg, "sigma_att_deg")
        self.sigma_y_m = _finite(sigma_y_m, "sigma_y_m")
        self.initial_velocity_sigma_mps = _finite(
            initial_velocity_sigma_mps, "initial_velocity_sigma_mps"
        )
        for label, value in (
            ("q_accel_mps2", self.q_accel_mps2),
            ("sigma_px", self.sigma_px),
            ("sigma_att_deg", self.sigma_att_deg),
            ("sigma_y_m", self.sigma_y_m),
            ("initial_velocity_sigma_mps", self.initial_velocity_sigma_mps),
        ):
            if value <= 0.0:
                raise ValueError(f"{label} must be positive")
        self._mean: list[float] | None = None
        self._covariance: list[list[float]] | None = None
        self._time_s: float | None = None

    @property
    def initialized(self) -> bool:
        return self._mean is not None

    def initialize(
        self,
        box_norm: Sequence[float],
        metadata: Mapping[str, Any],
        ground_plane_y_m: float,
        at_monotonic_s: float,
    ) -> WorldEstimate:
        """Seed the filter from one measurement; position covariance = R."""
        intersection = box_ground_intersection(
            box_norm, metadata, ground_plane_y_m
        )
        covariance_xz = measurement_covariance_xz(
            box_norm,
            metadata,
            ground_plane_y_m,
            sigma_px=self.sigma_px,
            sigma_att_deg=self.sigma_att_deg,
            sigma_y_m=self.sigma_y_m,
        )
        sigma_v = self.initial_velocity_sigma_mps
        self._mean = [
            intersection.point_world_m[0],
            intersection.point_world_m[2],
            0.0,
            0.0,
        ]
        self._covariance = [
            [covariance_xz[0][0], covariance_xz[0][1], 0.0, 0.0],
            [covariance_xz[1][0], covariance_xz[1][1], 0.0, 0.0],
            [0.0, 0.0, sigma_v * sigma_v, 0.0],
            [0.0, 0.0, 0.0, sigma_v * sigma_v],
        ]
        self._time_s = _finite(at_monotonic_s, "at_monotonic_s")
        return self.estimate()

    def advance(self, at_monotonic_s: float) -> WorldEstimate:
        """Predict-only step (a frame without a usable measurement)."""
        self._require_initialized()
        self._predict(_finite(at_monotonic_s, "at_monotonic_s"))
        return self.estimate()

    def update(
        self,
        box_norm: Sequence[float],
        metadata: Mapping[str, Any],
        ground_plane_y_m: float,
        at_monotonic_s: float,
    ) -> WorldEstimate:
        """Predict to ``at_monotonic_s`` then fuse the box measurement."""
        self._require_initialized()
        at = _finite(at_monotonic_s, "at_monotonic_s")
        self._predict(at)
        intersection = box_ground_intersection(
            box_norm, metadata, ground_plane_y_m
        )
        covariance_xz = measurement_covariance_xz(
            box_norm,
            metadata,
            ground_plane_y_m,
            sigma_px=self.sigma_px,
            sigma_att_deg=self.sigma_att_deg,
            sigma_y_m=self.sigma_y_m,
        )
        z = (intersection.point_world_m[0], intersection.point_world_m[2])
        mean = self._mean
        covariance = self._covariance
        assert mean is not None and covariance is not None

        innovation = (z[0] - mean[0], z[1] - mean[1])
        s = (
            (
                covariance[0][0] + covariance_xz[0][0],
                covariance[0][1] + covariance_xz[0][1],
            ),
            (
                covariance[1][0] + covariance_xz[1][0],
                covariance[1][1] + covariance_xz[1][1],
            ),
        )
        determinant = s[0][0] * s[1][1] - s[0][1] * s[1][0]
        if determinant <= 0.0 or not math.isfinite(determinant):
            raise ValueError("innovation covariance is not positive definite")
        s_inv = (
            (s[1][1] / determinant, -s[0][1] / determinant),
            (-s[1][0] / determinant, s[0][0] / determinant),
        )
        # K (4x2) = P[:, :2] @ S^-1
        gain = [
            [
                covariance[row][0] * s_inv[0][col]
                + covariance[row][1] * s_inv[1][col]
                for col in range(2)
            ]
            for row in range(4)
        ]
        for state_index in range(4):
            mean[state_index] += (
                gain[state_index][0] * innovation[0]
                + gain[state_index][1] * innovation[1]
            )
        # Joseph form: P = (I - K H) P (I - K H)^T + K R K^T, H = [I2 0].
        kh = [[gain[row][col] if col < 2 else 0.0 for col in range(4)] for row in range(4)]
        i_kh = [
            [(1.0 if row == col else 0.0) - kh[row][col] for col in range(4)]
            for row in range(4)
        ]
        intermediate = [
            [
                sum(i_kh[row][k] * covariance[k][col] for k in range(4))
                for col in range(4)
            ]
            for row in range(4)
        ]
        updated = [
            [
                sum(intermediate[row][k] * i_kh[col][k] for k in range(4))
                for col in range(4)
            ]
            for row in range(4)
        ]
        for row in range(4):
            for col in range(4):
                updated[row][col] += (
                    gain[row][0] * covariance_xz[0][0] * gain[col][0]
                    + gain[row][0] * covariance_xz[0][1] * gain[col][1]
                    + gain[row][1] * covariance_xz[1][0] * gain[col][0]
                    + gain[row][1] * covariance_xz[1][1] * gain[col][1]
                )
        self._covariance = updated
        self._innovation = innovation
        self._nis = (
            innovation[0] * s_inv[0][0] * innovation[0]
            + innovation[0] * s_inv[0][1] * innovation[1]
            + innovation[1] * s_inv[1][0] * innovation[0]
            + innovation[1] * s_inv[1][1] * innovation[1]
        )
        return self.estimate()

    def estimate(self) -> WorldEstimate:
        self._require_initialized()
        assert self._mean is not None and self._covariance is not None
        assert self._time_s is not None
        return WorldEstimate(
            mean=tuple(self._mean),  # type: ignore[arg-type]
            covariance=tuple(tuple(row) for row in self._covariance),
            valid_at_monotonic_s=self._time_s,
        )

    @property
    def last_innovation(self) -> tuple[float, float] | None:
        return getattr(self, "_innovation", None)

    @property
    def last_nis(self) -> float | None:
        return getattr(self, "_nis", None)

    def _require_initialized(self) -> None:
        if self._mean is None:
            raise ValueError("estimator is not initialized")

    def _predict(self, at_monotonic_s: float) -> None:
        assert self._mean is not None and self._covariance is not None
        assert self._time_s is not None
        dt = at_monotonic_s - self._time_s
        if dt < 0.0:
            raise ValueError("capture_monotonic_s moved backwards")
        if dt == 0.0:
            return
        mean = self._mean
        covariance = self._covariance
        mean[0] += mean[2] * dt
        mean[1] += mean[3] * dt
        # F = [[1,0,dt,0],[0,1,0,dt],[0,0,1,0],[0,0,0,1]]
        f = (
            (1.0, 0.0, dt, 0.0),
            (0.0, 1.0, 0.0, dt),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        )
        fp = [
            [sum(f[row][k] * covariance[k][col] for k in range(4)) for col in range(4)]
            for row in range(4)
        ]
        predicted = [
            [sum(fp[row][k] * f[col][k] for k in range(4)) for col in range(4)]
            for row in range(4)
        ]
        # White-noise acceleration: Q = q^2 G G^T with
        # G = [[dt^2/2, 0], [0, dt^2/2], [dt, 0], [0, dt]] (proposal 3.4).
        q = self.q_accel_mps2
        g = ((dt * dt * 0.5, 0.0), (0.0, dt * dt * 0.5), (dt, 0.0), (0.0, dt))
        for row in range(4):
            for col in range(4):
                predicted[row][col] += (
                    q * q * (g[row][0] * g[col][0] + g[row][1] * g[col][1])
                )
        self._covariance = predicted
        self._time_s = at_monotonic_s
