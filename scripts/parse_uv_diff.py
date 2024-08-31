#!/usr/bin/env python
import re
import sys

def parse_version(version_str):
    """Parses a version string into a tuple of integers."""
    try:
        return tuple(map(int, version_str.split('.')))
    except ValueError:
        # Handle non-numeric parts if necessary, or return a comparable value
        # For simplicity, returning a tuple that might not compare correctly
        # If complex versions (e.g., alpha, beta) are common, enhance this
        return tuple(version_str.split('.'))

def main():
    diff = sys.stdin.read()

    # Find all the packages that were upgraded
    # Regex handles optional quotes and equals sign
    packages = re.findall(r'\\+\\s+\\"?([a-zA-Z0-9-_]+)\\"?\\s*=\\s*\\"([0-9\\.]+)\\"', diff)

    upgrades_str = ''
    upgrades = []
    for pkg, new_ver_str in packages:
        # Find the old version of the package
        old_ver_match = re.search(
            r'-\\s+\\"?' + re.escape(pkg) + r'\\"?\\s*=\\s*\\"([0-9\\.]+)\\"',
            diff
        )
        if old_ver_match:
            old_ver_str = old_ver_match.group(1)
            upgrades.append({
                'pkg': pkg,
                'old_ver': old_ver_str,
                'new_ver': new_ver_str
            })

    for upgrade in upgrades:
        pkg = upgrade['pkg']
        old_ver = upgrade['old_ver']
        new_ver = upgrade['new_ver']

        old_parts = parse_version(old_ver)
        new_parts = parse_version(new_ver)

        is_major_minor_change = False
        # Compare major and minor parts (first two elements)
        for i in range(min(2, len(old_parts), len(new_parts))):
             # Ensure comparison is meaningful (e.g., comparing integers)
            try:
                if int(old_parts[i]) != int(new_parts[i]):
                    is_major_minor_change = True
                    break
            except ValueError:
                 # If parts are not integers, compare as strings
                 if old_parts[i] != new_parts[i]:
                     is_major_minor_change = True
                     break

        if is_major_minor_change:
            upgrades_str += f'* **{pkg} from {old_ver} to {new_ver}**\n'
        else:
            upgrades_str += f'* {pkg} from {old_ver} to {new_ver}\n'

    # Print the final formatted string to stdout
    print(upgrades_str.strip()) # Use strip to remove trailing newline

if __name__ == "__main__":
    main() 