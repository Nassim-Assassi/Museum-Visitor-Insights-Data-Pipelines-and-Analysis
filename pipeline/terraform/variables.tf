variable "S3_ACCESS_KEY" {
    type = string
    sensitive = true
}

variable "S3_SECRET_ACCESS_KEY" {
    type = string
    sensitive = true
}

variable "VPC_ID" {
    type = string
    description = "The ID of your VPC"
    }

variable "SUBNET_GROUP_NAME" {
    type = string
}

variable "DB_SECURITY_GROUP_NAME" {
    type = string
}
variable "DB_INSTANCE_NAME" {
    type = string
}

variable "DB_PASSWORD" {
    type = string
    sensitive = true
}

variable "DB_USERNAME" {
    type = string
}


variable "DB_NAME" {
    type = string
}

variable "ENV_PATH" {
    type = string
}

variable "ENV_TEMPLATE_PATH" {
    type = string
}