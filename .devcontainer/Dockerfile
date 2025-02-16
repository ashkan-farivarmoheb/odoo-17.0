FROM odoo:17

# Set the working directory
WORKDIR /mnt/extra-addons
RUN mkdir -p /mnt/data

# Copy your custom addons from the current context
COPY ./extra-addons /mnt/extra-addons
COPY ./resources/odoo-codespace.conf /etc/odoo/odoo.conf
COPY .devcontainer/requirements.txt /mnt/extra-addons/requirements.txt

# Install any additional Python packages if needed
RUN pip install -r /mnt/extra-addons/requirements.txt

# Expose Odoo services
EXPOSE 8069 8072

USER odoo
# Set the default command to run Odoo
CMD ["odoo"]
