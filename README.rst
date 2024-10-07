Chalix Edu Platform
#################
| |License: AGPL v3| |Status| |Python CI|

.. |License: AGPL v3| image:: https://img.shields.io/badge/License-AGPL_v3-blue.svg
  :target: https://www.gnu.org/licenses/agpl-3.0

.. |Python CI| image:: https://github.com/openedx/edx-platform/actions/workflows/unit-tests.yml/badge.svg
  :target: https://github.com/openedx/edx-platform/actions/workflows/unit-tests.yml

.. |Status| image:: https://img.shields.io/badge/status-maintained-31c653

Purpose
*******
The `Chalix Edu Platform <http://nuc.ali/>`_ is a service-oriented platform for authoring and
delivering online learning at any scale.  The platform is written in
Python and JavaScript and makes extensive use of the Django
framework. At the highest level, the platform is composed of a
monolith, some independently deployable applications (IDAs), and
micro-frontends (MFEs) based on the ReactJS.

This repository hosts the monolith at the center of the Chalix Edu
platform.  Functionally, the edx-platform repository provides two services:

* CMS (Content Management Service), which powers Chalix Edu Studio, the platform's learning content authoring environment; and
* LMS (Learning Management Service), which delivers learning content.

Documentation
*************

Documentation can be found at https://docs.openedx.org/projects/edx-platform.

Getting Started
***************

It is also possible to spin up an Chalix Edu platform directly on a Linux host.
This method is less common and mostly undocumented. The Chalix Edu community will
only be able to provided limited support for it.

Running "bare metal" is only advisable for (a) developers seeking an
adventure and (b) experienced system administrators who are willing to take the
complexity of Chalix Edu configuration and deployment into their own hands.

System Dependencies
-------------------

Interperters/Tools:

* Python 3.11

* Node 18

Services:

* MySQL 8.0

* Mongo 7.x

* Memcached

Language Packages:

* Frontend:

  - ``npm clean-install`` (production)
  - ``npm clean-install --dev`` (development)

* Backend build:

  - ``pip install -r requirements/edx/assets.txt``

* Backend application:

  - ``pip install -r requirements/edx/base.txt`` (production)
  - ``pip install -r requirements/edx/dev.txt`` (development)

Build Steps
-----------

Create two MySQL databases and a MySQL user with write permissions to both, and configure
Django to use them by updating the ``DATABASES`` setting.

Then, run migrations::

  ./manage.py lms migrate
  ./manage.py lms migrate --database=student_module_history
  ./manage.py cms migrate

Build static assets (for more details, see `building static
assets`_)::

  npm run build  # or, 'build-dev'

Download locales and collect static assets (can be skipped for development
sites)::

  make pull_translations
  ./manage.py lms collectstatic
  ./manage.py cms collectstatic

Run the Platform
----------------

First, ensure MySQL, Mongo, and Memcached are running.

Start the LMS::

  ./manage.py lms runserver

Start the CMS::

  ./manage.py cms runserver

This will give you a mostly-headless Chalix Edu platform. Most frontends have
been migrated to "Micro-Frontends (MFEs)" which need to be installed and run
separately. At a bare minimum, you will need to run the `Authentication MFE`_,
`Learner Home MFE`_, and `Learning MFE`_ in order meaningfully navigate the UI.

.. _Tutor: https://github.com/overhangio/tutor
.. _Site Ops home on docs.openedx.org: https://docs.openedx.org/en/latest/site_ops/index.html
.. _development mode: https://docs.tutor.edly.io/dev.html
.. _building static assets: ./docs/references/static-assets.rst
.. _Authentication MFE: https://github.com/openedx/frontend-app-authn/
.. _Learner Home MFE: https://github.com/openedx/frontend-app-learner-dashboard
.. _Learning MFE: https://github.com/openedx/frontend-app-learning/

License
*******

The code in this repository is licensed under version 3 of the AGPL
unless otherwise noted. Please see the `LICENSE`_ file for details.

.. _LICENSE: https://github.com/openedx/edx-platform/blob/master/LICENSE


More about Chalix Edu
*******************

See the `Chalix Edu site`_ to learn more about the Chalix Edu world. You can find
information about hosting, extending, and contributing to Chalix Edu software. In
addition, the Chalix Edu site provides product announcements, the Chalix Edu blog,
and other rich community resources.

.. _Chalix Edu site: http://nuc.ali/

Current Implementation
**********************
1. Additional plugins:
- [tutor-minio](https://github.com/overhangio/tutor-minio)
- [tutor-contrib-videoupload](https://github.com/dungdl/tutor-contrib-videoupload)

2. Custom tutor core:
- [alitutor](https://github.com/Alimento-Team/tutor)

3. Adjust tutor configs:
3.1. Caddyfile:
```caddy
# Global configuration
{

    
    
}

# proxy directive snippet (with logging) to be used as follows:
#
#     import proxy "containername:port"
(proxy) {
    log {
        output stdout
        format filter {
            wrap json
            fields {
                common_log delete
                request>headers delete
                resp_headers delete
                tls delete
            }
        }
    }

    # This will compress requests that matches the default criteria set by Caddy.
    # see https://caddyserver.com/docs/caddyfile/directives/encode
    # for information about the defaults; i.e. how/when this will be applied.
    encode gzip

    reverse_proxy {args.0} {
        header_up X-Forwarded-Port 80
    }

    
}

nuc.ali{$default_site_port}, preview.nuc.ali{$default_site_port} {
    @favicon_matcher {
        path_regexp ^/favicon.ico$
    }
    rewrite @favicon_matcher /theming/asset/images/favicon.ico

    # Limit profile image upload size
    handle_path /api/profile_images/*/*/upload {
        request_body {
            max_size 1MB
        }
    }

    import proxy "lms:8000"

    

    handle_path /* {
        request_body {
            max_size 4MB
        }
    }
}

studio.nuc.ali{$default_site_port} {
    @favicon_matcher {
        path_regexp ^/favicon.ico$
    }
    rewrite @favicon_matcher /theming/asset/images/favicon.ico

    import proxy "cms:8000"

    

    handle_path /* {
        request_body {
            max_size 250MB
        }
    }
}

apps.nuc.ali{$default_site_port} {
    redir / http://nuc.ali
    request_body {
        max_size 2MB
    }
    import proxy "mfe:8002"
}
# MinIO
files.nuc.ali{$default_site_port} {
    @video_id {
        query x-amz-meta-client_video_id=*
    }
    rewrite @video_id {http.request.uri.path}?{http.request.uri.query}
    header @video_id X-Amz-Meta-Client_video_id {http.request.uri.query.x-amz-meta-client_video_id}

    @course_key {
        query x-amz-meta-course_key=*
    }
    rewrite @course_key {http.request.uri.path}?{http.request.uri.query}
    header @course_key X-Amz-Meta-Course_key {http.request.uri.query.x-amz-meta-course_key}
    import proxy "minio:9000"
}
minio.nuc.ali{$default_site_port} {
    import proxy "minio:9001"
}%
```
3.2. config.yml:
```yaml
CMS_HOST: studio.nuc.ali
CMS_OAUTH2_SECRET: lYzC4JrsY9XIM4EQoxm7QqRF
CONTACT_EMAIL: alimento128@gmail.com
DOCKER_IMAGE_OPENEDX: overhangio/openedx:18.1.3-indigo
ELASTICSEARCH_HEAP_SIZE: 1g
ELASTICSEARCH_HOST: elasticsearch
ELASTICSEARCH_PORT: 9200
ELASTICSEARCH_SCHEME: http
ENABLE_HTTPS: false
ID: k6hoMKjzcaottLGPv369QXr8
JWT_RSA_PRIVATE_KEY: '-----BEGIN RSA PRIVATE KEY-----
<SOME PRIVATE KEY>
  -----END RSA PRIVATE KEY-----'
LANGUAGE_CODE: en
LMS_HOST: nuc.ali
MINIO_AWS_SECRET_ACCESS_KEY: RANDOM_MINIO_AWS_SECRET_ACCESS_KEY
MINIO_DOCKER_IMAGE: quay.io/minio/minio:RELEASE.2024-09-22T00-33-43Z
MINIO_MC_DOCKER_IMAGE: docker.io/minio/mc:RELEASE.2024-09-16T17-43-14Z
MONGODB_HOST: mongo
MONGODB_PASSWORD: alimento128
MONGODB_USERNAME: admin
MOUNTS:
- /home/alimento/dungdl/code/chalix-ed
MYSQL_HOST: mysql
MYSQL_PORT: 3306
MYSQL_ROOT_PASSWORD: alimento128
MYSQL_ROOT_USERNAME: root
OPENEDX_AWS_ACCESS_KEY: alimento
OPENEDX_AWS_SECRET_ACCESS_KEY: OPENEDX_AWS_SECRET_ACCESS_KEY
OPENEDX_CMS_UWSGI_WORKERS: 8
OPENEDX_LMS_UWSGI_WORKERS: 8
OPENEDX_MYSQL_PASSWORD: RANDOM_OPENEDX_MYSQL_PASSWORD
OPENEDX_SECRET_KEY: RANDOM_OPENEDX_SECRET_KEY 
PLATFORM_NAME: Chalix Edu
PLUGINS:
- indigo
- mfe
- minio
- videoupload
PLUGIN_INDEXES:
- https://overhang.io/tutor/main
REDIS_HOST: redis
REDIS_PORT: 6379
RUN_ELASTICSEARCH: false
RUN_FORUM: false
RUN_MONGODB: false
RUN_MYSQL: false
RUN_REDIS: false
RUN_SMTP: false
```