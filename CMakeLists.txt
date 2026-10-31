cmake_minimum_required(VERSION 3.15)

include(FetchContent)
project(_riag LANGUAGES CXX C)

set(CMAKE_CXX_STANDARD 20)
set(RIAG_SOURCE_DIR "" CACHE PATH "Path to the RiaGraph source tree used for pybind builds")

if(NOT TARGET pybind11::module)
    if(RIAG_SOURCE_DIR)
        add_subdirectory("${RIAG_SOURCE_DIR}/third_party/pybind11" "${CMAKE_BINARY_DIR}/third_party/pybind11" EXCLUDE_FROM_ALL)
    else()
        find_package(pybind11 CONFIG REQUIRED)
    endif()
endif()

if(NOT RIAG_API_USE_PRECOMPILED_LIB AND NOT TARGET riag)
    if(NOT RIAG_SOURCE_DIR)
        message(FATAL_ERROR "RIAG_SOURCE_DIR must be set when building the pybind extension from RiaGraph sources.")
    endif()

    set(BUILD_BENCHMARK FALSE CACHE BOOL "" FORCE)
    set(BUILD_EXAMPLES FALSE CACHE BOOL "" FORCE)
    set(BUILD_EXTENSION_TESTS FALSE CACHE BOOL "" FORCE)
    set(BUILD_JAVA FALSE CACHE BOOL "" FORCE)
    set(BUILD_NODEJS FALSE CACHE BOOL "" FORCE)
    set(BUILD_PYTHON FALSE CACHE BOOL "" FORCE)
    set(BUILD_SHELL FALSE CACHE BOOL "" FORCE)
    set(BUILD_TESTS FALSE CACHE BOOL "" FORCE)
    set(BUILD_WAL_DUMP FALSE CACHE BOOL "" FORCE)
    set(BUILD_WASM FALSE CACHE BOOL "" FORCE)

    add_subdirectory("${RIAG_SOURCE_DIR}" "${CMAKE_BINARY_DIR}/riag-source" EXCLUDE_FROM_ALL)
endif()

file(GLOB SOURCE_PY
        "src_py/*")

pybind11_add_module(_riag
        SHARED
        src_cpp/riag_binding.cpp
        src_cpp/cached_import/py_cached_item.cpp
        src_cpp/cached_import/py_cached_import.cpp
        src_cpp/py_connection.cpp
        src_cpp/py_database.cpp
        src_cpp/py_prepared_statement.cpp
        src_cpp/py_query_result.cpp
        src_cpp/py_query_result_converter.cpp
        src_cpp/py_scan_config.cpp
        src_cpp/py_udf.cpp
        src_cpp/py_conversion.cpp
        src_cpp/pyarrow/pyarrow_bind.cpp
        src_cpp/pyarrow/pyarrow_scan.cpp
        src_cpp/pandas/pandas_bind.cpp
        src_cpp/pandas/pandas_scan.cpp
        src_cpp/pandas/pandas_analyzer.cpp
        src_cpp/numpy/numpy_type.cpp
        src_cpp/numpy/numpy_scan.cpp)

set_target_properties(_riag
        PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/build/riag"
        RUNTIME_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/build/riag"
        ARCHIVE_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/build/riag")

if(RIAG_API_USE_PRECOMPILED_LIB)
    if(NOT RIAG_API_PRECOMPILED_LIB_PATH)
        message(FATAL_ERROR "RIAG_API_PRECOMPILED_LIB_PATH must be set when RIAG_API_USE_PRECOMPILED_LIB is enabled.")
    endif()
    target_link_libraries(_riag
            PRIVATE
            ${RIAG_API_PRECOMPILED_LIB_PATH}
            # riag_link_deps carries all third-party static libs (utf8proc, re2,
            # antlr4, zstd, …) that riag.lib references but does not bundle on
            # Windows. On Linux/macOS the precompiled libriag.a is a fat archive
            # with those objects already merged in, so this is a no-op there.
            riag_link_deps)
    # The precompiled lib is always a static archive. Without RIAG_STATIC_DEFINE,
    # api.h decorates every RIAG_API symbol with __declspec(dllimport) on Windows,
    # which causes LNK2001 unresolved-symbol errors because no DLL is present.
    target_compile_definitions(_riag PRIVATE RIAG_STATIC_DEFINE)
else()
    target_link_libraries(_riag
            PRIVATE
            riag)
endif()

target_include_directories(
        _riag
        PUBLIC
        src_cpp/include)

if(TARGET riag)
    get_target_property(RIAG_INCLUDE_DIRECTORIES riag INCLUDE_DIRECTORIES)
    if(RIAG_INCLUDE_DIRECTORIES)
        target_include_directories(_riag PRIVATE ${RIAG_INCLUDE_DIRECTORIES})
    endif()

    get_target_property(RIAG_COMPILE_DEFINITIONS riag COMPILE_DEFINITIONS)
    if(RIAG_COMPILE_DEFINITIONS)
        target_compile_definitions(_riag PRIVATE ${RIAG_COMPILE_DEFINITIONS})
    endif()

    get_target_property(RIAG_COMPILE_OPTIONS riag COMPILE_OPTIONS)
    if(RIAG_COMPILE_OPTIONS)
        target_compile_options(_riag PRIVATE ${RIAG_COMPILE_OPTIONS})
    endif()
endif()

get_target_property(PYTHON_DEST _riag LIBRARY_OUTPUT_DIRECTORY)

file(COPY ${SOURCE_PY} DESTINATION ${PYTHON_DEST})
