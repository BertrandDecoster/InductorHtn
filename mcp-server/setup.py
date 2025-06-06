"""Setup script for InductorHTN MCP Server"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="indhtn-mcp",
    version="1.0.0",
    author="InductorHTN MCP",
    description="MCP server for InductorHTN REPL interaction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "mcp>=0.1.0",
    ],
    entry_points={
        "console_scripts": [
            "indhtn-mcp=indhtn_mcp.server:main",
        ],
    },
)