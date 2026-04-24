from setuptools import setup
from glob import glob

package_name = "tb4_square"

setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/rviz", glob("rviz/*.rviz")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="masu_ubu",
    maintainer_email="masu_ubu@example.com",
    description="Simple square motion demo for TurtleBot 4.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "odom_path_publisher = tb4_square.odom_path_publisher:main",
            "square_driver = tb4_square.square_driver:main",
        ],
    },
)
