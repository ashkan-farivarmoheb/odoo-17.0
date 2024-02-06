

docker rm $(docker ps -q -f status=exited)

docker build -t ash-odoo:latest .
docker run -d --name ash-odoo  ash-odoo:latest


docker exec -it ash-odoo /bin/bash
docker stop $(docker ps -q)
