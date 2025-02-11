FROM odoo:17

# Set the working directory
WORKDIR /mnt/extra-addons

# Copy your custom addons
COPY ./extra-addons /mnt/extra-addons

# Install any additional Python packages if needed
RUN pip install -r ../requirements.txt

# Expose Odoo services
EXPOSE 8069

# Set the default command to run Odoo
CMD ["odoo"]
