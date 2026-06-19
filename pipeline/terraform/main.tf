terraform {
  required_providers {
    aws   = { source = "hashicorp/aws" }
    http  = { source = "hashicorp/http" }
    local = { source = "hashicorp/local" }
    tls   = { source = "hashicorp/tls" }
  }
}

provider "aws" {
  region = "eu-west-2"
}

locals {
  repo_root = abspath("${path.root}/../..")
}

# Create an SSH key pair and save the private key locally.

resource "tls_private_key" "ec2_ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "local_sensitive_file" "ec2_private_key" {
  filename        = "${local.repo_root}/${var.INFRASTRUCTURE_NAME}-ec2.pem"
  content         = tls_private_key.ec2_ssh.private_key_pem
  file_permission = "0600"
}

resource "aws_key_pair" "ec2_key" {
  key_name   = "${var.INFRASTRUCTURE_NAME}-ec2"
  public_key = tls_private_key.ec2_ssh.public_key_openssh
}


# Fetch your current public IP address

data "http" "my_public_ip" {
  url = "https://api.ipify.org"
}

# Create a Postgres database:

# Create a security group for the Postgres database instance
resource "aws_security_group" "database_sg" {
  name        = "${var.INFRASTRUCTURE_NAME}-db-sg"
  description = "Allow inbound access to a Postgres database on port 5432"
  vpc_id      = var.VPC_ID
}

# Allow inbound access to the Postgres database from your current public IP address on port 5432
resource "aws_vpc_security_group_ingress_rule" "allow_access_on_postgres_port_for_my_ip" {
  security_group_id = aws_security_group.database_sg.id
  cidr_ipv4         = "${data.http.my_public_ip.response_body}/32"
  from_port         = 5432
  ip_protocol       = "tcp"
  to_port           = 5432
}


# Allow inbound access to the Postgres database from the ec2 instance on port 5432
resource "aws_vpc_security_group_ingress_rule" "allow_access_on_postgres_port_for_ec2" {
  security_group_id            = aws_security_group.database_sg.id
  referenced_security_group_id = aws_security_group.ec2_sg.id
  from_port                    = 5432
  ip_protocol                  = "tcp"
  to_port                      = 5432
}


# Allow inbound access to the Postgres database from tableau client on port 5432
resource "aws_vpc_security_group_ingress_rule" "allow_access_on_postgres_port_for_tableau" {
  security_group_id = aws_security_group.database_sg.id
  cidr_ipv4         = "145.224.200.0/23"
  from_port         = 5432
  ip_protocol       = "tcp"
  to_port           = 5432
}


# Create a Postgres database instance in AWS RDS
resource "aws_db_instance" "postgres_db" {
  identifier             = "${var.INFRASTRUCTURE_NAME}-db"
  instance_class         = "db.t3.micro"
  allocated_storage      = 10
  engine                 = "postgres"
  username               = var.DB_USERNAME
  password               = var.DB_PASSWORD
  db_name                = var.DB_NAME
  db_subnet_group_name   = var.SUBNET_GROUP_NAME
  vpc_security_group_ids = [aws_security_group.database_sg.id]
  publicly_accessible    = true
  skip_final_snapshot    = true
}

# Create an EC2 instance to run the data pipeline

# Create a security group for the EC2 instance
resource "aws_security_group" "ec2_sg" {
  name        = "${var.INFRASTRUCTURE_NAME}-ec2-sg"
  description = "Allow inbound access to the EC2 instance on port 22 for SSH"
  vpc_id      = var.VPC_ID
}

# Allow inbound access to the EC2 instance from your current public IP address on port 22 for SSH
resource "aws_vpc_security_group_ingress_rule" "allow_ssh_from_my_ip" {
  security_group_id = aws_security_group.ec2_sg.id
  cidr_ipv4         = "${data.http.my_public_ip.response_body}/32"
  from_port         = 22
  ip_protocol       = "tcp"
  to_port           = 22
}

# Allow all outbound traffic from the EC2 instance.
resource "aws_vpc_security_group_egress_rule" "allow_all_outbound" {
  security_group_id = aws_security_group.ec2_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"

}

# Create an EC2 instance
resource "aws_instance" "data_pipeline_ec2" {
  ami                         = "ami-07c06c9f04a3f051f" # Ubuntu 22.04 LTS
  instance_type               = "t2.micro"
  key_name                    = aws_key_pair.ec2_key.key_name
  subnet_id                   = var.SUBNET_ID
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  associate_public_ip_address = true
  metadata_options {
    http_tokens = "required"
  }

  tags = {
    Name = "${var.INFRASTRUCTURE_NAME}-ec2"
  }
}



# Generate a .env file with sensitive information
resource "local_sensitive_file" "env_file" {
  filename = "${local.repo_root}/.env"
  content = templatefile("${local.repo_root}/env_template", {
    s3_access_key           = var.S3_ACCESS_KEY
    s3_secret_access_key    = var.S3_SECRET_ACCESS_KEY
    s3_bucket_name          = var.S3_BUCKET_NAME
    kafka_bootstrap_servers = var.KAFKA_BOOTSTRAP_SERVERS
    kafka_security_protocol = var.KAFKA_SECURITY_PROTOCOL
    kafka_sasl_mechanism    = var.KAFKA_SASL_MECHANISM
    kafka_sasl_username     = var.KAFKA_SASL_USERNAME
    kafka_sasl_password     = var.KAFKA_SASL_PASSWORD
    kafka_topic             = var.KAFKA_TOPIC
    infrastructure_name     = var.INFRASTRUCTURE_NAME
    rds_hostname            = aws_db_instance.postgres_db.address
    rds_port                = aws_db_instance.postgres_db.port
    rds_username            = aws_db_instance.postgres_db.username
    rds_password            = aws_db_instance.postgres_db.password
    rds_database_name       = aws_db_instance.postgres_db.db_name
    ec2_key_pair_name       = "${var.INFRASTRUCTURE_NAME}-ec2"
    ec2_instance_public_ip  = aws_instance.data_pipeline_ec2.public_ip
    github_repo_url         = var.GITHUB_REPO_URL
    smtp_server             = var.SMTP_SERVER
    smtp_port               = var.SMTP_PORT
    smtp_username           = var.SMTP_USERNAME
    smtp_password           = var.SMTP_PASSWORD
    email_from_address      = var.EMAIL_FROM_ADDRESS
    alerts_recipient_email_address = var.ALERTS_RECIPIENT_EMAIL_ADDRESS
  })
  file_permission = "0600"
}