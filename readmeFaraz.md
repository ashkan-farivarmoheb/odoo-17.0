

docker rm $(docker ps -q -f status=exited)


docker run -d --name ash-odoo  ash-odoo:latest
 docker build -t ash-odoo:latest .