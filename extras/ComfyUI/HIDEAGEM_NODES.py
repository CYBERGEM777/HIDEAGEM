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
import torch
import ctypes
import secrets
import numpy as np

#
#    HIDEAGEM C INTERFACE
#

current_dir = os.path.dirname(os.path.realpath(__file__))
dll_name = "HIDEAGEM.dll"
dll_path = os.path.join(current_dir, dll_name)

HIDEAGEM_CORE = ctypes.WinDLL(dll_path)

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
HIDEAGEM_CORE.HIDEAGEM_RUN_UNIT_TESTS_C.restype = ctypes.c_bool

#
#    GEM KIT
#

class HideAGemKit:

    def __init__(self, gem_protocol, base_image, passwords, output_dir=None):
        self.gem_protocol = gem_protocol
        self.passwords = passwords
        self.output_dir = output_dir
        self.base_image = base_image
        # NOTE: clone() always creates a contiguous tensor
        self.gem_img = None
        self.gem_img_bytes = (base_image.clone().cpu().numpy() * 255).astype(np.uint8)
        self.trailmap_img = base_image.clone().cpu().numpy()
        self.debug_img = torch.zeros(base_image.shape, dtype=torch.float32, device="cpu").numpy()
        self.mask_img = torch.zeros((base_image.size(1), base_image.size(2)), dtype=torch.float32, device="cpu").numpy()
        self.b_validate = False
        self.b_loop = False
        self.b_demo_mode = False


    def set_validate(self, comfyui_bool):
        if not isinstance(comfyui_bool, str):
            raise Exception("HideAGemKit set_validate() expects a string argument with value 'enable' or 'disable'")
        elif comfyui_bool == "enable":
            self.b_validate = True
        elif comfyui_bool == "disable":
            self.b_validate = False
        else:
            raise Exception("HideAGemKit set_validate() expects a string argument with value 'enable' or 'disable'")

    def set_loop(self, comfyui_bool):
        if not isinstance(comfyui_bool, str):
            raise Exception("HideAGemKit set_loop() expects a string argument with value 'enable' or 'disable'")
        elif comfyui_bool == "enable":
            self.b_loop = True
        elif comfyui_bool == "disable":
            self.b_loop = False
        else:
            raise Exception("HideAGemKit set_loop() expects a string argument with value 'enable' or 'disable'")

    def set_demo_mode(self, comfyui_bool):
        if not isinstance(comfyui_bool, str):
            raise Exception("HideAGemKit set_demo_mode() expects a string argument with value 'enable' or 'disable'")
        elif comfyui_bool == "enable":
            self.b_demo_mode = True
        elif comfyui_bool == "disable":
            self.b_demo_mode = False
        else:
            raise Exception("HideAGemKit set_demo_mode() expects a string argument with value 'enable' or 'disable'")

    def get_ocean_type(self):
        return 1 # OceanType::IMAGE_RGB

    def get_num_ocean_bytes(self):
        return self.base_image.shape[1] * self.base_image.shape[2] * self.base_image.shape[3]

    def get_image_height(self):
        return self.base_image.shape[1]

    def get_image_width(self):
        return self.base_image.shape[2]

    def get_image_size(self):
        return self.base_image.size

    def get_gem_image(self):
        self.gem_img = torch.from_numpy(self.gem_img_bytes).to(dtype=torch.float32)
        # Normalize the tensor to the range 0 to 1
        self.gem_img = self.gem_img / 255.0
        return self.gem_img

    def get_gem_image_c(self):
        return self.gem_img_bytes.ctypes.data_as(ctypes.POINTER(ctypes.c_void_p))

    def get_trailmap_image(self):
        return torch.tensor(self.trailmap_img)

    def get_debug_image(self):
        return torch.tensor(self.debug_img)

    def get_mask_image(self):
        return torch.tensor(self.mask_img)


    def gen_grid_image(self):
        grid_image = self.base_image
        grid_image = torch.cat((grid_image, self.get_gem_image()), dim=2) # Horizontal concat
        grid_image = torch.cat((grid_image, torch.cat((self.get_trailmap_image(), self.get_debug_image()), dim=2)), dim=1) # Vertical concat

        return grid_image

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

                "time_trap": (["enable", "disable"],),

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

        gem_kit = HideAGemKit(0, gem_image, [password], output_directory)
        
        password_c = password.encode('utf-8')

        b_time_trap = time_trap == "enable"

        HIDEAGEM_CORE.HIDEAGEM_FIND_GEMS_C(
            gem_kit.get_gem_image_c(),
            gem_kit.get_num_ocean_bytes(),
            gem_kit.get_ocean_type(),
            password_c,
            output_dir_c,
            b_time_trap
        )

        del gem_kit.passwords
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
                    "default": "Paste file paths here, one per line."
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

        # Gem Protocol 0 is auto mode
        gem_kit = HideAGemKit(0, gem_image, [password])
        gem_kit.set_validate(validate)

        file_paths = process_file_paths(gem_files)

        password_c = password.encode('utf-8')

        file_paths_c_char_arrays = [ctypes.create_string_buffer(path.encode('utf-8')) for path in file_paths]

        file_paths_pointers = (ctypes.POINTER(ctypes.c_char) * len(file_paths))(*[ctypes.cast(path, ctypes.POINTER(ctypes.c_char)) for path in file_paths_c_char_arrays])

        file_paths_array = ctypes.cast(file_paths_pointers, ctypes.POINTER(ctypes.POINTER(ctypes.c_char)))
        
        if time_trap_level > -1:
            gem_protocol_key = 2
        else:
            gem_protocol_key = 0
        
        # HIDE GEM !!!
        b_hid_gem = HIDEAGEM_CORE.HIDEAGEM_HIDE_GEMS_C(
            gem_protocol_key,
            gem_kit.get_gem_image_c(),
            gem_kit.get_num_ocean_bytes(),
            gem_kit.get_ocean_type(),
            file_paths_array,
            len(file_paths),
            password_c,
            time_trap_level,
            validate
        )

        del gem_kit.passwords
        del password

        if not b_hid_gem:
            raise Exception("Gem hide failed !!!")

        return (gem_kit.get_gem_image(),)

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
                    "default": "Paste file paths here, one per line."
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

        # Gem Protocol 0 is auto mode
        gem_kit = HideAGemKit(0, gem_image, [password])
        gem_kit.set_validate(validate)

        file_paths = process_file_paths(gem_files)

        password_c = password.encode('utf-8')

        file_paths_c_char_arrays = [ctypes.create_string_buffer(path.encode('utf-8')) for path in file_paths]

        file_paths_pointers = (ctypes.POINTER(ctypes.c_char) * len(file_paths))(*[ctypes.cast(path, ctypes.POINTER(ctypes.c_char)) for path in file_paths_c_char_arrays])

        file_paths_array = ctypes.cast(file_paths_pointers, ctypes.POINTER(ctypes.POINTER(ctypes.c_char)))
        
        if time_trap_level > -1:
            gem_protocol_key = 2
        else:
            gem_protocol_key = 0

        # HIDE GEM !!!
        b_hid_gem = HIDEAGEM_CORE.HIDEAGEM_HIDE_GEMS_C(
            gem_protocol_key,
            gem_kit.get_gem_image_c(),
            gem_kit.get_num_ocean_bytes(),
            gem_kit.get_ocean_type(),
            file_paths_array,
            len(file_paths),
            password_c,
            time_trap_level,
            validate
        )

        if not b_hid_gem:
            raise Exception("Gem hide failed !!!")

        print(f"Generated random Base62 password with {password_entropy} bits of entropy (estimated):\033[94m\n")
        print(password, "\033[0m\n")

        del gem_kit.passwords
        del password

        return (gem_kit.get_gem_image(),)

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

        gem_kit = HideAGemKit(0, ANY_IMAGE, ["CYBERGEM"])
        gem_kit.set_loop(LOOP)
        gem_kit.set_demo_mode(DEMO_MODE)

        # Run unit tests !!!
        HIDEAGEM_CORE.HIDEAGEM_RUN_UNIT_TESTS_C(
            gem_kit.b_loop,
            gem_kit.b_demo_mode
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


