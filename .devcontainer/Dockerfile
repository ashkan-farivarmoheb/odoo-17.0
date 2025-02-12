FROM odoo:17

USER root

# Install Docker
RUN apt-get update && \
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        software-properties-common && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" && \
    apt-get update && \
    apt-get install -y docker-ce docker-ce-cli containerd.io && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Docker Compose
RUN rm -f /usr/local/bin/docker-compose && \
    VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 2) && \
    curl -L "https://github.com/docker/compose/releases/download/${VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && \
    chmod +x /usr/local/bin/docker-compose

# Verify installations
RUN docker --version && docker-compose --version

# Set the working directory
WORKDIR /mnt/extra-addons

# Copy your custom addons from the current context
COPY ./extra-addons /mnt/extra-addons
COPY ./resources/odoo-local.conf /etc/odoo/odoo.conf
COPY .devcontainer/requirements.txt /mnt/extra-addons/requirements.txt

# Install any additional Python packages if needed
RUN pip install -r /mnt/extra-addons/requirements.txt

# Expose Odoo services
EXPOSE 8069

USER odoo
# Set the default command to run Odoo
CMD ["odoo"]
