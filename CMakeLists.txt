cmake_minimum_required(VERSION 3.25)
project(qcd_prediction LANGUAGES CXX CUDA)

set(CMAKE_CUDA_STANDARD 20)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)



include(CTest)
include(FetchContent)
option(ENABLE_COVERAGE "Build with coverage instrumentation" OFF)

FetchContent_Declare(
        tomlplusplus
        GIT_REPOSITORY https://github.com/marzer/tomlplusplus.git
        GIT_TAG v3.4.0
        GIT_SHALLOW TRUE)
FetchContent_MakeAvailable(tomlplusplus)

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
        include/qcd/network_config.h
        include/qcd/config.h
        src/config/config.cpp
)

target_include_directories(lattice PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_link_libraries(lattice PRIVATE tomlplusplus::tomlplusplus)

if (ENABLE_COVERAGE)
    target_link_libraries(lattice PUBLIC qcd_coverage_options)
endif ()

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

set_target_properties(qcd_cuda PROPERTIES
        CUDA_SEPARABLE_COMPILATION ON)

add_executable(qcd_prediction
        apps/main.cu
        apps/simulate.cpp
        apps/inspect.cpp)

target_link_libraries(qcd_prediction PRIVATE qcd_cuda)
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

set_target_properties(qcd_prediction PROPERTIES
        CUDA_SEPARABLE_COMPILATION ON)

if (BUILD_TESTING)
    FetchContent_Declare(
            googletest
            GIT_REPOSITORY https://github.com/google/googletest.git
            GIT_TAG v1.17.0
            GIT_SHALLOW TRUE)

    set(INSTALL_GTEST OFF CACHE BOOL "" FORCE)
    FetchContent_MakeAvailable(googletest)

    add_executable(qcd_sanity_tests
            tests/sanity_test.cpp
            tests/config_test.cpp)
    target_link_libraries(qcd_sanity_tests PRIVATE
            lattice
            tomlplusplus::tomlplusplus
            GTest::gtest_main)
    target_compile_definitions(qcd_sanity_tests PRIVATE
            QCD_CONFIG_DIR="${CMAKE_CURRENT_SOURCE_DIR}/configs")

    include(GoogleTest)
    gtest_discover_tests(qcd_sanity_tests)

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
                    DEPENDS qcd_sanity_tests
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
                    DEPENDS qcd_sanity_tests
                    USES_TERMINAL
                    COMMENT "Running tests and collecting raw coverage data")

            message(STATUS "gcovr not found: the coverage target will collect raw data without generating reports")
        endif ()
    endif ()
endif ()
