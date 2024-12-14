variable "aws_region" {
  description = "The aws region. https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html"
  type        = string
  default     = "ap-southeast-2"
}

variable "aws_account_id" {
  description = "aws account id"
  type = string
}

variable "environment" {
  description = "environment"
  type = string
}

variable "project" {
  description = "Project name"
  type = string
}

variable "repository_name" {
  description = "repository name"
  type = string
}

variable "nginx_repository_name" {
  description = "nginx repository name"
  type = string
}

variable "desired_task_count" {
  description = "Desired number of tasks for the ECS service"
  default     = 2
}

variable "imageId" {
  description = "Image ID"
  type = string
}

variable "instance_type" {
  description = "Instance type"
  type = string
}

variable "ec2_key_name" {
  description = "Ec2 Key Name"
  type        = string
}

variable "nfs_access_point_id" {
  description = "NFS access point"
  type        = string
}

variable "min_size_asg" {
  description = "ASG min size"
  type        = number
}

variable "max_size_asg" {
  description = "ASG min size"
  type        = number
}

variable "desired_size_asg" {
  description = "ASG min size"
  type        = number
}

variable "tag" {
  description = "service tag"
  type        = string
}

variable "nginx_tag" {
  description = "nginx tag"
  type        = string
}


variable "base_url" {
  description = "base url"
  type = string
}

variable "edge_url" {
  description = "edge url"
  type = string
}

variable "new_relic_license_key" {
  description = "new relic license key"
  type = string
}