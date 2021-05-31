import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="matplotlib-publishutil", # Replace with your own username
    version="0.0.4",
    author="Tom McTavish",
    author_email="tom@spikes.ai",
    description="Utilities to help configure matplotlib figures for publication.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tommct/matplotlib-publishutil",
    project_urls={
        "Bug Tracker": "https://github.com/tommct/matplotlib-publishutil/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    package_data={'publishutil': ['figure_layouts/*.yml']},
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    requires = ['matplotlib', 'pyaml']
)
