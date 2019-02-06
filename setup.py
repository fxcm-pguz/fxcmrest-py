from setuptools import setup, find_packages

setup(
	name = 'fxcmrest',
	packages = find_packages(),
	use_scm_version = True,
	setup_requires = ['setuptools_scm'],
	description = 'FXCM Rest API library for Python',
	author = 'Pawel Guz',
	author_email = 'pguz@fxcm.com',
	license = 'BSD',
	url = 'https://fxcm-pguz.github.io/fxcmrest-py/',
	download_url = 'https://github.com/fxcm-pguz/fxcmrest-py',
	keywords = 'FXCM REST API Wrapper Finance Algo Trading',
	install_requires = ['socketIO_client', 'requests'],
	python_requires = '>=3.4',
	include_package_data = True,
	package_data = {
		'': ['*.json']
	}
)
