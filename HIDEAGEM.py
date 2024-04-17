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
#  COPYRIGHT (c) 2024 WWW.CYBERGEM.NET

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
    ctypes.c_void_p,
    ctypes.c_uint64,
    ctypes.POINTER(ctypes.POINTER(ctypes.c_char)),
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_uint64),
    ctypes.c_bool
]

HIDEAGEM_CORE.HIDEAGEM_HIDE_GEMS_C.restype = ctypes.POINTER(ctypes.c_uint8)

# Find Gems
HIDEAGEM_CORE.HIDEAGEM_FIND_GEMS_C.argtypes = [
    ctypes.POINTER(ctypes.c_void_p), 
    ctypes.c_uint64, # Ocean Size
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

# Memory management
HIDEAGEM_CORE.HIDEAGEM_FREE_OCEAN_C.argtypes = [ctypes.c_void_p]
HIDEAGEM_CORE.HIDEAGEM_FREE_OCEAN_C.restype = None

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
        
    if args.timetrap is not None:
        b_time_trap = True
    else:
        b_time_trap = False

    with open(args.ocean, 'rb') as file:
        ocean_bytes = file.read()

    password_c = b''

    if args.password is not None:
        password_c = args.password.encode()

    ocean_size = len(ocean_bytes)
    mutable_array = (ctypes.c_char * len(ocean_bytes)).from_buffer(bytearray(ocean_bytes))
    ocean_ptr = ctypes.cast(mutable_array, ctypes.POINTER(ctypes.c_void_p))

    output_dir = None if args.output is None else args.output.encode()

    HIDEAGEM_CORE.HIDEAGEM_FIND_GEMS_C(
        ocean_ptr,
        ocean_size,
        password_c,
        output_dir,
        b_time_trap
    )

#
#    DEMO MODE <3
#

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

    # Load the ocean as a byte array directly
    with open(args.ocean, 'rb') as file:
        ocean_bytes = file.read()

    ocean_size = len(ocean_bytes)
    mutable_array = (ctypes.c_char * len(ocean_bytes)).from_buffer(bytearray(ocean_bytes))
    ocean_ptr = ctypes.cast(mutable_array, ctypes.POINTER(ctypes.c_void_p))

    # Convert list of paths to C-compatible array of byte strings
    files = [f.encode('utf-8') for f in args.files]
    arr = (ctypes.c_char_p * len(files))(*files)

    password_c = b''

    if args.password is not None:
        password_c = args.password.encode()

    if args.timetrap is not None:
        time_trap = args.timetrap
        gem_protocol = 2 # Auto protocol
    else:
        time_trap    = -1 # Time Trap disabled
        gem_protocol = 0 # Auto protocol

    # Prepare a c_uint64 variable to capture the output size
    out_ocean_size = ctypes.c_uint64()

    # Hide Gem Files in Ocean.
    # Returned GEM_OCEAN memory must be freed below!
    GEM_OCEAN = HIDEAGEM_CORE.HIDEAGEM_HIDE_GEMS_C(
        gem_protocol,
        ocean_ptr,
        ocean_size,
        ctypes.cast(arr, ctypes.POINTER(ctypes.POINTER(ctypes.c_char))),  # Assuming arr is an array of string pointers
        len(args.files),
        password_c,
        time_trap,
        ctypes.byref(out_ocean_size),  # Pass the reference to out_ocean_size
        args.validate
    )

    if not GEM_OCEAN:
        print("Gem Ocean is nullptr!")
        return

    if args.output is None: # Not saving Gem to disk
        print("No output directory specified. Gem not saved to disk.\n")
        return

    if not os.path.exists(args.output):
        print(f"Creating directory: {args.output}\n")
        os.makedirs(args.output)

    # Write Gem to disk
    base_name, _ = os.path.splitext(os.path.basename(args.ocean))  # Ignore the original extension
    output_file_path = os.path.join(args.output, f"{base_name}.png")
    counter = 1

    while os.path.exists(output_file_path):
        output_file_path = os.path.join(args.output, f"{base_name}_{counter}.png")
        counter += 1

    with open(output_file_path, 'wb') as output_file:
        output_file.write(bytearray((ctypes.c_uint8 * out_ocean_size.value).from_address(ctypes.addressof(GEM_OCEAN.contents))))

    #
    #    !!! FREE GEM OCEAN MEMORY !!!
    #

    HIDEAGEM_CORE.HIDEAGEM_FREE_OCEAN_C( GEM_OCEAN );

    print(f"SAVED GEM: {output_file_path}\n")

#
#    RUN UNIT TESTS
#

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

