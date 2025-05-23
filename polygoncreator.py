import pygame, pygame_gui, sys, json, os, math, numpy as np, colorsys
from tkinter import filedialog, Tk

root = Tk()
root.withdraw()


class PolygonCreator:
    def __init__(self):
        pygame.init()
        
        # For better text rendering
        pygame.freetype.init()
        
        self.fullscreen = True
        info = pygame.display.Info()
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = info.current_w, info.current_h
        self.PANEL_WIDTH = 200
        
        # Different hitbox sizes for different modes
        self.CONNECT_HITBOX_SIZE = 50  # Large hitbox for connect mode
        self.ADD_HITBOX_SIZE = 15  # Smaller hitbox for add mode
        
        self.CANVAS_WIDTH, self.CANVAS_HEIGHT = self.SCREEN_WIDTH - self.PANEL_WIDTH, self.SCREEN_HEIGHT
        
        # Define colors with better contrast and smoother feel
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GRAY = (80, 80, 80)
        self.LIGHT_GRAY = (220, 220, 220)  # Lighter for better contrast
        self.BLUE = (41, 128, 185)  # More muted blue
        self.CYAN = (0, 190, 218)  # Less harsh cyan
        self.YELLOW = (241, 196, 15)  # Warmer yellow
        self.GREEN = (46, 204, 113)  # More pleasant green
        self.RED = (231, 76, 60)  # Less harsh red
        self.HOVER_COLOR = (142, 68, 173)  # Purple for hover
        
        # Quality settings
        self.DRAW_AA = True  # Anti-aliasing
        self.LINE_WIDTH = 2
        self.POINT_BORDER = 1
        
        # Set display without OpenGL (which was causing black screen)
        display_flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        self.screen = pygame.display.set_mode((0, 0), display_flags)
        pygame.display.set_caption("Polygon Creator")
        
        # For better font rendering - using freetype if available
        try:
            self.font_small = pygame.freetype.SysFont('Arial', 14)
            self.font_medium = pygame.freetype.SysFont('Arial', 18)
            self.font_large = pygame.freetype.SysFont('Arial', 24, bold=True)
            self.use_freetype = True
        except:
            self.font_small = pygame.font.SysFont('Arial', 14)
            self.font_medium = pygame.font.SysFont('Arial', 18) 
            self.font_large = pygame.font.SysFont('Arial', 24, bold=True)
            self.use_freetype = False
        
        # Set flag defaults
        self.use_opengl = False  # Disabled since it was causing problems
        
        self.manager = pygame_gui.UIManager((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.points, self.lines, self.polygons, self.polygon_colors = [], [], [], []
        self.current_point = self.hovered_point = self.dragging_point = None
        self.last_added_point = None  # Track the last point added in add mode
        self.first_sequence_point = None  # Track the first point in a connected sequence
        self.add_point_mode, self.connect_point_mode = True, False
        self.grid_size, self.show_grid = 20, True
        
        self.clock, self.animation_time, self.status_timer, self.export_results = pygame.time.Clock(), 0, 0, None
        self.status_message, self.running = "Mode: Add Points", True
        self.setup_ui()

    def setup_ui(self):
        self.panel_rect = pygame.Rect(self.CANVAS_WIDTH, 0, self.PANEL_WIDTH, self.SCREEN_HEIGHT)
        button_width = self.PANEL_WIDTH - 20
        btn_data = [
            ("Add Points", 70, lambda: self.set_mode("add")),
            ("Connect Points", 120, lambda: self.set_mode("connect")),
            ("Clear All", 170, self.clear_all),
            ("Export", 220, self.export_polygons),
            ("Exit", self.SCREEN_HEIGHT - 50, lambda: setattr(self, 'running', False))
        ]
        self.buttons = {pygame_gui.elements.UIButton(pygame.Rect((self.CANVAS_WIDTH + 10, y), (button_width, 40)), t,
                                                     self.manager): f for t, y, f in btn_data}

    def set_mode(self, mode):
        self.add_point_mode, self.connect_point_mode = mode == "add", mode == "connect"
        self.status_message = f"Mode: {'Add' if mode == 'add' else 'Connect'} Points"
        self.current_point, self.status_timer = None if mode == "connect" else self.current_point, 90

    def draw_grid(self):
        if self.show_grid:
            # Draw a darker, less intrusive grid
            grid_color = (30, 30, 30)  # Darker grid lines
            
            # Draw vertical grid lines
            for x in range(0, self.CANVAS_WIDTH, self.grid_size):
                pygame.draw.line(self.screen, grid_color, (x, 0), (x, self.CANVAS_HEIGHT), 1)
            
            # Draw horizontal grid lines
            for y in range(0, self.CANVAS_HEIGHT, self.grid_size):
                pygame.draw.line(self.screen, grid_color, (0, y), (self.CANVAS_WIDTH, y), 1)

    def draw_panel(self):
        pygame.draw.rect(self.screen, self.LIGHT_GRAY, self.panel_rect)
        pygame.draw.line(self.screen, self.WHITE, (self.CANVAS_WIDTH, 0), (self.CANVAS_WIDTH, self.SCREEN_HEIGHT), 2)
        
        # Title
        if self.use_freetype:
            self.font_large.render_to(self.screen, (self.CANVAS_WIDTH + (self.PANEL_WIDTH - self.font_large.get_rect("Polygon Creator").width) // 2, 20), 
                                     "Polygon Creator", self.BLACK)
        else:
            title = self.font_large.render("Polygon Creator", True, self.BLACK)
            self.screen.blit(title, (self.CANVAS_WIDTH + (self.PANEL_WIDTH - title.get_width()) // 2, 20))

        # Stats
        stats = [f"Points: {len(self.points)}", f"Lines: {len(self.lines)}", f"Polygons: {len(self.polygons)}"]
        for i, stat in enumerate(stats):
            self.draw_text(self.screen, stat, self.font_medium, self.BLACK, (self.CANVAS_WIDTH + 10, 280 + i * 30))

        # Mode text
        mode_text = "Mode: Add Points" if self.add_point_mode else "Mode: Connect Points"
        self.draw_text(self.screen, mode_text, self.font_medium, self.BLACK, (self.CANVAS_WIDTH + 10, 380))

        # Hints
        if self.add_point_mode:
            hints = [
                "Hold Shift for isolated points",
                "Click first point to close polygon",
                "Right-click to delete a point"
            ]
            for i, hint in enumerate(hints):
                self.draw_text(self.screen, hint, self.font_small, self.BLACK, (self.CANVAS_WIDTH + 10, 405 + i * 20))
        else:
            hint = "Right-click to delete a point"
            self.draw_text(self.screen, hint, self.font_small, self.BLACK, (self.CANVAS_WIDTH + 10, 405))

        # Export results
        if self.export_results:
            # Calculate y offset
            y_offset = 465 if self.add_point_mode else 425
            self.draw_text(self.screen, "Exported Coordinates:", self.font_small, self.BLACK, (self.CANVAS_WIDTH + 10, y_offset))
            
            # Format display text
            display_text = ' '.join(map(str, self.export_results[:24])) + (
                " ..." if len(self.export_results) > 24 else "")
            
            # Wrap text
            wrapped = []
            line = ""
            if self.use_freetype:
                for word in display_text.split():
                    test = line + word + " "
                    if self.font_small.get_rect(test).width < self.PANEL_WIDTH - 20:
                        line = test
                    else:
                        wrapped.append(line)
                        line = word + " "
            else:
                for word in display_text.split():
                    test = line + word + " "
                    if self.font_small.size(test)[0] < self.PANEL_WIDTH - 20:
                        line = test
                    else:
                        wrapped.append(line)
                        line = word + " "
            
            if line: 
                wrapped.append(line)
            
            # Display wrapped text
            for i, line in enumerate(wrapped[:self.SCREEN_HEIGHT // 20 - 23]):
                self.draw_text(self.screen, line, self.font_small, self.BLACK, 
                             (self.CANVAS_WIDTH + 10, y_offset + i * 20))
            
            if len(wrapped) > self.SCREEN_HEIGHT // 20 - 23:
                self.draw_text(self.screen, "...", self.font_small, self.BLACK,
                             (self.CANVAS_WIDTH + 10, y_offset + (self.SCREEN_HEIGHT // 20 - 23) * 20))

        status_rect = pygame.Rect(self.CANVAS_WIDTH + 5, self.SCREEN_HEIGHT - 100, self.PANEL_WIDTH - 10, 30)
        pygame.draw.rect(self.screen, (200, 200, 200), status_rect)
        self.draw_text(self.screen, self.status_message, self.font_small, self.BLACK, (status_rect.x + 5, status_rect.y + 5))

    def wavelength_to_rgb(self, wavelength):
        gamma, i_max = 0.8, 255
        r, g, b = [(1, 0, 0) if wavelength >= 645 else (1, -(wavelength - 645) / 65, 0) if wavelength >= 580 else
        ((wavelength - 510) / 70, 1, 0) if wavelength >= 510 else (
            0, 1, -(wavelength - 510) / 20) if wavelength >= 490 else
        (0, (wavelength - 440) / 50, 1) if wavelength >= 440 else (-(wavelength - 440) / 60, 0, 1)][0]
        factor = 0.3 + 0.7 * (wavelength - 380) / 40 if wavelength < 420 else 0.3 + 0.7 * (
                780 - wavelength) / 120 if wavelength > 660 else 1
        return tuple(int(i_max * ((c * factor) ** gamma)) for c in (r, g, b))

    def compute_polygon_perimeter(self, polygon):
        return sum(
            math.sqrt((self.points[p2][0] - self.points[p1][0]) ** 2 + (self.points[p2][1] - self.points[p1][1]) ** 2)
            for p1, p2 in zip(polygon, polygon[1:] + [polygon[0]]))

    def find_polygons(self):
        self.polygons, self.polygon_colors = [], []
        if len(self.points) < 3 or len(self.lines) < 3: return
        graph = {i: [] for i in range(len(self.points))}
        for p1, p2 in self.lines: graph[p1].append(p2); graph[p2].append(p1)

        def find_cycles(node, visited, path, start):
            path.append(node);
            visited[node] = True
            for n in graph[node]:
                if n == start and len(path) >= 3:
                    self.polygons.append(path[:])
                elif not visited[n]:
                    find_cycles(n, visited.copy(), path[:], start)

        for i in range(len(self.points)): find_cycles(i, {j: False for j in range(len(self.points))}, [], i)
        self.polygons = [sorted(p) for p in set(tuple(sorted(p)) for p in self.polygons)]
        perimeters = [self.compute_polygon_perimeter(p) for p in self.polygons]
        min_p, max_p = min(perimeters, default=0), max(perimeters, default=0)
        self.polygon_colors = [self.wavelength_to_rgb(400 + 300 * (1 - (p - min_p) / (max_p - min_p + 0.1))) for p in
                               perimeters]

    def find_polygon_for_line(self, line):
        p1, p2 = line
        for i, p in enumerate(self.polygons):
            if p1 in p and p2 in p and (abs(p.index(p1) - p.index(p2)) in (1, len(p) - 1)): return i
        return None

    def draw_canvas(self):
        pygame.draw.rect(self.screen, self.BLACK, (0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT))
        self.draw_grid()
        self.animation_time += 0.05
        for line in self.lines:
            p1, p2 = [self.points[i] for i in line]
            pid = self.find_polygon_for_line(line)
            color, width = (self.polygon_colors[pid], 2 + int(
                (math.sin(self.animation_time + pid * 0.5) * 0.5 + 0.5) * 2)) if pid is not None else (self.CYAN, 2)
            self.draw_aa_line(self.screen, color, color, p1, p2, width)
        for i, p in enumerate(self.points):
            # Add special indicator for the first point in a sequence
            if i == self.first_sequence_point:
                # Draw an outer ring to highlight first point in sequence
                self.draw_aa_circle(self.screen, self.GREEN, p, 10, 2)

            c, r = (self.YELLOW, 8) if i == self.current_point else (
                self.HOVER_COLOR, 7) if i == self.hovered_point else (self.WHITE, 6)
            self.draw_aa_circle(self.screen, c, p, r)
            self.draw_text(self.screen, str(i + 1), self.font_small, self.WHITE, (p[0] + 8, p[1] - 8))

    def get_point_at_position(self, pos):
        # Use the appropriate hitbox size based on the current mode
        hitbox_size = self.CONNECT_HITBOX_SIZE if self.connect_point_mode else self.ADD_HITBOX_SIZE

        return next((i for i, p in enumerate(self.points) if
                     ((p[0] - pos[0]) ** 2 + (p[1] - pos[1]) ** 2) ** 0.5 < hitbox_size), None)

    def add_point(self, pos, shift_pressed=False):
        # If we're clicking on an existing point, start dragging it or close polygon
        if (p := self.get_point_at_position(pos)) is not None:
            # Check if this is the first point in the sequence - close the polygon
            if self.last_added_point is not None and p == self.first_sequence_point and p != self.last_added_point:
                # Close the polygon by connecting the last point to the first point
                self.lines.append((self.last_added_point, p))
                self.status_message = f"Closed polygon: connected point {self.last_added_point + 1} to point {p + 1}"
                self.find_polygons()

                # Reset sequence trackers to start a new polygon
                self.last_added_point = None
                self.first_sequence_point = None
                self.status_timer = 90
                return

            # Not closing a polygon, so start dragging the point
            self.dragging_point = p
            return

        # Add the new point
        point_idx = len(self.points)
        self.points.append(pos)

        # If we have a previous point and not holding shift, connect them
        if self.last_added_point is not None and not shift_pressed:
            self.lines.append((self.last_added_point, point_idx))
            self.status_message = f"Added point {point_idx + 1} and connected to {self.last_added_point + 1}"
            # Update polygons since we added a line
            self.find_polygons()
        else:
            self.status_message = f"Added isolated point {point_idx + 1}"
            # This is a new sequence, so set the first point of the sequence
            self.first_sequence_point = point_idx

        # Update the last added point
        self.last_added_point = point_idx
        self.status_timer = 90

    def select_point(self, pos):
        if not self.points: self.status_message, self.status_timer = "No points to select.", 90; return
        if (idx := self.get_point_at_position(
                pos)) is None: self.status_message, self.status_timer = "No point nearby.", 90; return
        if self.current_point is None:
            self.current_point, self.status_message = idx, f"Selected point {idx + 1}"
        elif self.current_point == idx:
            self.status_message = "Can't connect a point to itself."
        elif (self.current_point, idx) in self.lines or (idx, self.current_point) in self.lines:
            self.status_message = "These points are already connected."
        else:
            self.lines.append((self.current_point,
                               idx));
            self.status_message = f"Connected points {self.current_point + 1} and {idx + 1}";
            self.find_polygons();
            self.current_point = idx
        self.status_timer = 90

    def update_hover(self, pos):
        self.hovered_point = self.get_point_at_position(pos)

    def clear_all(self):
        self.points, self.lines, self.polygons, self.polygon_colors = [], [], [], []
        self.current_point, self.hovered_point, self.dragging_point = None, None, None
        self.last_added_point, self.first_sequence_point = None, None
        self.status_message, self.status_timer = "All cleared", 90

    def are_polygons_valid(self):
        if not self.lines: return False, "No lines drawn yet."
        counts = {i: 0 for i in range(len(self.points))}
        for p1, p2 in self.lines: counts[p1] += 1; counts[p2] += 1
        for i, c in counts.items():
            if c == 0: return False, f"Point {i + 1} is not connected to any line."
            if c == 1: return False, f"Point {i + 1} is only connected to one line."
            if c % 2: return False, f"Point {i + 1} has an odd number of lines ({c})."
        return True, "Polygons are valid!"

    def export_polygons(self):
        valid, msg = self.are_polygons_valid()
        if not valid: self.show_message_box("Invalid Polygons", msg); return
        flat_coords = [c for l in self.lines for p in (self.points[l[0]], self.points[l[1]]) for c in p]
        self.export_results = flat_coords
        if file_path := filedialog.asksaveasfilename(defaultextension=".txt",
                                                     filetypes=[("Text files", "*.txt"), ("All files", "*.*")]):
            with open(file_path, 'w') as f: f.write(' '.join(map(str, flat_coords)))
            self.status_message, self.status_timer = f"Exported {len(self.lines)} lines to file", 90

    def show_message_box(self, title, msg):
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        mw, mh = 300, 150;
        mx, my = (self.SCREEN_WIDTH - mw) // 2, (self.SCREEN_HEIGHT - mh) // 2
        pygame.draw.rect(overlay, (30, 30, 30), (mx, my, mw, mh));
        pygame.draw.rect(overlay, self.WHITE, (mx, my, mw, mh), 2)
        overlay.blit(self.font_medium.render(title, True, self.WHITE),
                     (mx + (mw - self.font_medium.size(title)[0]) // 2, my + 20))
        for i, line in enumerate(msg.split('\n')):
            overlay.blit(self.font_small.render(line, True, self.WHITE),
                         (mx + (mw - self.font_small.size(line)[0]) // 2, my + 50 + i * 25))
        pygame.draw.rect(overlay, self.BLUE, (mx + 100, my + mh - 40, 100, 30));
        pygame.draw.rect(overlay, self.WHITE, (mx + 100, my + mh - 40, 100, 30), 1)
        overlay.blit(self.font_small.render("OK", True, self.WHITE),
                     (mx + 150 - self.font_small.size("OK")[0] // 2, my + mh - 35))
        self.screen.blit(overlay, (0, 0));
        pygame.display.flip()
        while True:
            for e in pygame.event.get():
                if e.type in (pygame.QUIT, pygame.KEYDOWN) and (
                        e.type == pygame.QUIT or e.key == pygame.K_ESCAPE): pygame.quit(); sys.exit()
                if e.type == pygame.MOUSEBUTTONDOWN and mx + 100 <= e.pos[0] <= mx + 200 and my + mh - 40 <= e.pos[
                    1] <= my + mh - 10: return
            self.clock.tick(30)

    def delete_point(self, point_idx):
        if point_idx is None or point_idx >= len(self.points):
            return

        # Remember if this was the first point in a sequence
        was_first_point = (point_idx == self.first_sequence_point)

        # Remove the point
        deleted_point = self.points.pop(point_idx)

        # Find all lines connected to this point
        lines_to_remove = []
        for i, (p1, p2) in enumerate(self.lines):
            if p1 == point_idx or p2 == point_idx:
                lines_to_remove.append(i)

        # Remove lines in reverse order to not mess up indices
        for i in sorted(lines_to_remove, reverse=True):
            self.lines.pop(i)

        # Update indices in remaining lines
        updated_lines = []
        for p1, p2 in self.lines:
            new_p1 = p1 if p1 < point_idx else p1 - 1
            new_p2 = p2 if p2 < point_idx else p2 - 1
            updated_lines.append((new_p1, new_p2))
        self.lines = updated_lines

        # Update trackers
        if self.current_point is not None:
            if self.current_point == point_idx:
                self.current_point = None
            elif self.current_point > point_idx:
                self.current_point -= 1

        if self.last_added_point is not None:
            if self.last_added_point == point_idx:
                self.last_added_point = None
            elif self.last_added_point > point_idx:
                self.last_added_point -= 1

        if self.first_sequence_point is not None:
            if was_first_point:
                self.first_sequence_point = None
            elif self.first_sequence_point > point_idx:
                self.first_sequence_point -= 1

        if self.dragging_point is not None:
            if self.dragging_point == point_idx:
                self.dragging_point = None
            elif self.dragging_point > point_idx:
                self.dragging_point -= 1

        # Update polygons
        self.find_polygons()

        self.status_message = f"Deleted point at {deleted_point}"
        self.status_timer = 90

    def draw_aa_line(self, surface, color1, color2, start_pos, end_pos, width=2):
        """Draw a high quality anti-aliased line with gradient color"""
        if not self.DRAW_AA:
            pygame.draw.line(surface, color1, start_pos, end_pos, width)
            return
            
        # Draw the main line with anti-aliasing
        pygame.draw.aaline(surface, color1, start_pos, end_pos, 1)
        
        # For thicker lines, draw multiple anti-aliased lines
        if width > 1:
            # Calculate perpendicular vectors
            dx, dy = end_pos[0] - start_pos[0], end_pos[1] - start_pos[1]
            length = max(1, math.sqrt(dx*dx + dy*dy))
            udx, udy = dx/length, dy/length
            # Perpendicular vector
            px, py = -udy, udx
            
            # Draw multiple lines for thickness
            for i in range(1, width//2 + 1):
                # Offset in perpendicular direction
                offset1 = (px * i, py * i)
                offset2 = (-px * i, -py * i)
                
                # Calculate positions
                start1 = (start_pos[0] + offset1[0], start_pos[1] + offset1[1])
                end1 = (end_pos[0] + offset1[0], end_pos[1] + offset1[1])
                start2 = (start_pos[0] + offset2[0], start_pos[1] + offset2[1])
                end2 = (end_pos[0] + offset2[0], end_pos[1] + offset2[1])
                
                # Draw offset lines
                pygame.draw.aaline(surface, color1, start1, end1, 1)
                pygame.draw.aaline(surface, color1, start2, end2, 1)

    def draw_aa_circle(self, surface, color, center, radius, width=0):
        """Draw a high quality anti-aliased circle"""
        if not self.DRAW_AA:
            pygame.draw.circle(surface, color, center, radius, width)
            return
            
        # For filled circles
        if width == 0:
            pygame.draw.circle(surface, color, center, radius)
            return
            
        # For outlined circles, draw two circles and fill between them
        pygame.draw.circle(surface, color, center, radius)
        inner_radius = max(1, radius - width)
        # Draw inner circle in background color
        pygame.draw.circle(surface, self.BLACK, center, inner_radius)

    def draw_text(self, surface, text, font, color, position, centered=False):
        """Draw text with the best available method"""
        if self.use_freetype:
            text_rect = font.get_rect(text)
            if centered:
                text_rect.center = position
            else:
                text_rect.topleft = position
            font.render_to(surface, text_rect, text, color)
        else:
            text_surface = font.render(text, True, color)
            if centered:
                text_rect = text_surface.get_rect(center=position)
            else:
                text_rect = text_surface.get_rect(topleft=position)
            surface.blit(text_surface, text_rect)

    def run(self):
        while self.running:
            time_delta = self.clock.tick(60) / 1000.0  # Increase to 60 FPS for smoother animation
            pos = pygame.mouse.get_pos()
            
            if pos[0] < self.CANVAS_WIDTH:
                self.update_hover(pos)
                
            for e in pygame.event.get():
                self.manager.process_events(e)
                
                if e.type in (pygame.QUIT, pygame.KEYDOWN) and (e.type == pygame.QUIT or e.key == pygame.K_ESCAPE):
                    self.running = False
                    
                elif e.type == pygame.MOUSEBUTTONDOWN and pos[0] < self.CANVAS_WIDTH:
                    if e.button == 1:  # Left button
                        # Check if shift is pressed when adding points
                        shift_pressed = pygame.key.get_mods() & pygame.KMOD_SHIFT
                        if self.add_point_mode:
                            self.add_point(pos, shift_pressed)
                        else:
                            self.select_point(pos)
                    elif e.button == 3:  # Right button - delete point
                        point_idx = self.get_point_at_position(pos)
                        if point_idx is not None:
                            self.delete_point(point_idx)
                            
                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and self.dragging_point is not None:
                    self.status_message = f"Point {self.dragging_point + 1} moved"
                    self.status_timer = 90
                    self.dragging_point = None
                    self.find_polygons()
                    
                elif e.type == pygame.MOUSEMOTION and self.dragging_point is not None and self.add_point_mode and pos[0] < self.CANVAS_WIDTH:
                    self.points[self.dragging_point] = pos
                    
                elif e.type == pygame.USEREVENT and e.user_type == pygame_gui.UI_BUTTON_PRESSED and e.ui_element in self.buttons:
                    self.buttons[e.ui_element]()
                    
            self.manager.update(time_delta)
            
            # Draw everything
            self.draw_canvas()
            self.draw_panel()
            self.manager.draw_ui(self.screen)
            
            # Update the display
            pygame.display.flip()
            
            # Update status timer
            if self.status_timer > 0:
                self.status_timer -= 1
                
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    PolygonCreator().run()