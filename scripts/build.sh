#!/bin/bash
# """
# Binary build script using "pyinstaller".
# """

su -s /bin/bash \
-c "source $(pwd)/../.venvs/maps-import/bin/activate && \
    cd .. && pyinstaller app.py --onefile && \
    mv dist/app dist/maps-import" \
    knauf-batiment
