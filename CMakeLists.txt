cmake_minimum_required(VERSION 3.13.4)

project(BreastCalc)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/BreastCalc")
set(EXTENSION_CATEGORY "Quantification")
set(EXTENSION_CONTRIBUTORS "Lance Levine (University of Miami Miller School of Medicine)")
set(EXTENSION_DESCRIPTION "This extension measures breast volume from MRI data to aid in pre-operative planning of breast surgery such as breast reconstruction after mastectomy.")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/BreastCalc.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/BreastCalc/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(BreastCalc)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
