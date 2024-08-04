# Create a launch template for ECS instances
resource "aws_launch_template" "odoo_launch_template" {
  name_prefix   = "${var.environment}-${var.project}"
  image_id      = "${var.imageId}"
  instance_type = "${var.instance_type}"
  key_name = "${var.ec2_key_name}"
  vpc_security_group_ids = data.aws_security_groups.vpc-odoo-asg.ids
  iam_instance_profile {
    name = "ecsInstanceRole"
  }

  user_data = base64encode(<<-EOF
                #!/bin/bash
                echo ECS_CLUSTER=${aws_ecs_cluster.ecs_cluster.name} >> /etc/ecs/ecs.config
              EOF
            )

  depends_on = [
    data.aws_security_groups.vpc-odoo-asg,
    aws_ecs_cluster.ecs_cluster
  ]
}
