resource "aws_ecs_task_definition" "ecs_task_definition" {
    family = "odoo17"
    container_definitions = data.template_file.ecs_task_template.rendered
    volume {
      name = "${var.environment}-${var.project}-efs"
      efs_volume_configuration {
        file_system_id = data.aws_efs_file_systems.efs.ids[0]
        root_directory =  "/"
        transit_encryption = "ENABLED"
        authorization_config {
            access_point_id = data.aws_efs_access_point.odoo_access.ids[0]
            iam = "ENABLED"
            }
        }
    }
    task_role_arn = "arn:aws:iam::${var.aws_account_id}:role/${var.environment}-${var.project}-task-exec-role"
    execution_role_arn = "arn:aws:iam::${var.aws_account_id}:role/${var.environment}-${var.project}-task-exec-role"
    network_mode = "bridge"
    cpu = "2048"
    memory = "4096"
}
