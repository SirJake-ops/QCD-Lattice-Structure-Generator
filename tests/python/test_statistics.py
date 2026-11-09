import numpy as np
import pytest
from analysis.statistics import (covariance, integrated_autocorrelation, jackknife_means,
                                 make_blocks, plateau, response, split_rhat)
from analysis.analyze import cornell_fit


def test_correlated_chain_blocking_inflates_uncertainty():
    rng = np.random.default_rng(101)
    x = np.zeros((4, 6000, 1))
    for t in range(1, 6000): x[:, t, 0] = .8 * x[:, t-1, 0] + rng.normal(size=4)
    tau = integrated_autocorrelation(x[0, :, 0])
    assert 3 < tau < 6.5  # exact AR(1): tau=(1+rho)/(2*(1-rho))=4.5
    blocks = make_blocks(x, 50)
    error = np.sqrt(covariance(jackknife_means(blocks))[0, 0])
    naive = x.std() / np.sqrt(x.size)
    assert 2 < error / naive < 4
    assert split_rhat(x[:, :, 0]) < 1.01
    x[0, :, 0] += 2
    assert split_rhat(x[:, :, 0]) > 1.1


def test_correlated_plateau_and_nonpositive_estimates():
    rng = np.random.default_rng(17)
    time = np.arange(1, 7)
    # Explicit synthetic fixture: exact potential .3 with correlated block fluctuations.
    blocks = np.exp(-.3 * time)[None, :] * (1 + .015 * rng.normal(size=(80, 6)))
    fit = plateau(blocks, 2, 4)
    assert abs(fit["value"] - .3) < 4 * fit["error"]
    assert fit["error"] > 0
    assert len(fit["replicas"]) == 80
    blocks[:, 2] = -1
    with pytest.raises(ValueError, match="Nonpositive"): plateau(blocks, 2, 4)


def test_flux_recomputes_joint_ratio_and_vacuum_subtraction():
    rng = np.random.default_rng(21)
    w = rng.uniform(.6, .9, 80)
    s = rng.uniform(.1, .3, (80, 2))
    ws = w[:, None] * s + np.array([.03, -.02])
    blocks = np.column_stack((w, s, ws))
    values, error = response(blocks, 2)
    expected = ws.mean(axis=0) / w.mean() - s.mean(axis=0)
    np.testing.assert_allclose(values, expected)
    assert np.all(error > 0)
    assert np.max(np.abs(values - (ws / w[:, None] - s).mean(axis=0))) > 1e-5
    with pytest.raises(ValueError): response(np.column_stack((w - 1, s, ws)), 2)


def test_cornell_correlated_fit_and_insufficient_range():
    n = np.arange(1., 6.)
    y = .8 - .3/n + .15*n
    cov = .0001 * np.eye(5) + .00002 * np.ones((5,5))
    fit = cornell_fit(n, y, cov)
    assert fit["status"] == "fitted approximation"
    np.testing.assert_allclose(list(fit["coefficients"].values()), [.8, .3, .15], atol=1e-10)
    assert cornell_fit(n[:2], y[:2], cov[:2,:2])["status"] == "unavailable"
