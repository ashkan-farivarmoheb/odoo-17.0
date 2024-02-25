# Define variables
terraform {
  required_version = ">= 1.1.0"

  backend "s3" {
    key            = "odoo/terraform.tfstate"  # This is the path to the state file in the bucket
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