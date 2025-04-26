#!/usr/bin/env python3
"""
Script to update documentation versions for GitHub Pages deployment.
This script handles the versioning logic for the documentation by creating
and updating the switcher.json file for the pyData theme version switcher.
"""

import os
import json
import argparse
import re


def natural_sort_key(s):
    """
    Sort version strings naturally by converting numeric parts to integers.
    This ensures versions like 1.10 come after 1.9, not before 1.2.
    """
    return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', s)]


def update_versions_json(site_dir, version, is_latest=False, base_url=None):
    """
    Update the switcher.json file for the pyData theme version switcher.
    
    The format follows the pyData theme requirements:
    [
        {
            "name": "v2.1 (stable)",
            "version": "2.1",
            "url": "https://mysite.org/en/2.1/"
        },
        ...
    ]
    
    Args:
        site_dir: Directory where the switcher.json file should be saved
        version: Version string (e.g., "1.0.0")
        is_latest: Boolean indicating if this is the latest stable version
        base_url: Base URL for documentation (default: relative paths)
    """
    json_path = os.path.join(site_dir, "switcher.json")
    
    # Use relative paths by default
    if base_url is None:
        base_url = "./"
    elif not base_url.endswith('/'):
        base_url += '/'
    
    # Create default structure if file doesn't exist
    if not os.path.exists(json_path):
        versions_data = []
    else:
        with open(json_path, 'r') as f:
            versions_data = json.load(f)
    
    # Check if version already exists in the data
    version_exists = False
    for entry in versions_data:
        if entry.get("version") == version:
            version_exists = True
            # Update URL if needed
            entry["url"] = f"{base_url}versions/{version}/"
            # Update name if this is the latest version
            if is_latest and "stable" not in entry.get("name", ""):
                entry["name"] = f"v{version} (stable)"
                entry["preferred"] = True
            break
    
    # Add new version if it doesn't exist
    if not version_exists and version != "latest":
        new_entry = {
            "version": version,
            "url": f"{base_url}versions/{version}/",
        }
        
        # Add name and preferred flag if this is the latest version
        if is_latest:
            new_entry["name"] = f"v{version} (stable)"
            new_entry["preferred"] = True
        else:
            new_entry["name"] = f"v{version}"
            
        versions_data.append(new_entry)
    
    # Add dev/latest version if it doesn't exist
    latest_exists = any(
        entry.get("version") == "latest" for entry in versions_data
    )
    if not latest_exists:
        versions_data.append({
            "name": "dev",
            "version": "latest",
            "url": f"{base_url}latest/"
        })
    
    # Sort versions by semantic versioning (excluding "latest")
    regular_versions = [
        v for v in versions_data if v.get("version") != "latest"
    ]
    latest_versions = [
        v for v in versions_data if v.get("version") == "latest"
    ]
    
    # Sort regular versions
    regular_versions.sort(
        key=lambda x: natural_sort_key(x.get("version", "")), reverse=True
    )
    
    # Combine sorted regular versions with latest version at the top
    sorted_versions = latest_versions + regular_versions
    
    # Write updated data back to file
    with open(json_path, 'w') as f:
        json.dump(sorted_versions, f, indent=4)
    
    return sorted_versions


def main():
    parser = argparse.ArgumentParser(
        description="Update documentation versions for GitHub Pages deployment"
        )
    parser.add_argument(
        "--version",
        required=True,
        help="Version being built (e.g., 1.0.0 or latest)"
    )
    parser.add_argument(
        "--site-dir",
        required=True,
        help="Path to the site directory"
    )
    parser.add_argument(
        "--is-latest",
        action="store_true",
        help="Flag indicating if this is the latest version"
    )
    parser.add_argument(
        "--base-url",
        help="Base URL for documentation (default: relative paths)"
    )
    
    args = parser.parse_args()
    
    # Update switcher.json
    update_versions_json(
        args.site_dir,
        args.version,
        args.is_latest,
        args.base_url
    )
    
    print(
        f"Switcher.json for version {args.version} has been updated"
        "successfully."
    )


if __name__ == "__main__":
    main()
