variable "S3_ACCESS_KEY" {
    type = string
    sensitive = true
    description = "The access key for your S3 bucket"
}

variable "S3_SECRET_ACCESS_KEY" {
    type = string
    sensitive = true
    description = "The secret access key for your S3 bucket"
}

variable "S3_BUCKET_NAME" {
    type = string
    sensitive = true
    description = "The name of your S3 bucket"
}

variable "KAFKA_BOOTSTRAP_SERVERS" {
    type = string
    sensitive = true
    description = "The bootstrap servers for your Kafka cluster"
}

variable "KAFKA_SECURITY_PROTOCOL" {
    type = string
    sensitive = true
    description = "The security protocol for your Kafka cluster"
}

variable "KAFKA_SASL_MECHANISM" {
    type = string
    sensitive = true
    description = "The SASL mechanism for your Kafka cluster"
}

variable "KAFKA_SASL_USERNAME" {
    type = string
    sensitive = true
    description = "The SASL username for your Kafka cluster"
}

variable "KAFKA_SASL_PASSWORD" {
    type = string
    sensitive = true
    description = "The SASL password for your Kafka cluster"
}

variable "KAFKA_TOPIC" {
    type = string
    sensitive = true
    description = "The topic for your Kafka cluster"
}

variable "VPC_ID" {
    type = string
    sensitive = true
    description = "The ID of your VPC"
    }

variable "SUBNET_GROUP_NAME" {
    type = string
    sensitive = true
    description = "The name of the subnet group"
}

variable "DB_SECURITY_GROUP_NAME" {
    type = string
    sensitive = true
    description = "The name of the DB security group"
}
variable "DB_INSTANCE_NAME" {
    type = string
    sensitive = true
    description = "The name of the DB instance"
}

variable "DB_PASSWORD" {
    type = string
    sensitive = true
    description = "The password for the DB instance"
}

variable "DB_USERNAME" {
    type = string
    sensitive = true
    description = "The username for the DB instance"
}


variable "DB_NAME" {
    type = string
    sensitive = true
    description = "The name of the DB"
}

variable "EC2_SECURITY_GROUP_NAME" {
    type = string
    sensitive = true
    description = "The name of the EC2 security group"
}

variable "EC2_INSTANCE_NAME" {
    type = string
    sensitive = true
    description = "The Name tag for the EC2 instance"
}

variable "EC2_KEY_PAIR_NAME" {
    type = string
    sensitive = true
    description = "The name of the EC2 key pair for SSH access"
}

variable "SUBNET_ID" {
    type = string
    sensitive = true
    description = "The subnet ID where the EC2 instance will be created"
}

variable "GITHUB_REPO_URL" {
    type = string
    default = ""
    description = "GitHub repository URL to clone on EC2. Leave empty to skip clone."
}

variable "GITHUB_BRANCH" {
    type = string
    default = "main"
    description = "Git branch to checkout on EC2 bootstrap"
}

variable "BASE_DIR" {
    type = string
    sensitive = true
    description = "Base directory where .env, env.template and generated PEM are located"
}
