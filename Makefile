# Compiler settings
CXX = g++
EMCXX = emcc
CXXFLAGS = -std=c++17 -fPIC -Wfatal-errors
EMCXXFLAGS = -std=c++17 -s WASM=1 -Wfatal-errors -s INITIAL_MEMORY=72MB -s ALLOW_MEMORY_GROWTH=1 \
             -s EXPORTED_FUNCTIONS='["_HIDEAGEM_RUN_UNIT_TESTS_C", "_HIDEAGEM_ACTIVATE_DEMO_MODE_C", "_HIDEAGEM_HIDE_GEM_FILES_32_BIT_C", "_HIDEAGEM_HIDE_GEMS_32_BIT_C", "_HIDEAGEM_FIND_GEMS_32_BIT_C", "_HIDEAGEM_GET_NUM_GEM_FILES_C", "_HIDEAGEM_GET_GEM_FILE_DATA_C", "_HIDEAGEM_GET_GEM_FILE_SIZE_C", "_HIDEAGEM_GET_GEM_FILE_NAME_C", "_HIDEAGEM_EMPTY_GEM_FILES_C", "_HIDEAGEM_PRINT_SPLASH_SCREEN_C", "_malloc", "_free"]' \
             -s EXPORTED_RUNTIME_METHODS=stringToUTF8 \
             -s DISABLE_EXCEPTION_CATCHING=0
LDFLAGS =

# Directories
OUTPUT_DIR = bin/
WASM_OUTPUT_DIR = wasm/
FOLDER = HIDEAGEM
DEP_DIR = dependencies/
BUILD_DIR = builds/
TEMP_DIR = $(BUILD_DIR)$(FOLDER)/

# Dependency paths
LIBSODIUM_DIR = $(DEP_DIR)libsodium
MINIZ_DIR = $(DEP_DIR)miniz
LIBUTF8PROC_DIR = $(DEP_DIR)utf8proc
STB_DIR = $(DEP_DIR)stb

# Dependency library files
LIBSODIUM = $(LIBSODIUM_DIR)/src/libsodium/.libs/libsodium.a
LIBSODIUM_WASM = $(LIBSODIUM_DIR)/src/libsodium/.libs/libsodium_wasm.a
LIBMINIZ = $(MINIZ_DIR)/libminiz.a
LIBMINIZ_WASM = $(MINIZ_DIR)/libminiz_wasm.a
LIBUTF8PROC = $(LIBUTF8PROC_DIR)/libutf8proc.a
LIBUTF8PROC_WASM = $(LIBUTF8PROC_DIR)/libutf8proc_wasm.a

# Include paths
INCLUDES = -I./include \
           -I./$(LIBSODIUM_DIR)/src/libsodium/include \
           -I./$(MINIZ_DIR) \
           -I./$(LIBUTF8PROC_DIR) \
           -I./$(STB_DIR)

# Source and target
SOURCE = $(wildcard src/*.cpp)
TARGET = $(OUTPUT_DIR)HIDEAGEM.so
WASM_TARGET = $(WASM_OUTPUT_DIR)HIDEAGEM.js
PACKAGE = HIDEAGEM_Linux64.tar.gz

# CMake flags
CMAKE_FLAGS = -DBUILD_TESTS=OFF
CMAKE_C_FLAGS = -fPIC

# Specify the host system type (Emscripten target)
EM_HOST = wasm32-unknown-emscripten

all: $(LIBSODIUM) $(LIBMINIZ) $(LIBUTF8PROC) $(TARGET) package

# Emscripten-specific build
wasm: export EMSCRIPTEN=1
wasm: $(LIBSODIUM_WASM) $(LIBMINIZ_WASM) $(LIBUTF8PROC_WASM) $(WASM_TARGET) wasm_package

$(LIBSODIUM):
	cd $(LIBSODIUM_DIR) && git reset --hard && git clean -f
	cd $(LIBSODIUM_DIR) && ./configure --with-pic=yes && make

# Emscripten-specific commands for libsodium
$(LIBSODIUM_WASM):
	cd $(LIBSODIUM_DIR) && git reset --hard && git clean -f
	cd $(LIBSODIUM_DIR) && emconfigure ./configure --with-pic=yes --host=$(EM_HOST) --disable-ssp && emmake make
	mv $(LIBSODIUM) $(LIBSODIUM_WASM)

$(LIBMINIZ):
	cd $(MINIZ_DIR) && git reset --hard && git clean -f
	cd $(MINIZ_DIR) && cmake $(CMAKE_FLAGS) -DCMAKE_C_FLAGS=$(CMAKE_C_FLAGS) . && make

# Emscripten-specific commands for miniz
$(LIBMINIZ_WASM):
	cd $(MINIZ_DIR) && git reset --hard && git clean -f
	cd $(MINIZ_DIR) && emmake cmake $(CMAKE_FLAGS) -DCMAKE_C_FLAGS=$(CMAKE_C_FLAGS) . && emmake make
	mv $(LIBMINIZ) $(LIBMINIZ_WASM)

$(LIBUTF8PROC):
	cd $(LIBUTF8PROC_DIR) && git reset --hard && git clean -f
	cd $(LIBUTF8PROC_DIR) && make

# Emscripten-specific commands for utf8proc
$(LIBUTF8PROC_WASM):
	cd $(LIBUTF8PROC_DIR) && git reset --hard && git clean -f
	cd $(LIBUTF8PROC_DIR) && emmake make
	mv $(LIBUTF8PROC) $(LIBUTF8PROC_WASM)

$(TARGET): $(SOURCE)
	mkdir -p $(OUTPUT_DIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) -shared -o $(TARGET) $(SOURCE) $(LIBSODIUM) $(LIBMINIZ) $(LIBUTF8PROC)

$(WASM_TARGET): $(SOURCE)
	mkdir -p $(WASM_OUTPUT_DIR)
	$(EMCXX) $(EMCXXFLAGS) $(INCLUDES) -o $(WASM_TARGET) $(LDFLAGS) $(SOURCE) $(LIBSODIUM_WASM) $(LIBMINIZ_WASM) $(LIBUTF8PROC_WASM)

wasm_package:
	@echo "Packaging for WASM not implemented"

package:
#   Package into .tar.gz
	mkdir -p $(TEMP_DIR)
	cp HIDEAGEM.py LICENSE README.md requirements.txt $(TEMP_DIR)
	cp $(TARGET) $(TEMP_DIR)
	cp -r extras/ComfyUI/* $(TEMP_DIR)
	tar -czvf $(OUTPUT_DIR)$(PACKAGE) -C $(BUILD_DIR) $(FOLDER)
	rm -rf $(TEMP_DIR)

clean:
	rm -f $(TARGET)
	rm -f $(PACKAGE)
	rm -rf $(TEMP_DIR)
	cd $(LIBSODIUM_DIR) && make clean
	cd $(MINIZ_DIR) && make clean
	cd $(LIBUTF8PROC_DIR) && make clean
	
clean_wasm:
	rm -f $(WASM_TARGET)
	rm -f $(WASM_OUTPUT_DIR)HIDEAGEM.wasm

.PHONY: all clean package wasm wasm_package

