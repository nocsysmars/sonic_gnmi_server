import os, subprocess
from setuptools import setup, find_packages

here = os.path.dirname(os.path.realpath(__file__))
wdir = os.path.join(here, 'nocsys_sonic_gnmi_server')
desc_str=''
if os.path.exists(wdir):
    git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=wdir)

    # use the git hash in the setup
    desc_str = 'git hash [ %s ]' % git_hash.strip()

dependencies = [
#    'features',
#    'grpcio',
#    'pyangbind',
#    'protobuf',
#    'swsssdk',
#    'netaddr'
]

setup(
    name='nocsys_sonic_gnmi_server',
    install_requires=dependencies,
    version='0.1',
    description=desc_str,
    packages=find_packages(),
    license='Apache 2.0',
    author='macauley_cheng',
    author_email='macauley.cheng@nocsys.com.cn',
    entry_points={
        'console_scripts': [
            'nocsys_sonic_gnmi_server = nocsys_sonic_gnmi_server.nocsys_sonic_gnmi_server:main'
        ]
    },
    data_files = [
        ('/etc/systemd/system/', ['nocsys_sonic_gnmi_server.service'])
    ],
    maintainer='macauley_cheng',
    maintainer_email='macauley.cheng@nocsys.com.cn',
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: Linux',
        'Programming Language :: Python',
    ],
)
