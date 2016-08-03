from setuptools import setup

setup(
    name='despachante',
    version='0.1.0',
    author='Yonatan Romero',
    author_email='yromero@openmailbox.org',
    keywords='netcop despachante',
    packages=['netcop'],
    url='https://github.com/grupo106/despachante',
    description='Despachante de políticas de usuario',
    long_description=open('README.md').read(),
    install_requires=[
        'peewee>=2.8.1',
        'psycopg2>=2.6.2',
        'Jinja2>=2.8',
    ],
    scripts=["scripts/despachar"],
    test_suite="tests",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: Freely Distributable',
    ]
)
