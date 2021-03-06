from PIL import Image, ImageChops, ImageDraw, ImageFont
import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline, BSpline
plt.style.use('seaborn-white')
import json
import os
import math
import shutil
from pprint import pprint


font_large = ImageFont.truetype(r'C:\Windows\Fonts\tahoma.ttf', size=34)
font_small = ImageFont.truetype(r'C:\Windows\Fonts\tahoma.ttf', size=28)


class Common_Data(object):
    def __init__(self):
        self.diff_folder = None
        self.log_file = None
        self.max_diff = None

def process_image_pairs(a, b, identifier):
    print (f"Identifier: {identifier}")
    print (f"Image A: {a}")
    print (f"Image B: {b}\n")
    if os.path.exists(a) and os.path.exists(b):
        make_difference_images(a, b, identifier)
    else:
        if not os.path.exists(a):
            print (f"\tCan't find A image - check {a} ")
        if not os.path.exists(b):
            print (f"\tCan't find B image - check {b} ")

def convert_dict(data):
    if isinstance(data, bytes):  return data.decode()
    if isinstance(data, dict):   return dict(map(convert_dict, data.items()))
    if isinstance(data, tuple):  return tuple(map(convert_dict, data))
    if isinstance(data, list):   return list(map(convert_dict, data))
    return data

def flip_rgba_to_rgb(im, bg_colour=(255, 255, 255)):
    # Only process if image has transparency (http://stackoverflow.com/a/1963146)
    if im.mode == 'RGBA':
        background = Image.new("RGB", im.size, (255, 255, 255))
        background.paste(im, mask=im.split()[3])
        return background
    else:
        return im

def normalise_images():
    commons.im1 = commons.im1.convert("RGB")
    commons.im2 = commons.im2.convert("RGB")
    if commons.im1.size != commons.im2.size:
        if verbose:
            print ("Resizing image B to size of image A")
        commons.im2 = commons.im2.resize(commons.im1.size)
        commons.image_rescaled = True
    else:
        commons.image_rescaled = False


def rmsdiff():
    """returns rmse (float) between two Image items"""

    try:
        diff = ImageChops.difference(commons.im1, commons.im2)
        h = diff.histogram()
        sq = (value*((idx%256)**2) for idx, value in enumerate(h))
        sum_of_squares = sum(sq)
        rms = math.sqrt(sum_of_squares/float(commons.im1.size[0] * commons.im1.size[1]))
        return rms

    except ValueError:
        print (commons.im1.size, commons.im1.getbands())
        print (commons.im2.size, commons.im2.getbands())
        print ("RMSE process failed. Check image modes are compatable")
        quit()

def make_before_after_gif():
    frames = []
    if os.path.exists(os.path.join(commons.diff_folder,"diff_masks")):
        imgs = [os.path.join(commons.diff_folder,"diff_masks", x) for x in  os.listdir(os.path.join(commons.diff_folder,"diff_masks"))]
        if commons.max_diff > 0:
            draw1 = ImageDraw.Draw(commons.im1)
            font = ImageFont.truetype("arial.ttf", 120)
            draw1.text((50, 90), f"  A", font=font,  fill=(255, 0, 0))
            frames.append(commons.im1)
            draw2 = ImageDraw.Draw(commons.im2)
            draw2.text((50, 90), f"  B", font=font,  fill = (0, 255, 255))
            frames.append(commons.im2)
            
            frames[0].save(os.path.join(commons.diff_folder, "flipper.gif"), format='GIF', append_images=frames[1:], save_all=True, duration=500, loop=0)

def put_a_and_b_image_in_results_folder():
    a_root = os.path.join(commons.diff_folder, "a")
    if not os.path.exists(a_root):
        os.makedirs(a_root)
    shutil.copy(a, a_root)

    b_root = os.path.join(commons.diff_folder, "b")
    if not os.path.exists(b_root):
        os.makedirs(b_root)
    shutil.copy(b, b_root)

def make_differance_and_diff_inverted_image():
    commons.difference = ImageChops.difference(commons.im1, commons.im2)
    commons.difference_inverted = ImageChops.invert(ImageChops.difference(commons.im1, commons.im2))
    
    commons.difference.save(os.path.join(commons.diff_folder, "diff_inverted.png"))
    commons.difference_inverted.save(os.path.join(commons.diff_folder, "diff.png"))

def make_histo(log_data, limits_profile=None):

    bars_width = 0.5
    total_pixels = log_data["number of pixels"]
    commons.total_pixels = total_pixels
    width = log_data["width"]
    commons.width = width
    height = log_data["height"]
    commons.height = height
    commons.image_rescaled = log_data["image_rescaled"]

    bins = [x for x in range(0, 256)]
    values = []
    for level in log_data["difference_masks"]:
        values.append(log_data["difference_masks"][level]['pixels in band'])

    percent_values  = [100/total_pixels * x for x in values]
    plt.bar(bins, percent_values, color='r', width=bars_width, alpha=0.7)
    
    commons.has_limits_profile = False
    if limits_profile:
        commons.has_limits_profile = True
        pixel_percent_limit = limits_profile[1]
        diff_depth_limit = len(limits_profile)    
        while len(limits_profile) != 256:
            limits_profile.append(0)
  
        bins_new = np.linspace(min(bins), max(bins), 300) 
        my_spline = make_interp_spline(bins, limits_profile, k=3)
        pixel_percent_boundaries_smooth = my_spline(bins_new)

        # plt.plot(bins_new, pixel_percent_boundaries_smooth, color='g', linestyle=" ")
        plt.fill_between(bins_new, pixel_percent_boundaries_smooth, color='g', alpha=0.4)

    plt.title("Plotting the difference between two images as a ??? image")
    plt.ylabel("Percent of pixels in difference depth band (%)")
    plt.xlabel("Difference depth band (8-bit step increments)")

    plt.xticks(np.arange(0, 256, 32))

    if int(max(percent_values))+5 < 100:
        plt.ylim([0, int(max(percent_values))+5])
        y = int(max(percent_values))
    else:
        plt.ylim([0, 100])
        y = 95

    # x = 100/commons.max_diff*30
    # step_size = 1.5

    plt.xlim([0, commons.max_diff])
    plt.savefig(os.path.join( commons.diff_folder,"zoomed_chart.png"), dpi=300)
    add_chart_data(os.path.join( commons.diff_folder,"zoomed_chart.png"), percent_values)

    plt.bar(bins, percent_values, color='r', width=bars_width, alpha=0.7)
    plt.title("Plotting the difference between two images as a ??? image")
    plt.ylabel("Percent of pixels in difference depth band (%)")
    plt.xlabel("Difference depth band (8-bit step increments)")
    plt.xticks(np.arange(0, 256, 32))

    if limits_profile:
        # plt.plot(bins_new, pixel_percent_boundaries_smooth, color='')
        plt.fill_between(bins_new, pixel_percent_boundaries_smooth, color='g', alpha=0.4)

    # x = 125
    # y = 85
    # step_size = 4

    plt.ylim([0, 100])
    plt.xlim([0, 256])
    plt.savefig(os.path.join( commons.diff_folder,"full_chart.png"), dpi=300)
    add_chart_data(os.path.join( commons.diff_folder,"full_chart.png"), percent_values)


    plt.bar(bins, percent_values, color='r', width=bars_width, alpha=0.7)
    plt.title("Plotting the difference between two images as a ??? image")
    plt.ylabel("Percent of pixels in difference depth band (%)")
    plt.xlabel("Difference depth band (8-bit step increments)")
    plt.xticks(np.arange(0, 256, 32))

    if limits_profile:
        # plt.plot(bins_new, pixel_percent_boundaries_smooth, color='')
        plt.fill_between(bins_new, pixel_percent_boundaries_smooth, color='g', alpha=0.4)


    plt.ylim([0, 5])
    plt.xlim([0, 24])
    plt.savefig(os.path.join( commons.diff_folder,"detail_chart.png"), dpi=300)
    add_chart_data(os.path.join( commons.diff_folder,"detail_chart.png"), percent_values)

def add_chart_data(my_f, percent_values):
    
    img = Image.open(my_f)
    step = 40
    draw = ImageDraw.Draw(img)
    draw.text((1200, 300 + step*0 ),"Key Data",(0,0,0),font=font_large)
    draw.text((1200, 300 + step*1),f"Identifier: {identifier}",(0,0,0),font=font_small)
    draw.text((1200, 300 + step*2),f"Image Resolution: {commons.width}w x {commons.height}h",(0,0,0),font=font_small)
    draw.text((1200, 300 + step*3),f"Total Pixels: {commons.total_pixels}",(0,0,0),font=font_small)
    draw.text((1200, 300 + step*4),f"B image rescaled?: {commons.image_rescaled}",(0,0,0),font=font_small)
    draw.text((1200, 300 + step*5),f"Max Difference Size: {commons.max_diff}",(0,0,0),font=font_small)
    draw.text((1200, 300 + step*6),f"Percent Pixels Unchanged: {percent_values[0]:.2f}%",(0,0,0),font=font_small)
    draw.text((1200, 300 + step*7),f"RMSe: {commons.rmse:.3f}",(0,0,0),font=font_small)
    if commons.has_limits_profile:
        draw.text((1200, 300 + step*8),f"Profile Reference:",(0,0,0),font=font_small)
        draw.text((1200, 300 + step*9),f"  {commons.limits_reference}",(0,0,0),font=font_small)

    img.save(my_f.replace(".png", "_annotated.png"))


def make_pixel_stacker(log_data):
    stacker = Image.new(mode="L", size=(commons.width, commons.height))
    values = []
    for level in log_data["difference_masks"]:
        values.append(log_data["difference_masks"][level]['pixels in band'])

    pxl_map = []
    for i, v in enumerate(values):
        section = [255-i]*v
        pxl_map += section

    for y in range(commons.height-1, -1, -1):
        for x in range(commons.width):
            pixel_value = pxl_map.pop()
            stacker.putpixel((x, y), (pixel_value))
    stacker.save(os.path.join(commons.diff_folder,"stacked_diff.png"))



def make_composite_difference_mask(diff_img):
    
    """"""
    diff_img.save(os.path.join(commons.diff_folder,"composite_diff_mask.png"))

def make_difference_levels_gif():
    frames = []
    if os.path.exists(os.path.join(commons.diff_folder,"diff_masks")):
        imgs = [os.path.join(commons.diff_folder,"diff_masks", x) for x in  os.listdir(os.path.join(commons.diff_folder,"diff_masks"))]
        if commons.max_diff > 0:
            for counter, i in enumerate(imgs, 1):
                new_frame = Image.open(i)
                draw = ImageDraw.Draw(new_frame)
                font = ImageFont.truetype("arial.ttf", 30)
                draw.text((50, 90), f"diff depth: {counter}", font=font)
                new_frame = new_frame.convert('P') 
                frames.append(new_frame)
            frames[0].save(os.path.join(commons.diff_folder, "diff.gif"), format='GIF', append_images=frames[1:], save_all=True, duration=100, loop=0)

def make_difference_images(a, b, identifier=False, quickmode=False):
    """If there is a non-zero RMSe value, a difference image (and its inverse) is created.
    This is useful as a visual indicator
     for what the actual difference is. 
    The bi-tonal images are a threshold-ed representation of the diff starting at diff distance 1
    This is useful to see where the diff is in real terms - consider it an exaggeration of the diff we can see.  
    """
    # debug = True
    commons.im1, commons.im2 = Image.open(a), Image.open(b)
    
    if not quickmode:
        a_input = commons.im1.info
        a_input["bands"] = commons.im1.getbands()

        b_input = commons.im2.info
        b_input["bands"] = commons.im2.getbands()

    normalise_images()

    rmse = rmsdiff()
    commons.rmse = rmse
    log_data = {"a":{"source":a.replace("\\", "/")}, "b":{"source":b.replace("\\", "/")}, "difference_masks":{}}
    width, height = commons.im1.size
    number_of_pixels = width * height 
    log_data["number of pixels"] = number_of_pixels
    log_data["width"] = width
    log_data["height"] = height
    log_data['image_rescaled'] = commons.image_rescaled

    
    a_final = commons.im1.info
    a_final["bands"] = commons.im1.getbands()
    b_final = commons.im2.info
    b_final["bands"] = commons.im2.getbands()

    log_data["RMSE"] = rmse

    if "icc_profile" in a_input:
        del a_input['icc_profile']
    if "icc_profile" in a_final:
        del a_final['icc_profile']

    if "icc_profile" in b_input:
        del b_input['icc_profile']
    if "icc_profile" in b_final:
        del b_final['icc_profile']
    if "photoshop" in b_input: 
        del b_input['photoshop']
    if "photoshop" in b_final:
        del b_final['photoshop']

    log_data['a']['input_image'] = convert_dict(a_input)
    log_data['a']["bytes"] = os.stat(a).st_size
    log_data['a']["size"] = {}
    log_data['a']["size"]["width"], log_data['a']["size"]["height"] = commons.im1.size
    if a_input != a_final:
        log_data['a']['comparision_image'] = convert_dict(a_final)
        log_data['a']['conversion note'] = "Image was converted to an RGB image, so some measures are relative to this conversion, not the orignal image"
    
    log_data['b']['input_image'] = convert_dict(b_input)
    log_data['b']["bytes"] = os.stat(b).st_size
    log_data['b']["size"] = {}
    log_data['b']["size"]["width"], log_data['b']["size"]["height"] = commons.im2.size
    if b_input != b_final:
        log_data['b']['comparision_image'] = convert_dict(b_final)
        log_data['b']['conversion note'] = "Image was converted to an RGB image, so some measures are relative to this conversion, not the orignal image"
        
    print (f"RMSE: {rmse}")
    
    
    commons.diff_folder = os.path.join( destination_folder, identifier)
    if not os.path.exists(commons.diff_folder):
        os.makedirs(commons.diff_folder)

    commons.log_file = os.path.join(commons.diff_folder, identifier+".json")

    put_a_and_b_image_in_results_folder()


    diff_folder = os.path.join( destination_folder, identifier) 
        
    make_differance_and_diff_inverted_image()

    pixels_a = commons.im1.load()
    pixels_b = commons.im2.load()
    width, height = commons.im1.size

    pixels = list(commons.difference.convert('L').getdata())
    pixels = [pixels[i * width:(i + 1) * width] for i in range(height)]
    my_histo = {}
    for row in pixels:
        for pixel in row:
            if pixel not in my_histo:
                my_histo[pixel] = 0
            my_histo[pixel] += 1

    commons.max_diff = max(list(my_histo.keys()))
    print (f"Max diff depth: {commons.max_diff}")
    log_data["Number of difference levels"] = commons.max_diff

    for thresh in range (255, -1, -1):
        fn = lambda x : 255 if x > thresh else 0
        counter = 255-thresh
        counter_string = str(counter).zfill(3)

        if counter < commons.max_diff+2 and counter != 0:
            
            if not os.path.exists(os.path.join(commons.diff_folder,"diff_masks")):
                os.makedirs(os.path.join(commons.diff_folder,"diff_masks"))
            fname = f"bilevel_{counter_string}.png"
            diff_img = commons.difference_inverted.convert('L').point(fn, mode='1')
            diff_img.save(os.path.join(commons.diff_folder,"diff_masks", fname))

            if counter == 1:
                make_composite_difference_mask(diff_img)
        
        log_data["difference_masks"][counter] = {}

        if counter in my_histo:
            log_data["difference_masks"][counter]["pixels in band"] = my_histo[counter]
        else:
            log_data["difference_masks"][counter]["pixels in band"] = 0        
        
    make_difference_levels_gif()
    make_before_after_gif()

    my_profile = []
    
    limits = {"limits_profile":my_profile , "limits_reference":"Access Copy Profile"}
    
    commons.limits_profile = limits["limits_profile"]
    commons.limits_reference = limits["limits_reference"]

    make_histo(log_data, commons.limits_profile)

    make_pixel_stacker(log_data)

    print (f"\nSee:\n\n\t{commons.diff_folder}\n")
    with open(commons.log_file, "w") as outfile:
        outfile.write(json.dumps(log_data, indent=4, sort_keys=True))

verbose = True
commons = Common_Data()

### change the following variable to fit your use. 
## expects a two valid file input paths, a label (identifer) and folder location for the results. 

source_folder = r"C:\collections\image_comparision_inputs"
a = os.path.join(source_folder, "a.ppm")
b = os.path.join(source_folder, "b.ppm")

identifier = "test_1"
destination_folder = r"C:\collections\image_comparision_outputs"


process_image_pairs(a, b, identifier)