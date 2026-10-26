# nf-core/spatialvi: Output

## Introduction

This document describes the output produced by the pipeline. Most of the output
is contained within HTML reports created with [Quarto](https://quarto.org/), but
there are also other files which you can either take and analyse further by
yourself or explore interactively with _e.g._ [TissUUmaps](https://tissuumaps.github.io/).

The directories listed below will be created in the results directory after the
pipeline has finished. Results for individual samples will be created in
subdirectories following the `<OUTDIR>/<SAMPLE>/` structure. All paths are
relative to the top-level results directory.

The pipeline is built using [Nextflow](https://www.nextflow.io/) and processes
data using the following steps:

- [Space Ranger](#space-ranger)
- [FastQC](#fastqc)
- [Per-sample data](#per-sample-data)
- [Per-sample reports](#per-sample-reports)
- [Marker genes](#marker-genes)
- [Integration](#integration)
- [Workflow reporting](#workflow-reporting)
  - [Pipeline information](#pipeline-information) - Report metrics generated
    during the workflow execution

## Space Ranger

<details markdown="1">
<summary>Output files</summary>

- `<SAMPLE>/spaceranger/`
  - `outs/spatial/tissue_[hi/low]res_image.png`: High and low resolution images.
  - `outs/spatial/tissue_positions.csv`: Spot barcodes and their array
    positions.
  - `outs/spatial/scalefactors_json.json`: Scale conversion factors for the
    spots.
  - `outs/filtered_feature_bc_matrix/barcodes.tsv.gz`: List of barcode IDs.
  - `outs/filtered_feature_bc_matrix/features.tsv.gz`: List of feature IDs.
  - `outs/filtered_feature_bc_matrix/matrix.mtx.gz`: Matrix of UMIs, barcodes
    and features.
  - `outs/web_summary.html`: Interactive summary report from Space Ranger.
  - `outs/cloupe.cloupe`: File for visualization in 10X Loupe Browser.
  </details>

All files produced by Space Ranger are currently published as output of this
pipeline, regardless if they're being used downstream or not; you can find more
information about these files at the [10X website](https://support.10xgenomics.com/spatial-gene-expression/software/pipelines/latest/output/overview).

## FastQC

<details markdown="1">
<summary>Output files</summary>

- `<SAMPLE>/fastqc/`
  - `*_fastqc.html`: FastQC report.
  - `*_fastqc.zip`: FastQC data archive.

</details>

[FastQC](http://www.bioinformatics.babraham.ac.uk/projects/fastqc/) gives
general quality metrics about your sequenced reads. It provides information
about the quality score distribution across your reads and per base sequence
content among other metrics.

## Per-sample data

<details markdown="1">
<summary>Output files</summary>

- `<SAMPLE>/data/`
  - `<SAMPLE>-raw.h5ad`: Raw (unprocessed) data in AnnData format, as extracted
    from the SpatialData object before any downstream analysis.
  - `<SAMPLE>.h5ad`: Processed data in AnnData format, including QC metrics,
    clustering, differential expression, and spatial analysis results, as well
    as the raw counts in `adata.layers["raw"]`. The marker genes per cluster
    are in `uns["rank_genes_groups"]`, including the fraction of spots
    expressing each gene inside (`pts`) and outside (`pts_rest`) each cluster.
  - `<SAMPLE>_svg.csv`: List of spatially variable genes.
  - `<SAMPLE>_markers.json.gz`: Marker genes per cluster as gzipped JSON (see
    [Marker genes](#marker-genes)).

</details>

Data in `.h5ad` formats as processed by the pipeline, which can be used for
further downstream analyses if desired. It can also be used by the
[TissUUmaps](https://tissuumaps.github.io/) browser-based tool for visualisation
and exploration, allowing you to delve into the data in an interactive way. The
list of spatially variable genes are added as a convenience if you want to
explore them in _e.g._ Excel.

## Per-sample reports

<details markdown="1">
<summary>Output files</summary>

- `<SAMPLE>/reports/`
  - `report-<SAMPLE>.html`: Analysis report including quality controls, clustering,
    differential expression, and spatial analysis results.
  - `report.qmd`: Quarto source notebook of the report.
  - `report.yml`: Parameters used by the report.
  - `_extensions/`: Quarto nf-core extension, common to all reports.
- `<SAMPLE>/plots/`
  - `*.png`: Individual plots from the per-sample report, saved as PNG files for
    easy reuse.

</details>

The per-sample reports contain quality control metrics, clustering results,
marker genes, neighbourhood enrichment, cluster interaction matrices, and
spatially variable gene analysis. The marker genes section shows a heatmap and
a dotplot of the top marker genes per cluster, and a table per cluster with the
top `--report_n_top_markers` (default 250) ranked genes and their statistics.

## Marker genes

Marker genes are computed per cluster with `scanpy.tl.rank_genes_groups`,
comparing the spots of a cluster against all other spots with the method given
by `--rank_genes_method` (default: Wilcoxon rank-sum test). This is done per
sample on the Leiden clusters and, unless integration is skipped, on the
integrated clusters. The results are stored in the AnnData and SpatialData
outputs and shown in the reports.

The marker genes are also exported as gzipped JSON files
(`<SAMPLE>/data/<SAMPLE>_markers.json.gz` and
`integration/data/<METHOD>_markers.json.gz`), in the same format as the UK DRI
scdownstream pipeline. Each file contains one gene set per cluster, with the
id `genes<SEP>cluster<SEP><CLUSTER>` (`<SEP>` is `--markers_sep`, default
`--`), holding the gene names and their p-values, adjusted p-values, log2 fold
changes, scores and fractions of spots expressing the gene in and outside the
cluster. Only genes with an adjusted p-value below `--markers_thr_adj_pvalue`,
expressed in at least `--markers_pct_nz` of the cluster's spots and with a
log2 fold change of at least `--markers_min_logfc` are kept, at most
`--markers_n_top` per cluster, ordered by score. The filter parameters are
stored in the file as well. The JSON export is skipped with
`--rank_genes_method logreg`, which computes no p-values, fold changes or
expression fractions.

## Integration

Integration outputs are only produced when both `--skip_integration` and
`--skip_downstream` are unset (which is the default). This merges all per-sample
data and applies batch correction using the selected integration method (Harmony
or Scanorama). The merged raw counts are normalised again, with the same
parameters as the per-sample data, and highly variable genes and a PCA are
computed on the merged data before integration; the highly variable genes are
selected per sample and ranked by in how many samples they are highly variable.

<details markdown="1">
<summary>Output files</summary>

- `integration/data/`
  - `merged.zarr`: Merged SpatialData object containing all samples (before
    integration).
  - `<METHOD>.zarr`: Integrated SpatialData object with batch-corrected results.
  - `<METHOD>.h5ad`: Integrated AnnData object with batch-corrected embeddings
    and clustering. The PCA of the merged data is in `obsm["X_pca_merged"]`,
    while `obsm["X_pca"]` holds each spot's coordinates in the PCA of its own
    sample. Only gene annotations that are the same in every sample are kept
    in `var`; per-sample gene statistics are available in the per-sample
    output. The marker genes of the integrated clusters are in
    `uns["rank_genes_groups"]`.
  - `<METHOD>_markers.json.gz`: Marker genes per integrated cluster as gzipped
    JSON (see [Marker genes](#marker-genes)).
- `integration/reports/`
  - `report-integrated.html`: Integration report with cross-sample comparisons,
    batch mixing assessment, integrated clustering results and the marker
    genes of the integrated clusters.
  - `report-integrated.qmd`: Quarto source notebook of the integration report.
  - `report-integrated.yml`: Parameters used by the integration report.
  - `_extensions/`: Quarto nf-core extension.
- `integration/plots/`
  - `*.png`: Individual plots from the integration report.

</details>

## Workflow reporting

### Pipeline information

<details markdown="1">
<summary>Output files</summary>

- `pipeline_info/`
  - Reports generated by Nextflow: `execution_report.html`, `execution_timeline.html`, `execution_trace.txt` and `pipeline_dag.dot`/`pipeline_dag.svg`.
  - Reports generated by the pipeline: `pipeline_report.html`, `pipeline_report.txt` and `software_versions.yml`. The `pipeline_report*` files will only be present if the `--email` / `--email_on_fail` parameter's are used when running the pipeline.
  - Reformatted samplesheet files used as input to the pipeline: `samplesheet.valid.csv`.
  - Parameters used by the pipeline run: `params.json`.
- `multiqc/`
  - Report generated by MultiQC: `multiqc_report.html`. Includes FastQC results,
    Space Ranger metrics, per-sample filtering statistics (spots and genes
    removed at each QC step), and software versions.
  - Data and plots generated by MultiQC: `multiqc_data/` and `multiqc_plots/`.

</details>

[Nextflow](https://docs.seqera.io/platform-cloud/reports/overview) provides excellent functionality for generating various reports relevant to the running and execution of the pipeline. This will allow you to troubleshoot errors with the running of the pipeline, and also provide you with other information such as launch commands, run times and resource usage.
