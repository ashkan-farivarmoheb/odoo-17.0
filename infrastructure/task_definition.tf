resource "aws_ecs_task_definition" "ecs_task_definition" {
    family = "odoo17"
    container_definitions = data.template_file.ecs_task_template.rendered
    volume {
      name = "${var.project}-${var.environment}-efs"
      efs_volume_configuration {
        file_system_id = "${var.nfs_file_system_id}"
        root_directory =  "/"
        transit_encryption = "ENABLED"
        authorization_config {
            access_point_id = "${var.nfs_access_point_id}"
            iam = "ENABLED"
            }
        }
    }
    task_role_arn = "arn:aws:iam::${var.aws_account_id}:role/${var.taskRole}"
    execution_role_arn = "arn:aws:iam::${var.aws_account_id}:role/${var.executionRole}" 
    network_mode = "bridge"
    cpu = "2048"
    memory = "4096"
}   