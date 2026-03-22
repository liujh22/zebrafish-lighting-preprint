from pathlib import Path

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    geom_point,
    geom_smooth,
    ggplot,
    labs,
    scale_color_manual,
    scale_color_gradientn,
    theme,
    theme_minimal,
    element_blank,
    element_line,
)
from scipy.stats import pearsonr
from sklearn.decomposition import PCA


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RADIANCE_FILE = PROJECT_ROOT / "Box Radiance.csv"
FEATURE_FILE = PROJECT_ROOT / "Analyzed_data" / "wt_2025_all_Connected_bout_features_strict.csv"
STAT_DIR = PROJECT_ROOT / "Statistics"
PLOT_DIR = PROJECT_ROOT / "Plots_folder" / "radiance_effect"


def build_parameter_list(df: pd.DataFrame) -> list[str]:
    parameter_candidates = [
        ["rot_bout"],
        ["spd_peak"],
        ["displ_swim"],
        ["WHM"],
        ["pre_IBI_time"],
        ["rot_total"],
    ]
    params: list[str] = []
    for cand in parameter_candidates:
        found = next((x for x in cand if x in df.columns), None)
        if found is not None:
            params.append(found)
    return params


def run_pca(sub_df: pd.DataFrame, label: str, params: list[str]):
    use_cols = [c for c in params if c in sub_df.columns]
    if len(use_cols) < 2:
        return None

    dat = sub_df[use_cols + ["radiance_mW", "ztime"]].dropna().copy()
    n = len(dat)
    if n < 3:
        return None
    if dat["radiance_mW"].nunique() < 2:
        return None

    sds = dat[use_cols].std(ddof=1)
    keep = sds[sds > 0].index.tolist()
    if len(keep) < 2:
        return None

    x = dat[keep].to_numpy(dtype=float)
    x = (x - x.mean(axis=0)) / x.std(axis=0, ddof=1)

    pca = PCA()
    pcs = pca.fit_transform(x)
    pc_cols = [f"PC{i+1}" for i in range(pcs.shape[1])]
    scores = pd.DataFrame(pcs, columns=pc_cols)
    scores["radiance_mW"] = dat["radiance_mW"].to_numpy()
    scores["ztime"] = dat["ztime"].to_numpy()
    scores["subset"] = label

    evr = pca.explained_variance_ratio_
    rows = []
    for i, pc_name in enumerate(pc_cols):
        r, p = pearsonr(scores[pc_name], dat["radiance_mW"])
        rows.append(
            {
                "subset": label,
                "pc": pc_name,
                "explained_variance_ratio": float(evr[i]),
                "pearson_r_with_radiance": float(r),
                "pearson_p": float(p),
                "n": int(n),
            }
        )
    res = pd.DataFrame(rows)

    loadings = pd.DataFrame(pca.components_.T, columns=pc_cols)
    loadings.insert(0, "parameter", keep)

    return {"res": res, "loadings": loadings, "scores": scores, "evr": evr}


def plot_pc12(scores_df: pd.DataFrame, evr: np.ndarray, label: str, out_file: Path):
    if not {"PC1", "PC2", "radiance_mW"}.issubset(scores_df.columns):
        return
    if len(scores_df) < 2:
        return

    p = (
        ggplot(scores_df, aes(x="PC1", y="PC2", color="radiance_mW"))
        + geom_point(size=2.2, alpha=0.95)
        + scale_color_gradientn(colors=["#2c7bb6", "#abd9e9", "#ffffbf", "#fdae61", "#d7191c"])
        + labs(
            x=f"PC1 ({100 * evr[0]:.1f}%)",
            y=f"PC2 ({100 * evr[1]:.1f}%)",
            color="Radiance (mW)",
            title=f"PCA Score Plot: {label}",
        )
        + theme_minimal()
        + theme(
            panel_grid=element_blank(),
            axis_line=element_line(color="black"),
            axis_ticks=element_line(color="black"),
        )
    )
    p.save(filename=str(out_file), width=5.4, height=3.6, dpi=220, verbose=False)


def plot_pc12_by_ztime(scores_df: pd.DataFrame, evr: np.ndarray, label: str, out_file: Path):
    if not {"PC1", "PC2", "ztime"}.issubset(scores_df.columns):
        return
    if len(scores_df) < 2:
        return

    z_levels = [x for x in ["day", "night"] if x in set(scores_df["ztime"].astype(str).str.lower())]
    color_map = {"day": "#1f78b4", "night": "#e31a1c"}
    if not z_levels:
        z_levels = sorted(scores_df["ztime"].astype(str).unique().tolist())
        color_map = {k: "#1f78b4" for k in z_levels}

    scores_df = scores_df.copy()
    scores_df["ztime"] = scores_df["ztime"].astype(str).str.lower()

    p = (
        ggplot(scores_df, aes(x="PC1", y="PC2", color="ztime"))
        + geom_point(size=2.2, alpha=0.95)
        + scale_color_manual(values=color_map)
        + labs(
            x=f"PC1 ({100 * evr[0]:.1f}%)",
            y=f"PC2 ({100 * evr[1]:.1f}%)",
            color="ztime",
            title=f"PCA Score Plot (color = ztime): {label}",
        )
        + theme_minimal()
        + theme(
            panel_grid=element_blank(),
            axis_line=element_line(color="black"),
            axis_ticks=element_line(color="black"),
        )
    )
    p.save(filename=str(out_file), width=5.4, height=3.6, dpi=220, verbose=False)


def plot_pc1_vs_radiance(scores_df: pd.DataFrame, evr: np.ndarray, label: str, out_file: Path):
    if not {"PC1", "radiance_mW"}.issubset(scores_df.columns):
        return
    if len(scores_df) < 2:
        return

    subtitle = f"n={len(scores_df)}"
    if scores_df["radiance_mW"].nunique() > 1:
        r, p = pearsonr(scores_df["PC1"], scores_df["radiance_mW"])
        subtitle = f"r={r:.3f}, p={p:.3g}, n={len(scores_df)}"

    p = (
        ggplot(scores_df, aes(x="radiance_mW", y="PC1"))
        + geom_point(color="#2c7fb8", size=2.2, alpha=0.95)
        + geom_smooth(method="lm", se=False, color="#d7191c", size=1.1)
        + labs(
            x="Radiance (mW)",
            y=f"PC1 ({100 * evr[0]:.1f}%)",
            title=f"PC1 as a Function of Radiance: {label}",
            subtitle=subtitle,
        )
        + theme_minimal()
        + theme(
            panel_grid=element_blank(),
            axis_line=element_line(color="black"),
            axis_ticks=element_line(color="black"),
        )
    )
    p.save(filename=str(out_file), width=5.4, height=3.6, dpi=220, verbose=False)


def plot_pc1_vs_radiance_by_ztime(scores_df: pd.DataFrame, evr: np.ndarray, label: str, out_file: Path):
    if not {"PC1", "radiance_mW", "ztime"}.issubset(scores_df.columns):
        return
    if len(scores_df) < 2:
        return

    scores_df = scores_df.copy()
    scores_df["ztime"] = scores_df["ztime"].astype(str).str.lower()
    color_map = {"day": "#1f78b4", "night": "#e31a1c"}

    p = (
        ggplot(scores_df, aes(x="radiance_mW", y="PC1", color="ztime"))
        + geom_point(size=2.2, alpha=0.95)
        + geom_smooth(method="lm", se=False, size=1.0)
        + scale_color_manual(values=color_map)
        + labs(
            x="Radiance (mW)",
            y=f"PC1 ({100 * evr[0]:.1f}%)",
            color="ztime",
            title=f"PC1 vs Radiance (color = ztime): {label}",
        )
        + theme_minimal()
        + theme(
            panel_grid=element_blank(),
            axis_line=element_line(color="black"),
            axis_ticks=element_line(color="black"),
        )
    )
    p.save(filename=str(out_file), width=5.4, height=3.6, dpi=220, verbose=False)


def main():
    radiance = pd.read_csv(RADIANCE_FILE)
    radiance.columns = ["boxNum", "radiance_mW"]
    radiance["radiance_mW"] = pd.to_numeric(radiance["radiance_mW"], errors="coerce")

    df = pd.read_csv(FEATURE_FILE)
    merged = df.merge(radiance, on="boxNum", how="left")

    params = build_parameter_list(merged)
    for p in params:
        merged[p] = pd.to_numeric(merged[p], errors="coerce")

    merged["cond1"] = merged["cond1"].astype(str)
    merged["ztime"] = merged["ztime"].astype(str)

    clean = merged.dropna(subset=["radiance_mW", "cond1", "ztime"]).copy()
    cond = clean["cond1"].str.lower()
    ztime = clean["ztime"].str.lower()
    clean = clean[
        ((cond == "ll") & (ztime.isin(["day", "night"])))
        | ((cond == "ld") & (ztime == "day"))
    ]

    if "expNum" not in clean.columns:
        raise ValueError("Column 'expNum' is required for grouping.")

    group_cols = ["boxNum", "expNum", "cond1", "ztime"]
    agg = (
        clean[group_cols + params + ["radiance_mW"]]
        .groupby(group_cols, as_index=False)
        .median(numeric_only=True)
    )

    rr = run_pca(agg, "Pooled_LLday_LLnight_LDday", params)
    if rr is None:
        raise RuntimeError("No analyzable subset found")

    STAT_DIR.mkdir(parents=True, exist_ok=True)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    res_all = rr["res"]
    res_path = STAT_DIR / "pca_radiance_correlation_Pooled_LLday_LLnight_LDday.csv"
    res_all.to_csv(res_path, index=False)

    loadings_path = STAT_DIR / "pca_loadings_Pooled_LLday_LLnight_LDday.csv"
    rr["loadings"].to_csv(loadings_path, index=False)

    pc12_path = PLOT_DIR / "pca_pc1_pc2_Pooled_LLday_LLnight_LDday_colored_by_radiance.pdf"
    plot_pc12(rr["scores"], rr["evr"], "Pooled_LLday_LLnight_LDday", pc12_path)

    pc1_r_path = PLOT_DIR / "pca_pc1_vs_radiance_Pooled_LLday_LLnight_LDday.pdf"
    plot_pc1_vs_radiance(rr["scores"], rr["evr"], "Pooled_LLday_LLnight_LDday", pc1_r_path)

    pc12_ztime_path = PLOT_DIR / "pca_pc1_pc2_Pooled_LLday_LLnight_LDday_colored_by_ztime.pdf"
    plot_pc12_by_ztime(rr["scores"], rr["evr"], "Pooled_LLday_LLnight_LDday", pc12_ztime_path)

    pc1_r_ztime_path = PLOT_DIR / "pca_pc1_vs_radiance_Pooled_LLday_LLnight_LDday_colored_by_ztime.pdf"
    plot_pc1_vs_radiance_by_ztime(rr["scores"], rr["evr"], "Pooled_LLday_LLnight_LDday", pc1_r_ztime_path)

    print(f"Saved: {pc12_path}")
    print(f"Saved: {pc1_r_path}")
    print(f"Saved: {pc12_ztime_path}")
    print(f"Saved: {pc1_r_ztime_path}")
    print(f"Saved: {res_path}")
    print(f"Saved: {loadings_path}")

    show_df = res_all.copy()
    show_df["abs_r"] = show_df["pearson_r_with_radiance"].abs()
    show_df = show_df.sort_values("abs_r", ascending=False)
    print("\n=== Pooled_LLday_LLnight_LDday ===")
    print(show_df[["pc", "explained_variance_ratio", "pearson_r_with_radiance", "pearson_p", "n"]].head(3).to_string(index=False))


if __name__ == "__main__":
    main()
