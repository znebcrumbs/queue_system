#!/usr/bin/env python
# Remove duplicate code from views.py file

with open('apps/queues/views.py', 'r') as f:
    lines = f.readlines()

# Keep only first 811 lines (0-indexed, so up to 810)
with open('apps/queues/views.py', 'w') as f:
    f.writelines(lines[:811])

print(f"Removed duplicate code. File now has {len(lines[:811])} lines (was {len(lines)} lines)")
