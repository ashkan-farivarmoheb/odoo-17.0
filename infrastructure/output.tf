output "odoo-subnets" {
  value = data.aws_subnets.private-odoo.ids
}

output "vpc-odoo-asg" {
  value = data.aws_security_groups.vpc-odoo-asg.ids
}

output "rendered_template" {
  value = data.template_file.ecs_task_template.rendered
}