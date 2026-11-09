"""Correlated estimators from equal-length, independently seeded chains."""
from __future__ import annotations

import numpy as np
from scipy.stats import chi2


def integrated_autocorrelation(x: np.ndarray) -> float:
    """Initial positive paired autocovariances; return tau >= 1/2."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    x = x - x.mean()
    if n < 4 or np.dot(x, x) < 1e-28:
        return .5
    size = 1 << (2 * n - 1).bit_length()
    f = np.fft.rfft(x, n=size)
    ac = np.fft.irfft(f * f.conj(), n=size)[:n // 2]
    ac /= np.arange(n, n - len(ac), -1)
    ac /= ac[0]
    tau = .5
    for lag in range(1, len(ac) - 1, 2):
        pair = ac[lag] + ac[lag + 1]
        if pair <= 0:
            break
        tau += pair
        if lag > 6 * tau:
            break
    return max(.5, float(tau))


def split_rhat(chains: np.ndarray) -> float:
    chains = np.asarray(chains, float)
    n = chains.shape[1] // 2
    if n < 4 or chains.shape[0] < 2:
        return float("inf")
    split = np.concatenate((chains[:, :n], chains[:, -n:]))
    w = np.var(split, axis=1, ddof=1).mean()
    b = n * np.var(split.mean(axis=1), ddof=1)
    if w < 1e-28:
        return 1. if b < 1e-28 else float("inf")
    return float(np.sqrt(((n - 1) * w / n + b / n) / w))


def make_blocks(chains: np.ndarray, block_size: int) -> np.ndarray:
    nblocks = chains.shape[1] // block_size
    if nblocks < 2:
        raise ValueError("At least two complete blocks per chain required")
    return chains[:, :nblocks * block_size].reshape(
        chains.shape[0], nblocks, block_size, -1).mean(axis=2).reshape(-1, chains.shape[-1])


def jackknife_means(blocks: np.ndarray) -> np.ndarray:
    return (blocks.sum(axis=0) - blocks) / (len(blocks) - 1)


def covariance(replicates: np.ndarray) -> np.ndarray:
    centered = replicates - replicates.mean(axis=0)
    return (len(replicates) - 1) / len(replicates) * centered.T @ centered


def ratios(loops: np.ndarray) -> np.ndarray:
    if np.any(loops <= 0):
        raise ValueError("Nonpositive Wilson loop in central or resampled estimate")
    return np.log(loops[..., :-1] / loops[..., 1:])


def _gls(y: np.ndarray, cov: np.ndarray) -> tuple[float, float, float]:
    if not np.all(np.isfinite(cov)) or np.linalg.matrix_rank(cov) < len(y):
        raise ValueError("Singular plateau covariance")
    if np.linalg.cond(cov) > 1e10:
        raise ValueError("Ill-conditioned plateau covariance")
    precision = np.linalg.inv(cov)
    one = np.ones(len(y))
    denom = one @ precision @ one
    if denom <= 0:
        raise ValueError("Nonpositive plateau precision")
    value = float(one @ precision @ y / denom)
    statistic = float((y - value) @ precision @ (y - value))
    return value, statistic / max(1, len(y) - 1), float(chi2.sf(statistic, max(1, len(y) - 1)))


def plateau(blocks: np.ndarray, lo: int, hi: int) -> dict:
    """Fit log(W(t)/W(t+1)), lo..hi inclusive; recompute GLS in each delete-block sample.

    Inner delete-block replicates recompute the covariance within each outer
    replicate. No chains are joined before forming contiguous blocks.
    """
    if hi - lo < 1:
        raise ValueError("Plateau fit needs at least two consecutive effective masses")
    window = slice(lo - 1, hi)
    estimates = ratios(jackknife_means(blocks))
    central = ratios(blocks.mean(axis=0))
    cov = covariance(estimates)
    value, quality, pvalue = _gls(central[window], cov[window, window])
    samples = []
    for index in range(len(blocks)):
        reduced = np.delete(blocks, index, axis=0)
        inner = ratios(jackknife_means(reduced))[:, window]
        y = ratios(reduced.mean(axis=0))[window]
        samples.append(_gls(y, covariance(inner))[0])
    samples = np.asarray(samples)[:, None]
    return dict(value=value, error=float(np.sqrt(covariance(samples)[0, 0])),
                chi2_dof=quality, pvalue=pvalue, replicas=samples[:, 0],
                effective_mass=central.tolist(), effective_mass_error=np.sqrt(np.diag(cov)).tolist())


def response(blocks: np.ndarray, cells: int) -> tuple[np.ndarray, np.ndarray]:
    """Columns [W,s(cell...),Ws(cell...)]; preserve joint samples in ratio."""
    def estimator(means):
        if np.any(means[..., 0] <= 0):
            raise ValueError("Nonpositive source Wilson loop")
        return means[..., 1 + cells:] / means[..., :1] - means[..., 1:1 + cells]
    means = jackknife_means(blocks)
    werr = np.sqrt(covariance(means[:, :1])[0, 0])
    if blocks[:, 0].mean() <= 3 * werr:
        raise ValueError("Source Wilson loop denominator is not resolved at 3 sigma")
    central = estimator(blocks.mean(axis=0))
    errors = np.sqrt(np.diag(covariance(estimator(means))))
    return central, errors
