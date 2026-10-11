# Museum Visitor Insights: Data Pipelines and Analysis

## Project Overview

This project contains batch and real-time data pipelines for a natural history museum. Together, they prepare exhibition and historical data, process live visitor interactions from exhibition kiosks, store validated records, and support analysis of visitor and operational trends.

The batch workflows retrieve source data from AWS S3, transform it, and load it into PostgreSQL. A separate Kafka consumer continuously validates and stores kiosk events. Another consumer sends email notifications for recent emergency events. Terraform and Bash scripts support AWS provisioning and deployment, while a Jupyter notebook is provided for analysis.

The repository includes the application code, tests, infrastructure definitions, deployment scripts, and development skills. It does not include deployment credentials, Terraform variable values, Terraform state, or the generated analysis images.

## Project Objectives

* Extract, transform, and load source exhibition and historical data.
* Seed the database with exhibition, floor, department, and button reference data.
* Consume and validate live kiosk events from Apache Kafka.
* Store structured interaction records in PostgreSQL.
* Deploy the pipeline to AWS EC2 for continuous execution.
* Provision cloud infrastructure using Terraform.
* Automate deployment and startup using Bash scripts.
* Send email notifications for recent emergency events.
* Explore collected data with the supplied Jupyter notebook.

## Architecture and Technologies

The project has two related data flows:

1. **Batch preparation:** `data_seeding_pipeline/` downloads exhibition and historical data from S3, transforms it, and loads it into PostgreSQL. Its database seeding workflow builds reference tables from exhibition data.
2. **Live ingestion:** `live_data_pipeline/` consumes kiosk events from Kafka, validates them against the event rules and seeded exhibit IDs, then stores accepted interactions in PostgreSQL.
3. **Emergency notification:** A separate Kafka consumer detects emergency events and sends email alerts for events within its recent-event window.
4. **Infrastructure and deployment:** Terraform provisions AWS resources; scripts in `scripts/` transfer configuration and launch the processes on EC2.
5. **Analysis:** `visualisations/analysis.ipynb` provides exploratory analysis of the collected data.

### Technology Stack

* **Python:** Batch ETL, event processing, and notification consumers
* **Apache Kafka:** Real-time event streaming
* **PostgreSQL:** Persistent storage for reference and interaction data
* **AWS EC2:** Continuous execution of the pipeline
* **AWS RDS:** Managed PostgreSQL database hosting
* **AWS S3:** Source exhibition and historical data
* **Terraform:** Infrastructure provisioning
* **Bash and SSH:** Deployment automation and remote server management
* **Jupyter Notebook:** Exploratory data analysis and investigation of visitor interaction patterns
* **Email notifications:** Emergency event alerts for security staff

## Data Validation and Business Rules

The live stream may contain accidental interactions, malformed messages, mechanical errors, or events for unknown exhibits. The consumer applies these rules before inserting records:

| Validation             | Rule                                                                                  |
| ---------------------- | ------------------------------------------------------------------------------------- |
| Operating hours        | Accept interactions between 08:45 and 18:15, inclusive.                               |
| Values                 | Accept `val` values of -1 through 4.                                                   |
| Interaction type       | If `type` is present, accept 0 or 1; `type` is required when `val` is -1.              |
| Exhibition eligibility | Accept only `site` IDs present in the database's `exhibit` table.                     |
| Message structure      | Require `at`, `site`, and `val` fields with valid types; extra fields are not rejected solely for being present. |

The timestamp's time component is compared directly with the operating window; the consumer does not convert timestamps between time zones. Supply timestamps in the museum's local time.

## Emergency Email Notifications

The emergency notifier treats an event with `val == -1` and `type == 1` as an emergency. It sends an email only when that event is within 60 minutes of the current time. SMTP and recipient settings must be configured in the environment.

The notifier runs separately from the live data consumer. Use `scripts/start_emergency_notifier_on_ec2.sh` to start it on EC2.

## Repository Structure

```text
.
├── .github/
│   └── skills/
│       ├── clean-code-small-functions/
│       └── simple-unit-test-small-function/
├── data_seeding_pipeline/
├── live_data_pipeline/
├── scripts/
├── terraform/
├── test_suite/
├── visualisations/
│   └── analysis.ipynb
├── env_template
├── requirements.txt
└── README.md
```

`data_seeding_pipeline/` contains the batch ETL, database seeding code, schema, and temporary data handling. `live_data_pipeline/` contains the Kafka consumer and emergency notifier. `terraform/` contains AWS infrastructure definitions, `scripts/` contains deployment and operations commands, `test_suite/` contains automated tests, and `visualisations/` contains the analysis notebook. Project-specific AI development skills are stored in `.github/skills/`.

Install the Python dependencies and run the tests from the repository root:

```bash
python -m pip install -r requirements.txt
python -m pytest test_suite
```

Terraform generates a local `.env` file and an EC2 private key. Terraform variable values and state, `.env` files, and SSH deployment keys are local deployment materials; do not commit them. The deployment scripts expect locally configured deployment keys which are intentionally not included in this repository.

## Batch ETL and Database Seeding

From the repository root, run the historical/exhibition ETL pipeline with:

```bash
python -m data_seeding_pipeline.pipeline --help
python -m data_seeding_pipeline.pipeline --etl --schema data_seeding_pipeline/schema.sql
```

The pipeline can also run individual extraction, transformation, or load phases; see `--help` for the available flags. It needs AWS S3 and database configuration in the environment.

To create or rebuild the reference tables from the S3 exhibition data, run:

```bash
python -m data_seeding_pipeline.seed_database
```

**Warning:** Database seeding drops and recreates project tables. Back up any records that must be kept before running it. The live pipeline's `--reset_db` option invokes this rebuild as well.

## Deployment Guide

### Prerequisites

Install the following tools on the local machine:

* Terraform CLI
* AWS CLI
* Git
* OpenSSH client, including `ssh` and `scp`
* Bash

Configure valid AWS credentials with the permissions required to provision and manage the infrastructure.

Before deployment, provide:

* `terraform/terraform.tfvars`, containing all required Terraform variables
* A dedicated GitHub deploy key pair configured locally for the deployment scripts; do not add the private key to Git
* A valid GitHub repository URL
* The required Kafka, database, and email notification configuration

Do not create `.env` manually; it is generated by Terraform.

### Step 1: Provision AWS Infrastructure

From the repository root, run:

```bash
cd terraform
terraform init
terraform apply
cd ..
```

Review the Terraform plan before approving infrastructure changes.

This step provisions the configured AWS resources and generates the configuration and connection files used by subsequent deployment steps.

### Step 2: Prepare the EC2 Instance

From the repository root, run:

```bash
chmod +x scripts/*.sh
bash scripts/populate_ec2.sh
```

The deployment script transfers the deployment keys, clones the configured repository, installs Python and project dependencies, and copies the `.env` configuration to EC2.

### Step 3: Start the Live Pipeline

Run:

```bash
bash scripts/initial_start_pipeline_on_ec2.sh
```

This starts `live_data_pipeline.live_pipeline --reset_db` on EC2 using `nohup`.

**Important:** `--reset_db` drops and rebuilds the project tables, so existing database records will be lost. Back up any records that must be retained before running this command.

For subsequent starts, use `scripts/start_pipeline_on_ec2.sh` according to the script's implementation.

### Step 4: Verify the Deployment

Connect to the EC2 instance:

```bash
bash scripts/connect_to_ec2.sh
```

On the instance, inspect the pipeline logs:

```bash
source .env
REPO_DIR="$(basename "${GITHUB_REPO_URL%.git}")"
tail -f ~/$REPO_DIR/live_pipeline.log
```

Confirm that:

* The pipeline process is running.
* Kafka connectivity is established.
* PostgreSQL initialisation succeeds.
* Valid events are processed and inserted into the database.
* Emergency events trigger the configured email notification.
* Invalid events are filtered out.

## Jupyter Notebook Analysis

The supplied Jupyter notebook provides a separate environment for analysing the data collected by the pipeline.

Potential areas of investigation include:

* Visitor satisfaction distributions and trends over time.
* Comparisons of ratings across exhibitions.
* Interaction volumes by exhibition and time period.
* Frequency and distribution of assistance requests.
* Emergency incident patterns across participating exhibitions.
* Data quality checks and validation of stored records.

Analysis should use the cleaned records stored in PostgreSQL or an appropriate exported dataset. Where possible, notebooks should document their data sources, transformations, assumptions, and findings so that the analysis is reproducible.

The notebook is intended for exploratory analysis and investigation; it is separate from the long-running Kafka consumer responsible for processing live events.

## Troubleshooting

**Terraform deployment fails**

* Verify AWS credentials and permissions.
* Check that all required Terraform variables are populated.
* Review the Terraform error output and resource configuration.

**EC2 deployment fails during cloning**

* Confirm that `GITHUB_REPO_URL` is configured correctly.
* Verify that the deployment keys have the necessary repository access.
* Check network connectivity and SSH configuration.

**The pipeline starts but no records appear**

* Inspect `live_pipeline.log`.
* Verify Kafka connectivity and topic configuration.
* Check PostgreSQL credentials and connectivity.
* Confirm that incoming events satisfy the validation rules.
* Ensure that the reported exhibitions have corresponding files in the configured S3 bucket.

**Emergency emails are not delivered**

* Verify notification configuration and email service credentials.
* Confirm that emergency events are recognised correctly.
* Review application logs and check the email service's delivery restrictions.

**Notebook analysis cannot access the data**

* Verify database connectivity and credentials.
* Confirm that the notebook environment has the required Python dependencies.
* Check that the database contains processed records.
* Ensure that database access is restricted appropriately and secrets are not embedded in notebooks.

## Security and Operational Considerations

* Never commit AWS credentials, private deployment keys, database passwords, or sensitive `.env` values to version control.
* Restrict access to EC2, RDS, and deployment keys using appropriate AWS security controls.
* Configure security groups to permit only the network traffic required by the application.
* Store and rotate application secrets securely.
* Monitor pipeline failures, database availability, and emergency notification delivery.
* Back up existing records before running commands that may reset the database.
* Consider a managed process supervisor and automated recovery to improve reliability after crashes or instance restarts.
* Avoid committing sensitive data extracts or credentials in Jupyter Notebook outputs.

## Outcome

The project combines batch preparation of exhibition and historical data with live processing of kiosk events, PostgreSQL storage, AWS infrastructure automation, emergency email notifications, and notebook-based analysis.

## AI Usage and Development Skills

AI tools were used as development aids for this project. The project-specific skills I created in [`.github/skills/`](./.github/skills/) helped guide that work:

* [Clean Code With Small Functions](./.github/skills/clean-code-small-functions/SKILL.md) describes a workflow for improving readability by extracting focused, testable functions.
* [Simple Unit Test For Small Functions](./.github/skills/simple-unit-test-small-function/SKILL.md) describes how to add focused, deterministic tests using the repository's pytest conventions.

These skills are development guidance for AI-assisted work; they are not runtime dependencies of the pipelines.
