"""
Setup script per document-folder-monitor-agent.
"""

from setuptools import setup, find_packages

setup(
    name="document-folder-monitor-agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "aiofiles",
        "fastapi",
        "pydantic",
        "python-multipart",
        "requests",
        "watchdog",
        "urllib3"
    ],
    description="Agente per il monitoraggio di cartelle di documenti",
    author="PramaIA",
    author_email="info@pramaia.com",
    python_requires=">=3.8",
)
