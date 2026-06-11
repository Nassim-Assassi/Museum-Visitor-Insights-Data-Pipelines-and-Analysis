provider "aws" {
}

# make a security group in the cloud 
# allows inbound access to a database

resource "aws_security_group" "database_sg" {
    name        = var.DB_SECURITY_GROUP_NAME
    description = "Allow inbound access to a postgres database on port 5432"
    vpc_id      = var.VPC_ID
}

# Fetch your current public IP address
data "http" "my_public_ip" {
  url = "https://api.ipify.org"
}

resource "aws_vpc_security_group_ingress_rule" "allow_access_on_postgres_port_for_my_ip" {
  security_group_id = aws_security_group.database_sg.id
  cidr_ipv4         = "${data.http.my_public_ip.response_body}/32"
  from_port         = 5432
  ip_protocol       = "tcp"
  to_port           = 5432
}

resource "aws_db_instance" "postgres_db" {
  identifier           = var.DB_INSTANCE_NAME
  instance_class       = "db.t3.micro"
  allocated_storage    = 10
  engine               = "postgres"
  username             = var.DB_USERNAME
  password             = var.DB_PASSWORD
  db_name              = var.DB_NAME
  db_subnet_group_name = var.SUBNET_GROUP_NAME
  vpc_security_group_ids = [aws_security_group.database_sg.id]
  publicly_accessible = true
  skip_final_snapshot  = true
}

resource "local_sensitive_file" "env_file" {
  filename = var.ENV_PATH
  content  = templatefile(var.ENV_TEMPLATE_PATH, {
    s3_access_key     = var.S3_ACCESS_KEY
    s3_secret_access_key     = var.S3_SECRET_ACCESS_KEY
    rds_hostname      = aws_db_instance.postgres_db.address
    rds_port          = aws_db_instance.postgres_db.port
    rds_username      = aws_db_instance.postgres_db.username
    rds_password      = aws_db_instance.postgres_db.password
    rds_database_name = aws_db_instance.postgres_db.db_name
  })
}