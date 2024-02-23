# Define variables
terraform {
  required_version = ">= 1.1.0"

  backend "s3" {
    bucket         = "${var.environment}-${var.project}-bucket"
    key            = "${var.environment}-${var.project}-terraform.tfstate"  # This is the path to the state file in the bucket
    region         = "${var.aws_region}"          # Your AWS region
    dynamodb_table = "${var.environment}-${var.project}-terraform-lock"     # Optional: DynamoDB table for state locking
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.31.0"
    }
  }
}

# Define provider configuration
provider "aws" {
  region = var.aws_region # Update with your desired region
}