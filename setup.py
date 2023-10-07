from setuptools import setup, find_packages

setup(
    name='ascii_colors',
    version='0.1.0',
    description='A Python library for pretty console printing with colors and styles',
    long_description='A Python library for displaying text on the console with colors, styles, and exception handling.',
    author='Saifeddine ALOUI (ParisNeo)',
    author_email='aloui.saifeddine@gmail.com',
    url='https://github.com/ParisNeo/console_tools',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',  # Specify Apache 2.0 license
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',  # You can add more supported Python versions
    ],
    python_requires='>=3.8',  # Specify Python version requirements
)
