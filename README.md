FireCARES [![Build Status](https://travis-ci.org/FireCARES/firecares.svg?branch=master)](https://travis-ci.org/FireCARES/firecares)
=========
The FireCARES application


## Getting Started

A quick way to get started is with Vagrant and VirtualBox.

### Requirements

- [Ansible](http://docs.ansible.com/intro_installation.html)
- [Vagrant](http://www.vagrantup.com/downloads.html)
- [VirtualBox](https://www.virtualbox.org/wiki/Downloads)

```
git clone https://github.com/FireCARES/firecares.git
git clone https://github.com/FireCARES/firecares-ansible.git
cd firecares-ansible
vagrant up
```

Wait a few minutes for the magic to happen.  Access the app by going to this URL: http://192.168.33.15

### Development Considerations

When you install FireCARES using Vagrant, the default configuration will restart the Gunicorn process on every request
so your server-side modifications should immediately show up.

For client-side changes, you currently need to manually run the `collectstatic` in order to update the static assets. You
can run collect static from the `firecares-ansible` directory on the host machine using the following command:

`ansible-playbook vagrant.yml -i vagrant_server --tags django.collectstatic`

### Unit Testing

You'll need the following commands to run all of the unit tests.  Tests are run on each commit automatically, so please run them yourself before you commit.

```
vagrant ssh
sudo su firecares
workon firecares
python manage.py test
```

Additionally, individual tests can be run using the full module/classname/test name path.  If not testing migrations `--keepdb` will significantly speed up the whole process:

```
python manage.py test firecares.firestation.tests.test_metrics:FireDepartmentMetricsTests.test_calculate_structure_counts --noinput --keepdb
```

#### Generating CSS

This project uses LESS CSS pre-processor to generate CSS rules.  To make a modification to a CSS rule, follow these steps:

1. Make the modification in the appropriate LESS file.  For example: [style.less](firecares/firestation/static/firestation/theme/assets/less/style.less)
2. Use the `lessc` command to compile the CSS from LESS and pipe the output to the appropriate location `lessc style.less > ../css/style.css`.

#### Running IPython/Jupyter notebooks

To assist in the transparency of the calculations and data analysis, ipython notebooks in the `/scripts` folder can be run from your vagrant machine via:

```bash
ssh -L 8888:localhost:8888 vagrant@192.168.33.15
sudo chmod a+rwx /run/user/1000
sudo su firecares
workon firecares
python manage.py shell_plus --notebook --no-browser  # follow the instructions that follow in your shell regarding logging into ipython with a token
```
