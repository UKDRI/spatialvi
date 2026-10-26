#!/usr/bin/env python3
"""
Rank genes for characterizing groups (differential expression analysis).

Identifies marker genes for each group by comparing gene expression
between groups. Results are stored in adata.uns["rank_genes_groups"],
including the fraction of observations expressing each gene inside
(`pts`) and outside (`pts_rest`) of each group.
"""

# Disable OpenMP CPU topology detection for macOS compatibility
import os
os.environ["KMP_AFFINITY"] = "disabled"

# Keep caches in the task's work directory, which is always writable and
# private to the task
os.environ["NUMBA_CACHE_DIR"] = os.path.join(os.getcwd(), ".cache", "numba")
os.environ["MPLCONFIGDIR"] = os.path.join(os.getcwd(), ".cache", "matplotlib")
os.environ["XDG_CACHE_HOME"] = os.path.join(os.getcwd(), ".cache")

import importlib.metadata
import logging
import platform

import anndata as ad
import scanpy as sc
import yaml
from threadpoolctl import threadpool_limits

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Limit BLAS/OpenMP threads to the allocated CPUs
threadpool_limits(int("${task.cpus}"))


def rank_genes(adata, groupby, method):
    """
    Rank genes by groups for differential expression analysis.

    Each group is compared against all other observations. Ranking is skipped
    with a warning when `groupby` has fewer than two groups, since there is
    nothing to compare against.

    Parameters
    ----------
    adata : AnnData
        Annotated data matrix.
    groupby : str
        Column in adata.obs with the groups to compare.
    method : str
        Statistical test passed to `sc.tl.rank_genes_groups`.

    Returns
    -------
    AnnData
        AnnData with results in adata.uns["rank_genes_groups"], unless ranking
        was skipped.
    """
    logger.info(f"Adata shape: {adata.shape}")
    logger.info(f"Groupby: {groupby}")
    logger.info(f"Method: {method}")

    if groupby not in adata.obs.columns:
        raise ValueError(f"Column '{groupby}' not found in adata.obs")

    n_groups = adata.obs[groupby].nunique()
    if n_groups < 2:
        logger.warning(
            f"Column '{groupby}' has {n_groups} group(s); at least two are needed "
            f"to rank genes, so the ranking is skipped"
        )
        return adata

    # `pts=True` also stores the fraction of observations expressing each gene
    # in (`pts`) and outside (`pts_rest`) each group; the `logreg` method does
    # not compute these
    sc.tl.rank_genes_groups(
        adata,
        groupby=groupby,
        method=method,
        pts=True
    )

    logger.info(f"Computed DEGs for {n_groups} groups")

    # Print top genes per group
    for group in adata.obs[groupby].unique():
        genes = sc.get.rank_genes_groups_df(adata, group=str(group))
        top_genes = genes.head(5)["names"].tolist()
        logger.info(f"  Group {group} top 5: {', '.join(top_genes)}")

    return adata


def write_versions(process_name):
    """Write software versions to a YAML file."""
    versions = {
        process_name: {
            "python": platform.python_version(),
            "anndata": importlib.metadata.version("anndata"),
            "scanpy": importlib.metadata.version("scanpy"),
        }
    }
    with open("versions.yml", "w") as f:
        yaml.dump(versions, f)


def main():
    """Rank genes for characterizing groups in an AnnData object."""

    # Template variables
    h5ad = "${adata}"
    groupby = "${groupby}"
    method = "${method}"
    output_adata = "${prefix}.h5ad"
    write_adata = "${write_adata}" == "true"
    process_name = "${task.process}"

    # Read AnnData
    adata = ad.read_h5ad(h5ad)
    logger.info(f"Performing differential expression analysis on: {h5ad}")

    # Rank genes
    adata = rank_genes(adata, groupby, method)

    # Write output
    if write_adata:
        adata.write_h5ad(output_adata)
        logger.info(f"Written AnnData with DEGs to: {output_adata}")

    # Write versions
    write_versions(process_name)

if __name__ == "__main__":
    main()
