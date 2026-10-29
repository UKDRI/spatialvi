process SDATA_ZIP {
    tag "${meta.id}"
    label 'process_single'

    container "community.wave.seqera.io/library/harmonypy_scanorama_gcc_gxx_pruned:95f731fde0b9ddef"

    input:
    tuple val(meta), path(sdata, arity: '1')

    output:
    tuple val(meta), path("${prefix}.zarr.zip"), emit: zip
    path "versions.yml"                        , emit: versions, topic: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    prefix = task.ext.prefix ?: "${meta.id}"
    template 'zip.py'

    stub:
    prefix = task.ext.prefix ?: "${meta.id}"
    """
    python -c "import zipfile; zipfile.ZipFile('${prefix}.zarr.zip', 'w').close()"
    touch versions.yml
    """
}
