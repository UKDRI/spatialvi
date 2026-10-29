#!/usr/bin/env python3
"""
Pack a SpatialData Zarr directory into a single uncompressed ZIP archive.

The archive follows the BioImage Archive Zarr guidance
(https://www.ebi.ac.uk/bioimage-archive/help-zarr/): its single top-level
entry is the `<prefix>.zarr/` directory, so unzipping recreates the Zarr store.
"""

import logging
import os
import platform
import zipfile

import yaml

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def list_files(zarr_dir):
    """
    List all files in a Zarr directory in a stable order.

    Parameters
    ----------
    zarr_dir : str
        Path to the Zarr directory. Symlinks, including the one Nextflow stages
        the directory as, are followed.

    Returns
    -------
    list of tuple of str
        Pairs of (absolute path, path relative to `zarr_dir`), including dot
        files such as `.zgroup`, `.zattrs` and `.zmetadata`.
    """
    root = os.path.realpath(zarr_dir)
    files = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
        # Sort in place so that os.walk descends in a stable order
        dirnames.sort()
        for filename in sorted(filenames):
            path = os.path.join(dirpath, filename)
            files.append((path, os.path.relpath(path, root)))
    return files


def write_zip(files, output_zip, top_level):
    """
    Write files into a ZIP archive under a single top-level directory.

    Parameters
    ----------
    files : list of tuple of str
        Pairs of (path on disk, path relative to the Zarr directory).
    output_zip : str
        Path of the ZIP archive to write.
    top_level : str
        Name of the top-level directory inside the archive.
    """
    # Stored, not deflated: Zarr chunks and Parquet files are already compressed
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
        for path, relpath in files:
            zf.write(path, arcname=f"{top_level}/{relpath}")


def check_zip(output_zip, n_files):
    """
    Check that the ZIP archive holds as many file entries as files were walked.

    Only reads the central directory; a full `testzip()` would re-read every
    member, which is slow for large archives on network file systems.

    Parameters
    ----------
    output_zip : str
        Path of the ZIP archive to check.
    n_files : int
        Number of files that were written into the archive.
    """
    with zipfile.ZipFile(output_zip, "r") as zf:
        n_entries = sum(1 for info in zf.infolist() if not info.is_dir())
    if n_entries != n_files:
        raise RuntimeError(f"{output_zip} has {n_entries} file entries, expected {n_files}")


def write_versions(process_name):
    """Write software versions to a YAML file."""
    versions = {
        process_name: {
            "python": platform.python_version(),
        }
    }
    with open("versions.yml", "w") as f:
        yaml.dump(versions, f)


def main():
    """Pack a SpatialData Zarr directory into a single ZIP archive."""

    # Template variables
    zarr_dir = "${sdata}"
    top_level = "${prefix}.zarr"
    output_zip = "${prefix}.zarr.zip"
    process_name = "${task.process}"

    files = list_files(zarr_dir)
    logger.info(f"Packing {len(files)} files from {zarr_dir} into {output_zip}")

    write_zip(files, output_zip, top_level)
    check_zip(output_zip, len(files))

    size_gb = os.path.getsize(output_zip) / 1024**3
    logger.info(f"Written {output_zip}: {len(files)} files, {size_gb:.2f} GiB")

    write_versions(process_name)

if __name__ == "__main__":
    main()
