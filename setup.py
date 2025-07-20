#!/usr/bin/env python3
"""
Setup script for SoccerPredictor
"""

from setuptools import setup, find_packages
import os

def read_requirements():
    """Read requirements from requirements.txt"""
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

def read_readme():
    """Read README for long description"""
    if os.path.exists('README.md'):
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    return "SoccerPredictor - ML-based football match prediction system"

setup(
    name="soccerpredictor",
    version="1.0.0",
    description="Machine learning system for predicting football match outcomes",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="SoccerPredictor Team",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'soccerpredictor=main:main',
            'sp-update-data=update_data:main',
            'sp-test-api=test_api_endpoints:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    include_package_data=True,
    zip_safe=False,
)