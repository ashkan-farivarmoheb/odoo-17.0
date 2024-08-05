FROM ubuntu:jammy
MAINTAINER Ashkan Farivarmoheb <ashkan.farivarmoheb@gmail.com>

SHELL ["/bin/bash", "-xo", "pipefail", "-c"]

# Generate locale C.UTF-8 for postgres and general locale data
ENV LANG en_US.UTF-8
# Set the default config file
ENV ODOO_RC /etc/odoo/odoo-local.conf
ENV APP_CONF /opt/app/conf
ENV AWS_RDS_CA_BUNDLE_URL https://truststore.pki.rds.amazonaws.com
ENV AWS_REGION ap-southeast-2
ENV AWS_RDS_CA_BUNDLE ap-southeast-2-bundle.pem

# Retrieve the target architecture to install the correct wkhtmltopdf package
ARG TARGETARCH
ARG REPOSITORY
ARG GITHUB_TOKEN
ARG GITHUB_SHA
ARG ARTIFACT_ID


# Install pip for Python 3.10 and Upgrade pip and setuptools
RUN apt-get update && \
    apt-get install -y curl \
    python3.10 \
    python3.10-distutils \
    && curl -sSL https://bootstrap.pypa.io/get-pip.py | python3.10 - \
    && python3.10 -m pip install --upgrade pip setuptools

# Install some deps, lessc and less-plugin-clean-css, and wkhtmltopdf
RUN  apt-get update && \
        DEBIAN_FRONTEND=noninteractive \
         apt-get install -y --no-install-recommends \
            nfs-common \
            ca-certificates \
            dirmngr \
            fonts-noto-cjk \
            gnupg \
            python3-dev \
            libxml2-dev \
            libxslt1-dev \
            zlib1g-dev \
            libsasl2-dev \
            libldap2-dev \
            build-essential \
            libffi-dev \
            libmysqlclient-dev \
            libjpeg-dev \
            libpq-dev \
            libjpeg8-dev \
            liblcms2-dev \
            libblas-dev \
            libatlas-base-dev \
            libssl-dev \
            node-less \
            npm \
            python3-magic \
            python3-num2words \
            python3-odf \
            python3-pdfminer \
            python3-pip \
            python3-phonenumbers \
            python3-pyldap \
            python3-qrcode \
            python3-renderpm \
            python3-slugify \
            python3-vobject \
            python3-watchdog \
            python3-xlrd \
            python3-xlwt \
            python3-stdeb \
            fakeroot \
            python3-all \
            dpkg-dev \
            dh-python \
            xz-utils \
            unzip && \
        if [ -z "${TARGETARCH}" ]; then \
            TARGETARCH="$(dpkg --print-architecture)"; \
        fi; \
        WKHTMLTOPDF_ARCH=${TARGETARCH} && \
        case ${TARGETARCH} in \
        "amd64") WKHTMLTOPDF_ARCH=amd64 && WKHTMLTOPDF_SHA=967390a759707337b46d1c02452e2bb6b2dc6d59  ;; \
        "arm64")  WKHTMLTOPDF_SHA=90f6e69896d51ef77339d3f3a20f8582bdf496cc  ;; \
        "ppc64le" | "ppc64el") WKHTMLTOPDF_ARCH=ppc64el && WKHTMLTOPDF_SHA=5312d7d34a25b321282929df82e3574319aed25c  ;; \
        esac \
        && curl -o wkhtmltox.deb -sSL https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.jammy_${WKHTMLTOPDF_ARCH}.deb \
        && echo ${WKHTMLTOPDF_SHA} wkhtmltox.deb | sha1sum -c - \
        && apt-get install -y --no-install-recommends ./wkhtmltox.deb \
        && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* wkhtmltox.deb

ADD requirements.txt /mnt/sources/requirements.txt
RUN pip install -r /mnt/sources/requirements.txt

# install latest postgresql-client
RUN echo 'deb http://apt.postgresql.org/pub/repos/apt/ jammy-pgdg main' > /etc/apt/sources.list.d/pgdg.list \
    && GNUPGHOME="$(mktemp -d)" \
    && export GNUPGHOME \
    && repokey='B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8' \
    && gpg --batch --keyserver keyserver.ubuntu.com --recv-keys "${repokey}" \
    && gpg --batch --armor --export "${repokey}" > /etc/apt/trusted.gpg.d/pgdg.gpg.asc \
    && gpgconf --kill all \
    && rm -rf "$GNUPGHOME" \
    && apt-get update  \
    && apt-get install --no-install-recommends -y postgresql-client \
    && rm -f /etc/apt/sources.list.d/pgdg.list \
    && rm -rf /var/lib/apt/lists/*

# Install rtlcss (on Debian buster)
RUN npm install -g rtlcss

# Create the odoo user
RUN useradd --no-log-init -u 10000 odoo

RUN curl -LJO -H "Authorization: Bearer ${GITHUB_TOKEN}" \
"https://api.github.com/repos/${REPOSITORY}/actions/artifacts/${ARTIFACT_ID}/zip" \
    && unzip *.zip \
    && mv *.deb odoo.deb \
    && apt-get update \
    && apt-get -y install --no-install-recommends ./odoo.deb \
    && rm -rf /var/lib/apt/lists/* odoo.deb

# Copy entrypoint script and Odoo configuration file
COPY ./entrypoint.sh /
ADD resources /etc/odoo/
COPY wait-for-psql.py /usr/local/bin/wait-for-psql.py

# Set permissions
RUN chmod +x /entrypoint.sh && \
    chown odoo /etc/odoo/odoo*.conf && \
    mkdir -p /mnt/{extra-addons,sources} && \
    mkdir -p ${APP_CONF} && \
    chmod -R 775 /mnt && \
    chown -R odoo:odoo /mnt && \
    chown -R odoo:odoo ${APP_CONF}

# Install AWS RDS CA bundle
RUN curl -o ${APP_CONF}/${AWS_RDS_CA_BUNDLE} ${AWS_RDS_CA_BUNDLE_URL}/${AWS_REGION}/${AWS_RDS_CA_BUNDLE} && \
    chmod 644 ${APP_CONF}/${AWS_RDS_CA_BUNDLE} && \
    chown odoo:odoo ${APP_CONF}/${AWS_RDS_CA_BUNDLE}

ADD extra-addons /mnt/extra-addons
# Expose Odoo services
EXPOSE 8069 8071 8072

# Set default user when running the container
USER odoo

ENTRYPOINT ["/entrypoint.sh"]
CMD ["odoo"]
