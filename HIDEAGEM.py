#
#  888    888 8888888 8888888b.  8888888888        d8888  .d8888b.  8888888888 888b     d888
#  888    888   888   888  "Y88b 888              d88888 d88P  Y88b 888        8888b   d8888
#  888    888   888   888    888 888             d88P888 888    888 888        88888b.d88888
#  8888888888   888   888    888 8888888        d88P 888 888        8888888    888Y88888P888
#  888    888   888   888    888 888           d88P  888 888  88888 888        888 Y888P 888
#  888    888   888   888    888 888          d88P   888 888    888 888        888  Y8P  888
#  888    888   888   888  .d88P 888         d8888888888 Y88b  d88P 888        888   "   888
#  888    888 8888888 8888888P"  8888888888 d88P     888  "Y8888P88 8888888888 888       888
#
#  COPYRIGHT (c) 2023 WWW.CYBERGEM.NET

import os
import math
import ctypes
import argparse

import numpy as np

from PIL import Image
from ctypes import POINTER

#
#    HIDEAGEM C INTERFACE
#

HIDEAGEM_CORE = None

# Try to load HIDEAGEM.dll from current directory, then try bin/

dll_name = "HIDEAGEM.dll" if os.name == 'nt' else "HIDEAGEM.so"
this_dir = os.path.dirname(os.path.realpath(__file__))
dll_path = os.path.join(this_dir, dll_name)

if not os.path.exists(dll_path):
    dll_path = os.path.join(this_dir, "bin", dll_name)

# Load the library
if os.name == 'posix':
    HIDEAGEM_CORE = ctypes.CDLL(dll_path)
else:
    HIDEAGEM_CORE = ctypes.WinDLL(dll_path, winmode=0)


# Hide Gems
HIDEAGEM_CORE.HIDEAGEM_HIDE_GEMS_C.argtypes = [
    ctypes.c_int, 
    ctypes.POINTER(ctypes.c_void_p), 
    ctypes.c_uint64, # Ocean Size
    ctypes.c_int,    # Ocean Type
    ctypes.POINTER(ctypes.POINTER(ctypes.c_char)), 
    ctypes.c_int, 
    ctypes.c_char_p, 
    ctypes.c_int, 
    ctypes.c_bool
]
HIDEAGEM_CORE.HIDEAGEM_HIDE_GEMS_C.restype = ctypes.c_bool

# Find Gems
HIDEAGEM_CORE.HIDEAGEM_FIND_GEMS_C.argtypes = [
    ctypes.POINTER(ctypes.c_void_p), 
    ctypes.c_uint64, # Ocean Size
    ctypes.c_int,    # Ocean Type
    ctypes.c_char_p, 
    ctypes.c_char_p,
    ctypes.c_bool
]
HIDEAGEM_CORE.HIDEAGEM_FIND_GEMS_C.restype = None

# Debug
HIDEAGEM_CORE.HIDEAGEM_RUN_UNIT_TESTS_C.argtypes = [
    ctypes.c_bool, 
    ctypes.c_bool
]

#
#    HIDEAGEM <3 !!!
#

def is_image_file(file_path):
    try:
        Image.open(file_path)
        return True
    except IOError:
        return False

#
#    FIND GEMS
#

def run_find_gems(args):
    
    if not args.ocean:
        print("\nGem Ocean is missing.\n")
        return
    elif not args.password:
        print("\nGem password is missing.\n")
        return
        
    if args.timetrap is not None:
        b_time_trap = True
    else:
        b_time_trap = False

    ocean_bytes = None
    ocean_mode = 0 # Bytes mode

    # Check if the file is an image
    if is_image_file(args.ocean):
        # Open the image
        with Image.open(args.ocean) as img:
            # Convert the image to raw bytes without converting to float32
            ocean_bytes = img.tobytes()

            if img.mode == "RGB":
                ocean_mode = 1 # IMAGE_RGB mode
            elif img.mode == "RGBA":
                ocean_mode = 2 # IMAGE_RGBA mode

    else:
        # Load the ocean as a byte array directly
        with open(args.ocean, 'rb') as file:
            ocean_bytes = file.read()

    ocean_size = len(ocean_bytes)
    mutable_array = (ctypes.c_char * len(ocean_bytes)).from_buffer(bytearray(ocean_bytes))
    ocean_ptr = ctypes.cast(mutable_array, ctypes.POINTER(ctypes.c_void_p))

    output_dir = None if args.output is None else args.output.encode()

    HIDEAGEM_CORE.HIDEAGEM_FIND_GEMS_C(
        ocean_ptr,
        ocean_size,
        ocean_mode,
        args.password.encode(), # Password
        output_dir,
        b_time_trap
    )

def run_demo_mode(args):

    # Run unit tests
    HIDEAGEM_CORE.HIDEAGEM_RUN_UNIT_TESTS_C(
        True, # Loop
        True  # Demo mode
    )

#
#    HIDE GEMS
#

def run_hide_gems(args):

    ocean_mode = 0 # Bytes mode

    # Check if the file is an image
    if is_image_file(args.ocean):
        # Open the image
        with Image.open(args.ocean) as img:
            # Convert the image to raw bytes without converting to float32
            ocean_bytes = img.tobytes()
            img_width, img_height = img.size  # width and height are now cached
            img_mode = img.mode  # this caches the color mode which indicates the number of channels

            if img_mode == "RGB":
                ocean_mode = 1 # IMAGE_RGB mode
            elif img_mode == "RGBA":
                ocean_mode = 2 # IMAGE_RGBA mode
            else:
                print(f"Unsupported image mode {img_mode}. Exiting.")

                return

    else:
        # Load the ocean as a byte array directly
        with open(args.ocean, 'rb') as file:
            ocean_bytes = file.read()

    ocean_size = len(ocean_bytes)
    mutable_array = (ctypes.c_char * len(ocean_bytes)).from_buffer(bytearray(ocean_bytes))
    ocean_ptr = ctypes.cast(mutable_array, ctypes.POINTER(ctypes.c_void_p))

    # Convert list of paths to C-compatible array of byte strings
    files = [f.encode('utf-8') for f in args.files]
    arr = (ctypes.c_char_p * len(files))(*files)

    if args.timetrap is not None:
        time_trap = args.timetrap
        gem_protocol = 2 # Auto protocol
    else:
        time_trap    = -1 # Time Trap disabled
        gem_protocol = 0 # Auto protocol

    b_hid_gems = HIDEAGEM_CORE.HIDEAGEM_HIDE_GEMS_C(
        gem_protocol,
        ocean_ptr,
        ocean_size,
        ocean_mode,
        ctypes.cast(arr, ctypes.POINTER(ctypes.POINTER(ctypes.c_char))),
        len(args.files),
        args.password.encode(),
        time_trap,
        args.validate
    )

    if not b_hid_gems:
        return

    if args.output is None: # Not saving Gem to disk
        print("No output directory specified. Gem not saved to disk.\n")
        return

    if not os.path.exists(args.output):
        print(f"Creating directory: {args.output}\n")
        os.makedirs(args.output)

    # Write Gem to disk
    if is_image_file(args.ocean):

        if img_mode == "RGB":
            img_channels = 3
        elif img_mode == "RGBA":
            img_channels = 4
        else:
            print(f"Unsupported image mode {img_mode}. Exiting.")

            return

        base_name, _ = os.path.splitext(os.path.basename(args.ocean))  # Ignore the original extension
        output_file_path = os.path.join(args.output, f"{base_name}.png")
        counter = 1

        while os.path.exists(output_file_path):
            output_file_path = os.path.join(args.output, f"{base_name}_{counter}.png")
            counter += 1

        image_array = np.frombuffer(bytearray(mutable_array), dtype=np.uint8).reshape((img_height, img_width, img_channels))
        image = Image.fromarray(image_array)

        # Save the image with PNG format
        image.save(output_file_path, format='PNG')

        print(f"SAVED GEM: {output_file_path}\n")

    else:
        ocean_filename = os.path.basename(args.ocean)
        output_file_path = os.path.join(args.output, ocean_filename)
        
        with open(output_file_path, 'wb') as output_file:
            output_file.write(bytearray(mutable_array))

        print(f"SAVED GEM: {output_file_path}\n")


def run_unit_tests(args):

    # Run unit tests
    HIDEAGEM_CORE.HIDEAGEM_RUN_UNIT_TESTS_C(
        True, # Loop
        False # Demo mode
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CLI for Hide and Find Gems")

    parser.add_argument('mode', choices=['hide', 'find', 'demo', 'unit'], help='Gem Mode')

    parser.add_argument("--ocean", type=str, help="Cover media bit Ocean")
    parser.add_argument("--files", nargs='+', help="Gem Files to hide")
    parser.add_argument("--output", type=str, help="Output directory")
    parser.add_argument("--password", type=str, help="Gem password")
    parser.add_argument("--validate", action="store_true", help="Validate Gem hide")
    parser.add_argument("--timetrap", type=int, nargs='?', const=0, default=None, help="Time Trap level")


    args = parser.parse_args()

    if args.mode == "hide":
        run_hide_gems(args)
    elif args.mode == "find":
        run_find_gems(args)
    elif args.mode == "unit":
        run_unit_tests(args)
    elif args.mode == "demo":
        run_demo_mode(args)

