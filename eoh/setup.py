from setuptools import setup, find_packages

setup(
    name="eoh",
    version="0.1",
    author="MetaAI Group, CityU",
    description="Evolutionary Computation + Large Language Model for automatic algorithm design",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    package_data={
        'eoh': [
            'methods/eoh/reflection/common/*.txt',
            'methods/eoh/reflection/inventory/*.txt',
        ],
    },
    include_package_data=True,  # 确保包含所有声明的数据文件
    python_requires=">=3.10",
    install_requires=[
        "numpy",
        "numba",
        "joblib"
    ],
    test_suite="tests"
)