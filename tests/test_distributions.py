"""Deterministic broad distribution checks; no third-party statistics library.

5000 points per locale: thresholds are loose enough for a correct generator,
but reject common regressions (uniform normals, shared field RNG, flat latitude).
"""

import bisect
import math
import statistics

import pytest


pytestmark = [pytest.mark.database, pytest.mark.statistical]


@pytest.mark.parametrize("locale", ["en_US", "de_DE"])
@pytest.mark.parametrize("field,mean,sd", [("height_cm", 172, 10), ("weight_kg", 75, 12)])
def test_normal_moments_and_interval_frequencies(distribution_rows, locale, field, mean, sd):
    values = [row[field] for row in distribution_rows(locale)]
    sample_mean, sample_sd = statistics.mean(values), statistics.stdev(values)
    standardized = [(value - mean) / sd for value in values]
    counts = [0] * 6
    for value in standardized:
        counts[bisect.bisect_right((-2, -1, 0, 1, 2), value)] += 1
    # Independent theoretical N(0,1) interval probabilities, not generator code.
    probabilities = (0.02275013, 0.13590512, 0.34134475, 0.34134475, 0.13590512, 0.02275013)
    chi_squared = sum(
        (actual - len(values) * probability) ** 2 / (len(values) * probability)
        for actual, probability in zip(counts, probabilities)
    )
    print(f"\n{locale} {field}: n={len(values)}, mean={sample_mean:.4f}, sd={sample_sd:.4f}, bins={counts}, chi2={chi_squared:.3f}")
    assert abs(sample_mean - mean) < 0.08 * sd
    assert 0.93 * sd < sample_sd < 1.07 * sd
    assert chi_squared < 40, (locale, field, counts, chi_squared)


@pytest.mark.parametrize("locale", ["en_US", "de_DE"])
def test_sphere_is_equal_area_instead_of_uniform_latitude(distribution_rows, locale):
    rows = distribution_rows(locale)
    z_values = [math.sin(math.radians(row["latitude"])) for row in rows]
    longitudes = [row["longitude"] for row in rows]
    assert all(-1 <= z <= 1 for z in z_values)
    assert all(-180 <= longitude <= 180 for longitude in longitudes)
    for name, values, low, high in (("sin(latitude)", z_values, -1, 1), ("longitude", longitudes, -180, 180)):
        counts = [0] * 10
        for value in values:
            index = min(9, int(10 * (value - low) / (high - low)))
            counts[index] += 1
        expected = len(values) / 10
        chi_squared = sum((count - expected) ** 2 / expected for count in counts)
        print(f"\n{locale} {name}: mean={statistics.mean(values):.5f}, bins={counts}, chi2={chi_squared:.3f}")
        assert chi_squared < 45, (locale, name, counts, chi_squared)
    assert abs(statistics.mean(z_values)) < 0.04
    assert abs(statistics.mean(z * z for z in z_values) - 1 / 3) < 0.025
    assert abs(statistics.correlation(z_values, longitudes)) < 0.07


@pytest.mark.parametrize("locale", ["en_US", "de_DE"])
def test_normal_fields_have_independent_random_streams(distribution_rows, locale):
    rows = distribution_rows(locale)
    height = [row["height_cm"] for row in rows]
    weight = [row["weight_kg"] for row in rows]
    assert abs(statistics.correlation(height, weight)) < 0.07
