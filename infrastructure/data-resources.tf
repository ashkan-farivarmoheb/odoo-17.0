data "aws_vpcs" "odoo" {
  filter {
    name   = "tag:Name"
    values = ["${var.environment}-${var.project}-vpc"]
  }
}

data "aws_subnets" "private-odoo" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpcs.odoo.ids[0]]
  }
  filter {
    name   = "map-public-ip-on-launch"
    values = [false]
  }
}

data "aws_subnets" "public-odoo" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpcs.odoo.ids[0]]
  }
  filter {
    name   = "map-public-ip-on-launch"
    values = [true]
  }
}

data "aws_security_groups" "vpc-odoo-asg" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpcs.odoo.ids[0]]
  }
  filter {
    name = "group-name"
    values = [ "${var.environment}-${var.project}-default-sg" ]
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
    base_url = "${var.base_url}"
    edge_url = "${var.edge_url}"
    new_relic_license_key = "${var.new_relic_license_key}"
    new_relic_app_name = "${var.repository_name}-${var.environment}"
  })
}

data "aws_route53_zone" "tisol_com_au_zone" {
  name = "tisol.com.au"
}

data "aws_efs_file_system" "efs" {
  tags = {
    Name = "${var.environment}-${var.project}-efs"
  }
}

data "aws_ecs_cluster" "ecs_cluster" {
  cluster_name = "${var.environment}-${var.project}"
}