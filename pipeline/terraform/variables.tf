variable "S3_ACCESS_KEY" {
  type        = string
  sensitive   = true
  description = "The access key for your S3 bucket"
}

variable "S3_SECRET_ACCESS_KEY" {
  type        = string
  sensitive   = true
  description = "The secret access key for your S3 bucket"
}

variable "S3_BUCKET_NAME" {
  type        = string
  sensitive   = true
  description = "The name of your S3 bucket"
}

variable "KAFKA_BOOTSTRAP_SERVERS" {
  type        = string
  sensitive   = true
  description = "The bootstrap servers for your Kafka cluster"
}

variable "KAFKA_SECURITY_PROTOCOL" {
  type        = string
  sensitive   = true
  description = "The security protocol for your Kafka cluster"
}

variable "KAFKA_SASL_MECHANISM" {
  type        = string
  sensitive   = true
  description = "The SASL mechanism for your Kafka cluster"
}

variable "KAFKA_SASL_USERNAME" {
  type        = string
  sensitive   = true
  description = "The SASL username for your Kafka cluster"
}

variable "KAFKA_SASL_PASSWORD" {
  type        = string
  sensitive   = true
  description = "The SASL password for your Kafka cluster"
}

variable "KAFKA_TOPIC" {
  type        = string
  sensitive   = true
  description = "The topic for your Kafka cluster"
}

variable "VPC_ID" {
  type        = string
  sensitive   = true
  description = "The ID of your VPC"
}

variable "SUBNET_GROUP_NAME" {
  type        = string
  sensitive   = true
  description = "The name of the subnet group"
}


variable "DB_PASSWORD" {
  type        = string
  sensitive   = true
  description = "The password for the DB instance"
}

variable "DB_USERNAME" {
  type        = string
  sensitive   = true
  description = "The username for the DB instance"
}


variable "DB_NAME" {
  type        = string
  sensitive   = true
  description = "The name of the DB"
}



variable "SUBNET_ID" {
  type        = string
  sensitive   = true
  description = "The subnet ID where the EC2 instance will be created"
}

variable "GITHUB_REPO_URL" {
  type        = string
  default     = ""
  description = "GitHub repository URL to clone on EC2. Used for bootstrapping the EC2 instance."
}

variable "INFRASTRUCTURE_NAME" {
  type        = string
  sensitive   = true
  description = "The name of the infrastructure/project. Used for naming resources."
}
