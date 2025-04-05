import pygame
import pygame_gui
import sys
import json
import os
from tkinter import filedialog
import tkinter as tk
import math
import numpy as np
import colorsys

# Initialize Tkinter just for file dialogs (hidden)
root = tk.Tk()
root.withdraw()

class PolygonCreator:
    def __init__(self):
        pygame.init()
        
        # Screen setup for truly full screen
        self.fullscreen = True
        self.info = pygame.display.Info()
        self.SCREEN_WIDTH = self.info.current_w
        self.SCREEN_HEIGHT = self.info.current_h
        self.PANEL_WIDTH = 200  # Slimmer panel for cleaner look
        self.CANVAS_WIDTH = self.SCREEN_WIDTH - self.PANEL_WIDTH
        self.CANVAS_HEIGHT = self.SCREEN_HEIGHT
        
        # Point selection hitbox size (increased for easier selection)
        self.POINT_HITBOX_SIZE = 50  # Increased from 10
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GRAY = (80, 80, 80)
        self.LIGHT_GRAY = (120, 120, 120)
        self.BLUE = (0, 120, 255)
        self.CYAN = (0, 255, 255)
        self.YELLOW = (255, 255, 0)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.HOVER_COLOR = (180, 180, 255)  # Light blue color for hover
        
        # Display setup - ensure true fullscreen
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("Polygon Cretor")
        
        # GUI manager
        self.manager = pygame_gui.UIManager((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        
        # Data structures
        self.points = []  # List of (x, y) tuples
        self.lines = []   # List of (point_idx1, point_idx2) tuples
        self.current_point = None  # Currently selected point
        self.hovered_point = None  # Point being hovered over
        self.dragging_point = None  # Point being dragged
        self.polygons = []  # List of lists of point indices that form polygons
        self.polygon_colors = []  # List of colors for each polygon
        
        # Mode flags
        self.add_point_mode = True
        self.connect_point_mode = False
        
        # Grid settings
        self.grid_size = 20
        self.show_grid = True
        
        # Setup UI
        self.setup_ui()
        
        # Clock for controlling frame rate
        self.clock = pygame.time.Clock()
        
        # Animation time
        self.animation_time = 0
        
        # Status message
        self.status_message = "Mode: Add Points"
        self.status_timer = 0
        
        # Export results
        self.export_results = None  # To store exported lines for display
        
    def setup_ui(self):
        # Panel background
        self.panel_rect = pygame.Rect(self.CANVAS_WIDTH, 0, self.PANEL_WIDTH, self.SCREEN_HEIGHT)
        
        # Add buttons
        button_width = self.PANEL_WIDTH - 20
        
        self.add_point_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.CANVAS_WIDTH + 10, 70), (button_width, 40)),
            text="Add Points",
            manager=self.manager
        )
        
        self.connect_point_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.CANVAS_WIDTH + 10, 120), (button_width, 40)),
            text="Connect Points",
            manager=self.manager
        )
        
        self.clear_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.CANVAS_WIDTH + 10, 170), (button_width, 40)),
            text="Clear All",
            manager=self.manager
        )
        
        self.export_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.CANVAS_WIDTH + 10, 220), (button_width, 40)),
            text="Export",
            manager=self.manager
        )
        
        # Add exit button
        self.exit_btn = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((self.CANVAS_WIDTH + 10, self.SCREEN_HEIGHT - 50), (button_width, 40)),
            text="Exit",
            manager=self.manager
        )
    
    def draw_grid(self):
        if not self.show_grid:
            return
            
        # Draw vertical lines
        for x in range(0, self.CANVAS_WIDTH, self.grid_size):
            pygame.draw.line(self.screen, self.GRAY, (x, 0), (x, self.CANVAS_HEIGHT), 1)
            
        # Draw horizontal lines
        for y in range(0, self.CANVAS_HEIGHT, self.grid_size):
            pygame.draw.line(self.screen, self.GRAY, (0, y), (self.CANVAS_WIDTH, y), 1)
    
    def draw_panel(self):
        # Draw panel background
        pygame.draw.rect(self.screen, self.LIGHT_GRAY, self.panel_rect)
        pygame.draw.line(self.screen, self.WHITE, (self.CANVAS_WIDTH, 0), (self.CANVAS_WIDTH, self.SCREEN_HEIGHT), 2)
        
        # Draw title
        font_title = pygame.font.SysFont('Arial', 24, bold=True)
        title = font_title.render("Polygon Creator", True, self.BLACK)
        self.screen.blit(title, (self.CANVAS_WIDTH + (self.PANEL_WIDTH - title.get_width()) // 2, 20))
        
        # Draw statistics
        font_stats = pygame.font.SysFont('Arial', 18)
        points_text = font_stats.render(f"Points: {len(self.points)}", True, self.BLACK)
        lines_text = font_stats.render(f"Lines: {len(self.lines)}", True, self.BLACK)
        polygons_text = font_stats.render(f"Polygons: {len(self.polygons)}", True, self.BLACK)
        
        self.screen.blit(points_text, (self.CANVAS_WIDTH + 10, 280))
        self.screen.blit(lines_text, (self.CANVAS_WIDTH + 10, 310))
        self.screen.blit(polygons_text, (self.CANVAS_WIDTH + 10, 340))
        
        # Draw mode indicator
        mode_text = "Mode: Add Points" if self.add_point_mode else "Mode: Connect Points"
        mode_rendered = font_stats.render(mode_text, True, self.BLACK)
        self.screen.blit(mode_rendered, (self.CANVAS_WIDTH + 10, 380))
        
        # Draw exported coordinates if available
        if self.export_results:
            export_font = pygame.font.SysFont('Arial', 14)
            export_title = export_font.render("Exported Coordinates:", True, self.BLACK)
            self.screen.blit(export_title, (self.CANVAS_WIDTH + 10, 420))
            
            # Display the first few coordinates with continuation indicator if many
            display_text = ' '.join(map(str, self.export_results[:24]))
            if len(self.export_results) > 24:
                display_text += " ..."
            
            # Wrap the text to fit in panel
            wrapped_text = []
            current_line = ""
            for word in display_text.split(" "):
                test_line = current_line + word + " "
                if export_font.size(test_line)[0] < self.PANEL_WIDTH - 20:
                    current_line = test_line
                else:
                    wrapped_text.append(current_line)
                    current_line = word + " "
            if current_line:
                wrapped_text.append(current_line)
            
            # Draw the wrapped text
            y_pos = 450
            for line in wrapped_text:
                text_surf = export_font.render(line, True, self.BLACK)
                self.screen.blit(text_surf, (self.CANVAS_WIDTH + 10, y_pos))
                y_pos += 20
                if y_pos > self.SCREEN_HEIGHT - 150:  # Don't overflow the panel
                    text_surf = export_font.render("...", True, self.BLACK)
                    self.screen.blit(text_surf, (self.CANVAS_WIDTH + 10, y_pos))
                    break
        
        # Draw status message
        status_font = pygame.font.SysFont('Arial', 14)
        status = status_font.render(self.status_message, True, self.BLACK)
        
        # Draw status box at bottom of panel
        status_rect = pygame.Rect(self.CANVAS_WIDTH + 5, self.SCREEN_HEIGHT - 100, 
                                 self.PANEL_WIDTH - 10, 30)
        pygame.draw.rect(self.screen, (200, 200, 200), status_rect)
        self.screen.blit(status, (status_rect.x + 5, status_rect.y + 5))
    
    def wavelength_to_rgb(self, wavelength):
        """Convert wavelength (in nm) to RGB color"""
        # Map perimeter length to wavelength (400-700nm)
        # Simple conversion for demonstration
        gamma = 0.8
        intensity_max = 255
        
        if wavelength < 440:
            r = -(wavelength - 440) / (440 - 380)
            g = 0.0
            b = 1.0
        elif wavelength < 490:
            r = 0.0
            g = (wavelength - 440) / (490 - 440)
            b = 1.0
        elif wavelength < 510:
            r = 0.0
            g = 1.0
            b = -(wavelength - 510) / (510 - 490)
        elif wavelength < 580:
            r = (wavelength - 510) / (580 - 510)
            g = 1.0
            b = 0.0
        elif wavelength < 645:
            r = 1.0
            g = -(wavelength - 645) / (645 - 580)
            b = 0.0
        else:
            r = 1.0
            g = 0.0
            b = 0.0
        
        # Let intensity fall off near the vision limits
        if wavelength < 420:
            factor = 0.3 + 0.7 * (wavelength - 380) / (420 - 380)
        elif wavelength > 660:
            factor = 0.3 + 0.7 * (780 - wavelength) / (780 - 660)
        else:
            factor = 1.0
        
        r = int(intensity_max * ((r * factor)**gamma))
        g = int(intensity_max * ((g * factor)**gamma))
        b = int(intensity_max * ((b * factor)**gamma))
        
        return (r, g, b)
    
    def compute_polygon_perimeter(self, polygon):
        """Compute the perimeter of a polygon"""
        perimeter = 0
        for i in range(len(polygon)):
            p1_idx = polygon[i]
            p2_idx = polygon[(i + 1) % len(polygon)]
            p1 = self.points[p1_idx]
            p2 = self.points[p2_idx]
            dist = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            perimeter += dist
        return perimeter
    
    def find_polygons(self):
        """Detect polygons in the graph formed by points and lines"""
        # Clear existing polygons
        self.polygons = []
        self.polygon_colors = []
        
        if len(self.points) < 3 or len(self.lines) < 3:
            return
        
        # Create an adjacency list representation of the graph
        graph = {i: [] for i in range(len(self.points))}
        for p1, p2 in self.lines:
            graph[p1].append(p2)
            graph[p2].append(p1)
        
        # Function to find cycles (polygons) in the graph
        def find_cycles(node, visited, path, start):
            path.append(node)
            visited[node] = True
            
            for neighbor in graph[node]:
                if neighbor == start and len(path) >= 3:
                    # Found a cycle
                    self.polygons.append(path.copy())
                elif not visited[neighbor]:
                    find_cycles(neighbor, visited.copy(), path.copy(), start)
        
        # Find all cycles starting from each node
        for i in range(len(self.points)):
            visited = {j: False for j in range(len(self.points))}
            find_cycles(i, visited, [], i)
        
        # Remove duplicate polygons (same points in different order)
        unique_polygons = []
        for polygon in self.polygons:
            # Sort the polygon to create a canonical representation
            sorted_polygon = sorted(polygon)
            if sorted_polygon not in unique_polygons:
                unique_polygons.append(sorted_polygon)
        
        self.polygons = unique_polygons
        
        # Calculate perimeters and assign colors
        min_perimeter = float('inf')
        max_perimeter = 0
        perimeters = []
        
        for polygon in self.polygons:
            perimeter = self.compute_polygon_perimeter(polygon)
            perimeters.append(perimeter)
            min_perimeter = min(min_perimeter, perimeter)
            max_perimeter = max(max_perimeter, perimeter)
        
        # Assign colors based on perimeter length
        for perimeter in perimeters:
            # Map perimeter to wavelength (400-700nm)
            # Shorter = more red (700nm), Longer = more violet (400nm)
            normalized = 1 - (perimeter - min_perimeter) / (max_perimeter - min_perimeter + 0.1)
            wavelength = 400 + normalized * 300
            color = self.wavelength_to_rgb(wavelength)
            self.polygon_colors.append(color)
    
    def is_point_in_polygon(self, x, y, polygon):
        """Check if a line belongs to a specific polygon"""
        return x in polygon and y in polygon
        
    def find_polygon_for_line(self, line):
        """Find which polygon a line belongs to"""
        p1_idx, p2_idx = line
        
        for i, polygon in enumerate(self.polygons):
            if p1_idx in polygon and p2_idx in polygon:
                # Check if they are adjacent or wrap around
                p1_pos = polygon.index(p1_idx)
                p2_pos = polygon.index(p2_idx)
                
                if (abs(p1_pos - p2_pos) == 1) or (abs(p1_pos - p2_pos) == len(polygon) - 1):
                    return i
        
        return None
    
    def draw_canvas(self):
        # Clear canvas
        canvas_rect = pygame.Rect(0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT)
        pygame.draw.rect(self.screen, self.BLACK, canvas_rect)
        
        # Draw grid
        self.draw_grid()
        
        # Update animation time
        self.animation_time += 0.05
        
        # Draw lines with color based on polygon membership
        for i, line in enumerate(self.lines):
            p1 = self.points[line[0]]
            p2 = self.points[line[1]]
            
            # Find which polygon this line belongs to (if any)
            polygon_idx = self.find_polygon_for_line(line)
            
            if polygon_idx is not None:
                # Line is part of a polygon, use polygon's color
                color = self.polygon_colors[polygon_idx]
                
                # Add pulsing glow effect to the line if it's part of a polygon
                glow_intensity = math.sin(self.animation_time + polygon_idx * 0.5) * 0.5 + 0.5
                line_width = 2 + int(glow_intensity * 2)
                
                # Draw the line with the polygon's color
                pygame.draw.line(self.screen, color, p1, p2, line_width)
            else:
                # Line not part of any polygon, use normal cyan color
                pygame.draw.line(self.screen, self.CYAN, p1, p2, 2)
        
        # Draw points
        for i, point in enumerate(self.points):
            # Determine point color based on state
            if self.current_point is not None and i == self.current_point:
                # Selected point
                point_color = self.YELLOW
                radius = 8
            elif self.hovered_point is not None and i == self.hovered_point:
                # Hovered point
                point_color = self.HOVER_COLOR
                radius = 7
            else:
                # Normal point
                point_color = self.WHITE
                radius = 6
            
            # Draw the point
            pygame.draw.circle(self.screen, point_color, point, radius)
            
            # Draw point index
            font = pygame.font.SysFont('Arial', 12)
            idx_text = font.render(str(i+1), True, self.WHITE)
            self.screen.blit(idx_text, (point[0] + 8, point[1] - 8))
    
    def get_point_at_position(self, pos):
        """Get the index of a point at the given position, or None if no point is there"""
        for i, point in enumerate(self.points):
            # Check if the position is within the hitbox size of the point
            if ((point[0] - pos[0]) ** 2 + (point[1] - pos[1]) ** 2) ** 0.5 < self.POINT_HITBOX_SIZE:
                return i
        return None
    
    def add_point(self, pos):
        # Check if we're clicking an existing point (to drag it)
        clicked_point = self.get_point_at_position(pos)
        if clicked_point is not None:
            # Start dragging the point
            self.dragging_point = clicked_point
            return
            
        # Otherwise, add a new point
        self.points.append(pos)
        self.status_message = f"Point added at ({pos[0]}, {pos[1]})"
        self.status_timer = 90  # 3 seconds at 30 FPS
    
    def select_point(self, mouse_pos):
        if not self.points:
            self.status_message = "No points to select."
            self.status_timer = 90
            return
            
        # Find closest point
        closest_idx = self.get_point_at_position(mouse_pos)
        
        if closest_idx is None:
            self.status_message = "No point nearby."
            self.status_timer = 90
            return
            
        if self.current_point is None:
            # First point selection
            self.current_point = closest_idx
            self.status_message = f"Selected point {closest_idx+1}"
            self.status_timer = 90
        else:
            # Second point selection
            if self.current_point == closest_idx:
                self.status_message = "Can't connect a point to itself."
                self.status_timer = 90
                return
            
            # Check if line already exists
            if ((self.current_point, closest_idx) in self.lines or 
                (closest_idx, self.current_point) in self.lines):
                self.status_message = "These points are already connected."
                self.status_timer = 90
                return
            
            # Add the line
            self.lines.append((self.current_point, closest_idx))
            self.status_message = f"Connected points {self.current_point+1} and {closest_idx+1}"
            self.status_timer = 90
            
            # Update polygons
            self.find_polygons()
            
            # The second point becomes the new first point for chaining lines
            self.current_point = closest_idx
    
    def update_hover(self, mouse_pos):
        """Update the hovered point based on mouse position"""
        self.hovered_point = self.get_point_at_position(mouse_pos)
    
    def clear_all(self):
        self.points = []
        self.lines = []
        self.polygons = []
        self.polygon_colors = []
        self.current_point = None
        self.hovered_point = None
        self.dragging_point = None
        self.status_message = "All cleared"
        self.status_timer = 90
    
    def are_polygons_valid(self):
        if not self.lines:
            return False, "No lines drawn yet."
        
        # Count how many lines each point participates in
        point_line_count = {i: 0 for i in range(len(self.points))}
        for p1, p2 in self.lines:
            point_line_count[p1] += 1
            point_line_count[p2] += 1
        
        # Check if all points are part of at least 2 lines (to form polygons)
        for point_idx, count in point_line_count.items():
            if count == 0:
                return False, f"Point {point_idx+1} is not connected to any line."
            if count == 1:
                return False, f"Point {point_idx+1} is only connected to one line."
            if count % 2 != 0:
                return False, f"Point {point_idx+1} has an odd number of lines ({count})."
        
        return True, "Polygons are valid!"
    
    def export_polygons(self):
        valid, message = self.are_polygons_valid()
        if not valid:
            self.show_message_box("Invalid Polygons", message)
            return
        
        # Format the lines as flat list of numbers (x1, y1, x2, y2, x1, y1, x2, y2, ...)
        flat_coords = []
        for p1_idx, p2_idx in self.lines:
            x1, y1 = self.points[p1_idx]
            x2, y2 = self.points[p2_idx]
            flat_coords.extend([x1, y1, x2, y2])
        
        # Store for display in panel
        self.export_results = flat_coords
        
        # Open file dialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            # Save as simple space-separated numbers
            with open(file_path, 'w') as f:
                f.write(' '.join(map(str, flat_coords)))
            self.status_message = f"Exported {len(self.lines)} lines to file"
            self.status_timer = 90
    
    def show_message_box(self, title, message):
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Semi-transparent black
        
        # Draw message box
        msg_width, msg_height = 300, 150
        msg_x = (self.SCREEN_WIDTH - msg_width) // 2
        msg_y = (self.SCREEN_HEIGHT - msg_height) // 2
        
        pygame.draw.rect(overlay, (30, 30, 30), (msg_x, msg_y, msg_width, msg_height))
        pygame.draw.rect(overlay, self.WHITE, (msg_x, msg_y, msg_width, msg_height), 2)
        
        # Title
        font_title = pygame.font.SysFont('Arial', 18, bold=True)
        title_text = font_title.render(title, True, self.WHITE)
        overlay.blit(title_text, (msg_x + (msg_width - title_text.get_width()) // 2, msg_y + 20))
        
        # Message
        font_msg = pygame.font.SysFont('Arial', 16)
        msg_lines = message.split('\n')
        y_offset = msg_y + 50
        
        for line in msg_lines:
            msg_line = font_msg.render(line, True, self.WHITE)
            overlay.blit(msg_line, (msg_x + (msg_width - msg_line.get_width()) // 2, y_offset))
            y_offset += 25
        
        # OK button
        pygame.draw.rect(overlay, self.BLUE, (msg_x + 100, msg_y + msg_height - 40, 100, 30))
        pygame.draw.rect(overlay, self.WHITE, (msg_x + 100, msg_y + msg_height - 40, 100, 30), 1)
        
        ok_btn = font_msg.render("OK", True, self.WHITE)
        btn_pos = (msg_x + 100 + (100 - ok_btn.get_width()) // 2, 
                  msg_y + msg_height - 40 + (30 - ok_btn.get_height()) // 2)
        overlay.blit(ok_btn, btn_pos)
        
        # Display message box
        self.screen.blit(overlay, (0, 0))
        pygame.display.flip()
        
        # Wait for user to click OK button
        msg_active = True
        while msg_active:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if (msg_x + 100 <= mouse_pos[0] <= msg_x + 200 and 
                        msg_y + msg_height - 40 <= mouse_pos[1] <= msg_y + msg_height - 10):
                        msg_active = False
                        break
            self.clock.tick(30)
    
    def set_add_point_mode(self):
        self.add_point_mode = True
        self.connect_point_mode = False
        self.current_point = None
        self.status_message = "Mode: Add Points"
        self.status_timer = 90
    
    def set_connect_point_mode(self):
        self.add_point_mode = False
        self.connect_point_mode = True
        self.current_point = None
        self.status_message = "Mode: Connect Points"
        self.status_timer = 90
    
    def run(self):
        running = True
        
        while running:
            time_delta = self.clock.tick(30) / 1000.0
            
            # Get current mouse position for hover effects
            mouse_pos = pygame.mouse.get_pos()
            
            # Only update hover if in canvas area
            if mouse_pos[0] < self.CANVAS_WIDTH:
                self.update_hover(mouse_pos)
            
            # Process events
            for event in pygame.event.get():
                # Process UI events first
                self.manager.process_events(event)
                
                # Then handle other events
                if event.type == pygame.QUIT:
                    running = False
                
                # Handle keyboard events
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                
                # Handle mouse button down events
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        mouse_pos = pygame.mouse.get_pos()
                        
                        # Only process clicks on the canvas area
                        if mouse_pos[0] < self.CANVAS_WIDTH:
                            if self.add_point_mode:
                                self.add_point(mouse_pos)
                            elif self.connect_point_mode:
                                self.select_point(mouse_pos)
                
                # Handle mouse button up events
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # Left mouse button
                        # Stop dragging
                        if self.dragging_point is not None:
                            # Finalize the point position
                            self.status_message = f"Point {self.dragging_point+1} moved"
                            self.status_timer = 90
                            self.dragging_point = None
                            # Update polygons since point positions changed
                            self.find_polygons()
                
                # Handle mouse motion events
                elif event.type == pygame.MOUSEMOTION:
                    # If dragging a point, update its position
                    if self.dragging_point is not None and self.add_point_mode:
                        mouse_pos = pygame.mouse.get_pos()
                        # Only allow dragging within canvas
                        if mouse_pos[0] < self.CANVAS_WIDTH:
                            self.points[self.dragging_point] = mouse_pos
                
                # Handle UI button clicks
                elif event.type == pygame.USEREVENT:
                    if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                        if event.ui_element == self.add_point_btn:
                            self.set_add_point_mode()
                        elif event.ui_element == self.connect_point_btn:
                            self.set_connect_point_mode()
                        elif event.ui_element == self.clear_btn:
                            self.clear_all()
                        elif event.ui_element == self.export_btn:
                            self.export_polygons()
                        elif event.ui_element == self.exit_btn:
                            running = False
            
            # Update UI
            self.manager.update(time_delta)
            
            # Draw everything
            self.draw_canvas()
            self.draw_panel()
            
            # Draw UI elements
            self.manager.draw_ui(self.screen)
            
            # Update display
            pygame.display.flip()
            
            # Update status message timer
            if self.status_timer > 0:
                self.status_timer -= 1
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = PolygonCreator()
    app.run() 