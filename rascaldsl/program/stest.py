import timeit, random, numpy as np

color_ranges = {
        "Yellow": np.array([200, 200, 0]),
        "Black": np.array([50, 50, 50]),
        "White": np.array([255, 255, 255]),
        "Blue": np.array([50, 50, 255]),
        "Red": np.array([255, 50, 50]),
    }


def set_color_ranges(color_dict, ranges, color_name):
    for r_range, g_range, b_range in ranges:
        for red in range(r_range[0], r_range[1] + 1):
            for green in range(g_range[0], g_range[1] + 1):
                for blue in range(b_range[0], b_range[1] + 1):
                    color_dict[(red, green, blue)] = color_name


# COLOR_CATEGORIES = {}
# set_color_ranges(COLOR_CATEGORIES, [((0, 50), (0, 50), (0, 50))], 'black')
# set_color_ranges(COLOR_CATEGORIES, [((200, 255), (200, 255), (200, 255))], 'white')
# set_color_ranges(COLOR_CATEGORIES, [((0, 50), (0, 50), (200, 255))], 'blue')
# set_color_ranges(COLOR_CATEGORIES, [((200, 255), (0, 50), (0, 50))], 'red')

import pickle
# write color categories to file
# with open('color_categories.pkl', 'wb') as f:
#     pickle.dump(COLOR_CATEGORIES, f)

with open('color_categories.pkl', 'rb') as f:
    COLOR_CATEGORIES = pickle.load(f)

def f(red, green, blue):
    return COLOR_CATEGORIES.get((red, green, blue), 'nocolor')
    
    
    
    
    # if red <= 50 and green <= 50 and blue <= 50:
    #     return "black"
    # if red <= 100 and green <= 100 and 50 <= blue <= 150:
    #     return "blue"
    # if 100 < red < 200 and green < 100 and blue < 100:
    #     return "red"
    # if 150 < red < 250 and 150 < green < 250 and blue < 100:
    #     return "yellow"
    # else :
    #     return "white"



    # if 150 < red < 250 and 150 < green < 250 and blue < 100:
    #     return "yellow"
    
    # if 100 < red < 200 and 0 < green < 100 and 0 < blue < 100:
    #     return "red"

    # if 0 < red < 100 and 0 < green < 100 and 50 < blue < 150:
    #     return "blue"

    # if 200 < red < 255 and 200 < green < 255 and 200 < blue < 255:
    #     return "white"

    # if 0 < red < 50 and 0 < green < 50 and 0 < blue < 50:
    #     return "black"

    # return "nocolor"



red, green, blue = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
print(f"time with {red}, {green}, {blue} is: {timeit.timeit('f(red, green, blue)', number=1000000, globals=globals())}")