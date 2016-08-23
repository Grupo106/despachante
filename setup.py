from setuptools import setup

setup(
    name='despachante',
    version='0.2.0',
    author='Yonatan Romero',
    author_email='yromero@openmailbox.org',
    keywords='netcop despachante',
    packages=['netcop.despachante', 'netcop.despachante.templates'],
    url='https://github.com/grupo106/despachante',
    namespace_packages = ['netcop'],
   description='Despachante de politicas de usuario',
    long_description=open('README.md').read(),
    package_data = {
        # Incluir templates de Jinja2
        '': ['*.j2'],
    },
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
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: Freely Distributable',
    ]
)
