FROM odoo:17

# Set the working directory
WORKDIR /mnt/extra-addons

# Copy your custom addons from the current context
# COPY ./extra-addons /mnt/extra-addons
# COPY ./resources/odoo-local.conf /etc/odoo/odoo.conf

# Copy the requirements.txt file if it exists in the root directory
COPY .devcontainer/requirements.txt /mnt/extra-addons/requirements.txt

# Install any additional Python packages if needed
RUN pip install -r /mnt/extra-addons/requirements.txt

# Expose Odoo services
EXPOSE 8069

# Set the default command to run Odoo
CMD ["odoo"]
