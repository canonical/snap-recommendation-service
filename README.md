# Snap Recommendation Service
This service is responsible for generating and serving recommendations for snaps.

## Architecture
The service is composed of two components:
- The collector (written in python) is responsible for:
    - Collecting snap data from our APIs
    - Filtering snaps that can be recommended
    - Processing snaps and giving a ranking for each of the recommendation categories
- The server (written in go) is responsible for:
    - Serving rankings as JSON to be consumed by snapcraft.io
