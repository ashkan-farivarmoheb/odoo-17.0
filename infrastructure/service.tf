resource "aws_ecs_service" "ecs_service" {
  name            = "${var.environment}-${var.project}-service"
  cluster         = data.aws_ecs_cluster.ecs_cluster.id
  task_definition = aws_ecs_task_definition.ecs_task_definition.arn
  desired_count   = var.desired_task_count
  launch_type     = "EC2"
  wait_for_steady_state = true
  scheduling_strategy = "REPLICA"

  network_configuration {
    subnets          = data.aws_subnets.private-odoo.ids
    security_groups = data.aws_security_groups.vpc-odoo-asg.ids
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.tcp_tg.id
    container_name   = "nginx"
    container_port   = 443 
  }
  
  depends_on = [ aws_lb.aws_lb_nlb ]
}