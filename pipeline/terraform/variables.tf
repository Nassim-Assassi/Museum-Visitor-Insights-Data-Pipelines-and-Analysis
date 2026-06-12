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

variable "VPC_ID" {
    type = string
    description = "The ID of your VPC"
    }

variable "SUBNET_GROUP_NAME" {
    type = string
    description = "The name of the subnet group"
}

variable "DB_SECURITY_GROUP_NAME" {
    type = string
    description = "The name of the DB security group"
}
variable "DB_INSTANCE_NAME" {
    type = string
    description = "The name of the DB instance"
}

variable "DB_PASSWORD" {
    type = string
    sensitive = true
    description = "The password for the DB instance"
}

variable "DB_USERNAME" {
    type = string
    description = "The username for the DB instance"
}


variable "DB_NAME" {
    type = string
    description = "The name of the DB"
}

variable "ENV_PATH" {
    type = string
    description = "The path to the environment configuration"
}

variable "ENV_TEMPLATE_PATH" {
    type = string
    description = "The path to the environment template configuration"
}