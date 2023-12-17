# Compiler settings
CXX = g++
CXXFLAGS = -std=c++17 -fPIC

# Directories
OUTPUT_DIR = bin/
FOLDER = HIDEAGEM
DEP_DIR = dependencies/
BUILD_DIR = builds/
TEMP_DIR = $(BUILD_DIR)$(FOLDER)/

# Dependency paths
LIBSODIUM_DIR = $(DEP_DIR)libsodium
MINIZ_DIR = $(DEP_DIR)miniz
LIBUTF8PROC_DIR = $(DEP_DIR)utf8proc

# Dependency library files
LIBSODIUM = $(LIBSODIUM_DIR)/src/libsodium/.libs/libsodium.a
LIBMINIZ = $(MINIZ_DIR)/libminiz.a  # Adjust if the output name is different
LIBUTF8PROC = $(LIBUTF8PROC_DIR)/libutf8proc.a

# Include paths
INCLUDES = -I./include \
           -I./$(LIBSODIUM_DIR)/src/libsodium/include \
           -I./$(MINIZ_DIR) \
           -I./$(LIBUTF8PROC_DIR)

# Source and target
SOURCE = src/HIDEAGEM_CORE.cpp
TARGET = $(OUTPUT_DIR)HIDEAGEM.so
PACKAGE = HIDEAGEM_Linux64.tar.gz

# CMake flags
CMAKE_FLAGS = -DBUILD_TESTS=OFF
CMAKE_C_FLAGS = -fPIC

all: $(LIBSODIUM) $(LIBMINIZ) $(LIBUTF8PROC) $(TARGET) package

$(LIBSODIUM):
	cd $(LIBSODIUM_DIR) && git reset --hard && ./configure --with-pic="yes" && make

$(LIBMINIZ):
	cd $(MINIZ_DIR) && git reset --hard && git clean -f
	cd $(MINIZ_DIR) && cmake $(CMAKE_FLAGS) -DCMAKE_C_FLAGS=$(CMAKE_C_FLAGS) . && make

$(LIBUTF8PROC):
	cd $(LIBUTF8PROC_DIR) && git reset --hard && make

$(TARGET): $(SOURCE)
	mkdir -p $(OUTPUT_DIR)
	$(CXX) $(CXXFLAGS) $(INCLUDES) -shared -o $(TARGET) $(SOURCE) $(LIBSODIUM) $(LIBMINIZ) $(LIBUTF8PROC)

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

.PHONY: all clean package
