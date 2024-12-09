resource "aws_route53_record" "tisol_nlb_cname" {
  zone_id = data.aws_route53_zone.tisol_com_au_zone.id
  name    = "${var.environment}.${var.project}.awsnp.tisol.com.au"
  type    = "CNAME"
  ttl     = 60

  records = [
    "${aws_lb.aws_lb_nlb.dns_name}"
  ]

  depends_on = [ aws_ecs_service.ecs_service, aws_lb.aws_lb_nlb ]
}
