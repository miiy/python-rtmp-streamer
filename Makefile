TARGET=rtmp_streamer
UNAME=$(shell uname)

ifeq ($(UNAME),Darwin) # macOS
	PLAT_NAME=macosx_11_0_intel
	BUILD_CMD := @ARCHFLAGS="-arch x86_64" python setup_build.py build_ext
else ifeq ($(UNAME),Linux)
	PLAT_NAME=manylinux1_x86_64
	BUILD_CMD := python setup_build.py build_ext
endif

.PHONY: build
build:
#	use cpython build extension
#	https://cython.readthedocs.io/en/latest/src/userguide/source_files_and_compilation.html#compilation
#	@ARCHFLAGS="-arch x86_64" python setup.py build_ext --inplace
	@echo "Building for $(PLAT_NAME)..."
	$(BUILD_CMD)
	@mkdir -p build/$(TARGET)
	@cp -r build/lib.*/$(TARGET) build/
	@cp src/$(TARGET)/__init__.py build/$(TARGET)
	@cp src/$(TARGET)/*.pyi build/$(TARGET)
#	build wheel
	@python setup_build.py bdist_wheel --plat-name=$(PLAT_NAME)
	@echo "Build complete."

.PHONY: clean
clean:
	@echo "Cleaning up..."
	@python setup.py clean --all
	@rm -rf build
	@rm -rf src/*.egg-info
	@rm -f src/$(TARGET)/*.c
	@rm -rf dist
	@echo "Clean complete."

.PHONY: help
help:
	@echo "make build: build project"
	@echo "make clean: clean build file"
