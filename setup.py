import os
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

# Tell distutils not to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
walk_dir = 'firecares'

excluded_folders = ['uploaded']

for dirpath, dirnames, filenames in os.walk(walk_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.') or dirname in excluded_folders: del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

install_requires = [
        "psycopg2==2.4.5",
        "us==0.9.0",
        "django-phonenumber-field==0.7.2",
        "django-json-field==0.5.7",
        "geopy==1.9.1",
        "django-statsd-mozilla==0.3.15",
        "django-generic-m2m==0.3.0"
]

setup(
    name="firecares",
    version="0.0.1",
    author="Prominent Edge",
    author_email="garnertb@prominentedge.com",
    description="The FireCARES web application",
    long_description=(read('README.rst')),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
    ],
    license="MIT",
    keywords="firecares iaff",
    url='https://github.com/FireCARES/firecares',
    packages=packages,
    data_files=data_files,
    include_package_data=True,
    install_requires=install_requires,
    zip_safe=False,
)
