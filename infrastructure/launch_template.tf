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

# resource "aws_security_group" "odoo-ec2" {
#     name        = "${var.environment}-${var.project}"
#     description = "${var.environment}-${var.project}"
#     vpc_id      = data.aws_vpc.odoo.id
#     tags = {
#         Name = "${var.environment}-${var.project}"
#         Environment = "${var.environment}"
#     }
# }

# resource "aws_security_group_rule" "allow_inbound_nfs_ipv4" {
#   security_group_id = aws_security_group.odoo-ec2.id
#   protocol = "tcp"
#   type = "ingress"
#   from_port = 2049
#   to_port = 2049
#   source_security_group_id = data.aws_vpc.odoo.id
# }

# resource "aws_security_group_rule" "allow_nfs_ipv4" {
#   security_group_id = aws_security_group.odoo-ec2.id
#   protocol = "tcp"
#   type = "ingress"
#   from_port = 80
#   to_port = 80
#   cidr_blocks = ["0.0.0.0/0"]
# }

# resource "aws_security_group_rule" "allow_outbound_nfs_ipv4" {
#   security_group_id = aws_security_group.odoo-ec2.id
#   protocol = "tcp"
#   type = "egress"
#   from_port = 2049
#   to_port = 2049
#   source_security_group_id = data.aws_vpc.odoo.id
# }