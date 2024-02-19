

docker rm $(docker ps -q -f status=exited)

docker build -t ash-odoo:latest .
docker run -d --name ash-odoo  ash-odoo:latest


docker exec -it ash-odoo /bin/bash
docker stop $(docker ps -q)



sudo apt-get update
sudo apt-get install -y nfs-common ca-certificates curl dirmngr fonts-noto-cjk gnupg python3-dev libxml2-dev libxslt1-dev zlib1g-dev libsasl2-dev libldap2-dev build-essential libffi-dev libmysqlclient-dev libjpeg-dev libpq-dev libjpeg8-dev liblcms2-dev libblas-dev libatlas-base-dev libssl-dev node-less npm python3-magic python3-num2words python3-odf python3-pdfminer python3-pip python3-phonenumbers python3-pyldap python3-qrcode python3-renderpm python3-setuptools python3-slugify python3-vobject python3-watchdog python3-xlrd python3-xlwt python3-stdeb fakeroot python3-all xz-utils

curl -o wkhtmltox.deb -sSL https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.jammy_amd64.deb
echo "967390a759707337b46d1c02452e2bb6b2dc6d59 wkhtmltox.deb" | sha1sum -c -
sudo apt-get install -y ./wkhtmltox.deb

pip3 install -r requirements.txt

pip3 install --user --force-reinstall cffi

./odoo-bin -c resources/odoo-local.conf --without-demo=all
./odoo-bin -c resources/odoo-local.conf --test-enable --log-level=test --stop-after-init -u account
./odoo-bin -c resources/odoo-local.conf --test-enable --log-level=test  -u account,sale,purchase

sudo mkdir -p /mnt/efs/data/addons/17.0  /mnt/efs/data/sessions



sudo usermod -a -G odoo faraz
sudo pkill -f odoo-bin
# Change the group ownership to 'odoo' for both directories
sudo chown :odoo /mnt/efs/data/addons/17.0 /mnt/efs/data/sessions

# Ensure that the group has read, write, and execute permissions for both directories
sudo chmod 775 /mnt/efs/data/addons/17.0 /mnt/efs/data/sessions 

ps aux | grep odoo-bin
# Switch to the new group using newgrp
newgrp odoo


