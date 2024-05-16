from setuptools import find_packages, setup

package_name = 'robocar_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='lab',
    maintainer_email='rhiguerat00@gmail.com',
    description='TODO: Package description',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'car_control_node = robocar_pkg.car_control_node:main',
            'energy_node = robocar_pkg.energy_node:main',
            'camera_node = robocar_pkg.camera_node:main',
            'accelerometer_node = robocar_pkg.accelerometer_node:main',
            'distance_node = robocar_pkg.distance_node:main',
            'processing_node = robocar_pkg.processing_node:main',
            'controller_node = robocar_pkg.controller_node:main',
        ],
    },
)
