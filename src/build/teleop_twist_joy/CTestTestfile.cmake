# CMake generated Testfile for 
# Source directory: /home/lab/robocar/src/teleop_twist_joy
# Build directory: /home/lab/robocar/src/build/teleop_twist_joy
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(test_differential_joy_launch_test.py "/home/lab/robocar/.venv/bin/python3.10" "-u" "/opt/ros/iron/share/ament_cmake_test/cmake/run_test.py" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/test_differential_joy_launch_test.py.xunit.xml" "--package-name" "teleop_twist_joy" "--output-file" "/home/lab/robocar/src/build/teleop_twist_joy/launch_test/test_differential_joy_launch_test.py.txt" "--append-env" "PYTHONPATH=/home/lab/robocar/src/teleop_twist_joy/test" "--command" "/home/lab/robocar/.venv/bin/python3" "-m" "launch_testing.launch_test" "/home/lab/robocar/src/teleop_twist_joy/test/differential_joy_launch_test.py" "--junit-xml=/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/test_differential_joy_launch_test.py.xunit.xml" "--package-name=teleop_twist_joy")
set_tests_properties(test_differential_joy_launch_test.py PROPERTIES  LABELS "launch_test" TIMEOUT "10" WORKING_DIRECTORY "/home/lab/robocar/src/build/teleop_twist_joy" _BACKTRACE_TRIPLES "/opt/ros/iron/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/iron/share/launch_testing_ament_cmake/cmake/add_launch_test.cmake;131;ament_add_test;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;87;add_launch_test;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;0;")
add_test(test_holonomic_joy_launch_test.py "/home/lab/robocar/.venv/bin/python3.10" "-u" "/opt/ros/iron/share/ament_cmake_test/cmake/run_test.py" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/test_holonomic_joy_launch_test.py.xunit.xml" "--package-name" "teleop_twist_joy" "--output-file" "/home/lab/robocar/src/build/teleop_twist_joy/launch_test/test_holonomic_joy_launch_test.py.txt" "--append-env" "PYTHONPATH=/home/lab/robocar/src/teleop_twist_joy/test" "--command" "/home/lab/robocar/.venv/bin/python3" "-m" "launch_testing.launch_test" "/home/lab/robocar/src/teleop_twist_joy/test/holonomic_joy_launch_test.py" "--junit-xml=/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/test_holonomic_joy_launch_test.py.xunit.xml" "--package-name=teleop_twist_joy")
set_tests_properties(test_holonomic_joy_launch_test.py PROPERTIES  LABELS "launch_test" TIMEOUT "10" WORKING_DIRECTORY "/home/lab/robocar/src/build/teleop_twist_joy" _BACKTRACE_TRIPLES "/opt/ros/iron/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/iron/share/launch_testing_ament_cmake/cmake/add_launch_test.cmake;131;ament_add_test;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;87;add_launch_test;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;0;")
add_test(test_six_dof_joy_launch_test.py "/home/lab/robocar/.venv/bin/python3.10" "-u" "/opt/ros/iron/share/ament_cmake_test/cmake/run_test.py" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/test_six_dof_joy_launch_test.py.xunit.xml" "--package-name" "teleop_twist_joy" "--output-file" "/home/lab/robocar/src/build/teleop_twist_joy/launch_test/test_six_dof_joy_launch_test.py.txt" "--append-env" "PYTHONPATH=/home/lab/robocar/src/teleop_twist_joy/test" "--command" "/home/lab/robocar/.venv/bin/python3" "-m" "launch_testing.launch_test" "/home/lab/robocar/src/teleop_twist_joy/test/six_dof_joy_launch_test.py" "--junit-xml=/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/test_six_dof_joy_launch_test.py.xunit.xml" "--package-name=teleop_twist_joy")
set_tests_properties(test_six_dof_joy_launch_test.py PROPERTIES  LABELS "launch_test" TIMEOUT "10" WORKING_DIRECTORY "/home/lab/robocar/src/build/teleop_twist_joy" _BACKTRACE_TRIPLES "/opt/ros/iron/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/iron/share/launch_testing_ament_cmake/cmake/add_launch_test.cmake;131;ament_add_test;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;87;add_launch_test;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;0;")
add_test(test_no_enable_joy_launch_test.py "/home/lab/robocar/.venv/bin/python3.10" "-u" "/opt/ros/iron/share/ament_cmake_test/cmake/run_test.py" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/test_no_enable_joy_launch_test.py.xunit.xml" "--package-name" "teleop_twist_joy" "--output-file" "/home/lab/robocar/src/build/teleop_twist_joy/launch_test/test_no_enable_joy_launch_test.py.txt" "--append-env" "PYTHONPATH=/home/lab/robocar/src/teleop_twist_joy/test" "--command" "/home/lab/robocar/.venv/bin/python3" "-m" "launch_testing.launch_test" "/home/lab/robocar/src/teleop_twist_joy/test/no_enable_joy_launch_test.py" "--junit-xml=/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/test_no_enable_joy_launch_test.py.xunit.xml" "--package-name=teleop_twist_joy")
set_tests_properties(test_no_enable_joy_launch_test.py PROPERTIES  LABELS "launch_test" TIMEOUT "10" WORKING_DIRECTORY "/home/lab/robocar/src/build/teleop_twist_joy" _BACKTRACE_TRIPLES "/opt/ros/iron/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/iron/share/launch_testing_ament_cmake/cmake/add_launch_test.cmake;131;ament_add_test;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;87;add_launch_test;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;0;")
add_test(test_turbo_enable_joy_launch_test.py "/home/lab/robocar/.venv/bin/python3.10" "-u" "/opt/ros/iron/share/ament_cmake_test/cmake/run_test.py" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/test_turbo_enable_joy_launch_test.py.xunit.xml" "--package-name" "teleop_twist_joy" "--output-file" "/home/lab/robocar/src/build/teleop_twist_joy/launch_test/test_turbo_enable_joy_launch_test.py.txt" "--append-env" "PYTHONPATH=/home/lab/robocar/src/teleop_twist_joy/test" "--command" "/home/lab/robocar/.venv/bin/python3" "-m" "launch_testing.launch_test" "/home/lab/robocar/src/teleop_twist_joy/test/turbo_enable_joy_launch_test.py" "--junit-xml=/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/test_turbo_enable_joy_launch_test.py.xunit.xml" "--package-name=teleop_twist_joy")
set_tests_properties(test_turbo_enable_joy_launch_test.py PROPERTIES  LABELS "launch_test" TIMEOUT "10" WORKING_DIRECTORY "/home/lab/robocar/src/build/teleop_twist_joy" _BACKTRACE_TRIPLES "/opt/ros/iron/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/iron/share/launch_testing_ament_cmake/cmake/add_launch_test.cmake;131;ament_add_test;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;87;add_launch_test;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;0;")
add_test(test_only_turbo_joy_launch_test.py "/home/lab/robocar/.venv/bin/python3.10" "-u" "/opt/ros/iron/share/ament_cmake_test/cmake/run_test.py" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/test_only_turbo_joy_launch_test.py.xunit.xml" "--package-name" "teleop_twist_joy" "--output-file" "/home/lab/robocar/src/build/teleop_twist_joy/launch_test/test_only_turbo_joy_launch_test.py.txt" "--append-env" "PYTHONPATH=/home/lab/robocar/src/teleop_twist_joy/test" "--command" "/home/lab/robocar/.venv/bin/python3" "-m" "launch_testing.launch_test" "/home/lab/robocar/src/teleop_twist_joy/test/only_turbo_joy_launch_test.py" "--junit-xml=/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/test_only_turbo_joy_launch_test.py.xunit.xml" "--package-name=teleop_twist_joy")
set_tests_properties(test_only_turbo_joy_launch_test.py PROPERTIES  LABELS "launch_test" TIMEOUT "10" WORKING_DIRECTORY "/home/lab/robocar/src/build/teleop_twist_joy" _BACKTRACE_TRIPLES "/opt/ros/iron/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/iron/share/launch_testing_ament_cmake/cmake/add_launch_test.cmake;131;ament_add_test;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;87;add_launch_test;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;0;")
add_test(test_turbo_angular_enable_joy_launch_test.py "/home/lab/robocar/.venv/bin/python3.10" "-u" "/opt/ros/iron/share/ament_cmake_test/cmake/run_test.py" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/test_turbo_angular_enable_joy_launch_test.py.xunit.xml" "--package-name" "teleop_twist_joy" "--output-file" "/home/lab/robocar/src/build/teleop_twist_joy/launch_test/test_turbo_angular_enable_joy_launch_test.py.txt" "--append-env" "PYTHONPATH=/home/lab/robocar/src/teleop_twist_joy/test" "--command" "/home/lab/robocar/.venv/bin/python3" "-m" "launch_testing.launch_test" "/home/lab/robocar/src/teleop_twist_joy/test/turbo_angular_enable_joy_launch_test.py" "--junit-xml=/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/test_turbo_angular_enable_joy_launch_test.py.xunit.xml" "--package-name=teleop_twist_joy")
set_tests_properties(test_turbo_angular_enable_joy_launch_test.py PROPERTIES  LABELS "launch_test" TIMEOUT "10" WORKING_DIRECTORY "/home/lab/robocar/src/build/teleop_twist_joy" _BACKTRACE_TRIPLES "/opt/ros/iron/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/iron/share/launch_testing_ament_cmake/cmake/add_launch_test.cmake;131;ament_add_test;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;87;add_launch_test;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;0;")
add_test(test_no_require_enable_joy_launch_test.py "/home/lab/robocar/.venv/bin/python3.10" "-u" "/opt/ros/iron/share/ament_cmake_test/cmake/run_test.py" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/test_no_require_enable_joy_launch_test.py.xunit.xml" "--package-name" "teleop_twist_joy" "--output-file" "/home/lab/robocar/src/build/teleop_twist_joy/launch_test/test_no_require_enable_joy_launch_test.py.txt" "--append-env" "PYTHONPATH=/home/lab/robocar/src/teleop_twist_joy/test" "--command" "/home/lab/robocar/.venv/bin/python3" "-m" "launch_testing.launch_test" "/home/lab/robocar/src/teleop_twist_joy/test/no_require_enable_joy_launch_test.py" "--junit-xml=/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/test_no_require_enable_joy_launch_test.py.xunit.xml" "--package-name=teleop_twist_joy")
set_tests_properties(test_no_require_enable_joy_launch_test.py PROPERTIES  LABELS "launch_test" TIMEOUT "10" WORKING_DIRECTORY "/home/lab/robocar/src/build/teleop_twist_joy" _BACKTRACE_TRIPLES "/opt/ros/iron/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/iron/share/launch_testing_ament_cmake/cmake/add_launch_test.cmake;131;ament_add_test;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;87;add_launch_test;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;0;")
add_test(cppcheck "/home/lab/robocar/.venv/bin/python3.10" "-u" "/opt/ros/iron/share/ament_cmake_test/cmake/run_test.py" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/cppcheck.xunit.xml" "--package-name" "teleop_twist_joy" "--output-file" "/home/lab/robocar/src/build/teleop_twist_joy/ament_cppcheck/cppcheck.txt" "--command" "/opt/ros/iron/bin/ament_cppcheck" "--xunit-file" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/cppcheck.xunit.xml" "--include_dirs" "/home/lab/robocar/src/teleop_twist_joy/include")
set_tests_properties(cppcheck PROPERTIES  LABELS "cppcheck;linter" TIMEOUT "300" WORKING_DIRECTORY "/home/lab/robocar/src/teleop_twist_joy" _BACKTRACE_TRIPLES "/opt/ros/iron/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/iron/share/ament_cmake_cppcheck/cmake/ament_cppcheck.cmake;66;ament_add_test;/opt/ros/iron/share/ament_cmake_cppcheck/cmake/ament_cmake_cppcheck_lint_hook.cmake;87;ament_cppcheck;/opt/ros/iron/share/ament_cmake_cppcheck/cmake/ament_cmake_cppcheck_lint_hook.cmake;0;;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_execute_extensions.cmake;48;include;/opt/ros/iron/share/ament_lint_auto/cmake/ament_lint_auto_package_hook.cmake;21;ament_execute_extensions;/opt/ros/iron/share/ament_lint_auto/cmake/ament_lint_auto_package_hook.cmake;0;;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_execute_extensions.cmake;48;include;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_package.cmake;66;ament_execute_extensions;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;101;ament_package;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;0;")
add_test(cpplint "/home/lab/robocar/.venv/bin/python3.10" "-u" "/opt/ros/iron/share/ament_cmake_test/cmake/run_test.py" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/cpplint.xunit.xml" "--package-name" "teleop_twist_joy" "--output-file" "/home/lab/robocar/src/build/teleop_twist_joy/ament_cpplint/cpplint.txt" "--command" "/opt/ros/iron/bin/ament_cpplint" "--xunit-file" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/cpplint.xunit.xml")
set_tests_properties(cpplint PROPERTIES  LABELS "cpplint;linter" TIMEOUT "120" WORKING_DIRECTORY "/home/lab/robocar/src/teleop_twist_joy" _BACKTRACE_TRIPLES "/opt/ros/iron/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/iron/share/ament_cmake_cpplint/cmake/ament_cpplint.cmake;68;ament_add_test;/opt/ros/iron/share/ament_cmake_cpplint/cmake/ament_cmake_cpplint_lint_hook.cmake;39;ament_cpplint;/opt/ros/iron/share/ament_cmake_cpplint/cmake/ament_cmake_cpplint_lint_hook.cmake;0;;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_execute_extensions.cmake;48;include;/opt/ros/iron/share/ament_lint_auto/cmake/ament_lint_auto_package_hook.cmake;21;ament_execute_extensions;/opt/ros/iron/share/ament_lint_auto/cmake/ament_lint_auto_package_hook.cmake;0;;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_execute_extensions.cmake;48;include;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_package.cmake;66;ament_execute_extensions;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;101;ament_package;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;0;")
add_test(flake8 "/home/lab/robocar/.venv/bin/python3.10" "-u" "/opt/ros/iron/share/ament_cmake_test/cmake/run_test.py" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/flake8.xunit.xml" "--package-name" "teleop_twist_joy" "--output-file" "/home/lab/robocar/src/build/teleop_twist_joy/ament_flake8/flake8.txt" "--command" "/opt/ros/iron/bin/ament_flake8" "--xunit-file" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/flake8.xunit.xml")
set_tests_properties(flake8 PROPERTIES  LABELS "flake8;linter" TIMEOUT "60" WORKING_DIRECTORY "/home/lab/robocar/src/teleop_twist_joy" _BACKTRACE_TRIPLES "/opt/ros/iron/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/iron/share/ament_cmake_flake8/cmake/ament_flake8.cmake;69;ament_add_test;/opt/ros/iron/share/ament_cmake_flake8/cmake/ament_cmake_flake8_lint_hook.cmake;19;ament_flake8;/opt/ros/iron/share/ament_cmake_flake8/cmake/ament_cmake_flake8_lint_hook.cmake;0;;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_execute_extensions.cmake;48;include;/opt/ros/iron/share/ament_lint_auto/cmake/ament_lint_auto_package_hook.cmake;21;ament_execute_extensions;/opt/ros/iron/share/ament_lint_auto/cmake/ament_lint_auto_package_hook.cmake;0;;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_execute_extensions.cmake;48;include;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_package.cmake;66;ament_execute_extensions;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;101;ament_package;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;0;")
add_test(lint_cmake "/home/lab/robocar/.venv/bin/python3.10" "-u" "/opt/ros/iron/share/ament_cmake_test/cmake/run_test.py" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/lint_cmake.xunit.xml" "--package-name" "teleop_twist_joy" "--output-file" "/home/lab/robocar/src/build/teleop_twist_joy/ament_lint_cmake/lint_cmake.txt" "--command" "/opt/ros/iron/bin/ament_lint_cmake" "--xunit-file" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/lint_cmake.xunit.xml")
set_tests_properties(lint_cmake PROPERTIES  LABELS "lint_cmake;linter" TIMEOUT "60" WORKING_DIRECTORY "/home/lab/robocar/src/teleop_twist_joy" _BACKTRACE_TRIPLES "/opt/ros/iron/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/iron/share/ament_cmake_lint_cmake/cmake/ament_lint_cmake.cmake;47;ament_add_test;/opt/ros/iron/share/ament_cmake_lint_cmake/cmake/ament_cmake_lint_cmake_lint_hook.cmake;21;ament_lint_cmake;/opt/ros/iron/share/ament_cmake_lint_cmake/cmake/ament_cmake_lint_cmake_lint_hook.cmake;0;;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_execute_extensions.cmake;48;include;/opt/ros/iron/share/ament_lint_auto/cmake/ament_lint_auto_package_hook.cmake;21;ament_execute_extensions;/opt/ros/iron/share/ament_lint_auto/cmake/ament_lint_auto_package_hook.cmake;0;;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_execute_extensions.cmake;48;include;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_package.cmake;66;ament_execute_extensions;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;101;ament_package;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;0;")
add_test(pep257 "/home/lab/robocar/.venv/bin/python3.10" "-u" "/opt/ros/iron/share/ament_cmake_test/cmake/run_test.py" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/pep257.xunit.xml" "--package-name" "teleop_twist_joy" "--output-file" "/home/lab/robocar/src/build/teleop_twist_joy/ament_pep257/pep257.txt" "--command" "/opt/ros/iron/bin/ament_pep257" "--xunit-file" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/pep257.xunit.xml")
set_tests_properties(pep257 PROPERTIES  LABELS "pep257;linter" TIMEOUT "60" WORKING_DIRECTORY "/home/lab/robocar/src/teleop_twist_joy" _BACKTRACE_TRIPLES "/opt/ros/iron/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/iron/share/ament_cmake_pep257/cmake/ament_pep257.cmake;41;ament_add_test;/opt/ros/iron/share/ament_cmake_pep257/cmake/ament_cmake_pep257_lint_hook.cmake;18;ament_pep257;/opt/ros/iron/share/ament_cmake_pep257/cmake/ament_cmake_pep257_lint_hook.cmake;0;;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_execute_extensions.cmake;48;include;/opt/ros/iron/share/ament_lint_auto/cmake/ament_lint_auto_package_hook.cmake;21;ament_execute_extensions;/opt/ros/iron/share/ament_lint_auto/cmake/ament_lint_auto_package_hook.cmake;0;;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_execute_extensions.cmake;48;include;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_package.cmake;66;ament_execute_extensions;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;101;ament_package;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;0;")
add_test(uncrustify "/home/lab/robocar/.venv/bin/python3.10" "-u" "/opt/ros/iron/share/ament_cmake_test/cmake/run_test.py" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/uncrustify.xunit.xml" "--package-name" "teleop_twist_joy" "--output-file" "/home/lab/robocar/src/build/teleop_twist_joy/ament_uncrustify/uncrustify.txt" "--command" "/opt/ros/iron/bin/ament_uncrustify" "--xunit-file" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/uncrustify.xunit.xml")
set_tests_properties(uncrustify PROPERTIES  LABELS "uncrustify;linter" TIMEOUT "60" WORKING_DIRECTORY "/home/lab/robocar/src/teleop_twist_joy" _BACKTRACE_TRIPLES "/opt/ros/iron/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/iron/share/ament_cmake_uncrustify/cmake/ament_uncrustify.cmake;70;ament_add_test;/opt/ros/iron/share/ament_cmake_uncrustify/cmake/ament_cmake_uncrustify_lint_hook.cmake;43;ament_uncrustify;/opt/ros/iron/share/ament_cmake_uncrustify/cmake/ament_cmake_uncrustify_lint_hook.cmake;0;;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_execute_extensions.cmake;48;include;/opt/ros/iron/share/ament_lint_auto/cmake/ament_lint_auto_package_hook.cmake;21;ament_execute_extensions;/opt/ros/iron/share/ament_lint_auto/cmake/ament_lint_auto_package_hook.cmake;0;;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_execute_extensions.cmake;48;include;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_package.cmake;66;ament_execute_extensions;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;101;ament_package;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;0;")
add_test(xmllint "/home/lab/robocar/.venv/bin/python3.10" "-u" "/opt/ros/iron/share/ament_cmake_test/cmake/run_test.py" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/xmllint.xunit.xml" "--package-name" "teleop_twist_joy" "--output-file" "/home/lab/robocar/src/build/teleop_twist_joy/ament_xmllint/xmllint.txt" "--command" "/opt/ros/iron/bin/ament_xmllint" "--xunit-file" "/home/lab/robocar/src/build/teleop_twist_joy/test_results/teleop_twist_joy/xmllint.xunit.xml")
set_tests_properties(xmllint PROPERTIES  LABELS "xmllint;linter" TIMEOUT "60" WORKING_DIRECTORY "/home/lab/robocar/src/teleop_twist_joy" _BACKTRACE_TRIPLES "/opt/ros/iron/share/ament_cmake_test/cmake/ament_add_test.cmake;125;add_test;/opt/ros/iron/share/ament_cmake_xmllint/cmake/ament_xmllint.cmake;50;ament_add_test;/opt/ros/iron/share/ament_cmake_xmllint/cmake/ament_cmake_xmllint_lint_hook.cmake;18;ament_xmllint;/opt/ros/iron/share/ament_cmake_xmllint/cmake/ament_cmake_xmllint_lint_hook.cmake;0;;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_execute_extensions.cmake;48;include;/opt/ros/iron/share/ament_lint_auto/cmake/ament_lint_auto_package_hook.cmake;21;ament_execute_extensions;/opt/ros/iron/share/ament_lint_auto/cmake/ament_lint_auto_package_hook.cmake;0;;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_execute_extensions.cmake;48;include;/opt/ros/iron/share/ament_cmake_core/cmake/core/ament_package.cmake;66;ament_execute_extensions;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;101;ament_package;/home/lab/robocar/src/teleop_twist_joy/CMakeLists.txt;0;")
