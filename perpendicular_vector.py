"""
Find a vector perpendicular to a 3D vector.

This implementation is deterministic and handles the usual edge cases:
- rejects the zero vector because infinitely many perpendicular directions exist
  and there is no unique nonzero answer;
- rejects NaN/infinite components;
- avoids choosing a formula that can collapse to the zero vector.
"""

from __future__ import annotations

import math
from typing import Sequence


Vector3 = tuple[float, float, float]


def perpendicular_vector(v: Sequence[float], *, unit: bool = False) -> Vector3:
    """
    Return one nonzero vector perpendicular to the 3D vector v.

    Method:
    If x or y is nonzero, use (-y, x, 0). Its dot product with (x, y, z) is
    -xy + xy + 0z = 0. If x = y = 0, then the input is on the z-axis, so
    (1, 0, 0) is perpendicular to it.

    Args:
        v: 3 numeric components.
        unit: If True, normalize the returned perpendicular vector.

    Raises:
        ValueError: if v is not 3D, has non-finite values, or is the zero vector.
    """
    if len(v) != 3:
        raise ValueError("Input must contain exactly three components.")

    x, y, z = (float(component) for component in v)

    if not all(math.isfinite(component) for component in (x, y, z)):
        raise ValueError("Input components must be finite numbers.")

    if x == 0.0 and y == 0.0 and z == 0.0:
        raise ValueError("Zero vector has no unique nonzero perpendicular vector.")

    if x != 0.0 or y != 0.0:
        result = (-y, x, 0.0)
    else:
        result = (1.0, 0.0, 0.0)

    if unit:
        norm = math.sqrt(sum(component * component for component in result))
        result = tuple(component / norm for component in result)

    return result


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    """Return the 3D dot product."""
    if len(a) != 3 or len(b) != 3:
        raise ValueError("Both inputs must be 3D vectors.")
    return sum(float(ai) * float(bi) for ai, bi in zip(a, b))


if __name__ == "__main__":
    test_vectors = [
        (1, 2, 3),
        (0, 4, 5),
        (3, 0, 5),
        (0, 0, 7),
        (-2, 5, -9),
        (1e-12, 0, 1),
    ]

    for vector in test_vectors:
        p = perpendicular_vector(vector, unit=True)
        assert math.isclose(dot(vector, p), 0.0, abs_tol=1e-12), (vector, p)
        assert math.isclose(math.sqrt(dot(p, p)), 1.0, abs_tol=1e-12), p
        print(f"v={vector}, perpendicular={p}, dot={dot(vector, p):.3g}")

    for bad_vector in [(0, 0, 0), (1, 2), (1, 2, math.nan), (1, 2, math.inf)]:
        try:
            perpendicular_vector(bad_vector)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected ValueError for {bad_vector}")

    print("All tests passed.")
