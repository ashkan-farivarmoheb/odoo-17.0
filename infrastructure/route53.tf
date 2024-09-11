resource "aws_route53_zone" "private_zone" {
  name = "erp.tisol.com.au"
  vpc {
    vpc_id = data.aws_vpcs.odoo.ids[0]
  }
  private_zone = true
}

resource "aws_route53_record" "tisol_nlb_cname" {
  zone_id = aws_route53_zone.private_zone.id
  name    = "erp.tisol.com.au"
  type    = "CNAME"
  ttl     = 60

  records = [
    "${aws_lb.aws_lb_nlb.dns_name}"
  ]

  depends_on = [ aws_ecs_service.ecs_service, aws_lb.aws_lb_nlb ]
}

resource "aws_route53_record" "public_to_internal" {
  zone_id = data.aws_route53_zone.public_zone.zone_id
  name    = "erp.tisol.com.au"
  type    = "CNAME"
  ttl     = 60

  records = [
    aws_route53_record.aws_lb_nlb.fqdn
  ]
}
