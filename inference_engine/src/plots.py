from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def set_style() -> None:
    sns.set_theme(style="whitegrid", context="notebook", font_scale=1.05)
    plt.rcParams["figure.figsize"] = (10, 5)
    plt.rcParams["savefig.dpi"] = 120
    plt.rcParams["axes.titlesize"] = 12


def save_correlation_heatmap(corr: pd.DataFrame, path: Path, title: str = "Correlation") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(max(8, corr.shape[0] * 0.5), max(6, corr.shape[0] * 0.45)))
    sns.heatmap(corr, ax=ax, cmap="RdBu_r", center=0, annot=len(corr) <= 12, fmt=".2f")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def save_violin(
    df: pd.DataFrame,
    value_col: str,
    group_col: str,
    path: Path,
    title: str | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    order = sorted(df[group_col].dropna().unique().tolist())
    sns.violinplot(data=df, x=group_col, y=value_col, order=order, ax=ax, inner="box", cut=0)
    ax.set_title(title or f"{value_col} by {group_col}")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def save_pca_variance(explained: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(1, len(explained) + 1)
    ax.bar(x, explained)
    ax.set_xlabel("Principal component")
    ax.set_ylabel("Explained variance ratio")
    ax.set_title("PCA explained variance")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
