target_sources(runtests
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/AIHarness.h
        ${CMAKE_CURRENT_SOURCE_DIR}/HtnPlannerTests_Basics.cpp
        ${CMAKE_CURRENT_SOURCE_DIR}/HtnPlannerTests_SetOf.cpp
        ${CMAKE_CURRENT_SOURCE_DIR}/HtnPlannerTests_ControlFlow.cpp
        ${CMAKE_CURRENT_SOURCE_DIR}/HtnPlannerTests_Integration.cpp
        ${CMAKE_CURRENT_SOURCE_DIR}/HtnCompilerTests.cpp
        ${CMAKE_CURRENT_SOURCE_DIR}/DebugHtnTest.cpp
        ${CMAKE_CURRENT_SOURCE_DIR}/HtnWorkingFeaturesTests.cpp
        ${CMAKE_CURRENT_SOURCE_DIR}/HtnBasicFeaturesTests.cpp
        ${CMAKE_CURRENT_SOURCE_DIR}/HtnAdvancedFeaturesTests.cpp
)
target_include_directories(testLib PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/)
