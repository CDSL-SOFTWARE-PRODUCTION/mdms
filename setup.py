from setuptools import setup, find_packages

setup(
    name="DVT",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'PyQt6>=6.0.0',
        'SQLAlchemy>=2.0.0',
        'psycopg2-binary>=2.9.0',  # For PostgreSQL support
        'cryptography>=41.0.0',     # For encryption
        'bcrypt>=4.0.0',           # For password hashing
        'PyJWT>=2.8.0',           # For JWT tokens
        'aiohttp>=3.9.0',         # For async HTTP
        'pytest>=8.0.0',          # For testing
        'pytest-asyncio>=0.23.0',  # For async tests
    ],
    entry_points={
        'console_scripts': [
            'dvt=src.gui.main_window:main',
        ],
    },
    package_data={
        'DVT': [
            'config/*',
            'locale/*/LC_MESSAGES/*.mo',
            'locale/*/LC_MESSAGES/*.po',
        ],
    },
    python_requires='>=3.8',
    author="CDSL Software Production",
    description="Medical Device Management Software",
    long_description=open('DOC.md').read(),
    long_description_content_type="text/markdown",
)