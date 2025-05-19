# ML workflow + CI/CD scaffold

## Background

### How to set up Metaflow projects
There are many ways you can use Metaflow and Outerbounds, and it can be difficult to know where to get started in real-world projects. To provide a frame of reference, this repository implements an opinionated template for how to build on top of Outerbounds and Metaflow. You can use it directly, or fork and modify as needed. 

Features of this structure to consider:
- Python workflows are used to define connections between ML systems and the rest of the world.
    - Snowflake
    - S3
- SQL and Python are seamlessly mixed.
- Flow inheritance is used to define a base flow, a template for "application" flows.
- Config-driven workflows enable workflow code to stay fixed, and clarifying the relationship between workflows and research/business code.
- CI/CD approach to link workflow namespaces and code branches.

### Applying the scaffold with the `SensorFlow`
The rest of this page describes how the code can be used to implement a common way we've seen successful customers leverage Outerbounds in their AI stack, with simple business logic and broad implications.

Triggering workflows on system events is a powerful pattern that comes out of the box when running Metaflow on Outerbounds. Events can be anything. ML system designers may choose to send events on the arrival of new data, or in response to a change in a measure of a dataset. Eventing is a building block of reactive ML systems; workflows need to run in response to the outside world.

In the [use cases section](#use-cases), you'll see examples of the mechanism for doing this across common data storage platforms.
 
## Code overview

### `flowproject.toml`
A file driving configuration options in `sensorflow.py`. 

### `flowproject/baseflow.py`
Defines core operations for querying each event source. The flow provides an interface that `sensorflow.py` and other workflow definitions inherit from. 

### `sensorflow.py`
A flow that sends events into the Outerbounds ecosystem from external storage platforms. The `start` step detects changes in an upstream data storage entity. If changes are detected, the `end` step dispatches an event in the Outerbounds event bus. 

### Relevant configuration options
- `flowconfig.project_name`: The [Metaflow project](https://docs.metaflow.org/api/flow-decorators/project) name that organizes results.
- `flowconfig.sensor.cron_schedule`: A [cron schedule to run the sensor flow](https://docs.metaflow.org/production/scheduling-metaflow-flows/scheduling-with-argo-workflows#time-based-triggering) on.
- `flowconfig.sensor.event_name`: The name of the [event](https://docs.metaflow.org/production/event-triggering) to dispatch on change detection.
- `flowconfig.sensor.payload_key`: The name of the (dictionary) key in the event payload that maps to the new value detected. This (k, v) pair will be accessible to tasks in the workflow runs triggered by the event.

### Supported databases
Currently, Snowflake and S3 are supported. See [use cases](#use-cases) to understand how to use each in detail. 

## `deploy` script
A `deploy` script to use manually or in CI, that deploys workflows ending in the root directory matching `*.flow.py` to Argo Workflows. [Metaflow `branches`](https://docs.metaflow.org/production/coordinating-larger-metaflow-projects#custom-branches) are linked to GitHub branches, meaning code branches are now coupled to workflow namespaces. This pattern connects workflow changes with code changes, facilitating observability and debugging. 

## `SensorFlow` use cases

| Feature | Snowflake | S3 |
|---------|-----------|----|
| Trigger granularity | SQL query result | Metadata/file-level |
| Permissions required | Role & integration | Bucket IAM & access |

### Snowflake sensor
_Deploy a sensor that can dispatch events in an Outerbounds perimeter, when changes occur in a Snowflake table._

#### Set `flowproject.toml` required arguments
There are two sections of the config file to update.
First, in `[data]`, update the `type` option to `snowflake`. Then, in the same section set `integration` to your Outerbounds integration name associated with the desired Snowflake user and role combination. If you do not already have the Outerbounds integration set up you can visit the UI, consult your organization's Snowflake admin for the correct user and role to use.

To create an integration, visit the Integrations tab in Outerbounds, you'll see an option for Snowflake and it will walk you through the integration process, ending in a [`@secrets` value](https://docs.outerbounds.com/outerbounds/configuring-secrets/).

#### Set `sensorflow.py`

##### Pattern
Add `from flowproject import snowflake` in your flow, and annotate `@snowflake` on steps you to monitor. In `sensorflow.py` this is done in the `start` step. Look at `flowproject/baseflow.py` for implementation. This repository organization pattern keeps dependency definitions separated from workflow definitions, which become easier to read and work on. 

Read the flow to understand the example, but notice that everything that you'd want to update is now mostly frozen. Now we can drive the flow with a single config file to change the query, use a different access role on the storage layer, or tune the monitor flow's schedule. 

Run the flow:
```bash
python sensorflow.py --environment=fast-bakery run --with kubernetes
```

`SensorFlow` is deployed in the `deploy` bash script. 

#### The query
The query that implements how the Snowflake table is checked is implemented in `flowproject/baseflow.py`. It runs a query against the database. Example queries are in `sql/*.sql`.

### S3 sensor
_Deploy a sensor that can dispatch events in an Outerbounds perimeter, when changes occur in a S3 bucket/key._

#### Set `flowproject.toml` required arguments
There are two sections of the config file to update.
First, in `[data]`, update the `type` option to `s3`. Then, in the same section set `bucket` and `key` to a file or directory. The third option is `check_mode`. 
If you set `check_mode` to `files_metadata`, then `key` should be a directory within a bucket path. 
If you set `check_mode` to `file_size` or `file_modified_ts`, then `key` should be a file within a bucket path. 

##### Bucket permissions
For the bucket you want to use, go to Outerbounds UI and visit the Integrations page. There, you'll see an S3 option. Click and follow the instructions to configure the bucket where the file or directory you want to monitor is stored.

#### Set `sensorflow.py`

Run the flow:
```bash
python sensorflow.py --environment=fast-bakery run --with kubernetes
```

`SensorFlow` is deployed in the `deploy` bash script. 

#### The query

The query that implements how the S3 key is checked is implemented in `flowproject/baseflow.py`. It runs one of the `[files_metadata, file_modified_ts, file_size]` check modes against the S3 key. 
