CXX ?= g++

SDK_DIR := rplidar_sdk
SDK_BUILD := $(SDK_DIR)/output/Linux/Release
SDK_LIB := $(SDK_BUILD)/libsl_lidar_sdk.a

CXXFLAGS += -std=c++11 -O2 -Wall -Wextra
CXXFLAGS += -I$(SDK_DIR)/sdk/include -I$(SDK_DIR)/sdk/src
LDLIBS += $(SDK_LIB) -lpthread

.PHONY: all sdk clean

all: rplidar_stream rplidar_check

sdk:
	$(MAKE) -C $(SDK_DIR)

rplidar_stream: rplidar_stream.cpp $(SDK_LIB)
	$(CXX) $(CXXFLAGS) -o $@ $< $(LDLIBS)

rplidar_check: rplidar_check.cpp $(SDK_LIB)
	$(CXX) $(CXXFLAGS) -o $@ $< $(LDLIBS)

$(SDK_LIB):
	$(MAKE) -C $(SDK_DIR)

clean:
	rm -f rplidar_stream rplidar_check
