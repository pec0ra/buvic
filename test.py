import sys
from uv_file import UVFileReader

file = sys.argv[1]

uv_file_reader = UVFileReader(file)
for entry in uv_file_reader.get_uv_file_entries():
    print()
    print(entry.type)
    print(entry.integration_time)
    for v in entry.values:
        print(v)

