data "aws_vpc" "odoo" {
  id = var.vpc_id
}


data "aws_subnets" "private-odoo" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }
  filter {
    name   = "map-public-ip-on-launch"
    values = [false]
  }
}

data "aws_subnets" "public-odoo" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }
  filter {
    name   = "map-public-ip-on-launch"
    values = [true]
  }
}

data "aws_security_groups" "vpc-odoo-asg" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }
  filter {
    name = "group-name"
    values = [ "default" ]
  }
}

data "template_file" "ecs_task_template" {
  template = templatefile("ecs_task_template.json", {
    aws_region = "${var.aws_region}"
    project = "${var.project}"
    environment = "${var.environment}"
    repository_name = "${var.repository_name}"
    aws_account_id = "${var.aws_account_id}"
    tag = "${var.tag}"
    nginx_repository_name = "${var.nginx_repository_name}"
    nginx_tag = "${var.nginx_tag}"
  })
}