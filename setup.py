from setuptools import setup

setup(
    name='actualizador',
    version='0.1.0',
    author='Yonatan Romero',
    author_email='yromero@openmailbox.org',
    keywords='netcop actualizador',
    packages=['netcop'],
    url='https://github.com/grupo106/actualizador',
    description='Actualizador de clases de trafico de Netcop',
    long_description=open('README.md').read(),
    install_requires='requests>=2.4.3',
    scripts=["scripts/actualizador"],
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
