
import math

# From: https://stackoverflow.com/a/1937202
# Answer by Andreas Brinck
def expand_line(x0, y0, x1, y1, t):
	"""
	Returns an array of four coordinate sets expanding the input line into a rectangle with thickness t
	:param x0:
	:param y0:
	:param x1:
	:param y1:
	:param t:
	:return:
	"""
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
	return [{"x": x2, "y": y2}, {"x": x3, "y": y3},{"x": x4, "y": y4},{"x": x5, "y": y5}]
