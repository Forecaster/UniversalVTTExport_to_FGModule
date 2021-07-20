
import math

# From: https://stackoverflow.com/a/1937202
# Answer by Andreas Brinck
# <editor-fold>

def expand_line(line, t):
	"""
	Returns an array of four coordinate sets expanding the input line into a rectangle with thickness t
	"""
	x0 = line[0][0]
	y0 = line[0][1]
	x1 = line[1][0]
	y1 = line[1][1]
	t = int(t)
	dx = x1 - x0 # delta x
	dy = y1 - y0 # delta y
	line_length = math.sqrt(dx * dx + dy * dy)
	dx /= line_length
	dy /= line_length
	# Ok, (dx, dy) is now a unit vector pointing in the direction of the line
	# A perpendicular vector is given by (-dy, dx)
	px = 0.5 * t * (-dy) # perpendicular vector with length thickness * 0.5
	py = 0.5 * t * dx

	x2 = x0 + px
	y2 = y0 + py
	x3 = x1 + px
	y3 = y1 + py
	x4 = x1 - px
	y4 = y1 - py
	x5 = x0 - px
	y5 = y0 - py
	return ((x2, y2), (x3, y3), (x4, y4), (x5, y5))

def expand_line2(line, thickness):
	length = distance(line[0], line[1])
	line_calc = ((line[0][0] - line[1][0]), (line[0][1] - line[1][1]))
	line_calc = (-line_calc[1], line_calc[0])
	line_calc = (line_calc[0] / length, line_calc[1] / length)
	line_calc = (line_calc[0] * (thickness/2), line_calc[1] * (thickness/2))
	nl1 = ((line[0][0] + line_calc[0], line[0][1] + line_calc[1]), (line[1][0] + line_calc[0], line[1][1] + line_calc[1]))
	nl2 = ((line[0][0] - line_calc[0], line[0][1] - line_calc[1]), (line[1][0] - line_calc[0], line[1][1] - line_calc[1]))
	return (nl1[0], nl1[1], nl2[0], nl2[1])

# check if r lies on (p,q)
def on_segment(p, q, r):
	if r[0] <= max(p[0], q[0]) and r[0] >= min(p[0], q[0]) and r[1] <= max(p[1], q[1]) and r[1] >= min(p[1], q[1]):
		return True
	return False

# return 0/1/-1 for colinear/clockwise/counterclockwise
def orientation(p, q, r):
	val = ((q[1] - p[1]) * (r[0] - q[0])) - ((q[0] - p[0]) * (r[1] - q[1]))
	if val == 0 : return 0
	return 1 if val > 0 else -1

#check if seg1 and seg2 intersect
def intersects(seg1, seg2):
	p1, q1 = seg1
	p2, q2 = seg2

	o1 = orientation(p1, q1, p2) #find all orientations

	o2 = orientation(p1, q1, q2)
	o3 = orientation(p2, q2, p1)
	o4 = orientation(p2, q2, q1)

	if o1 != o2 and o3 != o4: #check general case
		return True

	if o1 == 0 and on_segment(p1, q1, p2) : return True #check special cases
	if o2 == 0 and on_segment(p1, q1, q2) : return True
	if o3 == 0 and on_segment(p2, q2, p1) : return True
	if o4 == 0 and on_segment(p2, q2, q1) : return True
	return False
# </editor-fold>

def get_intersect_point(line1, line2):
	from shapely.geometry import LineString, Point

	line1 = LineString(line1)
	line2 = LineString(line2)

	int_pt = line1.intersection(line2)
	try:
		return int_pt.x, int_pt.y
	except:
		return None

def points_close(point1, point2, sensitivity = 1):
	x0 = point1[0]
	y0 = point1[1]
	x1 = point2[0]
	y1 = point2[1]

	if x0 > x1 - sensitivity and x0 < x1 + sensitivity:
		if y0 > y1 - sensitivity and y0 < y1 + sensitivity:
			return True
	return False

def true_intersect_check(line_a, line_b, intersect, sensitivity = 1):
	if points_close(line_a[0], intersect, sensitivity):
		return False
	if points_close(line_a[1], intersect, sensitivity):
		return False
	if points_close(line_b[0], intersect, sensitivity):
		return False
	if points_close(line_b[1], intersect, sensitivity):
		return False
	return True

def distance(p1, p2):
	return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def tuple_to_point_list(tup, stringify = False):
	points = []
	for t in tup:
		if type(t) is tuple:
			points = points + tuple_to_point_list(t, stringify)
		else:
			if stringify:
				points.append(str(t))
			else:
				points.append(t)
	return points

def point_to_bounding_box(point, size = 5):
	return ((point[0] - size, point[1] - size), (point[0] + size, point[1] + size))

def polygon_to_line_set(polygon):
	points = []
	first_point = None
	prev_point = None
	for point in polygon:
		if first_point is None:
			first_point = point
		if prev_point is not None:
			points.append((prev_point, point))
		prev_point = point
	points.append((first_point, prev_point))
	return points

try:
	from PIL import ImageDraw
	def draw_polygon(draw: ImageDraw, polygon, color = (255, 255, 255), line_width = 2):
		for line in polygon_to_line_set(polygon):
			draw.line(tuple_to_point_list(line), fill=color, width=line_width)
except Exception:
	def draw_polygons():
		return None
	pass

def check_point_is_inside_polygon(point, polygon):
	line = (point, (point[0] + 10000, point[1]))
	intersect_count = 0
	for p_line in polygon_to_line_set(polygon):
		inter = get_intersect_point(line, p_line)
		# print(inter)
		if inter is not None:
			intersect_count += 1
	return not intersect_count % 2 == 0

def get_polygon_intersect_points(line, polygon):
	intersections = []
	for p_line in polygon_to_line_set(polygon):
		inter = get_intersect_point(line, p_line)
		if inter is not None:
			intersections.append(inter)
	return intersections
