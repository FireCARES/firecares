FireCARES [![Build Status](https://travis-ci.org/FireCARES/firecares.svg?branch=master)](https://travis-ci.org/FireCARES/firecares)
=========
The FireCARES application

Getting Started
---------------

A quick way to get started is with Vagrant and VirtualBox.

### Docker
1.  Add `.env.local` file to project root (this file can be obtained in the 1Password account for Firecares).

2.  Run `./build.sh` to build the Docker container.

3.  Run `./run.sh` to start the Firecares app.

4.  Load snapshot of Database (if you don't have .pg_conf, consult a system
    admin for RDS host credentials)
    ```bash
    pg_dump -d "service=exposure" -f firecares.sql
    
    psql -h 0.0.0.0 -U firecares -W firecares < firecares.sql
    ```

5.  Finally, you should be able to open see the app in your browser by opening:
    `0.0.0.0:8000` 

To make tileserver changes, see the Prominent Edge `tessera-ansible` repository, specifically the `firecares` branch

### Pre-commit configuration

We use [pre-commit](http://pre-commit.com/), see how to [install](http://pre-commit.com/#install) in your local repository.

### Unit Testing

You'll need the following commands to run all of the unit tests.  Tests are run on each commit automatically, so please run them yourself before you commit.

#### Docker
```
docker exec -it firecares_firecares_1 bash -c "python ./manage.py test
```


```bash
vagrant ssh
sudo su firecares
workon firecares
python manage.py test
```

Additionally, individual tests can be run using the full module/classname/test name path.  If not testing migrations `--keepdb` will significantly speed up the whole process:

```bash
python manage.py test firecares.firestation.tests.test_metrics:FireDepartmentMetricsTests.test_calculate_structure_counts --noinput --keepdb
```

### Generating CSS

This project uses LESS CSS pre-processor to generate CSS rules.  To make a modification to a CSS rule, follow these steps:

1. Make the modification in the appropriate LESS file.  For example: [style.less](firecares/firestation/static/firestation/theme/assets/less/style.less)
2. Use the `lessc` command to compile the CSS from LESS and pipe the output to the appropriate location `lessc style.less > ../css/style.css`.

### Running IPython/Jupyter notebooks

To assist in the transparency of the calculations and data analysis, ipython notebooks in the `/scripts` folder can be run from your vagrant machine via:

```bash
ssh -L 8888:localhost:8888 vagrant@192.168.33.15
sudo chmod a+rwx /run/user/1000
sudo su firecares
workon firecares
python manage.py shell_plus --notebook --no-browser  # follow the instructions that follow in your shell regarding logging into ipython with a token
```

### Symlinking Static Files

When developing client-side functionality for FireCARES it is often helpful to symlink client-side assets so they refresh when the browser is refreshed.

```bash
vagrant ssh
sudo sed -i '/location \/static/a sendfile off;' /etc/nginx/sites-enabled/firecares
sudo service nginx restart
sudo su firecares
workon firecares
python manage.py collectstatic --noinput -l --clear
```

### Testing osgeo importer within FireCARES

In order to test the osgeo_importer functionality within FireCARES, specifically being able to step via debugger into specific celery processes, you will need to ensure that `CELERY_ALWAYS_EAGER = True`; however, this will not yield a resulting task state other than `PENDING` so items that depend on a celery result will never finish (eg. the osgeo upload dialog will never close on its own).  Additionally, in order to support a multi-node deployment, celery results are stored using the memcached backend and the actual uploaded file is pushed/pulled to/from an S3 bucket as specified by `OSGEO_STORAGE_BUCKET_NAME` before being acted-upon by GDAL, but specifying a bucket name is not necessary for local development as the FireCARES importer and inspector can handle these tasks using a local filesystem.
