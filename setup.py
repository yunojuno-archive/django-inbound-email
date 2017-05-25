from os import path, pardir, chdir
from setuptools import setup, find_packages

README = open(path.join(path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
chdir(path.normpath(path.join(path.abspath(__file__), pardir)))

setup(
    name='django-inbound-email',
    version='0.11.4',
    packages=find_packages(),
    install_requires=['Django>=1.8'],
    include_package_data=True,
    description='A Django app for receiving inbound emails.',
    license='MIT',
    long_description=README,
    url='https://github.com/yunojuno/django-inbound-email',
    author='YunoJuno',
    author_email='code@yunojuno.com',
    maintainer='YunoJuno',
    maintainer_email='code@yunojuno.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
