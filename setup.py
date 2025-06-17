from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="arxiv-zotero-connector",
    version="0.1.0",
    author="Stepan Kropachev",
    author_email="kropachev.st@gmail.com",
    description="Automatically collect papers from ArXiv and organize them in your Zotero library with AI-powered summarization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/StepanKropachev/arxiv-zotero-connector",
    project_urls={
        "Bug Reports": "https://github.com/StepanKropachev/arxiv-zotero-connector/issues",
        "Source": "https://github.com/StepanKropachev/arxiv-zotero-connector",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="arxiv, zotero, research, papers, academic, ai, summarization",
    packages=find_packages(exclude=["tests", "tests.*", "examples"]),
    python_requires=">=3.7",
    install_requires=[
        "arxiv>=1.4.0",
        "pyzotero>=1.5.0",
        "requests>=2.25.0",
        "pytz>=2021.1",
        "python-dotenv>=0.19.0",
        "aiohttp>=3.8.0",
        "pyyaml>=5.4.0",
        "PyPDF2>=2.0.0",
        "google-generativeai>=0.3.0",
    ],
    entry_points={
        "console_scripts": [
            "arxiv-zotero=arxiv_zotero.cli:main",
        ],
    },
    include_package_data=True,
)
