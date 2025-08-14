# Snap Recommendation Service
This service is responsible for generating and serving recommendations for snaps.

## Development

### Prerequisites
- Python 3.8

### Collector

You can use `docker compose up -d` to start the service alongside a postgres DB. But first you'll need to follow the instructions in collector/README.md to populate the `FLASK_SNAPSTORE_MACAROON_KEY` env variable.

If running for the first time, you must run the following to apply migrations:

```
docker compose exec web flask db upgrade
```

#### Manual Setup

```bash
# create a virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Running the collector
```bash
flask collector start
```

### Starting the local environment
In development for hot module reloding the backend api's accessed through flask. If the user enters any paths other than the ones that are listed in the vite configuration they are navigated to react frontend otherwise they are navigated to the corresponding backend api.

To make it work 
Terminal 1
```bash
flask run
```

Terminal 2
```bash
cd frontend
yarn
yarn dev
```

In dev mode, Vite runs on port 5173 and proxies API calls to Flask on port 5000.

### Troubleshoot
- If you got an error that is related with connection to server at "db", change the "db" in the POSTGRESQL_DB_CONNECT_STRING to "localhost" in the .env file.

## Production

In production there is one server. Flask serve the built React files plus API endpoints.

1. Build with `yarn build`
2. Move build output into Flask
   - All the .js and .css files need to be moved to 'static' folder
   - 'index.html' needs to be in the 'templates' folder
3. Run the server with `flask run`

## Architecture
The Snap Recommendation Service consists of two main components:
1. Collector (Python): A pipeline for collects data from multiple sources and processes it to generate recommendations. This is a job that runs weekly
2. Server (Flask): Serves rankings as JSON to be consumed by other services such as snapcraft.io.

Both components use a shared database (SQLite) to store both snap data and rankings (see `models.py` for the schemas)

### Collector
The collector is a multi-stage pipeline, each stage can be run independently if needed by running the corresponding script. The stages are:
1. `collect.py`: Collecting data from the snap store [for all public (searchable) snaps]. 
2. `filter.py`: Filter out snaps that are not suitable for recommendations (e.g snaps that don't have an icon, etc)
3. `extrafields.py` Collect extra data from the snap store (e.g. active devices), this is done after filtering to reduce the number of requests
4. `score.py`: Generate ratings for each snap based on multiple categories (e.g. popularity, trendiness, etc)

The entire pipeline can be run by running `flask collector start` which will run all the stages in order. See `flask collector --help` if you'd like to run a stage individually.

### Server
The server is a very lightweight Flask server that serves the rankings for a given category.

### DB & Migrations

Any modifications to the models inside `snaprecommend/models.py` should result in a new migration that will be applied to the DB on the next deployment. To create a new migration:

```
flask db migrate -m "Added icon column"
```

Then apply the migration with `flask db upgrade`.

Any of the commands above can be prefixed with `docker exec web` if running using docker compose

## Flowchart
```mermaid
flowchart TB

    subgraph "Recommendations service"
        
        subgraph "Collector (Python)"
            
            C1[Collect data] --> C2[Filter snaps]
            C2 --> C3[Collect extra fields]
            C3 --> C4[Generate ratings]
        end

        subgraph "Database (Postgres)"
            %% snapdata[Snap data]
            ratings[Ratings]
        end

        subgraph "Server (Flask)"
            S1[Serve ratings as JSON]
        end
    end

    subgraph "Snapcraft API"
        search[Search endpoint]
        metrics[Metrics endpoint]
    end
    
    search -.-> C1
    metrics -.-> C3
    C4 -.-> ratings
    ratings -.-> S1
    %% C1 -.-> snapdata
    %% snapdata -.-> C2

```
