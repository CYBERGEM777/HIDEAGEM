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
import torch
import ctypes
import secrets
import platform
import numpy as np

#
#    HIDEAGEM C LIBRARY
#

HIDEAGEM_CORE = None
current_dir = os.path.dirname(os.path.realpath(__file__))

lib_path = "HIDEAGEM"

if platform.system() == "Windows":
    lib_path += ".dll"
else:
    lib_path += ".so"

lib_path = os.path.join(current_dir, lib_path)

if platform.system() == "Windows":
    HIDEAGEM_CORE = ctypes.WinDLL(lib_path)
else:
    HIDEAGEM_CORE = ctypes.CDLL(lib_path)

#
#    HIDEAGEM C INTERFACE
#

HIDEAGEM_CORE.HIDEAGEM_HIDE_GEMS_C.argtypes = [
    ctypes.c_int,                       # gem_protocol
    ctypes.c_void_p,                    # ocean
    ctypes.c_uint64,                    # ocean_size
    ctypes.POINTER(ctypes.c_char_p),    # file_paths
    ctypes.c_int,                       # file_paths_length
    ctypes.c_char_p,                    # password
    ctypes.c_int,                       # time_trap
    ctypes.POINTER(ctypes.c_uint64),    # out_ocean_size
    ctypes.c_bool                       # b_validate
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

HIDEAGEM_CORE.HIDEAGEM_RUN_UNIT_TESTS_C.restype = ctypes.c_bool

# Memory management
HIDEAGEM_CORE.HIDEAGEM_FREE_OCEAN_C.argtypes = [ctypes.c_void_p]
HIDEAGEM_CORE.HIDEAGEM_FREE_OCEAN_C.restype = None

#
#    UTILITIES
#

def process_file_paths(input_string):
    # Split the string by new lines and commas
    paths = input_string.replace('\n', ',').split(',')

    # Remove single and double quotation marks and strip whitespace
    cleaned_paths = [path.strip().strip('\'"') for path in paths if path.strip()]

    return cleaned_paths

#
#    HIDEAGEM FIND NODE
#

class HideAGem_FindGems:
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "gem_image": ("IMAGE",),
                "password": ("STRING", {
                    "multiline": False, #True if you want the field to look like the one on the ClipTextEncode node
                    "default": ""
                }),

                "time_trap": (["disable", "enable"],),

                "output_directory": ("STRING", {
                    "multiline": False, #True if you want the field to look like the one on the ClipTextEncode node
                    "default": ""
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("GEM_IMAGE",)

    FUNCTION = "entry_point"

    #OUTPUT_NODE = False

    CATEGORY = "HIDEAGEM"

    # ENTRY POINT

    def entry_point(self, gem_image, password, time_trap, output_directory):

        output_directory = output_directory.strip('"')

        if len(output_directory) == 0:
            output_dir_c = ctypes.c_char_p()
        else:
            output_dir_c = output_directory.encode('utf-8')

        # Clone base image and convert to pointer
        in_ocean = (gem_image.clone().cpu().numpy() * 255).astype(np.uint8)
        in_ocean_pointer = in_ocean.ctypes.data_as(ctypes.POINTER(ctypes.c_void_p))

        num_ocean_bytes = gem_image.shape[1] * gem_image.shape[2] * gem_image.shape[3]
        
        password_c = password.encode('utf-8')

        b_time_trap = time_trap == "enable"

        HIDEAGEM_CORE.HIDEAGEM_FIND_GEMS_C(
            in_ocean_pointer,
            num_ocean_bytes,
            password_c,
            output_dir_c,
            b_time_trap
        )

        del password

        return (gem_image,)

#
#    HIDEAGEM AUTO HIDE
#

class HideAGem_AutoHide:
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {

                "gem_image": ("IMAGE",),

                "password": ("STRING", {
                    "multiline": False, #True if you want the field to look like the one on the ClipTextEncode node
                    "default": ""
                }),

                "time_trap_level": ("INT", {
                    "default": -1, 
                    "min": -1, #Minimum value
                    "max": 7, #Maximum value
                    "step": 1  #Slider's step
                }),

                "validate": (["enable", "disable"],),

                "gem_files": ("STRING", {
                    "multiline": True, #True if you want the field to look like the one on the ClipTextEncode node
                    "default": "Paste file paths here, one per line and/or comma separated."
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("GEM_IMAGE",)

    FUNCTION = "entry_point"

    #OUTPUT_NODE = False

    CATEGORY = "HIDEAGEM"

    # ENTRY POINT

    def entry_point(self, gem_image, password, time_trap_level, validate, gem_files):

        password_c = password.encode('utf-8')

        file_paths = process_file_paths(gem_files)

        file_paths_array = (ctypes.c_char_p * len(file_paths))(*[bytes(fp, 'utf-8') for fp in file_paths])

        out_ocean_size = ctypes.c_uint64()
        
        if time_trap_level > -1:
            gem_protocol_key = 2
        else:
            gem_protocol_key = 0

        # Clone base image and convert to pointer
        in_ocean = (gem_image.clone().cpu().numpy() * 255).astype(np.uint8)
        in_ocean_pointer = in_ocean.ctypes.data_as(ctypes.POINTER(ctypes.c_void_p))

        num_ocean_bytes = gem_image.shape[1] * gem_image.shape[2] * gem_image.shape[3]

        # HIDE GEM !!!
        out_ocean_pointer = HIDEAGEM_CORE.HIDEAGEM_HIDE_GEMS_C(
            ctypes.c_int(gem_protocol_key),
            in_ocean_pointer,
            ctypes.c_uint64(num_ocean_bytes),
            file_paths_array,
            ctypes.c_int(len(file_paths)),
            password_c,
            ctypes.c_int(time_trap_level),
            ctypes.byref(out_ocean_size),
            ctypes.c_bool(validate)
        )

        del password

        if not out_ocean_pointer or out_ocean_size.value == 0:
            raise Exception("Gem hide failed !!!")

        # To numpy array
        out_ocean_array_flat = np.ctypeslib.as_array(out_ocean_pointer, shape=(out_ocean_size.value,))
        
        # Reshape array
        expected_shape = gem_image.shape
        out_ocean_array = out_ocean_array_flat.reshape(expected_shape)

        # To tensor
        out_ocean = torch.from_numpy(out_ocean_array).to(dtype=torch.float32)
        out_ocean = out_ocean / 255.0
        
        #
        #    !!! FREE GEM OCEAN MEMORY !!!
        #

        HIDEAGEM_CORE.HIDEAGEM_FREE_OCEAN_C( out_ocean_pointer );

        return (out_ocean,)

#
#    HIDEAGEM AUTO HIDE + RANDOM PASSWORD
#

import random

def gen_random_password(bits_of_entropy: int) -> str:
    """
    Generates a random password using a base62 character set (A-Z, a-z, 0-9) with a minimum length necessary to satisfy the given bits of entropy.

    Parameters:
        bits_of_entropy (int): The target bits of entropy.

    Returns:
        str: The generated random password.
    """
    # Define the base62 character set
    base62_charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    
    # Calculate the entropy per character for the base62 set
    entropy_per_char = math.log2(len(base62_charset))
    
    # Calculate the minimum password length needed to achieve the target entropy
    min_length = math.ceil(bits_of_entropy / entropy_per_char)
    
    # Generate the random password
    return ''.join(secrets.choice(base62_charset) for _ in range(min_length))


class HideAGem_AutoHide_RandomPassword:
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {

                "gem_image": ("IMAGE",),

                "password_entropy": ("INT", {
                    "default": 512, 
                    "min": 256,  #Minimum value
                    "max": 512, #Maximum value
                    "step": 1 #Slider's step
                }),

                "time_trap_level": ("INT", {
                    "default": -1, 
                    "min": -1, #Minimum value
                    "max": 7, #Maximum value
                    "step": 1  #Slider's step
                }),

                "validate": (["enable", "disable"],),

                "gem_files": ("STRING", {
                    "multiline": True, #True if you want the field to look like the one on the ClipTextEncode node
                    "default": "Paste file paths here, one per line and/or comma separated."
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("GEM_IMAGE",)

    FUNCTION = "entry_point"

    #OUTPUT_NODE = False

    CATEGORY = "HIDEAGEM"

    # ENTRY POINT

    def entry_point(self, gem_image, password_entropy, time_trap_level, validate, gem_files):

        password = gen_random_password(password_entropy)
        password_c = password.encode('utf-8')

        file_paths = process_file_paths(gem_files)

        file_paths_array = (ctypes.c_char_p * len(file_paths))(*[bytes(fp, 'utf-8') for fp in file_paths])

        out_ocean_size = ctypes.c_uint64()
        
        if time_trap_level > -1:
            gem_protocol_key = 2
        else:
            gem_protocol_key = 0

        # Clone base image and convert to pointer
        in_ocean = (gem_image.clone().cpu().numpy() * 255).astype(np.uint8)
        in_ocean_pointer = in_ocean.ctypes.data_as(ctypes.POINTER(ctypes.c_void_p))

        num_ocean_bytes = gem_image.shape[1] * gem_image.shape[2] * gem_image.shape[3]

        # HIDE GEM !!!
        out_ocean_pointer = HIDEAGEM_CORE.HIDEAGEM_HIDE_GEMS_C(
            ctypes.c_int(gem_protocol_key),
            in_ocean_pointer,
            ctypes.c_uint64(num_ocean_bytes),
            file_paths_array,
            ctypes.c_int(len(file_paths)),
            password_c,
            ctypes.c_int(time_trap_level),
            ctypes.byref(out_ocean_size),
            ctypes.c_bool(validate)
        )

        if not out_ocean_pointer or out_ocean_size.value == 0:
            raise Exception("Gem hide failed !!!")

        print(f"Generated random Base62 password with {password_entropy} bits of entropy (estimated):\033[94m\n")
        print(password, "\033[0m\n")

        del password

        # To numpy array
        out_ocean_array_flat = np.ctypeslib.as_array(out_ocean_pointer, shape=(out_ocean_size.value,))
        
        # Reshape array
        expected_shape = gem_image.shape
        out_ocean_array = out_ocean_array_flat.reshape(expected_shape)

        # To tensor
        out_ocean = torch.from_numpy(out_ocean_array).to(dtype=torch.float32)
        out_ocean = out_ocean / 255.0
        
        #
        #    !!! FREE GEM OCEAN MEMORY !!!
        #

        HIDEAGEM_CORE.HIDEAGEM_FREE_OCEAN_C( out_ocean_pointer );

        return (out_ocean,)

#
#    HIDEAGEM UNIT TESTS
#

class HideAGem_UnitTests:
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {

                "ANY_IMAGE": ("IMAGE",),

                "LOOP": (["enable", "disable"],),

                "DEMO_MODE": (["enable", "disable"],),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("UNUSED",)

    FUNCTION = "entry_point"

    #OUTPUT_NODE = False

    CATEGORY = "HIDEAGEM"

    # ENTRY POINT

    def entry_point(self, ANY_IMAGE, LOOP, DEMO_MODE):

        if LOOP == "enable":
            b_loop = True
        elif LOOP == "disable":
            b_loop = False

        if DEMO_MODE == "enable":
            b_demo_mode = True
        elif DEMO_MODE == "disable":
            b_demo_mode = False

        # Run unit tests !!!
        HIDEAGEM_CORE.HIDEAGEM_RUN_UNIT_TESTS_C(
            b_loop,
            b_demo_mode
        )

        return (ANY_IMAGE,)

#
#    HIDEAGEM SAVE IMAGE
#

import json
import folder_paths
from PIL import Image, ImageOps
from PIL.PngImagePlugin import PngInfo

class HideAGem_SaveImage:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""

    @classmethod
    def INPUT_TYPES(s):
        return {"required": 
                    {"images": ("IMAGE", ),
                     "filename_prefix": ("STRING", {"default": "HIDEAGEM"})},
                     "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"}, # UNUSED
                }

    RETURN_TYPES = ()
    FUNCTION = "save_images"

    OUTPUT_NODE = True

    CATEGORY = "HIDEAGEM"

    def save_images(self, images, filename_prefix="HIDEAGEM", prompt=None, extra_pnginfo=None):

        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])
        results = list()

        for image in images:

            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            metadata = PngInfo() # EMPTY METADATA

            file = f"{filename}_{counter:05}_.png"

            img.save(os.path.join(full_output_folder, file), pnginfo=metadata, compress_level=4)

            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type
            })

            counter += 1

        return { "ui": { "images": results } }


