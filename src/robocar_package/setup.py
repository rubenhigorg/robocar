from setuptools import find_packages, setup

package_name = 'robocar_package'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/msg', ['msg/Energy.msg']),
    ],
    install_requires=['setuptools', 'adafruit-circuitpython-servokit'],
    zip_safe=True,
    maintainer='lab',
    maintainer_email='lab@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'robocar_node = robocar_package.robocar_node:main',
            'current_node = robocar_package.current_node:main',
        ],
    },
)
