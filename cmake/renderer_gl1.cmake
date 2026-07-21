if(NOT BUILD_CLIENT)
    return()
endif()

include(renderer_common)

set(RENDERER_GL1_SOURCES
    ${SOURCE_DIR}/renderergl1/tr_backend.c
    ${SOURCE_DIR}/renderergl1/tr_bsp.c
    ${SOURCE_DIR}/renderergl1/tr_cmds.c
    ${SOURCE_DIR}/renderergl1/tr_curve.c
    ${SOURCE_DIR}/renderergl1/tr_draw.c
    ${SOURCE_DIR}/renderergl1/tr_flares.c
    ${SOURCE_DIR}/renderergl1/tr_font.cpp
    ${SOURCE_DIR}/renderergl1/tr_ghost.cpp
    ${SOURCE_DIR}/renderergl1/tr_image.c
    ${SOURCE_DIR}/renderergl1/tr_init.c
    ${SOURCE_DIR}/renderergl1/tr_light.c
    ${SOURCE_DIR}/renderergl1/tr_main.c
    ${SOURCE_DIR}/renderergl1/tr_marks_permanent.c
    ${SOURCE_DIR}/renderergl1/tr_marks.c
    ${SOURCE_DIR}/renderergl1/tr_model.cpp
    ${SOURCE_DIR}/renderergl1/tr_scene.c
    ${SOURCE_DIR}/renderergl1/tr_shade_calc.c
    ${SOURCE_DIR}/renderergl1/tr_shade.c
    ${SOURCE_DIR}/renderergl1/tr_shader.c
    ${SOURCE_DIR}/renderergl1/tr_shadows.c
    ${SOURCE_DIR}/renderergl1/tr_sky_portal.cpp
    ${SOURCE_DIR}/renderergl1/tr_sky.c
    ${SOURCE_DIR}/renderergl1/tr_sphere_shade.cpp
    ${SOURCE_DIR}/renderergl1/tr_sprite.c
    ${SOURCE_DIR}/renderergl1/tr_staticmodels.cpp
    ${SOURCE_DIR}/renderergl1/tr_sun_flare.cpp
    ${SOURCE_DIR}/renderergl1/tr_surface.c
    ${SOURCE_DIR}/renderergl1/tr_swipe.cpp
    ${SOURCE_DIR}/renderergl1/tr_terrain.c
    ${SOURCE_DIR}/renderergl1/tr_util.cpp
    ${SOURCE_DIR}/renderergl1/tr_vis.cpp
    ${SOURCE_DIR}/renderergl1/tr_world.c
)

# The renderer is linked into the client
list(APPEND RENDERER_SOURCES
    ${RENDERER_COMMON_SOURCES}
    ${RENDERER_GL1_SOURCES}
    ${SDL_RENDERER_SOURCES}
    ${RENDERER_LIBRARY_SOURCES})
