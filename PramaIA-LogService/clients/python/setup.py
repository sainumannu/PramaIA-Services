"""
Setup script per il client Python di PramaIA-LogService.
"""

from setuptools import setup

setup(
    name="pramaialog",
    version="1.0.0",
    description="Client Python per il servizio di logging PramaIA",
    author="PramaIA Team",
    author_email="info@pramaia.com",
    py_modules=["pramaialog"],  # Usa py_modules invece di packages
    install_requires=[
        "requests>=2.25.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
