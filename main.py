import os
import random
import sys

import pygame

import colors
import patterns

# Initialisierung von Pygame
pygame.init()

# Setup display
tile_size = 8
world_width = 100
world_height = 100
screen_width = tile_size * world_width
screen_height = tile_size * world_height
display_offset_x = -screen_width / 2
display_offset_y = -screen_height / 2
screen = pygame.display.set_mode((screen_width, screen_height), pygame.SRCALPHA)
pygame.display.set_caption("Game of Life")

# root dir
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.abspath(".")

# icon
icon_path = os.path.join(base_path, 'Icon.png')
icon = pygame.image.load(icon_path)
pygame.display.set_icon(icon)

# font
font = pygame.font.Font(None, 12)

font_path = os.path.join(base_path, 'fonts', '8bitOperatorPlus8-Bold.ttf')
px_b_font_12 = pygame.font.Font(font_path, 12)
px_b_font_16 = pygame.font.Font(font_path, 16)
px_b_font_26 = pygame.font.Font(font_path, 26)

font_path = os.path.join(base_path, 'fonts', 'neoletters.ttf')
neo_font_14 = pygame.font.Font(font_path, 14)

living = []
queue = []
calcs = 0


def rotate_point_clockwise(point, center):
    x_, y_ = point
    c_x, c_y = center
    new_x = c_x - (y_ - c_y)
    new_y = c_y + (x_ - c_x)
    new_point = (new_x, new_y)
    return new_point


def rotate_point_counterclockwise(point, center):
    x_, y_ = point
    c_x, c_y = center
    new_x = c_x + (y_ - c_y)
    new_y = c_y - (x_ - c_x)
    new_point = (new_x, new_y)
    return new_point


def reflect_point_horizontally(point, center):
    x_, y_ = point
    c_x, c_y = center
    new_x = c_x - (x_ - c_x)
    new_y = y_
    new_point = (new_x, new_y)
    return new_point


def reflect_point_vertically(point, center):
    x_, y_ = point
    c_x, c_y = center
    new_x = x_
    new_y = c_y - (y_ - c_y)
    new_point = (new_x, new_y)
    return new_point


def print_world():
    grid_surface = pygame.Surface((screen_width * 2, screen_height * 2))
    grid_surface.fill(colors.grey3)

    # Zeichne das Gitter auf das Surface
    for grid_x in range(0, grid_surface.get_width(), tile_size):
        pygame.draw.line(grid_surface, colors.grey4, (grid_x, 0), (grid_x, grid_surface.get_height()))
    for grid_y in range(0, grid_surface.get_height(), tile_size):
        pygame.draw.line(grid_surface, colors.grey4, (0, grid_y), (grid_surface.get_width(), grid_y))

    grid_offset_x = display_offset_x % tile_size
    grid_offset_y = display_offset_y % tile_size

    screen.blit(grid_surface, (-grid_offset_x, -grid_offset_y))

    pygame.draw.line(screen,
                     colors.dodgerBlue,
                     (0 + (display_offset_x * -1), 0), (0 + (display_offset_x * -1), screen_height))
    pygame.draw.line(screen,
                     colors.dodgerBlue,
                     (0, 0 + (display_offset_y * -1)), (screen_width, 0 + (display_offset_y * -1)))

    for c in living:
        if (0 + display_offset_x - tile_size < c[0] * tile_size < screen_width + display_offset_x
                and 0 + display_offset_y - tile_size < c[1] * tile_size < screen_height + display_offset_y):
            pygame.draw.rect(screen,
                             colors.black,
                             (
                                 (c[0] * tile_size) + display_offset_x * -1,
                                 (c[1] * tile_size) + display_offset_y * -1,
                                 tile_size,
                                 tile_size)
                             )


def check_status(pos_x, pos_y, rep):
    global calcs
    lives = 0
    checked = set()
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            new_x, new_y = pos_x + dx, pos_y + dy
            if (new_x, new_y) in living:
                lives += 1
            if not rep and (new_x, new_y) not in checked:
                check_status(new_x, new_y, True)
                checked.add((new_x, new_y))
            calcs += 1

    if (pos_x, pos_y) in living:
        if not (pos_x, pos_y) in queue and 1 < lives <= 3:
            queue.append((pos_x, pos_y))
    elif not (pos_x, pos_y) in queue and lives == 3:
        queue.append((pos_x, pos_y))


# Game state
running = True
paused = True
selecting_cell = True
selected_area = [(0, 0), (0, 0)]
selected_tile = (0, 0)
area_selected = False
old_tile_pos = ()
options = False
stats = False
placing_object = False
selected_object_index = 0
selected_object = patterns.objects[selected_object_index][1]
object_center = (0, 0)
place_offset_x = 0
place_offset_y = 0
tick_speed = 10
min_tick_speed = 5
clicked_coordinates = None
slider_dragging = False
panning = False
old_mouse_pos = ()

# Game clock
clock = pygame.time.Clock()

# Schieberegler
slider_rect = pygame.Rect(screen_width // 2 - 100, 70, 200, 10)
slider_rect_inner = pygame.Rect(screen_width // 2 - 98, 72, 200 - 4, 10 - 4)
slider_handle_rect = pygame.Rect(slider_rect.left + 30, slider_rect.centery - 5, 10, 10)

h = 20

# Option buttons
home_button = pygame.Rect(screen_width // 2 - 55, 100, 110, h)
clear_button = pygame.Rect(screen_width // 2 - 55, 130, 110, h)

clear_selected_button = pygame.Rect(screen_width // 2 - 55, 180, 110, h)
fill_button = pygame.Rect(screen_width // 2 - 55, 210, 110, h)
fill_rnd_button = pygame.Rect(screen_width // 2 - 55, 240, 110, h)
save_button = pygame.Rect(screen_width // 2 - 55, 270, 110, h)

stats_button = pygame.Rect(screen_width // 2 - 55, 320, 110, h)
placing_button = pygame.Rect(screen_width // 2 - 55, 350, 110, h)
exit_button = pygame.Rect(screen_width // 2 - 55, 380, 110, h)

# Placing buttons
previous_button = pygame.Rect(screen_width // 2 - 80 - h, 30, h * 2, h)
next_button = pygame.Rect(screen_width // 2 + 80, 30, h * 2, h)

cx = previous_button.left - h * 3
cy = 30

center_button = pygame.Rect(cx, cy, h, h)
up_button = pygame.Rect(cx, cy - h - 2, h, h)
down_button = pygame.Rect(cx, cy + h + 2, h, h)
left_button = pygame.Rect(cx - h - 2, cy, h, h)
right_button = pygame.Rect(cx + h + 2, cy, h, h)

turn_left_button = pygame.Rect(cx - h - 2, cy - h - 2, h, h)
turn_right_button = pygame.Rect(cx + h + 2, cy - h - 2, h, h)

reflect_h_button = pygame.Rect(cx - h - 2, cy + h + 2, h, h)
reflect_v_button = pygame.Rect(cx + h + 2, cy + h + 2, h, h)

place_button = pygame.Rect(next_button.right + h, 8, h * 3 + 4, h)
clear_grid_button = pygame.Rect(next_button.right + h, 30, h * 3 + 4, h)
cancel_button = pygame.Rect(next_button.right + h, 52, h * 3 + 4, h)

# Game loop
while running:
    calcs = 0
    tick_speed = max(tick_speed, min_tick_speed)
    current_fps = int(clock.get_fps())
# Check game event
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
# Key input
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if placing_object:
                    placing_object = False
                else:
                    options = not options
            elif event.key == pygame.K_SPACE:
                paused = not paused
            elif event.key == pygame.K_RETURN:
                selecting_cell = not selecting_cell
            if placing_object:
                if event.key == pygame.K_UP:
                    place_offset_y -= 1
                elif event.key == pygame.K_DOWN:
                    place_offset_y += 1
                elif event.key == pygame.K_LEFT:
                    place_offset_x -= 1
                elif event.key == pygame.K_RIGHT:
                    place_offset_x += 1
# Left click
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if selecting_cell and not options:
                tile_pos_x = (event.pos[0] + display_offset_x)//tile_size
                tile_pos_y = (event.pos[1] + display_offset_y)//tile_size
                old_tile_pos = (tile_pos_x, tile_pos_y)
                selected_area = ((tile_pos_x, tile_pos_y), (tile_pos_x, tile_pos_y))

            if options:
                if slider_handle_rect.collidepoint(event.pos):
                    slider_dragging = True

                if home_button.collidepoint(event.pos):
                    display_offset_x = -screen_width / 2
                    display_offset_y = -screen_height / 2

                if clear_button.collidepoint(event.pos):
                    living.clear()
                    queue.clear()

                start_x = selected_area[0][0] if selected_area[0][0] < selected_area[1][0] else selected_area[1][0]
                start_y = selected_area[0][1] if selected_area[0][1] < selected_area[1][1] else selected_area[1][1]
                end_x = selected_area[1][0] if selected_area[1][0] > selected_area[0][0] else selected_area[0][0]
                end_y = selected_area[1][1] if selected_area[1][1] > selected_area[0][1] else selected_area[0][1]
                if clear_selected_button.collidepoint(event.pos):
                    for y in range(int(start_y), int(end_y) + 1):
                        for x in range(int(start_x), int(end_x) + 1):
                            if (x, y) in living:
                                living.remove((x, y))
                            if (x, y) in queue:
                                living.remove((x, y))
                                queue.remove((x, y))

                if fill_button.collidepoint(event.pos):
                    for y in range(int(start_y), int(end_y) + 1):
                        for x in range(int(start_x), int(end_x) + 1):
                            if not (x, y) in living:
                                living.append((x, y))

                if fill_rnd_button.collidepoint(event.pos):
                    for y in range(int(start_y), int(end_y) + 1):
                        for x in range(int(start_x), int(end_x) + 1):
                            rnd = random.randint(0, 1)
                            if not (x, y) in living and rnd == 1:
                                living.append((x, y))

                if save_button.collidepoint(event.pos):
                    if len(living) > 0:
                        patterns.objects.append(("Custom", list(living)))

                if stats_button.collidepoint(event.pos):
                    stats = not stats

                if placing_button.collidepoint(event.pos):
                    placing_object = True
                    paused = True
                    selecting_cell = False

                if exit_button.collidepoint(event.pos):
                    running = False

            if placing_object:
                if previous_button.collidepoint(event.pos):
                    selected_object_index = (selected_object_index - 1) % len(patterns.objects)
                    selected_object = patterns.objects[selected_object_index][1]

                    min_x = min(coord[0] for coord in selected_object)
                    max_x = max(coord[0] for coord in selected_object)
                    min_y = min(coord[1] for coord in selected_object)
                    max_y = max(coord[1] for coord in selected_object)

                    middle_x = (min_x + max_x) // 2
                    middle_y = (min_y + max_y) // 2

                    object_center = (middle_x, middle_y)

                if next_button.collidepoint(event.pos):
                    selected_object_index = (selected_object_index + 1) % len(patterns.objects)
                    selected_object = patterns.objects[selected_object_index][1]

                    min_x = min(coord[0] for coord in selected_object)
                    max_x = max(coord[0] for coord in selected_object)
                    min_y = min(coord[1] for coord in selected_object)
                    max_y = max(coord[1] for coord in selected_object)

                    middle_x = (min_x + max_x) // 2
                    middle_y = (min_y + max_y) // 2

                    object_center = (middle_x, middle_y)

                if center_button.collidepoint(event.pos):
                    place_offset_x = 0
                    place_offset_y = 0
                    display_offset_x = -screen_width/2
                    display_offset_y = -screen_height/2

                if up_button.collidepoint(event.pos):
                    place_offset_y -= 1

                if down_button.collidepoint(event.pos):
                    place_offset_y += 1

                if left_button.collidepoint(event.pos):
                    place_offset_x -= 1

                if right_button.collidepoint(event.pos):
                    place_offset_x += 1

                if turn_left_button.collidepoint(event.pos):
                    selected_object = [rotate_point_counterclockwise(coord, object_center) for coord in selected_object]

                if turn_right_button.collidepoint(event.pos):
                    selected_object = [rotate_point_clockwise(coord, object_center) for coord in selected_object]

                if reflect_h_button.collidepoint(event.pos):
                    selected_object = [reflect_point_horizontally(coord, object_center) for coord in selected_object]

                if reflect_v_button.collidepoint(event.pos):
                    selected_object = [reflect_point_vertically(coord, object_center) for coord in selected_object]

                if place_button.collidepoint(event.pos):
                    for cell in selected_object:
                        x = (cell[0] + place_offset_x)
                        y = (cell[1] + place_offset_y)
                        if not (x, y) in living:
                            living.append((x, y))

                if cancel_button.collidepoint(event.pos):
                    placing_object = False

                if clear_grid_button.collidepoint(event.pos):
                    living.clear()
                    queue.clear()

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:

            slider_dragging = False

            if selecting_cell and not options:
                tile_pos_x = (event.pos[0] + display_offset_x)//tile_size
                tile_pos_y = (event.pos[1] + display_offset_y)//tile_size
                if tile_pos_x == old_tile_pos[0] and tile_pos_y == old_tile_pos[1]:
                    clicked_coordinates = pygame.mouse.get_pos()
                    x = (clicked_coordinates[0] + display_offset_x) // tile_size
                    y = (clicked_coordinates[1] + display_offset_y) // tile_size

                    if (x, y) in living:
                        living.remove((x, y))
                    else:
                        living.append((x, y))
                    area_selected = False
# Mouse motion
        elif event.type == pygame.MOUSEMOTION:
            if panning:
                if not old_mouse_pos == ():
                    display_offset_x += (old_mouse_pos[0] - event.pos[0])
                    display_offset_y += (old_mouse_pos[1] - event.pos[1])
                    old_mouse_pos = event.pos
                else:
                    old_mouse_pos = event.pos

            tile_pos_x = (event.pos[0] + display_offset_x)//tile_size
            tile_pos_y = (event.pos[1] + display_offset_y)//tile_size
            selected_tile = (tile_pos_x, tile_pos_y)
            if pygame.mouse.get_pressed()[0] and not options and len(old_tile_pos) > 0:
                selected_area = ((old_tile_pos[0], old_tile_pos[1]), (tile_pos_x, tile_pos_y))
                if selected_area[0][0] == selected_area[1][0] and selected_area[0][1] == selected_area[1][1]:
                    area_selected = False
                    selected_area = ((tile_pos_x, tile_pos_y), (tile_pos_x, tile_pos_y))
                else:
                    area_selected = True

            if not area_selected:
                selected_area = ((tile_pos_x, tile_pos_y), (tile_pos_x, tile_pos_y))

            if slider_dragging and options:
                slider_handle_rect.centerx = min(max(event.pos[0], slider_rect.left + 5), slider_rect.right - 5)
                tick_speed = int((slider_handle_rect.centerx - slider_rect.left) / (slider_rect.width - 5) * 60)
# Mousewheel/button
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
            panning = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 2:
            panning = False
            old_mouse_pos = ()

        elif event.type == pygame.MOUSEWHEEL:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if event.y > 0 and tile_size < 16:
                tile_size = max(1, min(tile_size * 2, 16))
                world_width = max(50, min(world_width // 2, 1600))
                world_height = max(50, min(world_height // 2, 1600))
                display_offset_x += (display_offset_x + pygame.mouse.get_pos()[0])
                display_offset_y += (display_offset_y + pygame.mouse.get_pos()[1])
                screen = pygame.display.set_mode((screen_width, screen_height))
            if event.y < 0 and tile_size > 1:
                display_offset_x -= (display_offset_x + mouse_x) // 2
                display_offset_y -= (display_offset_y + mouse_y) // 2
                tile_size = max(1, min(tile_size // 2, 16))
                world_width = max(50, min(world_width * 2, 1600))
                world_height = max(50, min(world_height * 2, 1600))
                screen = pygame.display.set_mode((screen_width, screen_height))

    # Game logik
    if not paused:
        for cell in living:
            check_status(cell[0], cell[1], False)

        living.clear()
        for cell in queue:
            living.append(cell)

        queue.clear()

# Draw screen
    # define button layout
    def draw_button(button, name):
        if len(name) <= 1:
            button_font = neo_font_14
        else:
            button_font = px_b_font_12
        pygame.draw.rect(screen,
                         colors.steelBlue
                         if
                         pygame.mouse.get_pressed()[0] and button.collidepoint(pygame.mouse.get_pos())
                         else
                         (colors.darkSlateGrey if button.collidepoint(pygame.mouse.get_pos()) else colors.grey5),
                         button,
                         border_radius=6)
        pygame.draw.rect(screen, colors.dodgerBlue, button, 2, 6)
        button_text = button_font.render(name, True, colors.grey2)
        button_rect = button_text.get_rect(center=button.center)
        screen.blit(button_text, button_rect)

    # define text layout
    def draw_text(f, str_text, pos, color, text_alignment):
        t = f.render(str_text, True, color)
        t_rect = t.get_rect()
        if text_alignment == 'center':
            t_rect.center = pos
        elif text_alignment == 'midleft':
            t_rect.midleft = pos
        elif text_alignment == 'topleft':
            t_rect.topleft = pos
        screen.blit(t, t_rect)

    # print world
    print_world()

    # print highlight and selected area
    selected_tile_rect = pygame.Rect(selected_tile[0]*tile_size, selected_tile[1]*tile_size, tile_size, tile_size)
    selected_tile_rect.move_ip(display_offset_x*-1, display_offset_y*-1)
    pygame.draw.rect(screen, colors.dodgerBlue, selected_tile_rect, 1)
    if area_selected:
        start_x = selected_area[0][0] * tile_size \
            if selected_area[0][0] < selected_area[1][0] else selected_area[1][0] * tile_size
        start_y = selected_area[0][1] * tile_size \
            if selected_area[0][1] < selected_area[1][1] else selected_area[1][1] * tile_size
        end_x = selected_area[1][0] * tile_size - start_x \
            if selected_area[1][0] > selected_area[0][0] else selected_area[0][0] * tile_size - start_x
        end_y = selected_area[1][1] * tile_size - start_y \
            if selected_area[1][1] > selected_area[0][1] else selected_area[0][1] * tile_size - start_y
        selected_rect = pygame.Rect(
            start_x,
            start_y,
            end_x + tile_size,
            end_y + tile_size
        )
        selected_rect.move_ip(display_offset_x*-1, display_offset_y*-1)
        pygame.draw.rect(screen, colors.dodgerBlue, selected_rect, 1)

    # Pause
    if options and not placing_object:
        draw_text(px_b_font_26, "Options", (screen_width // 2, 18), colors.grey5, 'center')
        draw_text(px_b_font_16, "Tick Speed", (screen_width // 2, 60), colors.grey5, 'center')

        pygame.draw.rect(screen, colors.dodgerBlue, slider_rect, border_radius=4)
        pygame.draw.rect(screen, colors.grey5, slider_rect, 2, 4)
        pygame.draw.rect(screen, colors.grey5, slider_handle_rect, border_radius=4)

        draw_button(home_button, "Home")
        draw_button(clear_button, "Clear Grid")

        draw_button(clear_selected_button, "Clear Select")
        draw_button(fill_button, "Fill Area")
        draw_button(fill_rnd_button, "Fill Random")
        draw_button(save_button, "Save Patern")

        draw_button(stats_button, "Show Stats")
        draw_button(placing_button, "Place Object")
        draw_button(exit_button, "Exit")
    # Placing
    elif placing_object:
        text_display = pygame.Rect(previous_button.right - 6,
                                   previous_button.top,
                                   next_button.left - previous_button.right + 12,
                                   20
                                   )
        pygame.draw.rect(screen, colors.grey5, text_display)
        pygame.draw.rect(screen, colors.dodgerBlue, text_display, 2)

        draw_text(px_b_font_12, str(patterns.objects[selected_object_index][0]), text_display.center, colors.grey2, 'center')

        draw_button(previous_button, "Prev")
        draw_button(next_button, "Next")
        draw_button(center_button, "⌂")
        draw_button(up_button, "↑")
        draw_button(down_button, "↓")
        draw_button(left_button, "←")
        draw_button(right_button, "→")
        draw_button(turn_left_button, "↺")
        draw_button(turn_right_button, "↻")
        draw_button(reflect_h_button, "↔")
        draw_button(reflect_v_button, "↕")
        draw_button(place_button, "Place")
        draw_button(clear_grid_button, "Clear")
        draw_button(cancel_button, "Cancel")

        for cell in selected_object:
            pygame.draw.rect(screen, colors.oliveDrab, (
                ((cell[0] + place_offset_x) * tile_size) + display_offset_x*-1,
                ((cell[1] + place_offset_y) * tile_size) + display_offset_y*-1, tile_size, tile_size), 2)

    else:
        pygame.draw.rect(screen,
                         colors.grey5,
                         (screen_width / 2 - 50, -6, 100,
                          38
                          if selecting_cell and paused
                          else (22 if selecting_cell or paused else 6)),
                         border_radius=6)
        pygame.draw.rect(screen,
                         colors.dodgerBlue,
                         (screen_width / 2 - 50, -6, 100,
                          38
                          if selecting_cell and paused
                          else (22 if selecting_cell or paused else 6)),
                         2,
                         6)
        if selecting_cell:
            draw_text(px_b_font_12,
                      "[Selecting]",
                      (screen_width // 2, 6),
                      colors.grey2,
                      'center')
        if paused:
            draw_text(px_b_font_12,
                      "[Paused]",
                      (screen_width // 2, 22 if selecting_cell else 6),
                      colors.grey2,
                      'center')
    # Show stats
    if stats:
        pygame.draw.rect(screen,
                         colors.grey5,
                         (screen_width - 110, screen_height - 32, 112, 70),
                         border_top_left_radius=6)
        pygame.draw.rect(screen,
                         colors.dodgerBlue,
                         (screen_width - 110, screen_height - 32, 112, 70),
                         2,
                         border_top_left_radius=6)
        draw_text(px_b_font_12,
                  f"tps: {tick_speed}",
                  (screen_width - 105, screen_height - 24),
                  colors.grey2,
                  'midleft')
        draw_text(px_b_font_12,
                  f"fps: {current_fps}",
                  (screen_width - 105, screen_height - 8),
                  colors.grey2,
                  'midleft')

        pygame.draw.rect(screen, colors.grey5, (-2, screen_height - 32, 110, 38), border_top_right_radius=6)
        pygame.draw.rect(screen, colors.dodgerBlue, (-2, screen_height - 32, 110, 38), 2, border_top_right_radius=6)
        draw_text(px_b_font_12, f"Cells: {len(living)}", (5, screen_height - 24), colors.grey2, 'midleft')
        draw_text(px_b_font_12, f"Calcs: {calcs}", (5, screen_height - 8), colors.grey2, 'midleft')

        coord_rect = pygame.Rect(screen_width // 2 - (len(str(int(selected_tile[0]))) +
                                                      len(str(int(selected_tile[1]))) * 9) // 2 - 45,
                                 screen_height - 36,
                                 (len(str(int(selected_tile[0]))) + len(str(int(selected_tile[1]))) * 9) + 90,
                                 32)
        pygame.draw.rect(screen, colors.grey5, coord_rect, border_radius=6)
        pygame.draw.rect(screen, colors.dodgerBlue, coord_rect, 2, border_radius=6)
        draw_text(px_b_font_12,
                  f"X[{int(selected_tile[0])}] Y[{int(selected_tile[1])}]",
                  (screen_width//2, screen_height - 26),
                  colors.grey2,
                  'center'
                  )

    # Info text
    text_ln = "[ESC for Options]   [Enter for selecting]   [Spacebar for Pause]"
    text = px_b_font_12.render(text_ln.upper(), True, colors.grey2)
    fw = px_b_font_12.get_linesize()//2
    text_rect = text.get_rect(topleft=(screen_width // 2 - (len(text_ln) * fw) // 2, screen_height - 12))
    pygame.draw.rect(screen,
                     colors.grey5,
                     (screen_width // 2 - (len(text_ln) * fw) // 2 - 15,
                      screen_height - 20,
                      (len(text_ln) * fw) + 30,
                      32
                      ),
                     border_radius=6)
    pygame.draw.rect(screen,
                     colors.dodgerBlue,
                     (screen_width // 2 - (len(text_ln) * fw) // 2 - 15,
                      screen_height - 20,
                      (len(text_ln) * fw) + 30,
                      32
                      ),
                     2,
                     6)
    screen.blit(text, text_rect)

    # Update screen
    pygame.display.update()
    clock.tick(tick_speed)

pygame.quit()
