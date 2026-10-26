process SCANPY_EXPORT_MARKERS {
    tag "${meta.id}"
    label 'process_single'

    container "community.wave.seqera.io/library/harmonypy_scanorama_gcc_gxx_pruned:95f731fde0b9ddef"

    input:
    tuple val(meta), path(adata, stageAs: "input.h5ad", arity: '1')
    val thr_adj_pvalue
    val n_top
    val pct_nz_group
    val min_logfc
    val sep

    output:
    tuple val(meta), path("${prefix}.json.gz"), emit: json
    path "versions.yml"                       , emit: versions, topic: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    prefix = task.ext.prefix ?: "${meta.id}_markers"
    template 'export_markers.py'

    stub:
    prefix = task.ext.prefix ?: "${meta.id}_markers"
    """
    touch ${prefix}.json.gz
    touch versions.yml
    """
}
