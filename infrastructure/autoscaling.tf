resource "aws_autoscaling_group" "ecs_asg" {
  name                   = "${var.environment}-${var.project}"
  min_size               = "${var.min_size_asg}"
  max_size               = "${var.max_size_asg}"
  desired_capacity       = "${var.desired_size_asg}"
  termination_policies = [ "OldestLaunchTemplate" ]
  default_cooldown = 60
  vpc_zone_identifier    = data.aws_subnets.private-odoo.ids
  health_check_grace_period = 300
  health_check_type = "EC2"

  launch_template {
    id      = aws_launch_template.odoo_launch_template.id
    version = "$Latest"
  }

  tag {
   key                 = "Name"
   value               = "${var.environment}-${var.project}"
   propagate_at_launch = true 
 }
  depends_on = [
    data.aws_subnets.private-odoo
  ]

   lifecycle { 
    ignore_changes = [desired_capacity]
  }

  initial_lifecycle_hook {
    name                 = "foobar"
    default_result       = "CONTINUE"
    heartbeat_timeout    = 30
    lifecycle_transition = "autoscaling:EC2_INSTANCE_LAUNCHING"
  }
}

resource "aws_autoscaling_policy" "scale_down" {
  name                   = "${var.environment}-${var.project}_scale_down"
  autoscaling_group_name = aws_autoscaling_group.ecs_asg.name
  adjustment_type        = "ChangeInCapacity"
  scaling_adjustment     = -1
  cooldown               = 120
}

resource "aws_autoscaling_policy" "scale_up" {
  name                   = "${var.environment}-${var.project}_scale_up"
  autoscaling_group_name = aws_autoscaling_group.ecs_asg.name
  adjustment_type        = "ChangeInCapacity"
  scaling_adjustment     = 1
  cooldown               = 120
}

resource "aws_cloudwatch_metric_alarm" "scale_down" {
  alarm_description   = "Monitors CPU utilization"
  alarm_actions       = [aws_autoscaling_policy.scale_down.arn]
  alarm_name          = "${var.environment}-${var.project}_scale_down"
  comparison_operator = "LessThanOrEqualToThreshold"
  namespace           = "AWS/EC2"
  metric_name         = "CPUUtilization"
  threshold           = "25"
  evaluation_periods  = "5"
  period              = "30"
  statistic           = "Average"

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.ecs_asg.name
  }
}