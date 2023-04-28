.. index:: direct, deployment, bare-metal, vm

**********************************
Direct/Bare metal or VM deployment
**********************************

.. contents::
   :depth: 3
   :local:

Introduction
============

Direct installation on a VM or bare metal is the preferred option as you have
the best possible customizability. NAT and firewalling is possible with the
default system tooling and you won't have to fiddle with Docker or K8s
specialized configuration.


.. index:: requirements

Requirements
============

This project is designed to be run in a Linux environment, if you want to run
the server on a Mac or on Windows you will probably have to replace the systemd
configuration and some scripts with something that will support that
environment. It could be possible but was not tested by the developers.

For this service to work you'll need some packages from your linux distribution
installed as well as some other requirements:

1. Wireguard compiled into Linux kernel (should be the case for any modern distro)
2. Installed wireguard tools (we need the ``wg-quick`` and ``wg`` tools here)
3. Systemd (sorry non-systemd users, I don't want to debug any other solutions)
4. Python >= 3.9 with ``pip`` and ``virtualenv`` support (extra packages on Ubuntu!)
5. ``sudo``
6. ``dnsmasq`` if you want to use the routed DNS functionality
7. ``nginx`` as a reverse proxy
8. ``certbot`` for Letsencrypt certificates.


.. index:: python, venv, virtualenv, pip, pipenv

Python environment
==================

To be independent from system-packaging quirks and have the correct versions of
all Python dependencies installed we're using a Python virtualenv for this
service.

1. Unpack the release zip/tar.gz and switch to unpacked directory
2. Create python venv: ``python -m venv ~/.virtualenvs/wireguard_web``
3. Activate venv: ``source ~/.virtualenvs/wireguard_web``
4. Install dependency manager: ``pip install pipenv``
5. Install dependencies: ``pipenv sync``

Ideally you'll create a new user for this service to run and add the activation
of the virtualenv to the shell profile, for example:

.. code-block::
   :caption: Example .bash_profile

    #
    # ~/.bash_profile
    #

    [[ -f ~/.bashrc ]] && . ~/.bashrc

    source $HOME/,virtualenvs/bin/activate


.. index:: setup, config, configuration

Application setup
=================

Before you can run the service we need some configuration to be done.


.. index:: env, environment, config, configuration

Environment config
------------------

To configure the application the only file you have to touch is the `.env` file
in the source directory. To get a template for this run ``cp .env.sample .env``.

Description of configuration options:

* ``WIREGUARD_WEB_BASE_URL``: Base URL on which the service will be run. Usually
  you'll run the service behind a reverse proxy like ``nginx`` to terminate
  TLS. Make sure to use the externally visible URL for this.
* ``WIREGUARD_STAGING_CONFIG_DIRECTORY`` where to store new configuration files
  for the systemd services to pick them up and deploy them. See below for a
  description of the mechanism used to deploy the configuration.
* ``WIREGUARD_WEB_EMAIL_*`` settings to be used by the email module to send mail
* ``WIREGUARD_WEB_EMAIL_BACKEND`` this one defines which Django mail backend to
  use. Use one of the following:

  * ``django.core.mail.backends.console.EmailBackend``: just log to console, do
    not send any mail.
  * ``django.core.mail.backends.dummy.EmailBackend``: do not send mails
  * ``django.core.mail.backends.smtp.EmailBackend``: Use SMTP to send mail

  It is possible to add other e-mail backends (for example Amazon SES), please
  consult the Django documentation for more information on that.
* ``WIREGUARD_WEB_DEBUG`` set this to 1 if you need to debug the Django
  application. It is not recommended to run the service on production with this
  set to 1 as it may leak information in generated backtraces.


.. index:: migrate, db, superuser, initial-user

Migrate Database
----------------

Create the database and a first user:

.. code-block::

    python manage.py migrate
    python manage.py createsuperuser


.. index:: sudo, sudoers

Sudo configuration
==================

To allow the web-interface to display wireguard connection information you'll
need to allow some commands to be run via sudo without a password:

.. code-block::
   :linenos:
   :caption: /etc/sudoers.d/wireguard-web
   
    wireguard-web ALL=(ALL) NOPASSWD: /usr/bin/wg show all endpoints
    wireguard-web ALL=(ALL) NOPASSWD: /usr/bin/wg show all latest-handshakes


.. index:: systemd, service, unit

Systemd configuration
=====================

To run the service there are some systemd-unit-files in the ``systemd``
sub-directory of the source-tree. Be aware that you cannot use them as they are
because they contain some placeholders to be replaced by the install-script.

The following placeholders will be replaced:

* ``{path}`` with the path of the source code checkout
* ``{dnsmasq}`` path to ``dnsmasq`` binary
* ``{wg}`` path to ``wg`` binary
* ``{wgquick}`` path to ``wq-quick`` binary
* ``{config}`` path to ``interfaces.conf`` in configured config staging
  directory

Let's go through each file and describe what it does:


.. index:: config, configuration, path, watcher, trigger, systemd

``wireguard-web-config.path``
-----------------------------

.. literalinclude:: ../../systemd/wireguard-web-config.path
   :linenos:

This is a path trigger to run the ``wireguard-web-config.service`` when the
``interfaces.conf`` in the staging directory changes.


.. index:: config, configuration, systemd, service

``wireguard-web-config.service``
--------------------------------

.. literalinclude:: ../../systemd/wireguard-web-config.service
   :linenos:

This service copies the configuration from the staging-directory to the
corresponding ``/etc/wireguard-web`` directory which is only writeable by
the ``root`` user.


.. index:: dns, dnsmasq, systemd, service

``wireguard-web-dnsmasq@.service``
----------------------------------

.. literalinclude:: ../../systemd/wireguard-web-dnsmasq@.service
   :linenos:

This runs the DNS service when enabled for a server. This is a parametrized
service file which can be enabled multiple times for multiple WireGuard
interfaces (example: ``systemctl --enable wireguard-web-dnsmas@wg0`` for the
``wg0`` interface)


.. index:: wg-quick, wireguard, systemd, service

``wireguard-web-wg-quick@.service``
-----------------------------------

.. literalinclude:: ../../systemd/wireguard-web-wg-quick@.service
   :linenos:

This runs a new ``wg-quick`` based WireGuard tunnel. The service is parametrized
with an interface name and loads it's config file from
``/etc/wireguard-web/<interface>.conf``. It may be enabled multiple times for
multiple interfaces to support more than one VPN endpoint.


.. index:: systemd, service, webinterface, web-ui

``wireguard-web-ui.service``
----------------------------

.. literalinclude:: ../../systemd/wireguard-web-ui.service
   :linenos:

This runs the Django web-interface that manages the configuration used by the
services above. You'll have to modify it before installing it to match your
system.

This one runs on ``gunicorn`` so it requires the additional ``gunicorn``
dependency to be installed into your virtualenv.

You can install this by activating your virtualenv:
``source $HOME/.virtualenvs/wireguard-web`` and installing the package with:
``pip install gunicorn``.

Then change the following things in the ``.service``-file:

1. Change ``EnvironmentFile`` to point to your ``.env`` configuration.
2. Change ``WorkingDirectory`` to point to your source-code checkout.
3. Change ``ExecStartPre`` and ``ExecStart`` to point to your virtualenv.
4. Change ``User`` and ``Group`` to match your choosen username and group-name
   for the service. **Do not use root here**.
5. Copy the changed service file to your systemd configuration:
   ``cp wireguard-web-ui.service /etc/systemd/system``
6. Reload the systemd config: ``systemctl daemon-reload``
7. Enable and run the service: ``systemctl enable --now wireguard-web-ui``


.. index:: nginx, reverse-proxy

Nginx configuration
===================

If you want to use ``nginx`` as a reverse proxy to enable SSL/TLS make sure to
allow for plain HTTP access without a redirect too if you want to use zero
configuration peer2peer communication between VPN clients. If you don't need
that feature, feel free to redirect all HTTP traffic to HTTPS.


.. index:: nginx, ssl, tls, certificate, p2p, peer2peer

Example configuration with peer2peer support
--------------------------------------------

If you want to use peer2peer support you'll have to allow plain HTTP to go
through to the application as the peering clients will contact the service on
it's IP address and usually the issued SSL/TLS certificates do not include the
IP in their common name, so nginx has trouble to do propper SNI to route the
requests and the clients get a certificate that is technically not valid.

The Django application automatically sets ``HSTS`` headers when the base URL is
configured as a HTTPS URL, so redirecting your browser based ui to a secure
channel without explicitly redirecting all requests. The API endpoints that
will be called by the peering client will not set ``HSTS`` headers and the API
client will ignore them anyways.

.. code-block::
   :linenos:

    server {
        listen [::]:443 ssl default_server
        listen 443 ssl default_server
        listen 80 default_server;
        listen [::]:80 default_server;

        root /var/www/html;

        index index.html index.htm index.nginx-debian.html;

        server_name my.vpn.dev;

        location / {
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Proxy "";
            proxy_pass_header Server;

            proxy_pass http://127.0.0.1:8000;
            tcp_nodelay on;
        }

        ssl_certificate /etc/letsencrypt/live/my.vpn.dev/fullchain.pem; # managed by Certbot
        ssl_certificate_key /etc/letsencrypt/live/my.vpn.dev/privkey.pem; # managed by Certbot
        include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
        ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
    }

This is a server-snippet that may be used as an item in
``/etc/nginx/sites-available`` and linked to ``/etc/nginx/sites-enabled`` on
Debian or Ubuntu. Alternatively you may replace the ``server`` section of your
``/etc/nginx/nginx.conf`` file.

You'll have to replace the ``server_name`` and the certificate paths with the
domain name of your server (here we used ``my.vpn.dev``).

As you can see the certificates are managed by ``certbot``. For instructions to
enable ``certbot`` see below.


.. index:: nginx, ssl, tls, certificate

Example configuration without peer2peer support
-----------------------------------------------

If you don't need direct peer2peer support for your VPN clients you may redirect
all traffic to https in nginx configuration:

.. code-block::
   :linenos:

    server {
        if ($host = my.vpn.dev) {
            return 301 https://$host$request_uri;
        } # managed by Certbot

        server_name my.vpn.dev;
        listen 80;
        return 404; # managed by Certbot
    }

    server {
        listen [::]:443 ssl default_server
        listen 443 ssl default_server

        root /var/www/html;

        index index.html index.htm index.nginx-debian.html;

        server_name my.vpn.dev;

        location / {
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Proxy "";
            proxy_pass_header Server;

            proxy_pass http://127.0.0.1:8000;
            tcp_nodelay on;
        }

        ssl_certificate /etc/letsencrypt/live/my.vpn.dev/fullchain.pem; # managed by Certbot
        ssl_certificate_key /etc/letsencrypt/live/my.vpn.dev/privkey.pem; # managed by Certbot
        include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
        ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
    }

This is a server-snippet that may be used as an item in
``/etc/nginx/sites-available`` and linked to ``/etc/nginx/sites-enabled`` on
Debian or Ubuntu. Alternatively you may replace the ``server`` section of your
``/etc/nginx/nginx.conf`` file.

You'll have to replace the ``server_name`` and the certificate paths with the
domain name of your server (here we used ``my.vpn.dev``).

As you can see the certificates are managed by ``certbot``. For instructions to
enable ``certbot`` see below.

.. index:: certbot, ssl, tls, certificate, auto-renew

Certbot
=======

To configure ``certbot`` to manage your HTTPS certificates do the following:

1. Install ``certbot`` and it's nginx plugin
2. Make sure your DNS entries are working correctly (at least an ``A``-Record)
3. Configure your web-server like above
4. Run ``certbot`` without any parameters and follow the interactive prompt
   to enable HTTPS support for your domain
5. Install the auto-renewal-service: 
   ``systemctl daemon-reload && systemctl enable --now certbot.timer``

Voila, your system will now automatically maintain it's certificates.

