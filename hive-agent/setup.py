from setuptools import setup, find_packages

setup(
    name="hive-agent",
    version="1.0.0",
    description="Autonomous Codebase Analyst and Documentation Generator",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "anthropic==0.25.1",
        "langchain==0.1.20",
        "langgraph==0.0.55",
    ],
)
