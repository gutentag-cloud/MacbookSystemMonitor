from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="macbook-monitor",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive system monitoring tool for MacBook",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/macbook-monitor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: MacOS :: MacOS X",
    ],
    python_requires=">=3.8",
    install_requires=[
        "psutil>=5.9.0",
        "rich>=13.0.0",
        "click>=8.0.0",
        "pyyaml>=6.0",
        "pandas>=1.5.0",
        "plotext>=5.0.0",
    ],
    entry_points={
        "console_scripts": [
            "macbook-monitor=monitor:main",
        ],
    },
)
