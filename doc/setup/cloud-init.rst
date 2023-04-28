Cloud-Init
==========

Following is an example ``cloud-init`` file for a debian host:

.. code-block::
   :linenos:
   :caption: cloud-init.txt

        #cloud-config

        ---
        package_update: true
        package_upgrade: true
        packages:
        - wireguard-tools
        - dnsmasq
        - nginx
        - python3
        - python3-venv
        - python3-pip
        - python3-certbot
        - python3-certbot-nginx
        - git
        - vim-nox
        - dnsutils
        - wget
        users:
        -   groups: users
            name: wireguard-web
            shell: /bin/bash
            sudo:
            -   ALL=(ALL) NOPASSWD: /usr/bin/wg show all endpoints
            -   ALL=(ALL) NOPASSWD: /usr/bin/wg show all latest-handshakes
            ssh_authorized_keys:
            - <key>
        write_files:
        - owner: wireguard-web:users
          path: /home/wireguard-web/wireguard-web/.env
          permissions: '0644'
          content: |
            WIREGUARD_WEB_BASE_URL=http://localhost:8000
            WIREGUARD_STAGING_CONFIG_DIRECTORY=/tmp/wireguard-staging
            WIREGUARD_WEB_EMAIL_HOST=localhost
            WIREGUARD_WEB_EMAIL_PORT=25
            WIREGUARD_WEB_EMAIL_USER=
            WIREGUARD_WEB_EMAIL_PASSWORD=
            WIREGUARD_WEB_EMAIL_TLS=0
            WIREGUARD_WEB_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
            WIREGUARD_WEB_EMAIL_FROM=root@localhost
            WIREGUARD_WEB_DEBUG=0
        runcmd:
        - "wget https://github.com/dunkelstern/wireguard-web/archive/refs/tags/0.4.0.tar.gz -O /home/wireguard-web/wireguard-web-0.4.0.tar.gz"
        - "tar -xvz -C /home/wireguard-web -f /home/wireguard-web/wireguard-web-0.4.0.tar.gz"
        - "su wireguard-web -c 'cd /home/wireguard-web/wireguard-web ; ./setup_wireguard_web.sh'"
        - "systemctl enable --now wireguard-web-config.path"

TODO: Nginx, certbot