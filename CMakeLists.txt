cmake_minimum_required(VERSION 3.25)
project(qcd_prediction LANGUAGES CXX)

option(QCD_ENABLE_CUDA "Build the CUDA backend scaffolding" OFF)
if (QCD_ENABLE_CUDA)
    include(CheckLanguage)
    check_language(CUDA)
    if (NOT CMAKE_CUDA_COMPILER)
        message(FATAL_ERROR "CUDA was requested but no CUDA compiler was found; configure with -DQCD_ENABLE_CUDA=OFF for a CPU-only build")
    endif ()
    enable_language(CUDA)
    set(CMAKE_CUDA_STANDARD 20)
    set(CMAKE_CUDA_STANDARD_REQUIRED ON)
    set(CMAKE_CUDA_EXTENSIONS OFF)
endif ()

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(CTest)
include(FetchContent)
option(ENABLE_COVERAGE "Build with coverage instrumentation" OFF)
option(QCD_ENABLE_WARNINGS "Enable strict compiler warnings for project code" ON)
option(QCD_ENABLE_SANITIZERS "Enable address and undefined-behavior sanitizers" OFF)

add_library(qcd_project_options INTERFACE)
if (QCD_ENABLE_WARNINGS)
    target_compile_options(qcd_project_options INTERFACE
            $<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang>:
            -Wall
            -Wextra
            -Wpedantic
            -Wconversion
            -Wsign-conversion
            -Wshadow>)
endif ()

if (QCD_ENABLE_SANITIZERS)
    if (CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(qcd_project_options INTERFACE
                $<$<COMPILE_LANGUAGE:CXX>:-fsanitize=address,undefined;-fno-omit-frame-pointer>)
        target_link_options(qcd_project_options INTERFACE
                $<$<LINK_LANGUAGE:CXX>:-fsanitize=address,undefined>)
    else ()
        message(FATAL_ERROR "QCD_ENABLE_SANITIZERS currently requires GCC or Clang")
    endif ()
endif ()

FetchContent_Declare(
        tomlplusplus
        GIT_REPOSITORY https://github.com/marzer/tomlplusplus.git
        GIT_TAG v3.4.0
        GIT_SHALLOW TRUE)
FetchContent_MakeAvailable(tomlplusplus)

# Header-only linear algebra, shared by all consumers of the public QCD headers.
set(EIGEN_BUILD_TESTING OFF)
set(EIGEN_BUILD_DOC OFF)
FetchContent_Declare(
        eigen
        GIT_REPOSITORY https://gitlab.com/libeigen/eigen.git
        GIT_TAG 5.0.0
        GIT_SHALLOW TRUE)
FetchContent_MakeAvailable(eigen)

if (ENABLE_COVERAGE)
    if (NOT BUILD_TESTING)
        message(FATAL_ERROR "ENABLE_COVERAGE requires BUILD_TESTING=ON")
    endif ()

    if (NOT CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
        message(FATAL_ERROR "Coverage currently requires the GNU C++ compiler and gcov")
    endif ()

    add_library(qcd_coverage_options INTERFACE)
    target_compile_options(qcd_coverage_options INTERFACE
            $<$<COMPILE_LANGUAGE:CXX>:--coverage;-O0;-g>)
    target_link_options(qcd_coverage_options INTERFACE
            $<$<LINK_LANGUAGE:CXX>:--coverage>)
endif ()

add_library(lattice
        src/core/rng.cpp
        src/core/statistics.cpp
        src/lattice/lattice.cpp
        include/qcd/lattice.h
        include/qcd/boundary.h
        include/qcd/rng.h
        include/qcd/statistics.h
        include/qcd/gauge_group.h
        include/qcd/gauge_field.h
        include/qcd/action.h
        include/qcd/update.h
        include/qcd/observables.h
        include/qcd/config.h
        src/config/config.cpp
)
add_library(qcd::core ALIAS lattice)

target_include_directories(lattice PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_include_directories(lattice SYSTEM PUBLIC
        $<TARGET_PROPERTY:Eigen3::Eigen,INTERFACE_INCLUDE_DIRECTORIES>)
target_link_libraries(lattice PUBLIC Eigen3::Eigen PRIVATE tomlplusplus::tomlplusplus)
target_link_libraries(lattice PRIVATE qcd_project_options)

if (ENABLE_COVERAGE)
    target_link_libraries(lattice PUBLIC qcd_coverage_options)
endif ()

if (QCD_ENABLE_CUDA)
    add_library(qcd_cuda
            src/cuda/gauge_field.cu
            src/cuda/update.cu
            src/cuda/kernels.cu
            include/qcd/cuda/gauge_field.cuh
            include/qcd/cuda/update.cuh
            include/qcd/cuda/kernels.cuh
            include/qcd/cuda/device_rng.cuh)

    target_include_directories(qcd_cuda PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
    target_link_libraries(qcd_cuda PUBLIC lattice)
    set_target_properties(qcd_cuda PROPERTIES CUDA_SEPARABLE_COMPILATION ON)
endif ()

add_executable(qcd_prediction
        apps/main.cpp
        apps/simulate.cpp
        apps/inspect.cpp)

target_link_libraries(qcd_prediction PRIVATE qcd_project_options)
if (QCD_ENABLE_CUDA)
    target_link_libraries(qcd_prediction PRIVATE qcd_cuda)
else ()
    target_link_libraries(qcd_prediction PRIVATE lattice)
endif ()
target_compile_definitions(qcd_prediction PRIVATE
        QCD_DEFAULT_CONFIG_PATH="${CMAKE_CURRENT_BINARY_DIR}/configs/default.toml")

set(QCD_CONFIG_FILES
        default.toml
        small-test.toml
        example-su3.toml)
file(MAKE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/configs")
foreach (QCD_CONFIG_FILE IN LISTS QCD_CONFIG_FILES)
    configure_file(
            "${CMAKE_CURRENT_SOURCE_DIR}/configs/${QCD_CONFIG_FILE}"
            "${CMAKE_CURRENT_BINARY_DIR}/configs/${QCD_CONFIG_FILE}"
            COPYONLY)
endforeach ()

if (BUILD_TESTING)
    FetchContent_Declare(
            googletest
            GIT_REPOSITORY https://github.com/google/googletest.git
            GIT_TAG v1.17.0
            GIT_SHALLOW TRUE)

    set(INSTALL_GTEST OFF CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(googletest)

    include(GoogleTest)

    function(qcd_add_unit_test target source)
        add_executable(${target} ${source})
        target_link_libraries(${target} PRIVATE
                qcd::core
                qcd_project_options
                GTest::gtest_main)
        gtest_discover_tests(${target}
                DISCOVERY_MODE PRE_TEST
                DISCOVERY_TIMEOUT 30)
        set_property(GLOBAL APPEND PROPERTY QCD_TEST_TARGETS ${target})
    endfunction()

    qcd_add_unit_test(qcd_sanity_tests tests/sanity_test.cpp)
    qcd_add_unit_test(qcd_config_tests tests/config_test.cpp)
    qcd_add_unit_test(qcd_lattice_tests tests/lattice_test.cpp)
    qcd_add_unit_test(qcd_rng_tests tests/rng_test.cpp)
    qcd_add_unit_test(qcd_statistics_tests tests/statistics_test.cpp)
    qcd_add_unit_test(qcd_gauge_field_tests tests/gauge_field_test.cpp)

    target_compile_definitions(qcd_config_tests PRIVATE
            QCD_CONFIG_DIR="${CMAKE_CURRENT_SOURCE_DIR}/configs")

    get_property(QCD_TEST_TARGETS GLOBAL PROPERTY QCD_TEST_TARGETS)

    if (ENABLE_COVERAGE)
        find_program(GCOVR_EXECUTABLE gcovr)
        set(COVERAGE_REPORT_DIR ${CMAKE_BINARY_DIR}/coverage)

        if (GCOVR_EXECUTABLE)
            add_custom_target(coverage
                    COMMAND ${CMAKE_COMMAND}
                            -DCOVERAGE_BINARY_DIR=${CMAKE_BINARY_DIR}
                            -P ${CMAKE_SOURCE_DIR}/cmake/ResetCoverage.cmake
                    COMMAND ${CMAKE_CTEST_COMMAND} --test-dir ${CMAKE_BINARY_DIR} --output-on-failure
                    COMMAND ${CMAKE_COMMAND} -E make_directory ${COVERAGE_REPORT_DIR}
                    COMMAND ${GCOVR_EXECUTABLE}
                            --root ${CMAKE_SOURCE_DIR}
                            --object-directory ${CMAKE_BINARY_DIR}
                            --filter ${CMAKE_SOURCE_DIR}/include/
                            --filter ${CMAKE_SOURCE_DIR}/src/
                            --exclude ${CMAKE_SOURCE_DIR}/include/qcd/cuda/
                            --exclude ${CMAKE_SOURCE_DIR}/src/cuda/
                            --html-details ${COVERAGE_REPORT_DIR}/index.html
                            --xml ${COVERAGE_REPORT_DIR}/coverage.xml
                            --xml-pretty
                            --txt ${COVERAGE_REPORT_DIR}/coverage.txt
                            --print-summary
                    DEPENDS ${QCD_TEST_TARGETS}
                    USES_TERMINAL
                    COMMENT "Running tests and generating coverage reports")
        else ()
            add_custom_target(coverage
                    COMMAND ${CMAKE_COMMAND}
                            -DCOVERAGE_BINARY_DIR=${CMAKE_BINARY_DIR}
                            -P ${CMAKE_SOURCE_DIR}/cmake/ResetCoverage.cmake
                    COMMAND ${CMAKE_CTEST_COMMAND} --test-dir ${CMAKE_BINARY_DIR} --output-on-failure
                    COMMAND ${CMAKE_COMMAND} -E echo
                            "gcovr was not found - raw .gcno/.gcda coverage data is available in ${CMAKE_BINARY_DIR}"
                    DEPENDS ${QCD_TEST_TARGETS}
                    USES_TERMINAL
                    COMMENT "Running tests and collecting raw coverage data")

            message(STATUS "gcovr not found: the coverage target will collect raw data without generating reports")
        endif ()
    endif ()
endif ()
