# Museum Visitor Insights: Real-Time Data Engineering Pipeline

## Project Overview

This project implements a real-time data engineering pipeline for a natural history museum to collect, validate, store, and analyse visitor interactions from exhibition kiosks.

The kiosks capture visitor satisfaction ratings on a five-point scale, alongside assistance requests and emergency alerts. The project addresses the need for an automated system to process these interactions continuously, maintain data quality, and make the resulting data available for further analysis.

A Python ETL pipeline consumes live events from Apache Kafka, validates and cleans incoming messages, and stores eligible records in a PostgreSQL database hosted on AWS RDS. The pipeline runs continuously on an AWS EC2 instance, with Terraform and shell scripts automating infrastructure provisioning and deployment.

The system also includes an emergency email notification mechanism that alerts security staff when an emergency event is detected. Jupyter Notebook analysis supports exploration of the collected data and investigation of visitor satisfaction and operational trends.

## Project Objectives

* Build an automated, real-time ETL pipeline for kiosk interactions.
* Consume live event data from Apache Kafka.
* Validate, clean, and transform incoming messages before database insertion.
* Store structured interaction records in a remote PostgreSQL database.
* Deploy the pipeline to AWS EC2 for continuous execution.
* Provision cloud infrastructure using Terraform.
* Automate deployment and startup using Bash scripts.
* Send email notifications to security staff when emergency events are detected.
* Use Jupyter Notebooks to explore the data and investigate visitor experience and operational patterns.

## Architecture and Technologies

The pipeline follows a continuous ingestion and processing workflow.

1. **Data ingestion:** Kiosk interactions arrive through an Apache Kafka stream.
2. **Data validation:** Python checks message structure, interaction values, timestamps, and exhibition eligibility.
3. **Data transformation:** Valid events are cleaned and converted into the required database format.
4. **Data storage:** Processed records are inserted into PostgreSQL hosted on AWS RDS.
5. **Emergency notifications:** Detected emergency events trigger email alerts to security staff.
6. **Infrastructure provisioning:** Terraform provisions the required AWS resources.
7. **Deployment and execution:** Bash scripts configure EC2, install dependencies, transfer configuration files, and start the pipeline.
8. **Data analysis:** Jupyter Notebooks support exploratory data analysis using the stored visitor interaction data.

### Technology Stack

* **Python:** ETL processing and Kafka consumption
* **Apache Kafka:** Real-time event streaming
* **PostgreSQL:** Persistent storage for validated interactions
* **AWS EC2:** Continuous execution of the pipeline
* **AWS RDS:** Managed PostgreSQL database hosting
* **AWS S3:** Exhibition data files used to determine eligible exhibitions
* **Terraform:** Infrastructure provisioning
* **Bash and SSH:** Deployment automation and remote server management
* **Jupyter Notebook:** Exploratory data analysis and investigation of visitor interaction patterns
* **Email notifications:** Emergency event alerts for security staff

## Data Validation and Business Rules

The live stream may contain accidental interactions, malformed messages, mechanical errors, or events from unrelated kiosks. The pipeline applies validation rules before inserting records into the database.

| Validation             | Rule                                                                                  |
| ---------------------- | ------------------------------------------------------------------------------------- |
| Operating hours        | Accept interactions between 08:45 and 18:15, inclusive.                               |
| Rating values          | Accept ratings from -1 to 4, inclusive.                                               |
| Interaction type       | Accept only type values of 0 or 1.                                                    |
| Exhibition eligibility | Process only exhibitions represented by the required data files in the AWS S3 bucket. |
| Message structure      | Ignore messages with invalid or unexpected keys.                                      |

These rules help maintain data quality and ensure that downstream analysis uses eligible visitor interactions.

Timestamp validation should account for the museum's local timezone. The accepted operating window includes a 15-minute buffer before opening and after closing to accommodate the defined business rules.

## Emergency Email Notifications

The pipeline includes an emergency email notification mechanism that sends an email to security staff when an emergency event is detected.

This extends the pipeline beyond data ingestion and storage by supporting a more responsive approach to visitor safety. The notification configuration and delivery depend on the email service and credentials supplied to the application.

## Repository Structure

```text
.
├── pipeline/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   ├── populate_ec2.sh
│   ├── start_pipeline_on_ec2.sh
│   ├── initial_start_pipeline_on_ec2.sh
│   ├── connect_to_ec2.sh
│   └── live_pipeline.py
├── notebooks/
│   └── exploratory_analysis.ipynb
├── github_deploy_key
├── github_deploy_key.pub
└── README.md
```

The `pipeline/terraform/` directory contains infrastructure definitions and configuration variables. Deployment scripts prepare the EC2 instance and start the application, while `live_pipeline.py` consumes, validates, and processes live Kafka events.

The `notebooks/` directory is intended for Jupyter Notebook analysis of the collected data. Update the example notebook filename to match the actual repository contents.

Terraform generates the root `.env` file and EC2 private key file as part of infrastructure provisioning. These generated files should not be committed to version control.

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

* `pipeline/terraform/terraform.tfvars`, containing all required Terraform variables
* `github_deploy_key` and `github_deploy_key.pub` in the repository root
* A valid GitHub repository URL
* The required Kafka, database, and email notification configuration

Do not create `.env` manually; it is generated by Terraform.

### Step 1: Provision AWS Infrastructure

From the repository root, run:

```bash
cd pipeline/terraform
terraform init
terraform apply
cd ../..
```

Review the Terraform plan before approving infrastructure changes.

This step provisions the configured AWS resources and generates the configuration and connection files used by subsequent deployment steps.

### Step 2: Prepare the EC2 Instance

From the repository root, run:

```bash
chmod +x pipeline/*.sh
bash pipeline/populate_ec2.sh
```

The deployment script transfers the deployment keys, clones the configured repository, installs Python and project dependencies, and copies the `.env` configuration to EC2.

### Step 3: Start the Live Pipeline

Run:

```bash
bash pipeline/initial_start_pipeline_on_ec2.sh
```

This starts `pipeline/live_pipeline.py --reset_db` on EC2 using `nohup`.

**Important:** The `--reset_db` option may clear existing database records, depending on the implementation. Use it only when a database reset is intended and existing data has been backed up or can safely be discarded.

For subsequent starts, use `pipeline/start_pipeline_on_ec2.sh` according to the script's implementation.

### Step 4: Verify the Deployment

Connect to the EC2 instance:

```bash
bash pipeline/connect_to_ec2.sh
```

On the instance, inspect the pipeline logs:

```bash
source .env
REPO_DIR="$(basename "${GITHUB_REPO_URL%.git}")"
tail -f ~/$REPO_DIR/pipeline/live_pipeline.log
```

Confirm that:

* The pipeline process is running.
* Kafka connectivity is established.
* PostgreSQL initialisation succeeds.
* Valid events are processed and inserted into the database.
* Emergency events trigger the configured email notification.
* Invalid events are filtered out.

## Jupyter Notebook Analysis

Jupyter Notebooks provide a separate environment for analysing the data collected by the pipeline.

Potential areas of investigation include:

* Visitor satisfaction distributions and trends over time.
* Comparisons of ratings across exhibitions.
* Interaction volumes by exhibition and time period.
* Frequency and distribution of assistance requests.
* Emergency incident patterns across participating exhibitions.
* Data quality checks and validation of stored records.

Analysis should use the cleaned records stored in PostgreSQL or an appropriate exported dataset. Where possible, notebooks should document their data sources, transformations, assumptions, and findings so that the analysis is reproducible.

The notebooks are intended for exploratory analysis and investigation; they are separate from the long-running Kafka consumer responsible for processing live events.

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

The project delivers a cloud-hosted, real-time data engineering pipeline that ingests live kiosk events, filters invalid interactions, stores structured records in PostgreSQL, and sends emergency email notifications.

By combining Kafka, Python, PostgreSQL, AWS infrastructure automation, and Jupyter Notebook analysis, the system provides a foundation for reliable data collection and evidence-based investigation of visitor satisfaction, exhibition performance, and operational safety.
