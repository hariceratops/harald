import sys

from harald.cli import main

# the guard matters: build workers re-import the main module
if __name__ == "__main__":
    sys.exit(main())
