#!/usr/bin/env python3
"""
Simple script to update documentation versions for GitHub Pages deployment.
This script handles the versioning logic for the documentation by updating
the switcher.json file for the pyData theme version switcher.
"""

import os
import json
import argparse
import tomllib
import sys


def verify_version_match(version, project_root):
    """
    Verify that the version matches the version in pyproject.toml.
    
    Args:
        version: Version string from the git tag (e.g., "0.2.15")
        project_root: Path to the project root directory
        
    Returns:
        bool: True if versions match, False otherwise
    """
    # Skip verification for non-version refs (like 'main')
    if version == "main":
        return True
        
    # Read version from pyproject.toml
    pyproject_path = os.path.join(project_root, "pyproject.toml")
    try:
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)
            toml_version = pyproject_data["project"]["version"]
            
        if version != toml_version:
            print(f"ERROR: Version mismatch! Git tag: {version}, pyproject.toml: {toml_version}")
            return False
        
        print(f"Version verification successful: {version} matches pyproject.toml")
        return True
    except Exception as e:
        print(f"ERROR: Failed to verify version match: {str(e)}")
        return False


def update_versions_json(site_dir, version):
    """
    Update the switcher.json file for the pyData theme version switcher.
    Simply adds the version if it doesn't exist.

    Args:
        site_dir: Directory where the switcher.json file should be saved
        version: Version string (e.g., "0.2.15" or "main")
        is_latest: Boolean indicating if this is the latest stable version
    """
    json_path = os.path.join(site_dir, "switcher.json")
    base_url = "https://jfouret.github.io/ispawn/"

    # Create default structure if file doesn't exist
    if not os.path.exists(json_path):
        versions_data = []
    else:
        with open(json_path, "r") as f:
            versions_data = json.load(f)

    # Check if version already exists in the data
    version_exists = False
    for entry in versions_data:
        if entry.get("version") == version:
            version_exists = True
            break

    # Add new version if it doesn't exist
    if not version_exists:
        new_entry = {
            "name": version,
            "version": version,
            "url": f"{base_url}{version}/",
        }

        versions_data.append(new_entry)

    # Write updated data back to file
    with open(json_path, "w") as f:
        json.dump(versions_data, f, indent=4)

    return versions_data




def main():
    parser = argparse.ArgumentParser(
        description="Update documentation versions for GitHub Pages deployment"
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Version being built (e.g., 0.2.15 or main)",
    )
    parser.add_argument(
        "--site-dir", 
        help="Path to the site directory",
    )

    parser.add_argument(
        "--project-root",
        default=".",
        help="Path to the project root directory",
    )

    args = parser.parse_args()

    # Verify version match if requested
    if args.version != "main":
        if not verify_version_match(args.version, args.project_root):
            sys.exit(1)

    # Update switcher.json if site_dir is provided
    if args.site_dir:
        update_versions_json(args.site_dir, args.version)

        print(f"Switcher.json for version {args.version} has been updated successfully.")


if __name__ == "__main__":
    main()
