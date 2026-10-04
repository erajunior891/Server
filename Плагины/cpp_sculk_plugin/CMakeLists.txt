cmake_minimum_required(VERSION 3.20)
project(endstone_sculk_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Поиск заголовков Endstone
find_package(endstone REQUIRED)

add_library(${PROJECT_NAME} SHARED
    src/sculk_plugin.cpp
)

target_include_directories(${PROJECT_NAME} PRIVATE
    include
)

target_link_libraries(${PROJECT_NAME} PRIVATE
    endstone::endstone
)
