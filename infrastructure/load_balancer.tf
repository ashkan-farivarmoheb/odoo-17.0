resource "aws_lb" "aws_lb_nlb" {
    name = "${var.environment}-${var.project}-nlb"
    internal = true
    load_balancer_type = "network"
    security_groups = data.aws_security_groups.vpc-odoo-asg.ids
    subnets = data.aws_subnets.public-odoo.ids
    tags = {
        Name = "${var.environment}-${var.project}"
        Environment = "${var.environment}"
    }
}

resource "aws_lb_target_group" "http_tg" {
  name     = "http-tg"
  target_type = "ip" # Use "instance" if targets are EC2 instances.
  port        = 80
  protocol    = "TCP"
  vpc_id = data.aws_vpcs.odoo.ids[0]

  health_check {
    port               = "traffic-port"
    protocol           = "HTTP"
    path               = "/health"
    interval           = 30
    timeout            = 5
    healthy_threshold  = 3
    unhealthy_threshold = 3
  }

  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

resource "aws_lb_listener" "http_listener" {
  load_balancer_arn = aws_lb.aws_lb_nlb.arn
  port              = "80"
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.http_tg.arn
  }
}

resource "aws_lb_target_group" "tcp_tg" {
  name     = "tcp-tg"
  target_type = "ip"
  vpc_id = data.aws_vpcs.odoo.ids[0]
  port     = 443
  protocol = "TCP"
  health_check {
    enabled             = true
    port = "traffic-port"
    protocol            = "TCP"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 5
  }
}

resource "aws_lb_listener" "tcp_listener" {
  load_balancer_arn = aws_lb.aws_lb_nlb.arn
  port              = "443"
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tcp_tg.arn
  }
}
